"""
PLEXIS v6 — All fixes: GAT attention, 40% feature regression with 15 targets,
256d embedding (128+128), 200 epochs with early stopping, expanded OD_FLOW.
NO log transform — raw features proven better.
"""
import time, json, os, warnings
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.decomposition import PCA
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, normalized_mutual_info_score
from sklearn.cluster import KMeans
from scipy.stats import spearmanr
from collections import Counter, defaultdict
import zipfile, csv, io
warnings.filterwarnings('ignore')

t0 = time.time()
def tick(m): print(f"[{time.time()-t0:6.1f}s] {m}", flush=True)

DATA = "data"
OUT = f"{DATA}/plexis"

tick("Loading...")
trips = pd.read_parquet(f"{OUT}/plexis_triplets_v2.parquet")
pl = pd.read_parquet(f"{DATA}/places_consolidated/sgp_places_featured.parquet")
h8 = pd.read_parquet(f"{DATA}/hex_v10/hex8_final.parquet").set_index("hex8_id")
h9 = pd.read_parquet(f"{DATA}/hex_v10/hex9_final.parquet").set_index("hex_id")

# ============================================================
# FIX 5: Expand OD_FLOW edges (top-20 per station instead of top-5)
# ============================================================
tick("Expanding OD_FLOW edges...")
od_path = f"{DATA}/lta_live/pv_train_202601.zip"
new_od = []
if os.path.exists(od_path):
    try:
        # Use the OD file we already processed
        od_existing = trips[trips['relation']=='OD_FLOW']
        existing_pairs = set(zip(od_existing['head'], od_existing['tail']))
        
        # Try to get more from the zip
        od_zip = f"{DATA}/lta_live/od_train_202512.zip"
        if os.path.exists(od_zip):
            with zipfile.ZipFile(od_zip) as z:
                with z.open(z.namelist()[0]) as f:
                    od = pd.read_csv(f)
            if 'DAY_TYPE' in od.columns:
                od = od[od['DAY_TYPE']=='WEEKDAY']
            trip_col = [c for c in od.columns if 'TOTAL' in c.upper() or 'TRIP' in c.upper()]
            if trip_col:
                od['trips'] = pd.to_numeric(od[trip_col[0]], errors='coerce').fillna(0)
                # Top-20 per origin (was top-5)
                for orig, group in od.groupby('ORIGIN_PT_CODE'):
                    top20 = group.nlargest(20, 'trips')
                    for _, row in top20.iterrows():
                        h = f"STN_{orig}"; t = f"STN_{row['DESTINATION_PT_CODE']}"
                        if (h, t) not in existing_pairs and row['trips'] > 50:
                            new_od.append({'head': h, 'relation': 'OD_FLOW', 'tail': t, 'daily_trips': round(row['trips']/22)})
    except Exception as e:
        tick(f"  OD expansion error: {e}")

if new_od:
    trips = pd.concat([trips, pd.DataFrame(new_od)], ignore_index=True)
    tick(f"  Added {len(new_od)} new OD_FLOW edges (total now {len(trips):,})")
else:
    tick(f"  No new OD edges added")

# Build indices
all_nodes = sorted(set(trips['head']) | set(trips['tail']))
node2id = {n:i for i,n in enumerate(all_nodes)}
N = len(all_nodes)
all_rels = sorted(trips['relation'].unique())
rel2id = {r:i for i,r in enumerate(all_rels)}
R = len(all_rels)
tick(f"  {N:,} nodes, {R} relations, {len(trips):,} edges")

