// Chat widget. Talks to /chat. Works whether the server uses Claude or the offline engine.
(() => {
  const $ = (id) => document.getElementById(id);
  const log = $("log"), panel = $("panel"), bubble = $("bubble"), q = $("q"), hist = [];
  let busy = false;

  function add(text, cls) {
    const d = document.createElement("div");
    d.className = "m " + cls;
    d.textContent = text; // textContent, never innerHTML: replies are untrusted text
    log.appendChild(d);
    log.scrollTop = log.scrollHeight;
    return d;
  }
  function toggle(open) {
    panel.classList.toggle("open", open);
    bubble.setAttribute("aria-expanded", String(open));
    if (open) q.focus(); else bubble.focus();
  }
  async function send(text) {
    text = text.trim();
    if (!text || busy) return;
    busy = true;
    toggle(true);
    add(text, "me");
    hist.push({ role: "user", content: text });
    q.value = "";
    const wait = add("...", "bot");
    try {
      const r = await fetch("/chat", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ messages: hist }) });
      const j = await r.json();
      wait.textContent = j.reply;
      hist.push({ role: "assistant", content: j.reply });
    } catch (e) {
      wait.textContent = "Connection problem. Please try again.";
      hist.pop(); // drop the unanswered question so the history keeps alternating
    }
    busy = false;
  }

  bubble.addEventListener("click", () => toggle(!panel.classList.contains("open")));
  $("closeChat").addEventListener("click", () => toggle(false));
  panel.addEventListener("keydown", (e) => { if (e.key === "Escape") toggle(false); });
  $("row").addEventListener("submit", (e) => { e.preventDefault(); send(q.value); });
  document.querySelectorAll("#chips button").forEach((b) => b.addEventListener("click", () => send(b.textContent)));
  add("Hi! I can help with our menu, hours, flowers and delivery.", "bot");
})();
