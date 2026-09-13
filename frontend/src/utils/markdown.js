/**
 * Formats simple markdown strings into sanitized HTML markup for chatbot responses.
 * @param {string} text
 * @returns {string} HTML string
 */
export function renderMarkdown(text) {
  if (!text) return "";

  // Replace HTML tag brackets to prevent injection
  let safeText = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  // Bold (**text**)
  safeText = safeText.replace(/\*\*(.*?)\*\*/g, '<strong class="text-on-surface font-semibold">$1</strong>');

  // Inline code (`code`)
  safeText = safeText.replace(/`(.*?)`/g, '<code class="bg-surface-variant px-1.5 py-0.5 rounded font-mono text-xs text-primary">$1</code>');

  // Bullet points
  const lines = safeText.split("\n");
  const processedLines = lines.map(line => {
    const trimmed = line.trim();
    if (trimmed.startsWith("- ")) {
      return `<li class="ml-4 list-disc text-on-surface-variant my-1.5">${trimmed.slice(2)}</li>`;
    }
    if (trimmed.startsWith("* ")) {
      return `<li class="ml-4 list-disc text-on-surface-variant my-1.5">${trimmed.slice(2)}</li>`;
    }
    return trimmed ? `<p class="mb-4 leading-relaxed">${trimmed}</p>` : "";
  });

  return processedLines.join("");
}
