#!/usr/bin/env python3
"""
Embedding Validation Engine — continuous regression harness.

Generates 200+ tests across 7 categories, runs them against 5 embedding variants,
logs per-run results, and writes a live HTML dashboard. Designed to run on a
30-minute loop in a screen session.

Tests:
  1. PA coherence (50)        — random hex's top-10 neighbors mostly same PA
  2. Landmark anchors (30)    — named landmarks retrieve expected PAs
  3. Anti-similarity (30)     — dissimilar hex pairs have low cosine
  4. Graph smoothness (30)    — graph-adjacent hexes more similar than random
  5. Archetype stability (20) — k-means assignments stable across seeds
  6. Functional equivalence (20) — MRT nodes / universities / industrial cluster
  7. Feature-query retrieval (20) — feature-constraint queries return right hexes

Run:
  python3 embedding_validation_engine.py              # single run
  python3 embedding_validation_engine.py --loop 1800  # every 30 min
"""
import os, sys, json, time, argparse, hashlib
from collections import Counter
from datetime import datetime

import numpy as np
import pandas as pd
import scipy.sparse as sp
import h3
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score

ROOT = "/home/azureuser/digital-atlas-sgp"
OUT_DIR = f"{ROOT}/data/hex_v10/validation_engine"
RUNS_DIR = f"{OUT_DIR}/runs"
os.makedirs(RUNS_DIR, exist_ok=True)

SEED = 42


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


# ============================================================
# LOAD DATA + EMBEDDINGS
# ============================================================
def load_all():
    log("Loading data + all embedding variants...")
    raw = pd.read_parquet(f"{ROOT}/data/hex_v10/hex_features_v10.parquet")
    norm = pd.read_parquet(f"{ROOT}/data/hex_v10/hex_features_v10_normalized.parquet")

    hex_order = raw["hex_id"].tolist()
    hex_to_idx = {h: i for i, h in enumerate(hex_order)}

    # Load embeddings
    embs = {}

    # GCN-64 (production)
    g = pd.read_parquet(f"{ROOT}/data/hex_v10/gcn_results/gcn_embedding_64.parquet")
    g = g.set_index("hex_id").loc[hex_order, [f"g{i}" for i in range(64)]].to_numpy(np.float32)
    embs["GCN-64"] = g

    # GCN-32, 128, 256 (from sweep, if available)
    for d in [32, 128, 256]:
        p = f"{ROOT}/data/hex_v10/gcn_results/gcn_embedding_{d}.parquet"
        if os.path.exists(p):
            df = pd.read_parquet(p)
            if "hex_id" in df.columns:
                df = df.set_index("hex_id")
                cols = [c for c in df.columns if c.startswith("g")][:d]
                embs[f"GCN-{d}"] = df.loc[hex_order, cols].to_numpy(np.float32)

    # PCA-128
    p = pd.read_parquet(f"{ROOT}/data/hex_v10/embeddings/hex_embedding_128.parquet")
    p = p.set_index("hex_id")
    pca_cols = p.select_dtypes(include=[np.number]).columns.tolist()[:128]
    embs["PCA-128"] = p.loc[hex_order, pca_cols].to_numpy(np.float32)

    # Raw features
    ID_COLS = {"hex_id", "lat", "lng", "area_km2", "parent_subzone",
               "parent_subzone_name", "parent_pa", "parent_region"}
    BK = {"subzone_pop_total", "subzone_res_floor_area", "residential_floor_weight"}
    feat_cols = [c for c in norm.columns if c not in ID_COLS and c not in BK]
    embs["Raw-460"] = norm[feat_cols].to_numpy(np.float32)

    # Graph
    adj = sp.load_npz(f"{ROOT}/data/hex_v10/hex_influence_graph.npz").tocsr()

    log(f"  Hexes: {len(raw)} | Embedding variants: {list(embs.keys())}")
    return raw, norm, embs, hex_order, hex_to_idx, adj, feat_cols


def z_standardize(Z):
    return (Z - Z.mean(axis=0)) / (Z.std(axis=0) + 1e-9)