# Edge weights (same as v5)
EDGE_WEIGHTS = {
    'COMPETES_WITH':6.0,'IS_A':6.0,'SYNERGIZES_WITH':4.0,'SUBSTITUTES_FOR':4.0,
    'SAME_BRAND':5.0,'EXIT_FRONTAGE':3.5,'VOID_DECK_OF':3.0,
    'SUPPLY_HIGH':4.0,'SUPPLY_LOW':4.0,'SUPPLY_OK':1.0,'PRICE_POSITIONED':3.0,
    'UNDERSUPPLIED':3.5,'OVERSUPPLIED':3.5,
    'ANCHORED_BY':2.5,'OD_FLOW':3.0,'FEEDS_INTO':2.0,'CONNECTS_TO':2.0,
    'SERVES':1.5,'WALK_CATCHMENT':1.5,
    'SAME_CORRIDOR':2.0,'COMMERCIAL_GRADIENT':2.0,'PRICE_GRADIENT':2.0,
    'LU_TRANSITION':2.0,'SAME_CLUSTER':1.5,
    'ROAD_CONNECTED':1.0,'EXPRESSWAY_CONNECTED':1.0,'EXPRESSWAY_CORRIDOR':1.0,
    'BUS_CORRIDOR':1.0,'DEVELOPMENT_FRONT':1.0,'COASTAL':1.0,
    'NORTH_OF':0.8,'SOUTH_OF':0.8,'EAST_OF':0.8,'WEST_OF':0.8,
    'LOCATED_IN':0.6,'PARENT_OF':0.3,'PART_OF':0.3,'ADJACENT_TO':0.3,
    'DENSITY_GRADIENT':1.5,'HEIGHT_GRADIENT':1.5,'BARRIER_BETWEEN':1.5,
    'WORKER_INFLOW':2.0,'DEMAND_LEAKS_TO':2.5,'COMPARABLE_TO':2.0,
    'RESIDENTIAL_DEMAND_TO':2.0,'SYNERGY_PAIR':3.0,'SUBSTITUTES':3.0,
}
UNDIRECTED = {'ADJACENT_TO','COMPETES_WITH','SYNERGIZES_WITH','SUBSTITUTES_FOR',
              'COMPARABLE_TO','CONNECTS_TO','SYNERGY_PAIR','SUBSTITUTES','SAME_BRAND',
              'SAME_CORRIDOR','SAME_CLUSTER','ROAD_CONNECTED','EXPRESSWAY_CONNECTED',
              'EXPRESSWAY_CORRIDOR','BUS_CORRIDOR'}

edges_per_rel = {}; edge_weights = {}
for rel in all_rels:
    sub = trips[trips['relation']==rel]
    src = torch.tensor([node2id[h] for h in sub['head'] if h in node2id], dtype=torch.long)
    dst = torch.tensor([node2id[t] for t in sub['tail'] if t in node2id], dtype=torch.long)
    ml = min(len(src),len(dst)); src=src[:ml]; dst=dst[:ml]
    rid = rel2id[rel]; w = EDGE_WEIGHTS.get(rel, 1.0)
    edges_per_rel[rid] = (src, dst); edge_weights[rid] = w
    if rel in UNDIRECTED:
        edges_per_rel[rid+R] = (dst, src); edge_weights[rid+R] = w

# ============================================================
# PCA 64d features (RAW — no log transform)
# ============================================================
tick("PCA features (raw, no transform)...")
FEAT_DIM = 64
pid_map = {pid:i for i,pid in enumerate(pl['place_id'])}
pl_num = [c for c in pl.select_dtypes(include=[np.number]).columns if c not in ['latitude','longitude']]
pca_pl = PCA(n_components=min(32, len(pl_num))); pl_pca = pca_pl.fit_transform(pl[pl_num].fillna(0).values)
h9_num = [c for c in h9.select_dtypes(include=[np.number]).columns if c not in ['lat','lng']]
pca_h9 = PCA(n_components=min(32, len(h9_num))); h9_pca = pca_h9.fit_transform(h9[h9_num].fillna(0).values)
h9_idx_list = list(h9.index); h8_idx_list = list(h8.index)
h8_num = [c for c in h8.select_dtypes(include=[np.number]).columns if c not in ['lat','lng']]
pca_h8 = PCA(n_components=min(32, len(h8_num))); h8_pca = pca_h8.fit_transform(h8[h8_num].fillna(0).values)

X = torch.zeros(N, FEAT_DIM); n_init = 0
for node, idx in node2id.items():
    if node in pid_map: X[idx,:32]=torch.tensor(pl_pca[pid_map[node]],dtype=torch.float32); n_init+=1
    elif node in h9.index: X[idx,32:]=torch.tensor(h9_pca[h9_idx_list.index(node)],dtype=torch.float32); n_init+=1
    elif node in h8.index: X[idx,32:]=torch.tensor(h8_pca[h8_idx_list.index(node)],dtype=torch.float32); n_init+=1
Xm=X.mean(0,keepdim=True);Xs=X.std(0,keepdim=True);Xs[Xs<1e-6]=1;X=(X-Xm)/Xs

# Category labels
cat_names = sorted(pl['main_category'].unique()); cat2label={c:i for i,c in enumerate(cat_names)}; NUM_CATS=len(cat_names)
cat_labels = torch.full((N,),-1,dtype=torch.long)
for _,row in pl.iterrows():
    nid=node2id.get(row['place_id'])
    if nid is not None: cat_labels[nid]=cat2label[row['main_category']]
