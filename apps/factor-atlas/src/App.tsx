import { useEffect } from "react";
import { Header } from "./components/Header";
import { MetaBar } from "./components/MetaBar";
import { CenterMap } from "./components/CenterMap";
import { Footer } from "./components/Footer";
import { useStore } from "./state/store";

export default function App() {
  const setData = useStore((s) => s.setData);
  const loaded = useStore((s) => s.summary != null);

  const setView = useStore((s) => s.setView);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const v = params.get("view");
    if (v === "latent" || v === "geo") setView(v);
    (async () => {
      const [emb, lab, sum] = await Promise.all([
        fetch("/data/embedding.json").then((r) => r.json()),
        fetch("/data/labels.json").then((r) => r.json()),
        fetch("/data/cluster_summary.json").then((r) => r.json()),
      ]);
      setData(emb, lab, sum);
    })();
  }, [setData, setView]);

  return (
    <main className="min-h-screen bg-[#081915]">
      <div className="max-w-[1760px] mx-auto">
        <Header />
        <MetaBar />
        {!loaded && (
          <div className="px-10 py-24 label-mono">
            loading factor decomposition…
          </div>
        )}
        {loaded && <CenterMap />}
        {loaded && <Footer />}
      </div>
    </main>
  );
}