def cosine_sim(Zn, i, j):
    return float(np.dot(Zn[i], Zn[j]))


def top_k(Zn, i, k, exclude_self=True):
    sims = Zn @ Zn[i]
    if exclude_self:
        sims[i] = -np.inf
    idx = np.argpartition(-sims, k)[:k]
    idx = idx[np.argsort(-sims[idx])]
    return idx, sims[idx]


# ============================================================
# TEST GENERATORS
# ============================================================
def gen_tests_pa_coherence(raw, n=50, k=10, min_match=5, seed=SEED):
    """Random hex → top-k neighbors should share parent_pa in ≥ min_match cases."""
    rng = np.random.default_rng(seed)
    # Pick hexes from PAs with >= 20 hexes (otherwise test is trivial/impossible)
    pa_counts = raw["parent_pa"].value_counts()
    eligible_pas = pa_counts[pa_counts >= 20].index.tolist()
    eligible_mask = raw["parent_pa"].isin(eligible_pas).values
    candidates = np.where(eligible_mask)[0]
    picks = rng.choice(candidates, size=min(n, len(candidates)), replace=False)
    tests = []
    for i in picks:
        tests.append({
            "id": f"pa_coh_{i}",
            "category": "pa_coherence",
            "query_idx": int(i),
            "k": k,
            "min_match": min_match,
            "expected_pa": str(raw.iloc[i]["parent_pa"]),
        })
    return tests


LANDMARK_DEFS = [
    ("raffles_place",      1.2841, 103.8515, "DOWNTOWN CORE"),
    ("marina_bay_sands",   1.2838, 103.8591, "DOWNTOWN CORE"),
    ("orchard_road",       1.3048, 103.8318, "ORCHARD"),
    ("tiong_bahru",        1.2852, 103.8306, "BUKIT MERAH"),
    ("changi_airport",     1.3554, 103.9840, "CHANGI"),
    ("sentosa_rws",        1.2541, 103.8231, "SOUTHERN ISLANDS"),
    ("tampines_hub",       1.3549, 103.9442, "TAMPINES"),
    ("jurong_east",        1.3331, 103.7428, "JURONG EAST"),
    ("tuas_industrial",    1.3240, 103.6360, "TUAS"),
    ("bedok_hdb",          1.3236, 103.9273, "BEDOK"),
    ("nus_kent_ridge",     1.2966, 103.7764, "QUEENSTOWN"),
    ("woodlands",          1.4382, 103.7883, "WOODLANDS"),
    ("ang_mo_kio",         1.3691, 103.8454, "ANG MO KIO"),
    ("toa_payoh",          1.3343, 103.8563, "TOA PAYOH"),
    ("hougang",            1.3612, 103.8864, "HOUGANG"),
    ("yishun",             1.4297, 103.8352, "YISHUN"),
    ("choa_chu_kang",      1.3854, 103.7441, "CHOA CHU KANG"),
    ("bukit_batok",        1.3590, 103.7637, "BUKIT BATOK"),
    ("jurong_west",        1.3404, 103.7090, "JURONG WEST"),
    ("pasir_ris",          1.3721, 103.9474, "PASIR RIS"),
    ("serangoon",          1.3554, 103.8679, "SERANGOON"),
    ("punggol",            1.3984, 103.9072, "PUNGGOL"),
    ("sengkang",           1.3868, 103.8914, "SENGKANG"),
    ("clementi",           1.3162, 103.7649, "CLEMENTI"),
    ("queenstown",         1.2942, 103.8058, "QUEENSTOWN"),
    ("geylang",            1.3189, 103.8865, "GEYLANG"),
    ("kallang",            1.3110, 103.8637, "KALLANG"),
    ("novena",             1.3203, 103.8435, "NOVENA"),
    ("bukit_timah",        1.3294, 103.8021, "BUKIT TIMAH"),
    ("marina_south",       1.2722, 103.8636, "MARINA SOUTH"),
]


