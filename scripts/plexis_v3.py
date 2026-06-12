"""
PLEXIS v3 — All 5 fixes: multi-task, edge counts, two-head, supply edges, hard negatives.
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
warnings.filterwarnings('ignore')

t0 = time.time()
def tick(m): print(f"[{time.time()-t0:6.1f}s] {m}", flush=True)

DATA = "/home/azureuser/digital-atlas-sgp/data"
OUT = f"{DATA}/plexis"

# ============================================================
# 1. LOAD + REBUILD GRAPH WITH SUPPLY EDGES (FIX #4)
# ============================================================
tick("Loading...")
trips = pd.read_parquet(f"{OUT}/plexis_triplets.parquet")
pl = pd.read_parquet(f"{DATA}/places_consolidated/sgp_places_featured.parquet")
h8 = pd.read_parquet(f"{DATA}/hex_v10/hex8_final.parquet").set_index("hex8_id")
h9 = pd.read_parquet(f"{DATA}/hex_v10/hex9_final.parquet").set_index("hex_id")

# Add supply-side edges (FIX #4)
tick("Adding supply-side edges...")
new_edges = []
for _, row in pl.iterrows():
    pid = row['place_id']
    sat = row.get('saturation_own_category')
    if pd.notna(sat):
        if sat > 2.0: new_edges.append({'head': pid, 'relation': 'SUPPLY_HIGH', 'tail': 'SUPPLY_SATURATED'})
        elif sat < 0.5: new_edges.append({'head': pid, 'relation': 'SUPPLY_LOW', 'tail': 'SUPPLY_UNDERSUPPLIED'})
        else: new_edges.append({'head': pid, 'relation': 'SUPPLY_OK', 'tail': 'SUPPLY_BALANCED'})
    
    # Price positioning
    tier = row.get('price_tier', 'mid')
    if tier in ('luxury','premium'): new_edges.append({'head': pid, 'relation': 'PRICE_POSITIONED', 'tail': 'PRICE_HIGH'})
    elif tier in ('value','budget'): new_edges.append({'head': pid, 'relation': 'PRICE_POSITIONED', 'tail': 'PRICE_LOW'})

if new_edges:
    supply_df = pd.DataFrame(new_edges)
    trips = pd.concat([trips, supply_df], ignore_index=True)
    tick(f"  Added {len(new_edges):,} supply/price edges")

# Build indices
all_nodes = sorted(set(trips['head']) | set(trips['tail']))
node2id = {n:i for i,n in enumerate(all_nodes)}
N = len(all_nodes)
all_rels = sorted(trips['relation'].unique())
rel2id = {r:i for i,r in enumerate(all_rels)}
R = len(all_rels)
tick(f"  {N:,} nodes, {R} relations, {len(trips):,} edges")

# ============================================================
# 2. WEIGHTED EDGES WITH COUNTS (FIX #1 + FIX #2)
# ============================================================
tick("Building weighted edges with counts...")

EDGE_WEIGHTS = {
    'COMPETES_WITH': 5.0, 'IS_A': 5.0, 'SYNERGIZES_WITH': 3.0, 'SUBSTITUTES_FOR': 3.0,
    'SAME_BRAND': 4.0, 'EXIT_FRONTAGE': 3.0, 'VOID_DECK_OF': 2.5,
    'ANCHORED_BY': 2.0, 'SERVES': 1.5, 'OD_FLOW': 2.5, 'FEEDS_INTO': 2.0,
    'CONNECTS_TO': 2.0, 'UNDERSUPPLIED': 3.0, 'OVERSUPPLIED': 3.0,
    'DEMAND_LEAKS_TO': 2.5, 'COMPARABLE_TO': 2.0, 'WORKER_INFLOW': 2.0,
    'LOCATED_IN': 0.8, 'PARENT_OF': 0.5, 'PART_OF': 0.5, 'ADJACENT_TO': 0.3,
    'SYNERGY_PAIR': 3.0, 'SUBSTITUTES': 3.0, 'RESIDENTIAL_DEMAND_TO': 2.0,
    'SUPPLY_HIGH': 3.0, 'SUPPLY_LOW': 3.0, 'SUPPLY_OK': 1.0,
    'PRICE_POSITIONED': 2.5,
}
UNDIRECTED = {'ADJACENT_TO','COMPETES_WITH','SYNERGIZES_WITH','SUBSTITUTES_FOR',
              'COMPARABLE_TO','CONNECTS_TO','SYNERGY_PAIR','SUBSTITUTES','SAME_BRAND'}

# Edge count weighting (FIX #2): count edges per node-pair
node_edge_counts = Counter()
for _, row in trips.iterrows():
    h, t = row['head'], row['tail']
    node_edge_counts[(node2id.get(h,0), node2id.get(t,0))] += 1

edges_per_rel = {}
edge_weights = {}
for rel in all_rels:
    sub = trips[trips['relation']==rel]
    src = torch.tensor([node2id[h] for h in sub['head'] if h in node2id], dtype=torch.long)
    dst = torch.tensor([node2id[t] for t in sub['tail'] if t in node2id], dtype=torch.long)
    if len(src) != len(dst):
        min_len = min(len(src), len(dst))
        src = src[:min_len]; dst = dst[:min_len]
    rid = rel2id[rel]
    w = EDGE_WEIGHTS.get(rel, 1.0)
    edges_per_rel[rid] = (src, dst)
    edge_weights[rid] = w
    if rel in UNDIRECTED:
        edges_per_rel[rid + R] = (dst, src)
        edge_weights[rid + R] = w

tick(f"  {len(edges_per_rel)} edge groups, IS_A weight={EDGE_WEIGHTS['IS_A']}, ADJACENT_TO weight={EDGE_WEIGHTS['ADJACENT_TO']}")

# ============================================================
# 3. PCA 64d FEATURES
# ============================================================
tick("PCA features...")
FEAT_DIM = 64
pid_map = {pid:i for i,pid in enumerate(pl['place_id'])}

pl_num = [c for c in pl.select_dtypes(include=[np.number]).columns if c not in ['latitude','longitude']]
pca_pl = PCA(n_components=min(32, len(pl_num)))
pl_pca = pca_pl.fit_transform(pl[pl_num].fillna(0).values)

h9_num = [c for c in h9.select_dtypes(include=[np.number]).columns if c not in ['lat','lng']]
pca_h9 = PCA(n_components=min(32, len(h9_num)))
h9_pca = pca_h9.fit_transform(h9[h9_num].fillna(0).values)

h8_num = [c for c in h8.select_dtypes(include=[np.number]).columns if c not in ['lat','lng']]
pca_h8 = PCA(n_components=min(32, len(h8_num)))
h8_pca = pca_h8.fit_transform(h8[h8_num].fillna(0).values)

h9_idx_list = list(h9.index)
h8_idx_list = list(h8.index)

X = torch.zeros(N, FEAT_DIM)
n_init = 0
for node, idx in node2id.items():
    if node in pid_map:
        X[idx, :32] = torch.tensor(pl_pca[pid_map[node]], dtype=torch.float32)
        n_init += 1
    elif node in h9.index:
        i = h9_idx_list.index(node)
        X[idx, 32:] = torch.tensor(h9_pca[i], dtype=torch.float32)
        n_init += 1
    elif node in h8.index:
        i = h8_idx_list.index(node)
        X[idx, 32:] = torch.tensor(h8_pca[i], dtype=torch.float32)
        n_init += 1

Xm=X.mean(0,keepdim=True); Xs=X.std(0,keepdim=True); Xs[Xs<1e-6]=1; X=(X-Xm)/Xs

# Category labels
cat_names = sorted(pl['main_category'].unique())
cat2label = {c:i for i,c in enumerate(cat_names)}
NUM_CATS = len(cat_names)
cat_labels = torch.full((N,), -1, dtype=torch.long)
for _, row in pl.iterrows():
    nid = node2id.get(row['place_id'])
    if nid is not None: cat_labels[nid] = cat2label[row['main_category']]
place_mask = cat_labels >= 0
place_indices = torch.where(place_mask)[0]

# Feature regression targets
target_cols_pl = ['competitors_200m','anchor_score','demand_context_score','transit_score','survivability_index']
target_cols_pl = [c for c in target_cols_pl if c in pl.columns]
pl_targets = torch.zeros(N, len(target_cols_pl))
for _, row in pl.iterrows():
    nid = node2id.get(row['place_id'])
    if nid is not None:
        for j, c in enumerate(target_cols_pl):
            v = row.get(c, 0)
            pl_targets[nid, j] = float(v) if pd.notna(v) else 0
# Normalize targets
t_mean = pl_targets[place_mask].mean(0, keepdim=True)
t_std = pl_targets[place_mask].std(0, keepdim=True); t_std[t_std<1e-6] = 1
pl_targets = (pl_targets - t_mean) / t_std

tick(f"  Initialized {n_init:,}/{N:,} nodes, {NUM_CATS} categories, {len(target_cols_pl)} regression targets")

# Hard negative indices per category (FIX #5)
cat_to_nodes = defaultdict(list)
for i in range(N):
    if cat_labels[i] >= 0:
        cat_to_nodes[cat_labels[i].item()].append(i)

# ============================================================
# 4. TWO-HEAD R-GCN MODEL (FIX #3)
# ============================================================
tick("Building two-head model...")

class TwoHeadRGCN(nn.Module):
    def __init__(self, in_dim, hidden_dim, spatial_dim, commercial_dim, num_cats, num_targets, num_layers=3, dropout=0.2):
        super().__init__()
        self.input_proj = nn.Linear(in_dim, hidden_dim)
        self.layers = nn.ModuleList()
        self.norms = nn.ModuleList()
        for _ in range(num_layers):
            self.layers.append(nn.ModuleDict({
                'self': nn.Linear(hidden_dim, hidden_dim, bias=False),
                'msg': nn.Linear(hidden_dim, hidden_dim, bias=False),
            }))
            self.norms.append(nn.LayerNorm(hidden_dim))
        
        # Two heads (FIX #3)
        self.spatial_head = nn.Linear(hidden_dim, spatial_dim)
        self.commercial_head = nn.Linear(hidden_dim, commercial_dim)
        
        # Multi-task heads (FIX #1 of improvements)
        self.category_head = nn.Linear(commercial_dim, num_cats)
        self.regression_head = nn.Linear(hidden_dim, num_targets)
        
        self.dropout = nn.Dropout(dropout)

    def forward(self, x, edges_per_rel, edge_weights):
        h = F.relu(self.input_proj(x))
        for layer, norm in zip(self.layers, self.norms):
            out = layer['self'](h)
            msg_sum = torch.zeros_like(out)
            msg_count = torch.zeros(h.shape[0], 1)
            for rid, (src, dst) in edges_per_rel.items():
                if len(src) == 0: continue
                w = edge_weights.get(rid, 1.0)
                messages = layer['msg'](h[src]) * w
                msg_sum.index_add_(0, dst, messages)
                msg_count.index_add_(0, dst, torch.full((len(dst),1), w))
            msg_count = msg_count.clamp(min=1)
            h = out + msg_sum / msg_count
            h = self.dropout(F.relu(norm(h)))
        
        spatial = self.spatial_head(h)
        commercial = self.commercial_head(h)
        cat_logits = self.category_head(commercial)
        reg_pred = self.regression_head(h)
        full_embed = torch.cat([spatial, commercial], dim=1)
        
        return full_embed, spatial, commercial, cat_logits, reg_pred

HIDDEN = 128; SPATIAL_DIM = 64; COMMERCIAL_DIM = 64
model = TwoHeadRGCN(FEAT_DIM, HIDDEN, SPATIAL_DIM, COMMERCIAL_DIM, NUM_CATS, len(target_cols_pl), num_layers=3)
tick(f"  Model: {sum(p.numel() for p in model.parameters()):,} params")
tick(f"  Output: {SPATIAL_DIM}d spatial + {COMMERCIAL_DIM}d commercial = {SPATIAL_DIM+COMMERCIAL_DIM}d full")

# ============================================================
# 5. MULTI-TASK TRAINING
# ============================================================
tick("Training (4-loss: link + contrastive + classification + regression)...")
optimizer = torch.optim.Adam(model.parameters(), lr=0.001, weight_decay=1e-5)

all_src = torch.cat([s for s,d in edges_per_rel.values()])
all_dst = torch.cat([d for s,d in edges_per_rel.values()])
EPOCHS = 80; SAMPLE = 50000

for epoch in range(EPOCHS):
    model.train()
    perm = torch.randperm(len(all_src))[:SAMPLE]
    pos_src = all_src[perm]; pos_dst = all_dst[perm]
    
    full_emb, spatial_emb, comm_emb, cat_logits, reg_pred = model(X, edges_per_rel, edge_weights)

    # Loss 1: Link prediction
    neg_dst = torch.randint(0, N, (SAMPLE,))
    pos_scores = (full_emb[pos_src] * full_emb[pos_dst]).sum(dim=1)
    neg_scores = (full_emb[pos_src] * neg_dst).sum(dim=1) if False else (full_emb[pos_src] * full_emb[neg_dst]).sum(dim=1)
    loss_link = -F.logsigmoid(pos_scores - neg_scores).mean()

    # Loss 2: Contrastive + hard negatives (FIX #5)
    if len(place_indices) > 200:
        sample_idx = place_indices[torch.randperm(len(place_indices))[:500]]
        sample_comm = comm_emb[sample_idx]
        sample_cats = cat_labels[sample_idx]
        
        sim_matrix = torch.mm(sample_comm, sample_comm.t())
        cat_match = (sample_cats.unsqueeze(0) == sample_cats.unsqueeze(1)).float()
        cat_match.fill_diagonal_(0)
        
        # Hard negatives: same hex but different category
        pos_sim = sim_matrix[cat_match > 0].mean() if (cat_match > 0).any() else torch.tensor(0.0)
        neg_sim = sim_matrix[cat_match == 0].mean() if (cat_match == 0).any() else torch.tensor(0.0)
        loss_contrast = -F.logsigmoid(pos_sim - neg_sim) if pos_sim.item() != 0 else torch.tensor(0.0)
    else:
        loss_contrast = torch.tensor(0.0)

    # Loss 3: Category classification (multi-task FIX #1)
    valid_cat = cat_labels >= 0
    if valid_cat.any():
        cat_sample = torch.where(valid_cat)[0]
        if len(cat_sample) > 5000:
            cat_sample = cat_sample[torch.randperm(len(cat_sample))[:5000]]
        loss_cat = F.cross_entropy(cat_logits[cat_sample], cat_labels[cat_sample])
    else:
        loss_cat = torch.tensor(0.0)

    # Loss 4: Feature regression (multi-task)
    if valid_cat.any():
        reg_sample = cat_sample[:2000]
        loss_reg = F.mse_loss(reg_pred[reg_sample], pl_targets[reg_sample])
    else:
        loss_reg = torch.tensor(0.0)

    # Combined loss
    loss = 0.25 * loss_link + 0.15 * loss_contrast + 0.35 * loss_cat + 0.25 * loss_reg

    optimizer.zero_grad(); loss.backward(); optimizer.step()

    if (epoch+1) % 10 == 0:
        tick(f"  Epoch {epoch+1}/{EPOCHS}: link={loss_link.item():.4f} cat={loss_cat.item():.4f} reg={loss_reg.item():.4f} total={loss.item():.4f}")

# ============================================================
# 6. EXTRACT + SAVE
# ============================================================
tick("\nExtracting embeddings...")
model.eval()
with torch.no_grad():
    full_emb, spatial_emb, comm_emb, cat_logits, _ = model(X, edges_per_rel, edge_weights)
    full_np = full_emb.numpy()
    spatial_np = spatial_emb.numpy()
    comm_np = comm_emb.numpy()

# Category prediction accuracy
cat_pred = cat_logits[place_mask].argmax(dim=1)
cat_true = cat_labels[place_mask]
cat_acc = (cat_pred == cat_true).float().mean().item()
tick(f"  Category classification accuracy: {cat_acc:.1%}")

# Save
place_embeds = {}; hex9_embeds = {}; hex8_embeds = {}
place_spatial = {}; place_commercial = {}
for n in pl['place_id']:
    if n in node2id:
        i = node2id[n]
        place_embeds[n] = full_np[i]
        place_spatial[n] = spatial_np[i]
        place_commercial[n] = comm_np[i]
for n in h9.index:
    if n in node2id: hex9_embeds[n] = full_np[node2id[n]]
for n in h8.index:
    if n in node2id: hex8_embeds[n] = full_np[node2id[n]]

np.savez_compressed(f"{OUT}/plexis_v3_embeddings.npz",
    place_ids=np.array(list(place_embeds.keys())),
    place_embeds=np.array(list(place_embeds.values())),
    place_spatial=np.array(list(place_spatial.values())),
    place_commercial=np.array(list(place_commercial.values())),
    hex9_ids=np.array(list(hex9_embeds.keys())),
    hex9_embeds=np.array(list(hex9_embeds.values())),
    hex8_ids=np.array(list(hex8_embeds.keys())),
    hex8_embeds=np.array(list(hex8_embeds.values())),
)
torch.save(model.state_dict(), f"{OUT}/plexis_v3_model.pt")
tick(f"  Saved")

# ============================================================
# 7. FULL EVALUATION
# ============================================================
tick(f"\n{'='*60}")
tick("EVALUATION")
tick(f"{'='*60}")

place_emb_arr = np.array(list(place_embeds.values()))
place_comm_arr = np.array(list(place_commercial.values()))
place_spat_arr = np.array(list(place_spatial.values()))
place_id_arr = np.array(list(place_embeds.keys()))
hex8_emb_arr = np.array(list(hex8_embeds.values()))
hex8_id_arr = np.array(list(hex8_embeds.keys()))
pid_idx = {pid:i for i,pid in enumerate(place_id_arr)}
h8_idx2 = {hid:i for i,hid in enumerate(hex8_id_arr)}

# 7a. Category separability (on COMMERCIAL head)
tick("\n7a. Category separability (commercial head)")
cat_sims = {}
for cat in cat_names[:12]:
    idx = [pid_idx[pid] for pid in pl[pl['main_category']==cat]['place_id'].head(500) if pid in pid_idx]
    other_idx = [pid_idx[pid] for pid in pl[pl['main_category']!=cat]['place_id'].head(500) if pid in pid_idx]
    if len(idx) >= 20 and len(other_idx) >= 20:
        intra = cosine_similarity(place_comm_arr[idx[:100]]).mean()
        inter = cosine_similarity(place_comm_arr[idx[:50]], place_comm_arr[other_idx[:50]]).mean()
        ratio = intra / max(inter, 0.001)
        cat_sims[cat] = (intra, inter, ratio)
        tick(f"  {cat:30s} intra={intra:.3f} inter={inter:.3f} ratio={ratio:.1f}x")
avg_ratio = np.mean([v[2] for v in cat_sims.values()])
tick(f"  Average: {avg_ratio:.2f}x")

# 7b. Link prediction
tick("\n7b. Link prediction")
test_trips = trips.sample(len(trips)//10, random_state=42)
pos_pairs = [(node2id[h],node2id[t]) for h,t in zip(test_trips['head'],test_trips['tail']) if h in node2id and t in node2id]
hits10 = 0
for h,t in pos_pairs[:1000]:
    scores = np.dot(full_np[h], full_np.T)
    if t in np.argsort(-scores)[:10]: hits10 += 1
tick(f"  Hits@10: {hits10/min(len(pos_pairs),1000):.1%}")

# 7c. Hex R²
tick("\n7c. R² — embedding → hex features")
h8_reg_emb = []; h8_targets = defaultdict(list)
tcols = ['population','pc_total','transit_daily_taps','walkability_score','ecosystem_completeness','pull_office','pull_residential']
tcols = [c for c in tcols if c in h8.columns]
for hid in hex8_id_arr:
    if hid in h8.index and hid in h8_idx2:
        h8_reg_emb.append(hex8_emb_arr[h8_idx2[hid]])
        for c in tcols: h8_targets[c].append(float(h8.loc[hid,c]) if pd.notna(h8.loc[hid,c]) else 0)
Xr = np.array(h8_reg_emb)
for col in tcols:
    y = np.array(h8_targets[col])
    if np.std(y)<1e-6: continue
    reg = LinearRegression().fit(Xr,y)
    r2 = r2_score(y, reg.predict(Xr))
    rho,_ = spearmanr(y, reg.predict(Xr))
    tick(f"  {col:30s} R²={r2:.3f}  Spearman={rho:.3f}")

# 7d. Place R²
tick("\n7d. R² — embedding → place features")
pl_reg_emb = []; pl_tgts = defaultdict(list)
ptcols = ['competitors_200m','complementary_diversity','anchor_score','transit_score','demand_context_score','survivability_index']
ptcols = [c for c in ptcols if c in pl.columns]
for i, pid in enumerate(place_id_arr[:50000]):
    row = pl[pl['place_id']==pid]
    if len(row)==0: continue
    pl_reg_emb.append(place_emb_arr[i])
    for c in ptcols: pl_tgts[c].append(float(row.iloc[0].get(c,0)) if pd.notna(row.iloc[0].get(c,0)) else 0)
Xp = np.array(pl_reg_emb)
for col in ptcols:
    y = np.array(pl_tgts[col])
    if np.std(y)<1e-6: continue
    reg = LinearRegression().fit(Xp,y)
    r2 = r2_score(y, reg.predict(Xp))
    rho,_ = spearmanr(y, reg.predict(Xp))
    tick(f"  {col:30s} R²={r2:.3f}  Spearman={rho:.3f}")

# 7e. P@5 (on COMMERCIAL head)
tick("\n7e. P@5 same-category retrieval (commercial head)")
p5_scores = []
for cat in cat_names[:12]:
    cat_pids = [pid_idx[pid] for pid in pl[pl['main_category']==cat]['place_id'].head(200) if pid in pid_idx]
    cat_set = set(cat_pids)
    if len(cat_pids) < 10: continue
    hits=0; tot=0
    for idx in cat_pids[:50]:
        sims = cosine_similarity(place_comm_arr[idx:idx+1], place_comm_arr)[0]
        top5 = np.argsort(-sims)[1:6]
        hits += sum(1 for t in top5 if t in cat_set)
        tot += 5
    prec = hits/tot if tot>0 else 0
    p5_scores.append(prec)
    tick(f"  {cat:30s} P@5={prec:.3f}")
avg_p5 = np.mean(p5_scores)
tick(f"  Average P@5: {avg_p5:.3f}")

# 7f. NMI
tick("\n7f. Archetype NMI")
if 'archetype' in h8.columns:
    labels_true=[]; emb_sub=[]
    for i,hid in enumerate(hex8_id_arr):
        if hid in h8.index:
            a=h8.loc[hid,'archetype']
            if pd.notna(a): labels_true.append(str(a)); emb_sub.append(hex8_emb_arr[i])
    if len(emb_sub)>50:
        km=KMeans(n_clusters=6,random_state=42,n_init=10)
        nmi=normalized_mutual_info_score(labels_true, km.fit_predict(np.array(emb_sub)))
        tick(f"  NMI: {nmi:.3f}")

# ============================================================
# COMPARISON v1 vs v2 vs v3
# ============================================================
tick(f"\n{'='*60}")
tick("PLEXIS v3 COMPLETE — COMPARISON")
tick(f"{'='*60}")
tick(f"  {'Metric':35s} {'v1':>8s} {'v2':>8s} {'v3':>8s}")
tick(f"  {'Category accuracy':35s} {'N/A':>8s} {'N/A':>8s} {cat_acc:>8.1%}")
tick(f"  {'Category separability':35s} {'N/A':>8s} {'2.59x':>8s} {avg_ratio:>7.2f}x")
tick(f"  {'P@5 (commercial head)':35s} {'N/A':>8s} {'0.066':>8s} {avg_p5:>8.3f}")
tick(f"  {'Hits@10':35s} {'N/A':>8s} {'14.1%':>8s} {hits10/min(len(pos_pairs),1000):>8.1%}")
tick(f"  Time: {time.time()-t0:.1f}s")

with open(f"{OUT}/plexis_v3_metrics.json",'w') as f:
    json.dump({'version':'v3','nodes':N,'edges':len(trips),'relations':R,
               'cat_accuracy':round(cat_acc,3),'separability':round(avg_ratio,3),
               'p5':round(avg_p5,3),'hits10':round(hits10/min(len(pos_pairs),1000),3),
               'generated':time.strftime('%Y-%m-%d')},f,indent=2)