place_mask=cat_labels>=0; place_indices=torch.where(place_mask)[0]

# FIX 2: Expanded regression targets (15 instead of 5)
target_cols=['competitors_200m','anchor_score','demand_context_score','transit_score','survivability_index',
             'complementary_diversity','total_places_300m','pull_office','pull_residential','pull_transit',
             'nwalk_mrt_score','nwalk_bus_score','catchment_pop','catchment_elderly','context_score']
target_cols=[c for c in target_cols if c in pl.columns]
tick(f"  Regression targets: {len(target_cols)}")

pl_targets=torch.zeros(N,len(target_cols))
for _,row in pl.iterrows():
    nid=node2id.get(row['place_id'])
    if nid is not None:
        for j,c in enumerate(target_cols):
            v=row.get(c,0); pl_targets[nid,j]=float(v) if pd.notna(v) else 0
t_mean=pl_targets[place_mask].mean(0,keepdim=True);t_std=pl_targets[place_mask].std(0,keepdim=True);t_std[t_std<1e-6]=1
pl_targets=(pl_targets-t_mean)/t_std

tick(f"  {n_init:,} nodes initialized ({FEAT_DIM}d)")

# ============================================================
# FIX 1+3: GAT-style attention + 256d embedding (128+128)
# ============================================================
tick("Building GAT-R-GCN model (256d)...")

class GATRGCNLayer(nn.Module):
    def __init__(self, hidden_dim, n_heads=4, dropout=0.2):
        super().__init__()
        self.n_heads = n_heads
        head_dim = hidden_dim // n_heads
        self.W_self = nn.Linear(hidden_dim, hidden_dim, bias=False)
        self.W_msg = nn.Linear(hidden_dim, hidden_dim, bias=False)
        # Attention: per-head scoring
        self.attn = nn.Linear(2 * head_dim, 1, bias=False)
        self.norm = nn.LayerNorm(hidden_dim)
        self.dropout = nn.Dropout(dropout)
        self.head_dim = head_dim
    
    def forward(self, h, edges_per_rel, edge_weights):
        out = self.W_self(h)
        msg_sum = torch.zeros_like(out)
        msg_count = torch.zeros(h.shape[0], 1)
        
        for rid, (src, dst) in edges_per_rel.items():
            if len(src) == 0: continue
            w = edge_weights.get(rid, 1.0)
            
            h_src = self.W_msg(h[src])
            h_dst = h[dst]
            
            # Simple attention: dot product between src and dst per head
            # Reshape to heads
            B = len(src)
            hs = h_src.view(B, self.n_heads, self.head_dim)
            hd = h_dst.view(B, self.n_heads, self.head_dim)
            
            # Attention scores
            attn_input = torch.cat([hs, hd], dim=-1)  # B x n_heads x 2*head_dim
            attn_scores = self.attn(attn_input).squeeze(-1)  # B x n_heads
            attn_weights = torch.sigmoid(attn_scores).mean(dim=1, keepdim=True)  # B x 1
            
            messages = h_src * w * attn_weights
            msg_sum.index_add_(0, dst, messages)
            msg_count.index_add_(0, dst, torch.full((len(dst), 1), w))
        
        msg_count = msg_count.clamp(min=1)
        h = out + msg_sum / msg_count
        h = self.dropout(F.relu(self.norm(h)))
        return h

class PlexisV6(nn.Module):
    def __init__(self, in_dim, hidden_dim, spatial_dim, commercial_dim, num_cats, num_targets, num_layers=4, n_heads=4):
        super().__init__()
        self.input_proj = nn.Linear(in_dim, hidden_dim)
        self.layers = nn.ModuleList([GATRGCNLayer(hidden_dim, n_heads) for _ in range(num_layers)])
        self.spatial_head = nn.Linear(hidden_dim, spatial_dim)
        self.commercial_head = nn.Linear(hidden_dim, commercial_dim)
        self.category_head = nn.Linear(commercial_dim, num_cats)
        self.regression_head = nn.Linear(hidden_dim, num_targets)
    
    def forward(self, x, edges_per_rel, edge_weights):
        h = F.relu(self.input_proj(x))
        for layer in self.layers:
            h = layer(h, edges_per_rel, edge_weights)
        spatial = self.spatial_head(h)
        commercial = self.commercial_head(h)
        return (torch.cat([spatial, commercial], dim=1), spatial, commercial,
                self.category_head(commercial), self.regression_head(h))

