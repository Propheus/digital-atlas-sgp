import { useStore } from "../state/store";

export function MetaBar() {
  const summary = useStore((s) => s.summary);
  if (!summary) return null;
  const fmt = (v: number | null | undefined) =>
    v == null ? "—" : (v as number).toFixed(2);
  const items: Array<[string, string]> = [
    ["stability", fmt(summary.stability_ari)],
    ["silhouette", fmt(summary.silhouette)],
    ["modes", String(summary.n_clusters)],
    ["labels used", "0"],
    [
      "variance retained",
      `${Math.round(summary.pca_variance_retained * 100)}%`,
    ],
    ["resolver", "kmeans · pca → umap"],
  ];
  return (
    <div className="border-b border-[#18342d] px-10 py-5 flex flex-wrap gap-x-10 gap-y-3">
      {items.map(([k, v]) => (
        <span key={k} className="label-mono" style={{ fontSize: 10.5 }}>
          {k}{" "}
          <b className="text-[var(--color-accent)] font-medium tracking-[0.12em]">
            {v}
          </b>
        </span>
      ))}
    </div>
  );
}