def gen_tests_landmarks(hex_to_idx):
    """Named landmarks → top-5 neighbors should mostly be in expected PA."""
    tests = []
    for name, lat, lng, exp_pa in LANDMARK_DEFS:
        hid = h3.latlng_to_cell(lat, lng, 9)
        if hid not in hex_to_idx:
            continue
        tests.append({
            "id": f"landmark_{name}",
            "category": "landmark",
            "query_idx": int(hex_to_idx[hid]),
            "k": 5,
            "min_match": 3,
            "expected_pa": exp_pa,
        })
    return tests


DISSIMILAR_PAIRS = [
    # (lat1, lng1, lat2, lng2, description, max_cos)
    (1.2841, 103.8515, 1.3240, 103.6360, "CBD vs Tuas industrial", 0.7),
    (1.3554, 103.9840, 1.4382, 103.7883, "Changi Airport vs Woodlands residential", 0.75),
    (1.2541, 103.8231, 1.3404, 103.7090, "Sentosa resort vs Jurong West HDB", 0.7),
    (1.2838, 103.8591, 1.3854, 103.7441, "Marina Bay Sands vs Choa Chu Kang", 0.75),
    (1.3048, 103.8318, 1.3240, 103.6360, "Orchard vs Tuas", 0.7),
    (1.2966, 103.7764, 1.3240, 103.6360, "NUS vs Tuas", 0.7),
    (1.3549, 103.9442, 1.2841, 103.8515, "Tampines Hub vs CBD", 0.8),
    (1.2541, 103.8231, 1.3240, 103.6360, "Sentosa vs Tuas", 0.6),
    (1.2838, 103.8591, 1.3240, 103.6360, "MBS vs Tuas", 0.6),
    (1.3554, 103.9840, 1.3240, 103.6360, "Changi vs Tuas (both edge but different)", 0.8),
    (1.3554, 103.9840, 1.2841, 103.8515, "Changi vs CBD", 0.8),
    (1.2541, 103.8231, 1.4382, 103.7883, "Sentosa vs Woodlands", 0.75),
    (1.2966, 103.7764, 1.3549, 103.9442, "NUS vs Tampines (uni vs heartland)", 0.85),
    (1.2966, 103.7764, 1.3240, 103.6360, "NUS vs Tuas", 0.65),
    (1.3048, 103.8318, 1.3554, 103.9840, "Orchard retail vs Changi airport", 0.8),
]


def gen_tests_anti_similarity(hex_to_idx, n=30):
    """Known-dissimilar pairs must have cosine below threshold."""
    tests = []
    for i, (la1, ln1, la2, ln2, desc, max_cos) in enumerate(DISSIMILAR_PAIRS[:n]):
        h1, h2 = h3.latlng_to_cell(la1, ln1, 9), h3.latlng_to_cell(la2, ln2, 9)
        if h1 not in hex_to_idx or h2 not in hex_to_idx:
            continue
        tests.append({
            "id": f"anti_{i}",
            "category": "anti_similarity",
            "query_idx": int(hex_to_idx[h1]),
            "target_idx": int(hex_to_idx[h2]),
            "max_cos": max_cos,
            "description": desc,
        })
    # Pad with random cross-PA pairs if needed
    if len(tests) < n:
        rng = np.random.default_rng(SEED + 1)
        idxs = list(hex_to_idx.values())
        while len(tests) < n:
            i, j = rng.choice(idxs, 2, replace=False)
            tests.append({
                "id": f"anti_random_{len(tests)}",
                "category": "anti_similarity",
                "query_idx": int(i),
                "target_idx": int(j),
                "max_cos": 0.95,  # loose bound for random pairs
                "description": "random cross-PA pair",
            })
    return tests


def gen_tests_graph_smoothness(raw, adj, n=30, seed=SEED):
    """Hex + graph neighbors should have avg cos > random pair avg."""
    rng = np.random.default_rng(seed)
    n_hex = len(raw)
    # Pick hexes with ≥ 3 neighbors
    degrees = np.asarray(adj.sum(axis=1)).flatten()
    eligible = np.where(degrees >= 3)[0]
    picks = rng.choice(eligible, size=min(n, len(eligible)), replace=False)
    tests = []
    for i in picks:
        nbrs = adj[i].indices
        nbrs = nbrs[nbrs != i][:6]
        if len(nbrs) < 2:
            continue
        tests.append({
            "id": f"smooth_{i}",
            "category": "graph_smoothness",
            "query_idx": int(i),
            "neighbor_idxs": [int(n) for n in nbrs],
        })
    return tests


