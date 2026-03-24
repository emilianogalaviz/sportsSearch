/* app.js — Frontend logic for SportSearch */

const searchInput = document.getElementById("searchInput");
const searchBtn   = document.getElementById("searchBtn");
const autoList    = document.getElementById("autocompleteList");
const resultsArea = document.getElementById("resultsArea");
const emptyState  = document.getElementById("emptyState");
const chips       = document.querySelectorAll(".chip");

let currentCategory = "all";
let autocompleteIndex = -1;
let debounceTimer = null;
let lastResults = [];   // cached for category re-filtering

// ─── Category filter ────────────────────────────────────────────────────────
chips.forEach(chip => {
  chip.addEventListener("click", () => {
    chips.forEach(c => c.classList.remove("active"));
    chip.classList.add("active");
    currentCategory = chip.dataset.cat;
    if (lastResults.length) renderResults(lastResults, searchInput.value.trim());
  });
});

// ─── Autocomplete ────────────────────────────────────────────────────────────
searchInput.addEventListener("input", () => {
  const q = searchInput.value.trim();
  clearTimeout(debounceTimer);
  if (q.length < 2) { hideAuto(); return; }

  // Suggest on last word typed
  const lastWord = q.split(/\s+/).pop();
  if (lastWord.length < 2) { hideAuto(); return; }

  debounceTimer = setTimeout(() => fetchAutocomplete(lastWord, q), 160);
});

async function fetchAutocomplete(prefix, fullQuery) {
  try {
    const res  = await fetch(`/autocomplete?q=${encodeURIComponent(prefix)}`);
    const data = await res.json();
    showAuto(data.suggestions, prefix, fullQuery);
  } catch { hideAuto(); }
}

function showAuto(suggestions, prefix, fullQuery) {
  if (!suggestions.length) { hideAuto(); return; }
  autoList.innerHTML = "";
  autocompleteIndex = -1;

  suggestions.forEach(word => {
    const li = document.createElement("li");
    // Highlight matched prefix inside suggestion
    const highlighted = word.replace(
      new RegExp(`^(${escapeRegex(prefix)})`, "i"),
      `<span class="highlight">$1</span>`
    );
    li.innerHTML = highlighted;
    li.addEventListener("mousedown", e => {
      e.preventDefault();
      // Replace last word with suggestion
      const parts = fullQuery.split(/\s+/);
      parts[parts.length - 1] = word;
      searchInput.value = parts.join(" ");
      hideAuto();
      doSearch();
    });
    autoList.appendChild(li);
  });
  autoList.hidden = false;
}

function hideAuto() {
  autoList.hidden = true;
  autoList.innerHTML = "";
  autocompleteIndex = -1;
}

// Keyboard navigation in autocomplete
searchInput.addEventListener("keydown", e => {
  const items = autoList.querySelectorAll("li");
  if (!items.length) {
    if (e.key === "Enter") doSearch();
    return;
  }
  if (e.key === "ArrowDown") {
    e.preventDefault();
    autocompleteIndex = (autocompleteIndex + 1) % items.length;
    updateActiveItem(items);
  } else if (e.key === "ArrowUp") {
    e.preventDefault();
    autocompleteIndex = (autocompleteIndex - 1 + items.length) % items.length;
    updateActiveItem(items);
  } else if (e.key === "Enter") {
    e.preventDefault();
    if (autocompleteIndex >= 0 && items[autocompleteIndex]) {
      items[autocompleteIndex].dispatchEvent(new MouseEvent("mousedown"));
    } else {
      hideAuto();
      doSearch();
    }
  } else if (e.key === "Escape") {
    hideAuto();
  }
});

function updateActiveItem(items) {
  items.forEach((li, i) => li.classList.toggle("active", i === autocompleteIndex));
}

// Hide autocomplete on outside click
document.addEventListener("click", e => {
  if (!e.target.closest(".search-wrapper")) hideAuto();
});

// ─── Search ──────────────────────────────────────────────────────────────────
searchBtn.addEventListener("click", () => { hideAuto(); doSearch(); });

async function doSearch() {
  const q = searchInput.value.trim();
  if (!q) return;
  setLoading();

  try {
    const res  = await fetch(`/search?q=${encodeURIComponent(q)}`);
    const data = await res.json();
    lastResults = data.results || [];
    renderResults(lastResults, q, data.search_time);
  } catch {
    showError();
  }
}

// ─── Render ──────────────────────────────────────────────────────────────────
function renderResults(results, query, searchTime) {
  const filtered = currentCategory === "all"
    ? results
    : results.filter(r => r.category === currentCategory);

  resultsArea.innerHTML = "";

  if (!filtered.length) {
    resultsArea.innerHTML = `
      <div class="no-results">
        <h2>No results found</h2>
        <p>Try a different query or switch the category filter.</p>
      </div>`;
    return;
  }

  const meta = document.createElement("div");
  meta.className = "results-meta";
  meta.innerHTML = `
    <div class="results-count"><span>${filtered.length}</span> result${filtered.length !== 1 ? "s" : ""}</div>
    <div class="results-time">${searchTime ?? "—"} ms &nbsp;·&nbsp; BM25</div>
  `;
  resultsArea.appendChild(meta);

  filtered.forEach((r, i) => {
    const card = document.createElement("div");
    card.className = "result-card";
    card.style.animationDelay = `${i * 40}ms`;

    card.innerHTML = `
      <div class="card-header">
        <div class="card-rank">${String(i + 1).padStart(2, "0")}</div>
        <div class="card-title-area">
          <div class="card-title">${escapeHtml(r.title)}</div>
          <div class="card-meta">
            <span class="card-source">${escapeHtml(r.source)}</span>
            <span class="card-category">${r.category}</span>
          </div>
        </div>
        <div class="card-score-block">
          <span class="score-label">BM25</span>
          <span class="score-value">${r.score.toFixed(2)}</span>
        </div>
      </div>
      <div class="card-text">${highlightTerms(escapeHtml(r.text), query)}</div>
    `;
    resultsArea.appendChild(card);
  });
}

// ─── Highlighting ─────────────────────────────────────────────────────────────
function highlightTerms(text, query) {
  const terms = query.toLowerCase().split(/\s+/).filter(Boolean);
  // Deduplicate and sort longest first to avoid partial-match conflicts
  const unique = [...new Set(terms)].sort((a, b) => b.length - a.length);
  let highlighted = text;
  unique.forEach(term => {
    if (term.length < 2) return;
    const regex = new RegExp(`\\b(${escapeRegex(term)}\\w*)`, "gi");
    highlighted = highlighted.replace(regex, "<mark>$1</mark>");
  });
  return highlighted;
}

// ─── Helpers ─────────────────────────────────────────────────────────────────
function setLoading() {
  resultsArea.innerHTML = `
    <div class="empty-state">
      <div class="empty-icon">◌</div>
      <p>Searching…</p>
    </div>`;
}
function showError() {
  resultsArea.innerHTML = `
    <div class="no-results">
      <h2>Something went wrong</h2>
      <p>Could not reach the search engine.</p>
    </div>`;
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
function escapeRegex(s) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