# FIX 3: 256d (128+128) instead of 128d (64+64)
HIDDEN = 192; SPATIAL_DIM = 128; COMMERCIAL_DIM = 128; NUM_LAYERS = 4; N_HEADS = 4
model = PlexisV6(FEAT_DIM, HIDDEN, SPATIAL_DIM, COMMERCIAL_DIM, NUM_CATS, len(target_cols), NUM_LAYERS, N_HEADS)
tick(f"  Model: {sum(p.numel() for p in model.parameters()):,} params, {SPATIAL_DIM}+{COMMERCIAL_DIM}={SPATIAL_DIM+COMMERCIAL_DIM}d")

# ============================================================
# FIX 2+4: Training — 40% regression, 200 epochs, early stopping
# ============================================================
tick("Training (200 epochs, 40% regression, attention)...")
optimizer = torch.optim.Adam(model.parameters(), lr=0.001, weight_decay=1e-5)
scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=200, eta_min=1e-5)

all_src = torch.cat([s for s,d in edges_per_rel.values()])
all_dst = torch.cat([d for s,d in edges_per_rel.values()])
EPOCHS = 200; SAMPLE = 50000

best_loss = float('inf'); patience = 30; no_improve = 0

for epoch in range(EPOCHS):
    model.train()
    perm = torch.randperm(len(all_src))[:SAMPLE]
    pos_src=all_src[perm]; pos_dst=all_dst[perm]; neg_dst=torch.randint(0,N,(SAMPLE,))
    
    full_emb,_,comm_emb,cat_logits,reg_pred = model(X, edges_per_rel, edge_weights)

    # Link
    loss_link = -F.logsigmoid((full_emb[pos_src]*full_emb[pos_dst]).sum(1) - (full_emb[pos_src]*full_emb[neg_dst]).sum(1)).mean()

    # Contrastive
    si = place_indices[torch.randperm(len(place_indices))[:600]]
    sc=comm_emb[si]; sl=cat_labels[si]
    sm=torch.mm(sc,sc.t()); cm=(sl.unsqueeze(0)==sl.unsqueeze(1)).float(); cm.fill_diagonal_(0)
    ps=sm[cm>0].mean() if (cm>0).any() else torch.tensor(0.0)
    ns=sm[cm==0].mean() if (cm==0).any() else torch.tensor(0.0)
    loss_contrast=-F.logsigmoid(ps-ns) if ps.item()!=0 else torch.tensor(0.0)

    # Category
    vc=torch.where(cat_labels>=0)[0]
    cs=vc[torch.randperm(len(vc))[:5000]]
    loss_cat=F.cross_entropy(cat_logits[cs],cat_labels[cs])

    # FIX 2: 40% regression with 15 targets
    rs=cs[:3000]
    loss_reg=F.mse_loss(reg_pred[rs],pl_targets[rs])

    # Loss: 0.10 link + 0.15 contrastive + 0.35 category + 0.40 regression
    loss = 0.10*loss_link + 0.15*loss_contrast + 0.35*loss_cat + 0.40*loss_reg

    optimizer.zero_grad(); loss.backward(); optimizer.step(); scheduler.step()

    # FIX 4: Early stopping
    if loss.item() < best_loss:
        best_loss = loss.item(); no_improve = 0
        if (epoch+1) >= 50:  # save best after warmup
            torch.save(model.state_dict(), f"{OUT}/plexis_v6_best.pt")
    else:
        no_improve += 1

    if (epoch+1) % 25 == 0:
        tick(f"  Epoch {epoch+1}/{EPOCHS}: link={loss_link.item():.4f} cat={loss_cat.item():.4f} reg={loss_reg.item():.4f} total={loss.item():.4f} lr={scheduler.get_last_lr()[0]:.5f} patience={patience-no_improve}")

    if no_improve >= patience and epoch >= 100:
        tick(f"  Early stopping at epoch {epoch+1}")
        break

# Load best model
if os.path.exists(f"{OUT}/plexis_v6_best.pt"):
    model.load_state_dict(torch.load(f"{OUT}/plexis_v6_best.pt"))
    tick(f"  Loaded best model (loss={best_loss:.4f})")

# ============================================================
# EXTRACT
# ============================================================
tick("\nExtracting embeddings...")
model.eval()
with torch.no_grad():
    full_np,spatial_np,comm_np,cat_logits,_ = model(X, edges_per_rel, edge_weights)
    full_np=full_np.numpy(); spatial_np=spatial_np.numpy(); comm_np=comm_np.numpy()

