import { create } from "zustand";

export type ViewMode = "geo" | "latent";

export type HexPoint = {
  hex_id: string;
  x: number;
  y: number;
  lat: number;
  lng: number;
  cluster: number;
  subzone: string;
  region: string;
};

export type ClusterLabel = {
  code: string;
  name: string;
  blurb: string;
};

export type ClusterFeature = { name: string; z: number };

export type ClusterSummary = {
  cluster: number;
  n: number;
  share: number;
  centroid_lat: number;
  centroid_lng: number;
  top_positive_features: ClusterFeature[];
  top_negative_features: ClusterFeature[];
  top_subzones: Record<string, number>;
  top_regions: Record<string, number>;
};

export type SummaryDoc = {
  feature_set: string;
  n_hexes: number;
  n_features: number;
  pca_dim: number;
  pca_variance_retained: number;
  umap_n_neighbors: number;
  umap_min_dist: number;
  method: string;
  n_clusters: number;
  silhouette: number;
  stability_ari: number | null;
  seed: number;
  clusters: ClusterSummary[];
};

type Store = {
  embedding: HexPoint[];
  labels: Record<string, ClusterLabel>;
  summary: SummaryDoc | null;
  hoverHex: string | null;
  selectedCluster: number | null;
  view: ViewMode;
  setHoverHex: (id: string | null) => void;
  setSelectedCluster: (c: number | null) => void;
  setView: (v: ViewMode) => void;
  setData: (
    embedding: HexPoint[],
    labels: Record<string, ClusterLabel>,
    summary: SummaryDoc,
  ) => void;
};

export const useStore = create<Store>((set) => ({
  embedding: [],
  labels: {},
  summary: null,
  hoverHex: null,
  selectedCluster: null,
  view: "geo",
  setHoverHex: (id) => set({ hoverHex: id }),
  setSelectedCluster: (c) =>
    set((s) => ({ selectedCluster: s.selectedCluster === c ? null : c })),
  setView: (view) => set({ view }),
  setData: (embedding, labels, summary) => set({ embedding, labels, summary }),
}));

export const CLUSTER_PALETTE = [
  "#7af5c5", // mint
  "#f4cf9d", // cream
  "#9bd1ff", // sky
  "#c4f560", // lime
  "#ff8fa3", // rose
  "#b794f4", // lavender
  "#fce38a", // sand
  "#5eead4", // teal
];

export function colorForCluster(c: number, alpha = 255): [number, number, number, number] {
  const hex = CLUSTER_PALETTE[c % CLUSTER_PALETTE.length];
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return [r, g, b, alpha];
}
