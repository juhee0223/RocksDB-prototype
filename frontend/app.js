function formatJSON(data) {
  return JSON.stringify(data, null, 2);
}

// Recent activity tracking (client-side only)
const RECENT_LIMIT = 5;
let recentActivity = [];

function pushActivity(text) {
  // keep newest at the end; remove oldest when exceeding limit
  recentActivity.push(text);
  if (recentActivity.length > RECENT_LIMIT) recentActivity.shift();
  renderRecentActivity();
}

function renderRecentActivity() {
  const ul = document.getElementById("recentActivity");
  if (!ul) return;
  ul.innerHTML = "";
  // show newest first
  for (let i = recentActivity.length - 1; i >= 0; i--) {
    const li = document.createElement("li");
    li.textContent = recentActivity[i];
    ul.appendChild(li);
  }
}

function showResult(el, text, type = "info") {
  el.classList.remove("success", "error");
  if (type === "success") el.classList.add("success");
  if (type === "error") el.classList.add("error");
  el.textContent = text;
  // show Bootstrap toast as well if available
  try {
    showToast(type === "error" ? "Error" : "Info", text, type);
  } catch (e) {
    // ignore if bootstrap not available
  }
}

function escapeHtml(s) {
  if (s == null) return "";
  return String(s).replace(/[&<>"'`]/g, function (c) {
    return ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#39;',
      '`': '&#96;'
    })[c];
  });
}

function showToast(title, message, type = "info") {
  const toastEl = document.getElementById("liveToast");
  if (!toastEl) return;
  const toastTitle = toastEl.querySelector("#toastTitle");
  const toastBody = toastEl.querySelector("#toastBody");
  toastTitle.textContent = title;
  toastBody.textContent = message;
  // color header for error/success
  toastEl.querySelector(".toast-header").classList.remove("bg-success", "bg-danger", "text-white");
  if (type === "success") {
    toastEl.querySelector(".toast-header").classList.add("bg-success", "text-white");
  } else if (type === "error") {
    toastEl.querySelector(".toast-header").classList.add("bg-danger", "text-white");
  }
  const toast = new bootstrap.Toast(toastEl);
  toast.show();
}

async function submitWithUI(formEl, submitBtn, resultEl, fn) {
  submitBtn.disabled = true;
  const originalText = submitBtn.textContent;
  submitBtn.textContent = "...";
  showResult(resultEl, "Loading...");
  try {
    await fn();
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = originalText;
  }
}

async function handlePut(event) {
  event.preventDefault();
  const resultEl = document.getElementById("putResult");
  const key = document.getElementById("putKey").value.trim();
  const value = document.getElementById("putValue").value.trim();
  const submitBtn = event.submitter || document.querySelector("#putForm button");

  if (!value) {
    showResult(resultEl, "value is required.", "error");
    return;
  }

  await submitWithUI(event.currentTarget, submitBtn, resultEl, async () => {
    try {
      const response = await fetch("/put", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ key, value }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "PUT failed");
      showResult(resultEl, formatJSON(data), "success");
      // Log recent activity: PUT
      try {
        const k = data && data.key ? data.key : key || "(unknown)";
        pushActivity(`PUT key=${k} (OK)`);
      } catch (e) {
        /* ignore logging errors */
      }
      // PUT UX: show small success message in the card
      try {
        const putStatus = document.getElementById("putStatus");
        const savedKey = data && data.key ? data.key : key || "(unknown)";
        if (putStatus) putStatus.innerHTML = `<span class="status-success">[✔] Key saved: ${escapeHtml(savedKey)}</span>`;
      } catch (e) {}
      // Clear both key and value inputs to make the next entry fast,
      // and focus the value input for immediate typing.
      try {
        const keyInput = document.getElementById("putKey");
        const valueInput = document.getElementById("putValue");
        if (valueInput) valueInput.value = "";
        if (keyInput) keyInput.value = "";
        if (valueInput) valueInput.focus();
      } catch (e) {
        /* ignore focus errors */
      }
    } catch (err) {
      showResult(resultEl, `Error: ${err.message}`, "error");
      try { pushActivity(`PUT key=${key || '(generated)'} (Error: ${err.message})`); } catch (e) {}
      try {
        const putStatus = document.getElementById("putStatus");
        if (putStatus) putStatus.innerHTML = `<span class="status-error">[!] Failed to save key</span>`;
      } catch (e) {}
    }
  });
}

