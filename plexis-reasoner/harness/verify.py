"""
Verifier — grade a trajectory against its gold spec. This is the rejection-
sampling filter for SFT and (later) the GRPO reward. Deterministic where the
atlas can compute the answer; evidence-based for judgment.
"""
import re

ABSTAIN_CUES = ["not in the atlas", "doesn't contain", "does not contain",
                "no crime", "not track", "cannot provide", "don't have",
                "do not have", "not covered", "no data on", "isn't available",
                "not available"]


def _nums(text):
    return [float(x.replace(",", "")) for x in
            re.findall(r"-?\d[\d,]*\.?\d*", text or "")]


def grade(trace, gold):
    """Return (ok, reward, reason). ok = keep for SFT; reward in [0,1] for GRPO."""
    ans = (trace.get("answer") or "").lower()
    used = [c["tool"] for c in trace.get("calls", [])]
    kind = gold.get("kind")

    # grounding check: did it actually USE tools (not hallucinate)?
    grounded = len(used) >= 1
    # soft bonus if it used a relevant tool family (efficiency-agnostic)
    relevant = bool(set(used) & set(gold.get("must_use", []) +
                                    gold.get("must_use_any", [])))

    if kind == "abstain":
        abstained = any(c in ans for c in ABSTAIN_CUES)
        fabricated = len(_nums(ans)) > 0 and not abstained
        ok = abstained and not fabricated
        return ok, (1.0 if ok else 0.0), ("abstained" if ok else "should have abstained")

    if kind == "entity":
        if not gold.get("answer"):
            return False, 0.0, "no gold"
        hit = gold["answer"].lower() in ans
        ok = hit and grounded                       # correctness, not tool-path
        return ok, (1.0 if hit else 0.0), \
            ("correct" if hit else f"expected {gold['answer']}")

    if kind == "any_of":
        hit = any(n.lower() in ans for n in gold["answer"])
        ok = hit and grounded
        return ok, (1.0 if hit else 0.0), ("named a twin" if hit else "named none")

    if kind == "number":
        target = gold["answer"]; tol = gold.get("tol", 0.1)
        got = _nums(trace.get("answer", ""))
        hit = any(abs(g - target) <= abs(target) * tol for g in got) if got else False
        ok = hit and grounded
        return ok, (1.0 if hit else 0.0), ("in tolerance" if hit else f"expected ~{target}")

    if kind == "judgment":
        # no answer key; keep if it gathered relevant evidence + gave a real verdict
        ok = relevant and len(ans) > 80
        return ok, (1.0 if ok else 0.3), ("evidence-grounded" if ok else "thin evidence")

    return False, 0.0, f"unknown gold kind {kind}"