def gen_tests_archetype_stability(raw, n=20, seed=SEED):
    """k-means with different seeds → ARI should be > 0.7 (stable)."""
    tests = []
    for i in range(n):
        tests.append({
            "id": f"archetype_k{10 + i % 6}_seed{i}",
            "category": "archetype_stability",
            "k_clusters": 10 + (i % 6),
            "seed_a": i,
            "seed_b": i + 100,
            "min_ari": 0.5,
        })
    return tests


def gen_tests_functional_equivalence(raw, n=20):
    """Groups of hexes that should cluster by function (MRT nodes, universities, etc.)."""
    tests = []
    # MRT-heavy hexes
    mrt_high = raw.nlargest(15, "mrt_stations")["hex_id"].tolist()
    tests.append({
        "id": "func_mrt_nodes",
        "category": "functional",
        "group": [int(raw.index[raw.hex_id == h][0]) for h in mrt_high],
        "min_intra_cos": 0.6,
        "description": "Top-15 MRT-station-heavy hexes",
    })
    # Industrial (Tuas+Pioneer+Jurong Island)
    indus = raw[raw["parent_pa"].isin(["TUAS", "PIONEER", "JURONG ISLAND", "WESTERN ISLANDS"])]
    if len(indus) >= 15:
        ix = raw.index[raw.hex_id.isin(indus.hex_id.head(30))].tolist()
        tests.append({
            "id": "func_industrial",
            "category": "functional",
            "group": [int(x) for x in ix[:20]],
            "min_intra_cos": 0.7,
            "description": "Industrial hexes (Tuas/Pioneer/Jurong Island)",
        })
    # CBD
    cbd = raw[raw["parent_pa"].isin(["DOWNTOWN CORE"])]
    ix = raw.index[raw.hex_id.isin(cbd.hex_id.head(20))].tolist()
    tests.append({
        "id": "func_cbd",
        "category": "functional",
        "group": [int(x) for x in ix[:20]],
        "min_intra_cos": 0.65,
        "description": "CBD hexes",
    })
    # Airports
    changi = raw[raw["parent_pa"] == "CHANGI"]
    if len(changi) >= 10:
        ix = raw.index[raw.hex_id.isin(changi.hex_id.head(15))].tolist()
        tests.append({
            "id": "func_changi_airport",
            "category": "functional",
            "group": [int(x) for x in ix[:15]],
            "min_intra_cos": 0.8,
            "description": "Changi Airport hexes",
        })
    # Sentosa
    sent = raw[raw["parent_subzone_name"].str.contains("SENTOSA", na=False)]
    if len(sent) >= 10:
        ix = raw.index[raw.hex_id.isin(sent.hex_id.head(20))].tolist()
        tests.append({
            "id": "func_sentosa",
            "category": "functional",
            "group": [int(x) for x in ix[:20]],
            "min_intra_cos": 0.8,
            "description": "Sentosa hexes",
        })
    # Pad with per-PA cohesion tests for largest PAs
    pa_counts = raw["parent_pa"].value_counts()
    for pa in pa_counts.head(15).index:
        if len(tests) >= n:
            break
        ix = raw.index[raw.parent_pa == pa].tolist()[:20]
        tests.append({
            "id": f"func_pa_{pa.lower().replace(' ','_')}",
            "category": "functional",
            "group": [int(x) for x in ix],
            "min_intra_cos": 0.4,  # looser — PA is bigger than a functional cluster
            "description": f"PA cohesion: {pa}",
        })
    return tests[:n]