cat_acc=(cat_logits[place_mask].argmax(1)==cat_labels[place_mask]).float().mean().item()
tick(f"  Category accuracy: {cat_acc:.1%}")

place_embeds={}; place_commercial={}; hex9_embeds={}; hex8_embeds={}
for n in pl['place_id']:
    if n in node2id: i=node2id[n]; place_embeds[n]=full_np[i]; place_commercial[n]=comm_np[i]
for n in h9.index:
    if n in node2id: hex9_embeds[n]=full_np[node2id[n]]
for n in h8.index:
    if n in node2id: hex8_embeds[n]=full_np[node2id[n]]

np.savez_compressed(f"{OUT}/plexis_v6_embeddings.npz",
    place_ids=np.array(list(place_embeds.keys())), place_embeds=np.array(list(place_embeds.values())),
    place_commercial=np.array(list(place_commercial.values())),
    hex8_ids=np.array(list(hex8_embeds.keys())), hex8_embeds=np.array(list(hex8_embeds.values())))
torch.save(model.state_dict(), f"{OUT}/plexis_v6_model.pt")

# ============================================================
# EVALUATION
# ============================================================
tick(f"\n{'='*60}\nEVALUATION\n{'='*60}")

place_emb_arr=np.array(list(place_embeds.values())); place_comm_arr=np.array(list(place_commercial.values()))
place_id_arr=np.array(list(place_embeds.keys()))
hex8_emb_arr=np.array(list(hex8_embeds.values())); hex8_id_arr=np.array(list(hex8_embeds.keys()))
pid_idx={pid:i for i,pid in enumerate(place_id_arr)}; h8_idx2={hid:i for i,hid in enumerate(hex8_id_arr)}

# 7a. Category separability
tick("\n7a. Category separability (commercial head)")
cat_sims={}
for cat in cat_names[:12]:
    idx=[pid_idx[pid] for pid in pl[pl['main_category']==cat]['place_id'].head(500) if pid in pid_idx]
    oidx=[pid_idx[pid] for pid in pl[pl['main_category']!=cat]['place_id'].head(500) if pid in pid_idx]
    if len(idx)>=20 and len(oidx)>=20:
        intra=cosine_similarity(place_comm_arr[idx[:100]]).mean()
        inter=cosine_similarity(place_comm_arr[idx[:50]],place_comm_arr[oidx[:50]]).mean()
        ratio=intra/max(abs(inter),0.001)
        cat_sims[cat]=(intra,inter,ratio)
        tick(f"  {cat:30s} intra={intra:.3f} inter={inter:.3f} ratio={ratio:.1f}x")
avg_ratio=np.mean([v[2] for v in cat_sims.values()])
tick(f"  Average: {avg_ratio:.1f}x")

