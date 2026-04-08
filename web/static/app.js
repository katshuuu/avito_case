(function () {
  const form = document.getElementById("form");
  const demoModeEl = document.getElementById("mode_toggle");
  const modeLabelNormal = document.getElementById("mode-label-normal");
  const modeLabelDemo = document.getElementById("mode-label-demo");
  const demoSampleWrap = document.getElementById("demo-sample-wrap");
  const demoSampleSelect = document.getElementById("demo_sample_id");
  const out = document.getElementById("out");
  const demoSteps = document.getElementById("demo-steps");
  const stepsList = document.getElementById("steps-list");
  const demoProgress = document.getElementById("demo-progress");
  const progressStepEls = Array.from(document.querySelectorAll(".progress-step"));
  const downloadWrap = document.getElementById("download-wrap");
  const downloadLink = document.getElementById("download-link");
  const err = document.getElementById("error");
  const submit = document.getElementById("submit");
  const LOCAL_DEMO_FALLBACK = [
    { id: "case_1000002", title: "Комплексный ремонт под ключ (без split)" },
    { id: "case_1000012", title: "Короткое перечисление отделочных услуг (split)" },
    { id: "case_1002461", title: "Натяжные потолки (split)" },
  ];

  let demoSamplesLoaded = false;
  let demoSamplesLoading = false;
  let demoSamplesError = false;
  let demoSamples = [];

  initDemoSamples();
  demoModeEl.addEventListener("change", onDemoModeToggle);

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    err.classList.add("hidden");
    err.textContent = "";
    out.classList.add("hidden");
    demoSteps.classList.add("hidden");
    demoProgress.classList.add("hidden");
    downloadWrap.classList.add("hidden");
    stepsList.innerHTML = "";
    resetProgress();
    submit.disabled = true;

    const body = {
      description: document.getElementById("description").value.trim(),
      mcId: parseInt(document.getElementById("mcId").value, 10) || 101,
      mcTitle: document.getElementById("mcTitle").value.trim() || "Ремонт квартир и домов под ключ",
      use_llm_drafts: document.getElementById("use_llm_drafts").checked,
      async_drafts: document.getElementById("async_drafts").checked,
      demo_mode: demoModeEl.checked,
      demo_sample_id: demoSampleSelect.value || null,
    };

    try {
      if (body.demo_mode) {
        demoProgress.classList.remove("hidden");
        setProgressStep(1, "active");
      }
      const endpoint = body.demo_mode ? "/api/analyze_demo" : "/api/analyze";
      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data.detail || res.statusText || "Ошибка запроса");
      }
      if (body.demo_mode) {
        setProgressStep(1, "done");
        setProgressStep(2, "active");
        render(data.result || {});
        setProgressStep(2, "done");
        setProgressStep(3, "active");
        renderSteps(data.steps || []);
        if (data.downloadUrl) {
          downloadLink.href = data.downloadUrl;
          downloadWrap.classList.remove("hidden");
        }
        setProgressStep(3, "done");
        demoSteps.classList.remove("hidden");
      } else {
        render(data);
      }
      out.classList.remove("hidden");
      if (!body.demo_mode && data.draftJobId) {
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

  async function initDemoSamples() {
    demoSamplesLoading = true;
    demoSamplesError = false;
    demoSampleSelect.innerHTML = "";
    const loadingOpt = document.createElement("option");
    loadingOpt.value = "";
    loadingOpt.textContent = "Загрузка готовых примеров...";
    demoSampleSelect.appendChild(loadingOpt);
    try {
      const res = await fetch("/api/demo_samples?limit=10");
      const payload = await res.json().catch(() => ({}));
      const samples = payload.samples || [];
      demoSamples = samples;
      demoSampleSelect.innerHTML = "";
      if (!samples.length) {
        const emptyOpt = document.createElement("option");
        emptyOpt.value = "";
        emptyOpt.textContent = "Нет заготовленных примеров";
        demoSampleSelect.appendChild(emptyOpt);
      }
      samples.forEach((s) => {
        const opt = document.createElement("option");
        opt.value = s.id;
        opt.textContent = s.title || s.id;
        demoSampleSelect.appendChild(opt);
      });
      demoSampleSelect.addEventListener("change", applySelectedDemoSample);
      applySelectedDemoSample();
      demoSamplesLoaded = samples.length > 0;
    } catch (_e) {
      demoSampleSelect.innerHTML = "";
      LOCAL_DEMO_FALLBACK.forEach((s) => {
        const opt = document.createElement("option");
        opt.value = s.id;
        opt.textContent = s.title;
        demoSampleSelect.appendChild(opt);
      });
      demoSamples = [];
      demoSamplesError = true;
      demoSamplesLoaded = true;
    } finally {
      demoSamplesLoading = false;
    }
    onDemoModeToggle();
  }

  function onDemoModeToggle() {
    if (demoModeEl.checked) {
      modeLabelNormal.classList.remove("active");
      modeLabelDemo.classList.add("active");
      demoSampleWrap.classList.remove("hidden");
      if (!demoSamplesLoaded && !demoSamplesLoading && !demoSamplesError) {
        initDemoSamples();
      }
      document.getElementById("description").setAttribute("disabled", "disabled");
      document.getElementById("mcId").setAttribute("disabled", "disabled");
      document.getElementById("mcTitle").setAttribute("disabled", "disabled");
      applySelectedDemoSample();
    } else {
      modeLabelDemo.classList.remove("active");
      modeLabelNormal.classList.add("active");
      demoSampleWrap.classList.add("hidden");
      document.getElementById("description").removeAttribute("disabled");
      document.getElementById("mcId").removeAttribute("disabled");
      document.getElementById("mcTitle").removeAttribute("disabled");
    }
  }

  function applySelectedDemoSample() {
    if (!demoModeEl.checked) return;
    const selectedId = demoSampleSelect.value;
    const selected = demoSamples.find((s) => s.id === selectedId);
    if (!selected || !selected.item) return;
    document.getElementById("description").value = selected.item.description || "";
    if (selected.item.mcId != null) {
      document.getElementById("mcId").value = String(selected.item.mcId);
    }
    if (selected.item.mcTitle) {
      document.getElementById("mcTitle").value = selected.item.mcTitle;
    }
  }

  function resetProgress() {
    progressStepEls.forEach((el) => {
      el.classList.remove("active", "done");
    });
  }

  function setProgressStep(stepNum, state) {
    const el = progressStepEls.find((x) => x.dataset.step === String(stepNum));
    if (!el) return;
    el.classList.remove("active", "done");
    if (state === "active") el.classList.add("active");
    if (state === "done") el.classList.add("done");
  }

  function renderSteps(steps) {
    stepsList.innerHTML = "";
    if (!steps.length) {
      stepsList.innerHTML = '<p class="draft-meta">Шаги обработки не получены.</p>';
      return;
    }
    steps.forEach((step, idx) => {
      const block = document.createElement("div");
      block.className = "step-item";
      const details = step.details ? "<p>" + escapeHtml(step.details) + "</p>" : "";
      const items = Array.isArray(step.items) && step.items.length
        ? "<pre class=\"json-block\">" + escapeHtml(JSON.stringify(step.items, null, 2)) + "</pre>"
        : "";
      block.innerHTML =
        "<h4>Шаг " + (idx + 1) + ": " + escapeHtml(step.title || "Без названия") + "</h4>" +
        details +
        items;
      stepsList.appendChild(block);
    });
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