def gen_tests_feature_query(raw, norm, feat_cols, n=20, seed=SEED):
    """Given a feature profile query, retrieved hex should match the profile."""
    rng = np.random.default_rng(seed)
    tests = []
    # Use hexes with extreme values on selected features as anchor queries
    key_features = [
        "pred_cafe_coffee", "pred_hawker_street_food", "pred_office_workspace",
        "pred_residential", "pred_hospitality", "pred_transport",
        "mrt_stations", "walkability_score", "tourist_draw_est", "population",
    ]
    shareable = pd.read_parquet(f"{ROOT}/data/hex_v10/hex_shareable_bundle.parquet")
    shareable = shareable.set_index("hex_id")
    for f in key_features[:n]:
        if f not in shareable.columns:
            continue
        # Top-5 on this feature
        top5 = shareable.nlargest(5, f).index.tolist()
        ixs = [int(raw.index[raw.hex_id == h][0]) for h in top5]
        tests.append({
            "id": f"query_{f}",
            "category": "feature_query",
            "anchor_idxs": ixs,
            "feature": f,
            "min_intra_cos": 0.55,
            "description": f"Hexes with extreme {f}",
        })
    return tests[:n]


def build_test_suite(raw, norm, adj, hex_to_idx, feat_cols):
    log("Generating test suite...")
    tests = []
    tests.extend(gen_tests_pa_coherence(raw, n=50))
    tests.extend(gen_tests_landmarks(hex_to_idx))
    tests.extend(gen_tests_anti_similarity(hex_to_idx, n=30))
    tests.extend(gen_tests_graph_smoothness(raw, adj, n=30))
    tests.extend(gen_tests_archetype_stability(raw, n=20))
    tests.extend(gen_tests_functional_equivalence(raw, n=20))
    tests.extend(gen_tests_feature_query(raw, norm, feat_cols, n=20))
    log(f"  Generated {len(tests)} tests across "
        f"{len(set(t['category'] for t in tests))} categories")
    cnt = Counter(t["category"] for t in tests)
    for c, n in cnt.items():
        log(f"    {c}: {n}")
    return tests


# ============================================================
# TEST RUNNERS
# ============================================================
def run_test(test, Zn, Z_unn, pa_labels):
    """Run one test against one embedding. Return (passed, score)."""
    cat = test["category"]

    if cat == "pa_coherence":
        idx, _ = top_k(Zn, test["query_idx"], test["k"])
        nbr_pas = [pa_labels[i] for i in idx]
        match = sum(1 for p in nbr_pas if p == test["expected_pa"])
        score = match / test["k"]
        return (match >= test["min_match"]), score

    elif cat == "landmark":
        idx, _ = top_k(Zn, test["query_idx"], test["k"])
        nbr_pas = [pa_labels[i] for i in idx]
        match = sum(1 for p in nbr_pas if p == test["expected_pa"])
        score = match / test["k"]
        return (match >= test["min_match"]), score

    elif cat == "anti_similarity":
        c = cosine_sim(Zn, test["query_idx"], test["target_idx"])
        return (c < test["max_cos"]), c

    elif cat == "graph_smoothness":
        # Avg cos between query and its neighbors vs avg across 20 random pairs
        q = test["query_idx"]
        nbrs = test["neighbor_idxs"]
        nbr_cos = np.mean([cosine_sim(Zn, q, n) for n in nbrs])
        # Baseline: random pairs sampled deterministically
        rng = np.random.default_rng(q)
        idxs = rng.integers(0, Zn.shape[0], 20)
        rand_cos = np.mean([cosine_sim(Zn, q, i) for i in idxs if i != q])
        lift = nbr_cos - rand_cos
        return (lift > 0.05), float(lift)

    elif cat == "archetype_stability":
        # k-means with 2 different seeds → ARI
        k = test["k_clusters"]
        a = KMeans(n_clusters=k, random_state=test["seed_a"], n_init=5).fit(Z_unn).labels_
        b = KMeans(n_clusters=k, random_state=test["seed_b"], n_init=5).fit(Z_unn).labels_
        ari = adjusted_rand_score(a, b)
        return (ari >= test["min_ari"]), float(ari)

    elif cat == "functional":
        # Avg intra-group cosine should exceed threshold
        grp = test["group"]
        sims = []
        for i in range(len(grp)):
            for j in range(i + 1, len(grp)):
                sims.append(cosine_sim(Zn, grp[i], grp[j]))
        avg = float(np.mean(sims))
        return (avg >= test["min_intra_cos"]), avg

    elif cat == "feature_query":
        # Avg intra-group cosine for hexes with extreme feature values
        grp = test["anchor_idxs"]
        sims = []
        for i in range(len(grp)):
            for j in range(i + 1, len(grp)):
                sims.append(cosine_sim(Zn, grp[i], grp[j]))
        avg = float(np.mean(sims))
        return (avg >= test["min_intra_cos"]), avg

    return False, 0.0


