document.addEventListener("DOMContentLoaded", () => {
  fetch("registry.json")
    .then((r) => {
      if (!r.ok) return fetch("../registry.json");
      return r;
    })
    .then((r) => r.json())
    .then((tools) => {
      renderStats(tools);
      renderCards(tools);
      setupFilters(tools);
    })
    .catch(() => {
      const registry = getEmbeddedRegistry();
      renderStats(registry);
      renderCards(registry);
      setupFilters(registry);
    });
});

function getEmbeddedRegistry() {
  const el = document.getElementById("registry-data");
  if (el) {
    try {
      return JSON.parse(el.textContent);
    } catch (e) {
      return [];
    }
  }
  return [];
}

function renderStats(tools) {
  const totals = tools.reduce(
    (acc, t) => {
      acc.skills += t.skills || 0;
      acc.rules += t.rules || 0;
      acc.mcpTools += t.mcpTools || 0;
      acc.repos += 1;
      return acc;
    },
    { skills: 0, rules: 0, mcpTools: 0, repos: 0 }
  );

  document.getElementById("stat-repos").textContent = totals.repos;
  document.getElementById("stat-skills").textContent = totals.skills;
  document.getElementById("stat-rules").textContent = totals.rules;
  document.getElementById("stat-mcp").textContent = totals.mcpTools;
}

function renderCards(tools) {
  const grid = document.getElementById("card-grid");
  grid.innerHTML = "";

  tools.forEach((tool) => {
    const card = document.createElement("div");
    card.className = "tool-card";
    card.dataset.type = tool.type;
    card.dataset.topics = (tool.topics || []).join(",");

    const badgeClass = tool.type === "mcp-server" ? "badge-mcp" : "badge-plugin";
    const badgeLabel = tool.type === "mcp-server" ? "MCP Server" : "Plugin";

    const statsHtml = [];
    if (tool.skills > 0)
      statsHtml.push(
        `<span class="card-stat"><strong>${tool.skills}</strong> skills</span>`
      );
    if (tool.rules > 0)
      statsHtml.push(
        `<span class="card-stat"><strong>${tool.rules}</strong> rules</span>`
      );
    if (tool.mcpTools > 0)
      statsHtml.push(
        `<span class="card-stat"><strong>${tool.mcpTools}</strong> MCP tools</span>`
      );

    const extras = tool.extras || {};
    Object.entries(extras).forEach(([key, val]) => {
      if (val > 0) {
        const label = key === "natives" ? "natives" : key;
        statsHtml.push(
          `<span class="card-stat"><strong>${val.toLocaleString()}</strong> ${label}</span>`
        );
      }
    });

    const topicsHtml = (tool.topics || [])
      .slice(0, 5)
      .map((t) => `<span class="topic-tag">${t}</span>`)
      .join("");

    const linksHtml = [];
    linksHtml.push(
      `<a href="https://github.com/${tool.repo}" class="card-link" target="_blank" rel="noopener">
        <svg viewBox="0 0 16 16" fill="currentColor"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>
        Repository
      </a>`
    );

    if (tool.homepage) {
      linksHtml.push(
        `<a href="${tool.homepage}" class="card-link" target="_blank" rel="noopener">
          <svg viewBox="0 0 16 16" fill="currentColor"><path d="M4.72 3.22a.75.75 0 011.06 0l3.75 3.75a.75.75 0 010 1.06l-3.75 3.75a.75.75 0 01-1.06-1.06L7.94 8 4.72 4.78a.75.75 0 010-1.06z"/><path d="M10.72 3.22a.75.75 0 011.06 0l3.75 3.75a.75.75 0 010 1.06l-3.75 3.75a.75.75 0 11-1.06-1.06L13.94 8l-3.22-3.22a.75.75 0 010-1.06z"/></svg>
          Docs
        </a>`
      );
    }

    if (tool.npm) {
      const npmPkg = Array.isArray(tool.npm) ? tool.npm[0] : tool.npm;
      linksHtml.push(
        `<a href="https://www.npmjs.com/package/${npmPkg}" class="card-link card-link-npm" target="_blank" rel="noopener">
          <svg viewBox="0 0 16 16" fill="currentColor"><path d="M0 0v16h16V0H0zm13 13H8V5h2.5v5.5H13V3H3v10h10V0z"/></svg>
          npm
        </a>`
      );
    }

    card.innerHTML = `
      <div class="card-header">
        <span class="card-title">${tool.name}</span>
        <span class="card-badge ${badgeClass}">${badgeLabel}</span>
      </div>
      <p class="card-description">${tool.description}</p>
      <div class="card-stats">${statsHtml.join("")}</div>
      <div class="card-topics">${topicsHtml}</div>
      <div class="card-links">${linksHtml.join("")}</div>
    `;

    grid.appendChild(card);
  });
}

function setupFilters(tools) {
  const container = document.getElementById("filters");
  const buttons = container.querySelectorAll(".filter-btn");

  buttons.forEach((btn) => {
    btn.addEventListener("click", () => {
      buttons.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");

      const filter = btn.dataset.filter;
      const cards = document.querySelectorAll(".tool-card");

      cards.forEach((card) => {
        if (filter === "all") {
          card.style.display = "";
        } else if (filter === "cursor-plugin" || filter === "mcp-server") {
          card.style.display = card.dataset.type === filter ? "" : "none";
        } else {
          const topics = card.dataset.topics.split(",");
          card.style.display = topics.includes(filter) ? "" : "none";
        }
      });
    });
  });
}
