// Generate follow-up questions that ALWAYS embed the entity name literally,
// so the server's entity scanner re-grounds them (a pronoun like "it" would
// silently drop to the ungrounded mode). Picks templates not matching the
// just-asked question.

const TEMPLATES = [
  (e) => `What is ${e} most under-served for?`,
  (e) => `Where's the F&B opportunity in ${e}?`,
  (e) => `How family-friendly is ${e}, and what drives that score?`,
  (e) => `Is ${e} a bedroom town or an employment hub?`,
  (e) => `Why is ${e} vibrant — or isn't it?`,
  (e) => `What is ${e} a strong demand draw for?`,
  (e) => `How livable is ${e}, and what's holding it back?`,
  (e) => `Is ${e} a good place for young professionals?`,
];

export function followUps(entity, lastQuestion = "", n = 3) {
  if (!entity) return [];
  // entity may be "A & B" (comparison) — use the first named area for follow-ups
  const e = entity.split(" & ")[0].trim();
  const lq = (lastQuestion || "").toLowerCase();
  const picks = [];
  for (const t of TEMPLATES) {
    const q = t(e);
    // skip near-duplicates of what was just asked
    const key = q.toLowerCase().replace(e.toLowerCase(), "").slice(0, 18);
    if (lq && lq.includes(key.trim().split(" ").slice(0, 3).join(" "))) continue;
    picks.push(q);
    if (picks.length >= n) break;
  }
  return picks;
}