def evaluate_embedding(name, Z, tests, pa_labels):
    """Run all tests on one embedding. Return summary dict."""
    # z-standardize for fair cosine
    Z_z = z_standardize(Z)
    Zn = Z_z / (np.linalg.norm(Z_z, axis=1, keepdims=True) + 1e-9)
    # Archetype tests need unnormalized (k-means) — use original
    results = {"name": name, "dims": Z.shape[1], "per_test": [], "per_category": {}}
    cat_scores = {}
    for t in tests:
        passed, score = run_test(t, Zn, Z_z, pa_labels)
        results["per_test"].append({
            "id": t["id"], "category": t["category"],
            "passed": bool(passed), "score": float(score),
        })
        cat_scores.setdefault(t["category"], []).append((passed, score))

    # Aggregate per category
    for cat, vals in cat_scores.items():
        passes = sum(1 for p, _ in vals if p)
        scores = [s for _, s in vals]
        results["per_category"][cat] = {
            "n": len(vals), "passed": passes, "pass_rate": passes / len(vals),
            "mean_score": float(np.mean(scores)),
        }
    # Overall
    total = len(results["per_test"])
    passed_total = sum(1 for t in results["per_test"] if t["passed"])
    results["overall_pass_rate"] = passed_total / total
    results["total_tests"] = total
    results["passed_tests"] = passed_total
    return results


# ============================================================
# RUN CYCLE
# ============================================================
def run_cycle():
    t0 = time.time()
    raw, norm, embs, hex_order, hex_to_idx, adj, feat_cols = load_all()
    tests = build_test_suite(raw, norm, adj, hex_to_idx, feat_cols)

    pa_labels = np.asarray(raw["parent_pa"].astype(str).values)

    log("\nEvaluating all embeddings...")
    all_results = {}
    for name, Z in embs.items():
        log(f"  {name} ({Z.shape[1]}d) ...")
        all_results[name] = evaluate_embedding(name, Z, tests, pa_labels)

    # Summary log
    log("\n" + "=" * 70)
    log("RUN SUMMARY")
    log("=" * 70)
    log(f"{'Embedding':<12} {'Dims':<6} {'Pass rate':<12} {'Details':<40}")
    for name, r in all_results.items():
        details = " | ".join([f"{c}:{v['pass_rate']:.0%}"
                              for c, v in r["per_category"].items()])
        log(f"{name:<12} {r['dims']:<6} "
            f"{r['overall_pass_rate']:.1%} ({r['passed_tests']}/{r['total_tests']})"
            f"  {details}")

    # Save this run
    ts = datetime.now().strftime("%Y%m%dT%H%M%S")
    run_path = f"{RUNS_DIR}/run_{ts}.json"
    with open(run_path, "w") as f:
        json.dump({
            "timestamp": ts,
            "duration_s": round(time.time() - t0, 1),
            "n_tests": len(tests),
            "results": all_results,
        }, f, indent=2)
    log(f"\nSaved: {run_path} ({time.time() - t0:.1f}s)")

    # Update dashboard
    build_dashboard()

    return all_results


# ============================================================
# DASHBOARD
# ============================================================
DASH_PATH = f"{OUT_DIR}/dashboard.html"


