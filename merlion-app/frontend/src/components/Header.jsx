import PropheusLogo from "./PropheusLogo";

export default function Header({ apiStatus }) {
  return (
    <header className="glass sticky top-0 z-30 flex items-center justify-between px-6 py-3">
      <div className="flex items-center gap-3">
        <PropheusLogo size={30} />
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-lg font-semibold tracking-tight">
              <span className="text-accent">REAL WORLD ENGINE</span>
              <span className="text-fg-2 text-sm font-normal ml-2">by Propheus</span>
            </h1>
          </div>
          <p className="text-[10px] text-fg-3 tracking-wide uppercase">
            Singapore Urban Intelligence · powered by Merlion
          </p>
        </div>
      </div>
      <div className="flex items-center gap-4 text-xs text-fg-2">
        <a href="#" className="hover:text-accent">Use Cases</a>
        <a href="#" className="hover:text-accent">Audit</a>
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${apiStatus === "ok" ? "bg-ok live-dot" : "bg-err"}`} />
          <span>{apiStatus === "ok" ? "Engine live" : "Engine offline"}</span>
        </div>
      </div>
    </header>
  );
}
