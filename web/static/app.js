(function () {
  const form = document.getElementById("form");
  const out = document.getElementById("out");
  const err = document.getElementById("error");
  const submit = document.getElementById("submit");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    err.classList.add("hidden");
    err.textContent = "";
    out.classList.add("hidden");
    submit.disabled = true;

    const body = {
      description: document.getElementById("description").value.trim(),
      mcId: parseInt(document.getElementById("mcId").value, 10) || 101,
      mcTitle: document.getElementById("mcTitle").value.trim() || "Ремонт квартир и домов под ключ",
      use_llm_drafts: document.getElementById("use_llm_drafts").checked,
      async_drafts: document.getElementById("async_drafts").checked,
    };

    try {
      const res = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data.detail || res.statusText || "Ошибка запроса");
      }
      render(data);
      out.classList.remove("hidden");
      if (data.draftJobId) {
        pollDrafts(data.draftJobId);
      }
    } catch (x) {
      err.textContent = String(x.message || x);
      err.classList.remove("hidden");
    } finally {
      submit.disabled = false;
    }
  });

  function render(data) {
    document.getElementById("detected").textContent = JSON.stringify(
      data.detectedMcIds || [],
      null,
      0
    );
    document.getElementById("shouldSplit").textContent = JSON.stringify(
      data.shouldSplit,
      null,
      0
    );
    document.getElementById("raw").textContent = JSON.stringify(data, null, 2);

    const flag = document.getElementById("flag-split");
    if (data.shouldSplit) {
      flag.textContent = "Нужны дополнительные черновики (shouldSplit: true)";
      flag.className = "badge yes";
    } else {
      flag.textContent = "Дополнительные черновики не требуются (shouldSplit: false)";
      flag.className = "badge no";
    }

    renderDrafts(data.drafts || []);
  }

  function renderDrafts(drafts) {
    const draftsEl = document.getElementById("drafts");
    draftsEl.innerHTML = "";
    if (drafts.length === 0) {
      draftsEl.innerHTML =
        '<p class="draft-meta">Черновики не сформированы (сплит не требуется или нет услуг).</p>';
      return;
    }
    drafts.forEach((d) => {
      const div = document.createElement("div");
      div.className = "draft-item";
      div.innerHTML =
        '<div class="draft-meta">mcId: ' +
        escapeHtml(String(d.mcId)) +
        "</div>" +
        "<h4>" +
        escapeHtml(d.mcTitle || "") +
        "</h4>" +
        '<div class="draft-text">' +
        escapeHtml(d.text || "") +
        "</div>";
      draftsEl.appendChild(div);
    });
  }

  async function pollDrafts(jobId) {
    const draftsEl = document.getElementById("drafts");
    draftsEl.innerHTML =
      '<p class="draft-meta">Черновики генерируются в фоне. Обновляем...</p>';
    for (let i = 0; i < 20; i++) {
      await sleep(500);
      const res = await fetch("/api/drafts/" + encodeURIComponent(jobId));
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        draftsEl.innerHTML =
          '<p class="draft-meta">Не удалось получить статус фоновой задачи.</p>';
        return;
      }
      if (data.status === "completed") {
        renderDrafts(data.drafts || []);
        return;
      }
      if (data.status === "failed") {
        draftsEl.innerHTML =
          '<p class="draft-meta">Фоновая генерация завершилась с ошибкой.</p>';
        return;
      }
    }
    draftsEl.innerHTML =
      '<p class="draft-meta">Черновики формируются дольше обычного. Проверьте позже.</p>';
  }

  function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  function escapeHtml(s) {
    const map = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" };
    return s.replace(/[&<"]/g, (c) => map[c] || c);
  }
})();
