import { marked } from "marked";

marked.setOptions({ breaks: true, gfm: true });

// Wrap standalone numbers (with optional unit / % / commas) in a highlight span.
// Skips HTML tags AND entities (e.g. &#39; &amp;) so it never corrupts them —
// otherwise the "39" inside &#39; (an apostrophe) gets wrapped and breaks the entity.
function highlightNumbers(html) {
  return html.replace(/(<[^>]+>)|(&[#a-zA-Z0-9]+;)|([^<&]+)/g, (m, tag, ent, text) => {
    if (tag) return tag;
    if (ent) return ent;
    if (text == null) return m;
    return text.replace(
      /(\$?\d[\d,]*(?:\.\d+)?\s?(?:%|\/?km²|\/km|km|m\b|min)?)/g,
      '<span class="num">$1</span>'
    );
  });
}

export function renderMd(content) {
  try { return highlightNumbers(marked.parse(content || "")); }
  catch { return content || ""; }
}