async function handleGet(event) {
  event.preventDefault();
  const resultEl = document.getElementById("getResult");
  const key = document.getElementById("getKey").value.trim();
  const submitBtn = event.submitter || document.querySelector("#getForm button");

  if (!key) {
    showResult(resultEl, "key is required.", "error");
    return;
  }

  await submitWithUI(event.currentTarget, submitBtn, resultEl, async () => {
    try {
      const response = await fetch(`/get?key=${encodeURIComponent(key)}`);
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "GET failed");
      // If GET returned found:false, style result and toast as error; otherwise success
      const getResultType = (data && typeof data.found !== "undefined" && data.found === false) ? "error" : "success";
      showResult(resultEl, formatJSON(data), getResultType);
      // Log recent activity: GET (found / not found)
      try {
        if (data && typeof data.found !== "undefined") {
          if (data.found) pushActivity(`GET key=${key} (OK)`);
          else pushActivity(`GET key=${key} (not found)`);
        } else {
          pushActivity(`GET key=${key} (OK)`);
        }
      } catch (e) {
        /* ignore logging errors */
      }
      // GET UX: only show not-found message; on success clear previous messages
      try {
        const display = document.getElementById("getValueDisplay");
        const keyInput = document.getElementById("getKey");
        if (data && typeof data.found !== "undefined" && !data.found) {
          if (display) display.innerHTML = `<span class="status-error">[!] Key not found</span>`;
          if (keyInput) keyInput.classList.add("input-error");
        } else {
          // don't re-display the value; just clear any not-found message and error state
          if (display) display.innerHTML = "";
          if (keyInput) keyInput.classList.remove("input-error");
        }
      } catch (e) {}
    } catch (err) {
      showResult(resultEl, `Error: ${err.message}`, "error");
      try { pushActivity(`GET key=${key} (Error: ${err.message})`); } catch (e) {}
      try {
        const display = document.getElementById("getValueDisplay");
        if (display) display.innerHTML = `<span class="status-error">[!] Key not found</span>`;
        const keyInput = document.getElementById("getKey");
        if (keyInput) keyInput.classList.add("input-error");
      } catch (e) {}
    }
  });
}