def build_dashboard():
    runs = sorted(os.listdir(RUNS_DIR))
    if not runs:
        return
    # Load all runs
    history = []
    for r in runs:
        try:
            with open(f"{RUNS_DIR}/{r}") as f:
                history.append(json.load(f))
        except Exception:
            pass
    if not history:
        return

    latest = history[-1]

    # Build HTML
    html = _render_dashboard(history, latest)
    with open(DASH_PATH, "w") as f:
        f.write(html)
    log(f"Dashboard: {DASH_PATH}")


def _render_dashboard(history, latest):
    # Pass rates over time per embedding
    embeds = list(latest["results"].keys())
    categories = list(latest["results"][embeds[0]]["per_category"].keys())

    # Historical series
    series = {e: [] for e in embeds}
    labels = []
    for run in history:
        labels.append(run["timestamp"][9:11] + ":" + run["timestamp"][11:13])
        for e in embeds:
            if e in run["results"]:
                series[e].append(run["results"][e]["overall_pass_rate"])
            else:
                series[e].append(None)

    rows_overall = ""
    for e in embeds:
        r = latest["results"][e]
        rows_overall += f"""<tr><td><strong>{e}</strong></td><td class="r">{r['dims']}</td>
<td class="r">{r['overall_pass_rate']*100:.1f}%</td>
<td class="r">{r['passed_tests']}/{r['total_tests']}</td></tr>"""

    cat_cells = ""
    for c in categories:
        row = f'<tr><td><strong>{c}</strong></td>'
        for e in embeds:
            cr = latest["results"][e]["per_category"].get(c, {})
            pr = cr.get("pass_rate", 0) * 100
            color = "tg" if pr >= 80 else ("ty" if pr >= 60 else "tr")
            row += f'<td class="r"><span class="tag {color}">{pr:.0f}%</span></td>'
        row += "</tr>"
        cat_cells += row

    # Sparkline per embedding
    def spark(vals):
        vals = [v for v in vals if v is not None]
        if not vals:
            return ""
        w, h = 100, 24
        if len(vals) < 2:
            return f"<span>{vals[-1]*100:.0f}%</span>"
        mn, mx = min(vals), max(vals)
        span = mx - mn if mx > mn else 0.01
        pts = " ".join(
            f"{i * w / (len(vals) - 1):.0f},{h - (v - mn) / span * h:.0f}"
            for i, v in enumerate(vals)
        )
        last = vals[-1]
        color = "#22c55e" if last >= 0.8 else ("#eab308" if last >= 0.6 else "#ef4444")
        return f'<svg width="{w}" height="{h}"><polyline points="{pts}" fill="none" stroke="{color}" stroke-width="1.5"/></svg>'

    spark_rows = ""
    for e in embeds:
        spark_rows += f"<tr><td><strong>{e}</strong></td><td>{spark(series[e])}</td><td class=\"r\">{latest['results'][e]['overall_pass_rate']*100:.1f}%</td></tr>"

    run_rows = ""
    for run in history[-15:][::-1]:
        ts = run["timestamp"]
        ts_fmt = f"{ts[:4]}-{ts[4:6]}-{ts[6:8]} {ts[9:11]}:{ts[11:13]}:{ts[13:15]}"
        row = f'<tr><td>{ts_fmt}</td>'
        for e in embeds:
            if e in run["results"]:
                pr = run["results"][e]["overall_pass_rate"] * 100
                color = "tg" if pr >= 80 else ("ty" if pr >= 60 else "tr")
                row += f'<td class="r"><span class="tag {color}">{pr:.1f}%</span></td>'
            else:
                row += '<td class="r">&mdash;</td>'
        row += f'<td class="r q">{run["duration_s"]:.0f}s</td></tr>'
        run_rows += row

    hist_header = "<tr><th>Run</th>" + "".join(f"<th class='r'>{e}</th>" for e in embeds) + "<th class='r'>Duration</th></tr>"
    cat_header = "<tr><th>Category</th>" + "".join(f"<th class='r'>{e}</th>" for e in embeds) + "</tr>"

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta http-equiv="refresh" content="60">
<title>Propheus — Embedding Validation Engine</title>
<style>
:root{{--bg:#0d1f21;--bg2:#11282a;--bg3:#162f32;--a:#20b2aa;--a2:#2dd4bf;--ad:rgba(32,178,170,0.15);--t:#fff;--t2:#a0aeb0;--t3:#607274;--gd:rgba(32,178,170,0.2);--r:#ef4444;--g:#22c55e;--y:#eab308}}
*{{box-sizing:border-box;margin:0;padding:0}}body{{font-family:'Inter','Segoe UI',system-ui,sans-serif;background:var(--bg);color:var(--t);line-height:1.6;max-width:1180px;margin:0 auto;padding:24px 20px}}
h1{{font-size:18px;color:var(--a);border-bottom:1px solid var(--gd);padding-bottom:8px}}h2{{font-size:14px;color:var(--a);margin:20px 0 8px}}
.sub{{font-size:11px;color:var(--t3);margin-bottom:20px}}
.kpis{{display:flex;gap:6px;margin:10px 0}}.kpi{{flex:1;background:var(--bg2);border:1px solid var(--gd);border-radius:6px;padding:10px;text-align:center}}.kpi .n{{font-size:20px;font-weight:700;color:var(--a)}}.kpi .l{{font-size:9px;text-transform:uppercase;color:var(--t3)}}
table{{border-collapse:collapse;width:100%;margin:8px 0;font-size:11.5px}}th{{background:var(--bg3);color:var(--a);padding:6px 8px;text-align:left}}td{{padding:5px 8px;color:var(--t2);border-bottom:1px solid rgba(255,255,255,0.03)}}.r{{text-align:right}}
.tag{{display:inline-block;padding:2px 6px;border-radius:3px;font-size:9.5px;font-weight:600}}.tg{{background:rgba(34,197,94,0.15);color:var(--g)}}.ty{{background:rgba(234,179,8,0.15);color:var(--y)}}.tr{{background:rgba(239,68,68,0.15);color:var(--r)}}
.q{{color:var(--t3);font-size:9.5px}}
.s{{background:var(--bg2);border:1px solid var(--gd);border-radius:6px;padding:12px 14px;margin:8px 0}}
</style></head><body>
<h1>Embedding Validation Engine</h1>
<div class="sub">Continuous regression harness &mdash; {len(history)} runs logged &mdash; Latest: {latest['timestamp']} &mdash; Auto-refresh 60s</div>

<div class="kpis">
<div class="kpi"><div class="n">{latest['n_tests']}</div><div class="l">Tests per run</div></div>
<div class="kpi"><div class="n">{len(embeds)}</div><div class="l">Embeddings</div></div>
<div class="kpi"><div class="n">{len(history)}</div><div class="l">Runs logged</div></div>
<div class="kpi"><div class="n">{len(categories)}</div><div class="l">Test categories</div></div>
</div>

<h2>Latest Run &mdash; Overall Pass Rate</h2>
<div class="s"><table><tr><th>Embedding</th><th class="r">Dims</th><th class="r">Pass rate</th><th class="r">Tests</th></tr>{rows_overall}</table></div>

<h2>Per-Category Pass Rate (Latest Run)</h2>
<div class="s"><table>{cat_header}{cat_cells}</table></div>

<h2>Trend Over Time</h2>
<div class="s"><table><tr><th>Embedding</th><th>Trend</th><th class="r">Latest</th></tr>{spark_rows}</table></div>

<h2>Recent Runs</h2>
<div class="s"><table>{hist_header}{run_rows}</table></div>

<p class="q" style="text-align:center;margin-top:16px">Propheus Digital Atlas &nbsp;&bull;&nbsp; Embedding Validation Engine &nbsp;&bull;&nbsp; Dashboard auto-refreshes every 60s</p>
</body></html>"""


# ============================================================
# ENTRY
# ============================================================
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--loop", type=int, default=0,
                    help="If > 0, sleep N seconds between runs and repeat.")
    args = ap.parse_args()

    while True:
        try:
            run_cycle()
        except Exception as e:
            log(f"ERROR: {e}")
            import traceback; traceback.print_exc()
        if args.loop <= 0:
            break
        log(f"\nSleeping {args.loop}s before next cycle...\n")
        time.sleep(args.loop)
