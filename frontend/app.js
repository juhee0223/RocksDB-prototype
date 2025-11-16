function formatJSON(data) {
  return JSON.stringify(data, null, 2);
}

async function handlePut(event) {
  event.preventDefault();
  const resultEl = document.getElementById("putResult");
  const key = document.getElementById("putKey").value.trim();
  const value = document.getElementById("putValue").value.trim();
  if (!key || !value) {
    resultEl.textContent = "key and value are required.";
    return;
  }

  try {
    const response = await fetch("/put", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ key, value }),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "PUT failed");
    }
    resultEl.textContent = formatJSON(data);
  } catch (err) {
    resultEl.textContent = `Error: ${err.message}`;
  }
}

async function handleGet(event) {
  event.preventDefault();
  const resultEl = document.getElementById("getResult");
  const key = document.getElementById("getKey").value.trim();
  if (!key) {
    resultEl.textContent = "key is required.";
    return;
  }

  try {
    const response = await fetch(`/get?key=${encodeURIComponent(key)}`);
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "GET failed");
    }
    resultEl.textContent = formatJSON(data);
  } catch (err) {
    resultEl.textContent = `Error: ${err.message}`;
  }
}

async function refreshStats() {
  const memtableEl = document.getElementById("memtableSize");
  const sstEl = document.getElementById("sstCount");
  try {
    const response = await fetch("/stats");
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Stats request failed");
    }
    memtableEl.textContent = data.memtable_size ?? "-";
    sstEl.textContent = data.num_sst_files ?? "-";
  } catch (err) {
    memtableEl.textContent = "!";
    sstEl.textContent = "!";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const putForm = document.getElementById("putForm");
  const getForm = document.getElementById("getForm");
  const statsBtn = document.getElementById("refreshStats");

  putForm.addEventListener("submit", handlePut);
  getForm.addEventListener("submit", handleGet);
  statsBtn.addEventListener("click", refreshStats);

  refreshStats();
});
