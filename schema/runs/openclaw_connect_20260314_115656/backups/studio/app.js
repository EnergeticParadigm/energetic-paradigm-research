const OPENCLAW_API_BASE = "http://127.0.0.1:8000";
const API_BASE = OPENCLAW_API_BASE;
window.OPENCLAW_API_BASE = OPENCLAW_API_BASE;
window.API_BASE = API_BASE;

(function () {
  const topicEl = document.getElementById("topic");
  const materialEl = document.getElementById("material");
  const outputEl = document.getElementById("output");
  const statusEl = document.getElementById("status");
  const generateBtn = document.getElementById("generateBtn");
  const clearBtn = document.getElementById("clearBtn");

  const endpoints = ["/generate", "/api/generate", "/run", "/submit", "/prompt", "/jobs"];

  function setStatus(text) {
    statusEl.textContent = text;
  }

  function setOutput(value) {
    if (typeof value === "string") {
      outputEl.textContent = value;
      return;
    }
    outputEl.textContent = JSON.stringify(value, null, 2);
  }

  async function postJson(url, payload) {
    const resp = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const text = await resp.text();
    let data;
    try {
      data = JSON.parse(text);
    } catch {
      data = text;
    }
    return { ok: resp.ok, status: resp.status, data };
  }

  async function generate() {
    const topic = topicEl.value.trim();
    const material = materialEl.value.trim();
    const payload = {
      topic,
      material,
      input: material,
      text: material,
      prompt: topic ? `${topic}\n\n${material}`.trim() : material,
      content: material
    };

    setStatus("Generating");
    setOutput("");

    let lastResult = null;

    for (const endpoint of endpoints) {
      try {
        const result = await postJson(endpoint, payload);
        lastResult = { endpoint, ...result };
        if (result.ok) {
          setStatus(`Success: ${endpoint}`);
          setOutput(result.data);
          return;
        }
      } catch (err) {
        lastResult = { endpoint, ok: false, status: 0, data: String(err) };
      }
    }

    setStatus("Failed");
    setOutput(lastResult || "No backend route responded.");
  }

  generateBtn.addEventListener("click", generate);
  clearBtn.addEventListener("click", function () {
    topicEl.value = "";
    materialEl.value = "";
    setStatus("Idle");
    setOutput("");
  });
})();