async function refreshStats() {
  const memtableEl = document.getElementById("memtableSize");
  const sstEl = document.getElementById("sstCount");
  try {
    const response = await fetch("/stats");
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Stats request failed");
    const mem = data.memtable_size ?? "-";
    const sst = data.num_sst_files ?? "-";
    if (memtableEl) memtableEl.textContent = mem;
    if (sstEl) sstEl.textContent = sst;
    // also update side-panel copies if present
    const memSide = document.getElementById("memtableSizeSide");
    const sstSide = document.getElementById("sstCountSide");
    if (memSide) memSide.textContent = mem;
    if (sstSide) sstSide.textContent = sst;
  } catch (err) {
    if (memtableEl) memtableEl.textContent = "!";
    if (sstEl) sstEl.textContent = "!";
    const memSide = document.getElementById("memtableSizeSide");
    const sstSide = document.getElementById("sstCountSide");
    if (memSide) memSide.textContent = "!";
    if (sstSide) sstSide.textContent = "!";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const putForm = document.getElementById("putForm");
  const getForm = document.getElementById("getForm");
  const statsBtn = document.getElementById("refreshStats");
  const statsSideBtn = document.getElementById("refreshStatsSide");

  putForm.addEventListener("submit", handlePut);
  getForm.addEventListener("submit", handleGet);
  if (statsBtn) statsBtn.addEventListener("click", refreshStats);
  if (statsSideBtn) statsSideBtn.addEventListener("click", refreshStats);

  refreshStats();
  // Keys listing controls
  const refreshKeysBtn = document.getElementById("refreshKeys");
  const prevKeysBtn = document.getElementById("prevKeys");
  const nextKeysBtn = document.getElementById("nextKeys");
  const keysFilter = document.getElementById("keysFilter");
  const keysPageEl = document.getElementById("keysPage");
  const keysTableBody = document.querySelector("#keysTable tbody");

  let keysPage = 1;
  const perPage = 50;

  async function loadKeys() {
    const q = encodeURIComponent(keysFilter.value.trim());
    const url = `/keys?page=${keysPage}&per_page=${perPage}${q ? `&q=${q}` : ""}`;
    try {
      const resp = await fetch(url);
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.error || "Failed to load keys");
      keysTableBody.innerHTML = "";
      for (const item of data.keys) {
        const tr = document.createElement("tr");
        const tdKey = document.createElement("td");
        tdKey.style.padding = "8px";
        tdKey.textContent = item.key;
        const tdVal = document.createElement("td");
        tdVal.style.padding = "8px";
        tdVal.textContent = item.value ?? "";
        tr.appendChild(tdKey);
        tr.appendChild(tdVal);
        keysTableBody.appendChild(tr);
      }
      keysPageEl.textContent = data.page;
    } catch (err) {
      keysTableBody.innerHTML = `<tr><td style=\"padding:8px;color:#9f1239;\">Error: ${err.message}</td></tr>`;
    }
  }

  refreshKeysBtn.addEventListener("click", () => {
    keysPage = 1;
    loadKeys();
  });
  prevKeysBtn.addEventListener("click", () => {
    if (keysPage > 1) {
      keysPage -= 1;
      loadKeys();
    }
  });
  nextKeysBtn.addEventListener("click", () => {
    keysPage += 1;
    loadKeys();
  });
  keysFilter.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      keysPage = 1;
      loadKeys();
    }
  });

  // initial load
  loadKeys();

  // render any pre-existing recentActivity (empty at start)
  renderRecentActivity();

  // Simulate compact button (client-side only): push a COMPACT log entry
  const simCompactBtn = document.getElementById("simulateCompact");
  if (simCompactBtn) {
    simCompactBtn.addEventListener("click", (e) => {
      e.preventDefault();
      pushActivity("COMPACT (OK)");
    });
  }

  // Enable pressing Enter in inputs to submit forms and clear error state on input
  try {
    const putFormEl = document.getElementById("putForm");
    const putKeyEl = document.getElementById("putKey");
    const putValEl = document.getElementById("putValue");
    const getKeyEl = document.getElementById("getKey");

    function submitFormOnEnter(e, formEl) {
      if (e.key === "Enter") {
        e.preventDefault();
        if (typeof formEl.requestSubmit === "function") formEl.requestSubmit();
        else {
          const btn = formEl.querySelector('button[type="submit"]');
          if (btn) btn.click();
          else formEl.submit();
        }
      }
    }

    if (putKeyEl) putKeyEl.addEventListener("keydown", (e) => { submitFormOnEnter(e, putFormEl); const s = document.getElementById("putStatus"); if (s) s.innerHTML = ""; });
    if (putValEl) putValEl.addEventListener("keydown", (e) => { submitFormOnEnter(e, putFormEl); const s = document.getElementById("putStatus"); if (s) s.innerHTML = ""; });
    if (getKeyEl) {
      getKeyEl.addEventListener("keydown", (e) => { submitFormOnEnter(e, document.getElementById("getForm")); });
      // clear error highlight while typing
      getKeyEl.addEventListener("input", () => { getKeyEl.classList.remove("input-error"); const d = document.getElementById("getValueDisplay"); if (d) d.innerHTML = ""; });
    }
  } catch (e) {
    /* no-op if DOM nodes not present */
  }
});