# 7b. Hits@10
tick("\n7b. Link prediction")
test_trips=trips.sample(len(trips)//10,random_state=42)
pos_pairs=[(node2id[h],node2id[t]) for h,t in zip(test_trips['head'],test_trips['tail']) if h in node2id and t in node2id]
hits10=sum(1 for h,t in pos_pairs[:1000] if t in np.argsort(-np.dot(full_np[h],full_np.T))[:10])
tick(f"  Hits@10: {hits10/min(len(pos_pairs),1000):.1%}")

# 7c. Hex R²
tick("\n7c. Hex R²")
h8r=[]; h8t=defaultdict(list)
tcols=['population','pc_total','transit_daily_taps','walkability_score','ecosystem_completeness','pull_office','pull_residential']
tcols=[c for c in tcols if c in h8.columns]
for hid in hex8_id_arr:
    if hid in h8.index and hid in h8_idx2:
        h8r.append(hex8_emb_arr[h8_idx2[hid]])
        for c in tcols: h8t[c].append(float(h8.loc[hid,c]) if pd.notna(h8.loc[hid,c]) else 0)
Xr=np.array(h8r)
for col in tcols:
    y=np.array(h8t[col])
    if np.std(y)<1e-6:continue
    r2=r2_score(y,LinearRegression().fit(Xr,y).predict(Xr))
    rho,_=spearmanr(y,LinearRegression().fit(Xr,y).predict(Xr))
    tick(f"  {col:30s} R²={r2:.3f}  Spearman={rho:.3f}")

# 7d. Place R²
tick("\n7d. Place R²")
pr=[]; pt2=defaultdict(list)
ptcols=['competitors_200m','complementary_diversity','anchor_score','transit_score','demand_context_score','survivability_index',
        'pull_office','pull_residential','nwalk_mrt_score','context_score']
ptcols=[c for c in ptcols if c in pl.columns]
for i,pid in enumerate(place_id_arr[:50000]):
    row=pl[pl['place_id']==pid]
    if len(row)==0:continue
    pr.append(place_emb_arr[i])
    for c in ptcols: pt2[c].append(float(row.iloc[0].get(c,0)) if pd.notna(row.iloc[0].get(c,0)) else 0)
Xp=np.array(pr)
for col in ptcols:
    y=np.array(pt2[col])
    if np.std(y)<1e-6:continue
    r2=r2_score(y,LinearRegression().fit(Xp,y).predict(Xp))
    rho,_=spearmanr(y,LinearRegression().fit(Xp,y).predict(Xp))
    tick(f"  {col:30s} R²={r2:.3f}  Spearman={rho:.3f}")

# 7e. P@5
tick("\n7e. P@5 (commercial head)")
p5s=[]
for cat in cat_names[:12]:
    ci=[pid_idx[pid] for pid in pl[pl['main_category']==cat]['place_id'].head(200) if pid in pid_idx]
    cs2=set(ci)
    if len(ci)<10:continue
    h=0;t2=0
    for idx in ci[:50]:
        sims=cosine_similarity(place_comm_arr[idx:idx+1],place_comm_arr)[0]
        top5=np.argsort(-sims)[1:6];h+=sum(1 for t in top5 if t in cs2);t2+=5
    p=h/t2 if t2>0 else 0;p5s.append(p)
    tick(f"  {cat:30s} P@5={p:.3f}")
avg_p5=np.mean(p5s)
tick(f"  Average P@5: {avg_p5:.3f}")

# 7f. NMI
tick("\n7f. NMI")
if 'archetype' in h8.columns:
    lt=[];es=[]
    for i,hid in enumerate(hex8_id_arr):
        if hid in h8.index:
            a=h8.loc[hid,'archetype']
            if pd.notna(a):lt.append(str(a));es.append(hex8_emb_arr[i])
    if len(es)>50:
        nmi=normalized_mutual_info_score(lt,KMeans(6,random_state=42,n_init=10).fit_predict(np.array(es)))
        tick(f"  NMI: {nmi:.3f}")

# COMPARISON
tick(f"\n{'='*60}")
tick("PLEXIS v6 FINAL")
tick(f"{'='*60}")
tick(f"  {'Metric':35s} {'v3':>8s} {'v4':>8s} {'v6':>8s}")
tick(f"  {'Category accuracy':35s} {'69.8%':>8s} {'69.1%':>8s} {cat_acc:>8.1%}")
tick(f"  {'Category separability':35s} {'251x':>8s} {'310x':>8s} {avg_ratio:>7.0f}x")
tick(f"  {'P@5':35s} {'0.100':>8s} {'0.092':>8s} {avg_p5:>8.3f}")
tick(f"  {'Hits@10':35s} {'7.1%':>8s} {'8.1%':>8s} {hits10/min(len(pos_pairs),1000):>8.1%}")
tick(f"  {'Embedding dim':35s} {'128':>8s} {'128':>8s} {SPATIAL_DIM+COMMERCIAL_DIM:>8d}")
tick(f"  {'Model params':35s} {'124K':>8s} {'126K':>8s} {sum(p.numel() for p in model.parameters()):>8,}")
tick(f"  {'Regression targets':35s} {'5':>8s} {'5':>8s} {len(target_cols):>8d}")
tick(f"\n  Time: {time.time()-t0:.1f}s")

with open(f"{OUT}/plexis_v6_metrics.json",'w') as f:
    json.dump({'version':'v6','nodes':N,'edges':len(trips),'relations':R,
               'embed_dim':SPATIAL_DIM+COMMERCIAL_DIM,'params':sum(p.numel() for p in model.parameters()),
               'epochs_run':epoch+1,'best_loss':round(best_loss,4),
               'cat_accuracy':round(cat_acc,3),'separability':round(avg_ratio,1),
               'p5':round(avg_p5,3),'hits10':round(hits10/min(len(pos_pairs),1000),3),
               'n_targets':len(target_cols),'attention':'GAT 4-head',
               'generated':time.strftime('%Y-%m-%d')},f,indent=2)
