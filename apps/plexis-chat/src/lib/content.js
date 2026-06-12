import {
  Users, Train, UtensilsCrossed, Footprints, Scale, MapPin,
  Building2, GraduationCap, Sparkles, Map, MessageSquare, ShieldQuestion,
} from "lucide-react";

// Sample questions — every one resolves to a named subzone / planning area, so the
// model runs in its grounded "reason-in-context" production mode (its strong suit).
export const SAMPLE_QUESTIONS = [
  { icon: Map,             color: "#17c7ba", text: "Give me a full read on Punggol — people, transit, and where the opportunities are" },
  { icon: Users,           color: "#5AA9E6", text: "How family-friendly is Bishan, and what drives that score?" },
  { icon: UtensilsCrossed, color: "#FC6238", text: "Where's the F&B opportunity in Jurong East?" },
  { icon: Scale,           color: "#8E3CCB", text: "What is Tampines East most under-served for?" },
  { icon: Train,           color: "#F59E0B", text: "Does Woodlands keep its workers local, or do they commute out?" },
  { icon: Sparkles,        color: "#2A9D8F", text: "Why is Clementi vibrant, and who lives there?" },
];

// "Model-only" showcase questions — things RAG-alone can't do: closed-book
// Singapore-calibrated judgment, data-semantics it was trained on, and honest
// abstention. Shown as pills on the landing page.
export const SHOWCASE_QUESTIONS = [
  "What is Bedok North most under-served for, and is it a strong catchment?",
  "How livable is Toa Payoh, and what's driving it?",
  "Where's the biggest café gap in the East region?",
  "Is Tampines more of a bedroom town or an employment hub?",
  "What's the difference between a hawker centre and hawker eateries?",
  "What's the crime rate in Tampines?",
];

// What Plexis-Mind can / can't answer — shown in the Help modal.
export const CAPABILITIES = [
  {
    icon: MapPin, title: "Area profiles & character",
    desc: "“What's Punggol like?”, “Is Bedok North good for families?” — vibe, suitability and a feel for a neighbourhood.",
  },
  {
    icon: UtensilsCrossed, title: "Places & amenities",
    desc: "Hawker food, cafés, clinics, shops, schools — how many and what mix an area has.",
  },
  {
    icon: Users, title: "Population & demographics",
    desc: "Resident population, density, and the broad makeup of an area.",
  },
  {
    icon: Footprints, title: "Walkability & vibrancy",
    desc: "How walkable, transit-connected and lively a subzone is.",
  },
  {
    icon: Train, title: "Commuter flows",
    desc: "Where people travel on a typical weekday, top destinations, and how self-contained an area is.",
  },
  {
    icon: Scale, title: "Comparisons",
    desc: "Put two areas side by side — “Compare Tampines East and Jurong East”.",
  },
];

export const TIPS = [
  { icon: Map, title: "Name a specific area",
    desc: "Alchemy grounds answers in the atlas. Mention a subzone or planning area (e.g. “Tampines East”, “Clementi”) for the sharpest, fact-checked replies." },
  { icon: Sparkles, title: "Ask naturally",
    desc: "Plain questions work great — “is it dense?”, “good for families?”, “where do people commute to?”." },
  { icon: ShieldQuestion, title: "It won't bluff",
    desc: "If something isn't in the atlas, it tells you rather than inventing an answer." },
];

export const LIMITS = [
  "Singapore only — 332 subzones, 55 planning areas, 5 regions.",
  "No crime, weather, real-time conditions, or exact income figures.",
  "Commuter flows are weekday monthly aggregates (no weekend / time-of-day).",
  "For exact, up-to-the-minute counts, pair it with the atlas tools — closed-book numbers are approximate.",
];

export const ICONS = { Building2, GraduationCap, MessageSquare };
