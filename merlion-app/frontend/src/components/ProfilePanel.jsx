"use client";
import { motion } from "framer-motion";
import { Sparkles, DollarSign, Users, MapPin, Zap, Building } from "lucide-react";

const TIER_COLORS = {
  value: "bg-ok/15 text-ok",
  mid: "bg-accent-dim text-accent",
  premium: "bg-warn/15 text-warn",
  luxury: "bg-err/15 text-err",
};

export default function ProfilePanel({ profile }) {
  if (!profile) return null;

  const tierColor = TIER_COLORS[profile.price_tier] || "bg-bg-3 text-fg-2";

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass rounded-xl p-4 space-y-3"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2">
          <Sparkles size={16} className="text-accent" />
          <div>
            <div className="text-sm font-semibold text-fg">{profile.name}</div>
            <div className="text-[10px] text-fg-3 italic">{profile.kind}</div>
          </div>
        </div>
        <div className="flex items-center gap-1.5">
          <span className={`text-[10px] uppercase px-2 py-0.5 rounded ${tierColor}`}>
            {profile.price_tier}
          </span>
          <span className="text-[10px] uppercase px-2 py-0.5 rounded bg-bg-3 text-fg-3">
            {profile.source}
          </span>
        </div>
      </div>

      {profile.reasoning && (
        <p className="text-[11px] text-fg-2 italic leading-relaxed border-l-2 border-accent/50 pl-2">
          {profile.reasoning}
        </p>
      )}

      {/* Grid of profile facets */}
      <div className="grid grid-cols-2 gap-2 text-[11px]">
        {profile.primary_category && (
          <Facet icon={<Building size={11} />} label="Primary category" value={profile.primary_category} />
        )}
        {profile.target_demographics?.income_band && (
          <Facet icon={<DollarSign size={11} />} label="Income" value={profile.target_demographics.income_band} />
        )}
        {profile.target_demographics?.age_range && (
          <Facet icon={<Users size={11} />} label="Target" value={profile.target_demographics.age_range} />
        )}
        {profile.target_demographics?.household && (
          <Facet icon={<Building size={11} />} label="Household" value={profile.target_demographics.household} />
        )}
      </div>

      {(profile.locality_fit?.length > 0 || profile.locality_avoid?.length > 0) && (
        <div className="text-[11px] space-y-1">
          {profile.locality_fit?.length > 0 && (
            <div className="flex items-start gap-2">
              <MapPin size={11} className="text-ok mt-0.5 shrink-0" />
              <span className="text-fg-3 shrink-0">fit:</span>
              <span className="text-ok font-mono text-[10px] flex-1">
                {profile.locality_fit.join(", ")}
              </span>
            </div>
          )}
          {profile.locality_avoid?.length > 0 && (
            <div className="flex items-start gap-2">
              <MapPin size={11} className="text-err mt-0.5 shrink-0" />
              <span className="text-fg-3 shrink-0">avoid:</span>
              <span className="text-err font-mono text-[10px] flex-1">
                {profile.locality_avoid.join(", ")}
              </span>
            </div>
          )}
        </div>
      )}

      {profile.signals && Object.keys(profile.signals).length > 0 && (
        <div className="space-y-1 pt-2 border-t border-brd/30">
          <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-fg-3">
            <Zap size={10} className="text-accent" />
            scoring signals ({Object.keys(profile.signals).length})
          </div>
          <div className="space-y-0.5">
            {Object.entries(profile.signals).map(([feat, spec]) => (
              <div key={feat} className="flex items-center gap-2 text-[10.5px] font-mono">
                <div className="flex-1 text-fg-2 truncate">{feat}</div>
                <div className="flex items-center gap-1.5">
                  <WeightBar weight={spec.weight || 0} />
                  <span className={spec.direction === "low" ? "text-err" : "text-ok"}>
                    {spec.direction === "low" ? "↓" : "↑"}
                  </span>
                  {spec.min !== undefined && (
                    <span className="text-fg-3">≥{spec.min}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {profile.competitor_brands?.length > 0 && (
        <div className="flex items-center gap-2 text-[10px] pt-2 border-t border-brd/30 flex-wrap">
          <span className="text-fg-3 uppercase tracking-wider">competes with:</span>
          {profile.competitor_brands.map((b) => (
            <span key={b} className="px-1.5 py-0.5 bg-bg-3 rounded text-fg-2">{b}</span>
          ))}
        </div>
      )}
    </motion.div>
  );
}

function Facet({ icon, label, value }) {
  return (
    <div className="bg-bg-3/40 rounded px-2 py-1.5">
      <div className="flex items-center gap-1 text-fg-3 text-[9px] uppercase tracking-wide mb-0.5">
        {icon}
        {label}
      </div>
      <div className="text-fg-2 font-mono text-[10.5px] truncate">{value}</div>
    </div>
  );
}

function WeightBar({ weight }) {
  const pct = Math.min(100, Math.round(weight * 100));
  return (
    <div className="w-10 h-1 bg-bg-3 rounded-full overflow-hidden">
      <div className="h-full bg-accent" style={{ width: `${pct}%` }} />
    </div>
  );
}
