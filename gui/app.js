// ==========================================================================
// APEX MATRIX // FRONTEND CONTROLLER V1.0
// NVIDIA Power Green Architecture — DLSS Swapper & ShaderPurge
// ==========================================================================

let appState = {
  activeTab: "dlss",
  currentFilter: "all",
  statusFilter: "all",
  searchQuery: "",
  games: [],
  shaderData: null,
  telemetryData: null,
  libraryVersions: [],
  catalogItems: [],
  selectedTargetDll: null,
  selectedReplacementPath: null
};

// Elementos DOM
const dom = {
  tabBtns: document.querySelectorAll(".tab-btn"),
  views: {
    dlss: document.getElementById("view-dlss"),
    shaders: document.getElementById("view-shaders"),
    telemetry: document.getElementById("view-telemetry")
  },
  // Header & Telemetry Bar
  btnGlobalRefresh: document.getElementById("btn-global-refresh"),
  telemGpuName: document.getElementById("telem-gpu-name"),
  telemGpuDriver: document.getElementById("telem-gpu-driver"),
  telemCacheTotal: document.getElementById("telem-cache-total"),
  telemLifetimeReclaimed: document.getElementById("telem-lifetime-reclaimed"),
  tabCacheSize: document.getElementById("tab-cache-size"),

  // DLSS Tab
  dlssSearchInput: document.getElementById("dlss-search-input"),
  filterChips: document.querySelectorAll(".filter-chip:not(.status-chip)"),
  statusChips: document.querySelectorAll(".status-chip"),
  dlssLoading: document.getElementById("dlss-loading"),
  dlssEmpty: document.getElementById("dlss-empty"),
  dlssGamesGrid: document.getElementById("dlss-games-grid"),
  btnOpenCatalog: document.getElementById("btn-open-catalog"),
  btnAddFolder: document.getElementById("btn-add-folder"),
  btnImportDll: document.getElementById("btn-import-dll"),
  btnOpenLibrary: document.getElementById("btn-open-library"),

  // Counters
  countAllDlss: document.getElementById("count-all-dlss"),
  countDlssSr: document.getElementById("count-dlss-sr"),
  countDlssFg: document.getElementById("count-dlss-fg"),
  countDlssRr: document.getElementById("count-dlss-rr"),
  countXess: document.getElementById("count-xess"),
  countFsr: document.getElementById("count-fsr"),
  countStatusUpdated: document.getElementById("count-status-updated"),
  countStatusAvailable: document.getElementById("count-status-available"),
  countStatusOriginal: document.getElementById("count-status-original"),

  // Shader Tab
  btnPurgeAll: document.getElementById("btn-purge-all"),
  btnRescanShaders: document.getElementById("btn-rescan-shaders"),
  shaderHeroTotal: document.getElementById("shader-hero-total"),
  shaderHeroFiles: document.getElementById("shader-hero-files"),
  shaderCategoriesContainer: document.getElementById("shader-categories-container"),

  // Telemetry Tab
  telemCardName: document.getElementById("telem-card-name"),
  telemCardVram: document.getElementById("telem-card-vram"),
  telemCardDriver: document.getElementById("telem-card-driver"),
  telemCardDlssSupport: document.getElementById("telem-card-dlss-support"),
  telemCardFgSupport: document.getElementById("telem-card-fg-support"),
  telemCardCacheStatus: document.getElementById("telem-card-cache-status"),
  telemCardTotalReclaimed: document.getElementById("telem-card-total-reclaimed"),

  // Swap Modal
  swapModal: document.getElementById("swap-modal"),
  modalCloseBtn: document.getElementById("modal-close-btn"),
  btnCancelSwap: document.getElementById("btn-cancel-swap"),
  btnConfirmSwap: document.getElementById("btn-confirm-swap"),
  swapModalGameTitle: document.getElementById("swap-modal-game-title"),
  modalTargetDllName: document.getElementById("modal-target-dll-name"),
  modalTargetCurrVer: document.getElementById("modal-target-curr-ver"),
  modalTargetPath: document.getElementById("modal-target-path"),
  modalVersionsList: document.getElementById("modal-versions-list"),

  // Catalog Modal
  catalogModal: document.getElementById("catalog-modal"),
  catalogModalClose: document.getElementById("catalog-modal-close"),
  catalogModalDone: document.getElementById("catalog-modal-done"),
  catalogItemsList: document.getElementById("catalog-items-list"),

  // Toast
  toastContainer: document.getElementById("toast-container")
};

// 1. Inicialización
document.addEventListener("DOMContentLoaded", () => {
  setupEventListeners();

  if (window.pywebview) {
    onReady();
  } else {
    window.addEventListener("pywebviewready", onReady);
    // Fallback de demostración si se abre directamente en navegador
    setTimeout(() => {
      if (!window.pywebview) {
        initMockData();
      }
    }, 400);
  }
});

function onReady() {
  loadTelemetry();
  loadShaderCaches();
  loadGamesAndUpscalers();
}

function setupEventListeners() {
  // Cambio de pestañas
  dom.tabBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      const tab = btn.getAttribute("data-tab");
      switchTab(tab);
    });
  });

  // Búsqueda y Filtros DLSS
  dom.dlssSearchInput.addEventListener("input", (e) => {
    appState.searchQuery = e.target.value.toLowerCase().trim();
    renderDlssGames();
  });

  dom.filterChips.forEach(chip => {
    chip.addEventListener("click", () => {
      dom.filterChips.forEach(c => c.classList.remove("active"));
      chip.classList.add("active");
      appState.currentFilter = chip.getAttribute("data-filter");
      renderDlssGames();
    });
  });

  // Filtros por Estado de Archivo
  dom.statusChips.forEach(chip => {
    chip.addEventListener("click", () => {
      dom.statusChips.forEach(c => c.classList.remove("active"));
      chip.classList.add("active");
      appState.statusFilter = chip.getAttribute("data-status-filter");
      renderDlssGames();
    });
  });

  // Acciones Globales
  dom.btnGlobalRefresh.addEventListener("click", () => {
    showToast("Sincronizando bibliotecas y telemetría de shaders...", "info");
    loadTelemetry();
    loadShaderCaches();
    loadGamesAndUpscalers();
  });

  // Acciones Shaders
  dom.btnPurgeAll.addEventListener("click", () => {
    purgeShaders(["all"]);
  });

  dom.btnRescanShaders.addEventListener("click", () => {
    loadShaderCaches();
  });

  // Acciones Modal Swap
  dom.modalCloseBtn.addEventListener("click", closeSwapModal);
  dom.btnCancelSwap.addEventListener("click", closeSwapModal);
  dom.btnConfirmSwap.addEventListener("click", executeSwap);

  // Acciones Modal Catálogo DLSS
  if (dom.btnOpenCatalog) {
    dom.btnOpenCatalog.addEventListener("click", openCatalogModal);
  }
  if (dom.catalogModalClose) {
    dom.catalogModalClose.addEventListener("click", closeCatalogModal);
  }
  if (dom.catalogModalDone) {
    dom.catalogModalDone.addEventListener("click", closeCatalogModal);
  }

  // Agregar Carpeta de Juego
  if (dom.btnAddFolder) {
    dom.btnAddFolder.addEventListener("click", async () => {
      if (window.pywebview) {
        showToast("Selecciona la carpeta del juego o directorio de juegos...", "info");
        const res = await window.pywebview.api.add_custom_game_folder();
        if (res && res.success) {
          showToast(res.message, "success");
          loadGamesAndUpscalers();
        } else if (res && res.error) {
          showToast(res.error, "error");
        }
      } else {
        showToast("Función disponible en la aplicación de escritorio.", "info");
      }
    });
  }

  // Importar DLL
  dom.btnImportDll.addEventListener("click", async () => {
    if (window.pywebview) {
      const res = await window.pywebview.api.import_custom_dll();
      if (res && res.success) {
        showToast(res.message, "success");
      }
    } else {
      showToast("Función disponible en la aplicación de escritorio.", "info");
    }
  });

  dom.btnOpenLibrary.addEventListener("click", () => {
    if (window.pywebview) {
      window.pywebview.api.open_folder("library");
    }
  });
}

function switchTab(tabKey) {
  appState.activeTab = tabKey;
  dom.tabBtns.forEach(btn => {
    btn.classList.toggle("active", btn.getAttribute("data-tab") === tabKey);
  });
  Object.keys(dom.views).forEach(key => {
    dom.views[key].classList.toggle("active", key === tabKey);
  });
}

// 2. Carga y renderizado de DLSS & Upscaling
async function loadGamesAndUpscalers() {
  dom.dlssLoading.classList.remove("hidden");
  dom.dlssEmpty.classList.add("hidden");
  dom.dlssGamesGrid.classList.add("hidden");

  try {
    if (window.pywebview) {
      const res = await window.pywebview.api.scan_games_and_upscalers();
      appState.games = (res && res.games) ? res.games : [];
      appState.libraryVersions = await window.pywebview.api.get_library_versions();
    }
    updateDlssCounters();
    renderDlssGames();
  } catch (err) {
    console.error("Error al escanear DLSS:", err);
    dom.dlssLoading.classList.add("hidden");
    dom.dlssEmpty.classList.remove("hidden");
  }
}

function updateDlssCounters() {
  let counts = { all: 0, dlss_sr: 0, dlss_fg: 0, dlss_rr: 0, xess: 0, fsr: 0 };
  let statusCounts = { updated: 0, available: 0, original: 0 };

  appState.games.forEach(game => {
    counts.all++;
    const techs = new Set((game.dlls || []).map(d => d.tech_type));
    techs.forEach(t => {
      if (counts[t] !== undefined) counts[t]++;
    });

    const hasBackup = (game.dlls || []).some(d => d.has_backup);
    const hasAvailable = (game.dlls || []).some(d => {
      const vaultMatch = appState.libraryVersions.find(v => v.tech_type === d.tech_type);
      return vaultMatch && vaultMatch.version !== d.version && !d.has_backup;
    });

    if (hasBackup) {
      statusCounts.updated++;
    } else if (hasAvailable) {
      statusCounts.available++;
    } else {
      statusCounts.original++;
    }
  });

  dom.countAllDlss.textContent = counts.all;
  dom.countDlssSr.textContent = counts.dlss_sr;
  dom.countDlssFg.textContent = counts.dlss_fg;
  dom.countDlssRr.textContent = counts.dlss_rr;
  dom.countXess.textContent = counts.xess;
  dom.countFsr.textContent = counts.fsr;

  if (dom.countStatusUpdated) dom.countStatusUpdated.textContent = statusCounts.updated;
  if (dom.countStatusAvailable) dom.countStatusAvailable.textContent = statusCounts.available;
  if (dom.countStatusOriginal) dom.countStatusOriginal.textContent = statusCounts.original;
}

function renderDlssGames() {
  dom.dlssLoading.classList.add("hidden");

  const filtered = appState.games.filter(game => {
    // 1. Filtro por tecnología
    if (appState.currentFilter !== "all") {
      const hasTech = (game.dlls || []).some(d => d.tech_type === appState.currentFilter);
      if (!hasTech) return false;
    }

    // 2. Filtro por estado de archivo
    if (appState.statusFilter !== "all") {
      const hasBackup = (game.dlls || []).some(d => d.has_backup);
      const hasAvailable = (game.dlls || []).some(d => {
        const vaultMatch = appState.libraryVersions.find(v => v.tech_type === d.tech_type);
        return vaultMatch && vaultMatch.version !== d.version && !d.has_backup;
      });

      if (appState.statusFilter === "updated" && !hasBackup) return false;
      if (appState.statusFilter === "available" && !hasAvailable) return false;
      if (appState.statusFilter === "original" && (hasBackup || hasAvailable)) return false;
    }

    // 3. Filtro por búsqueda
    if (appState.searchQuery) {
      const matchName = (game.game_name || "").toLowerCase().includes(appState.searchQuery);
      const matchPath = (game.install_path || "").toLowerCase().includes(appState.searchQuery);
      if (!matchName && !matchPath) return false;
    }
    return true;
  });

  if (filtered.length === 0) {
    dom.dlssEmpty.classList.remove("hidden");
    dom.dlssGamesGrid.classList.add("hidden");
    return;
  }

  dom.dlssEmpty.classList.add("hidden");
  dom.dlssGamesGrid.classList.remove("hidden");
  dom.dlssGamesGrid.innerHTML = "";

  filtered.forEach(game => {
    const card = document.createElement("div");
    card.className = "game-matrix-card";

    const hasAnyBackup = (game.dlls || []).some(d => d.has_backup);
    const isCustom = game.platform === "Personalizado";

    let dllsHtml = (game.dlls || []).map(dll => {
      // Determinar si hay una versión disponible en la bóveda para esta tecnología
      const vaultMatch = appState.libraryVersions.find(v => v.tech_type === dll.tech_type);
      const isOutdated = vaultMatch && vaultMatch.version !== dll.version;

      let statusBadge = '';
      if (dll.has_backup) {
        statusBadge = `<span class="status-badge status-updated" title="Archivo modificado con copia original respaldada (.bak)">ACTUALIZADO (.BAK)</span>`;
      } else if (isOutdated) {
        statusBadge = `<span class="status-badge status-available" title="Versión más reciente disponible en la bóveda">DISPONIBLE v${vaultMatch.version}</span>`;
      } else {
        statusBadge = `<span class="status-badge status-original" title="Archivo original sin modificar">ORIGINAL</span>`;
      }

      return `
        <div class="dll-tech-item">
          <div class="tech-tag-group">
            <span class="tech-badge badge-${dll.tech_type}" title="${escapeHtml(dll.filename)}">${escapeHtml(dll.filename)}</span>
            <span class="ver-curr">v${escapeHtml(dll.version)}</span>
            ${statusBadge}
          </div>
          <div class="tech-actions">
            ${dll.has_backup ? `
              <button class="btn-matrix btn-matrix-outline" style="height:24px; padding:0 8px; font-size:9px;" onclick="restoreDll('${escapeJsStr(dll.full_path)}')">
                REVERTIR
              </button>
            ` : ''}
            <button class="btn-matrix btn-matrix-primary" style="height:24px; padding:0 8px; font-size:9px;" onclick="openSwapModal('${escapeJsStr(game.game_name)}', '${escapeJsStr(dll.full_path)}', '${escapeJsStr(dll.filename)}', '${escapeJsStr(dll.version)}', '${escapeJsStr(dll.tech_type)}', '${escapeJsStr(dll.tech_label)}')">
              ACTUALIZAR
            </button>
          </div>
        </div>
      `;
    }).join("");

    const bannerHtml = game.cover_url ? `
      <div class="game-card-banner">
        <img src="${escapeHtml(game.cover_url)}" alt="${escapeHtml(game.game_name)}" loading="lazy" onerror="this.parentElement.style.display='none'"/>
      </div>
    ` : '';

    const deleteBtnHtml = isCustom ? `
      <button class="btn-matrix btn-matrix-outline btn-delete-card" onclick="removeCustomFolder('${escapeJsStr(game.install_path)}')" title="Desvincular carpeta de ApexMatrix">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
      </button>
    ` : '';

    card.innerHTML = `
      ${bannerHtml}
      <div class="game-head">
        <div class="game-name">${escapeHtml(game.game_name)}</div>
        <div style="display:flex; align-items:center; gap:6px;">
          <span class="game-platform-badge">${escapeHtml(game.platform)}</span>
          ${deleteBtnHtml}
        </div>
      </div>
      <div class="game-path-row" title="${escapeHtml(game.install_path)}">
        ${escapeHtml(game.install_path)}
      </div>
      <div class="dll-tech-list">
        ${dllsHtml}
      </div>
      <div class="game-card-actions">
        <button class="btn-matrix btn-play" onclick="launchGame('${escapeJsStr(game.install_path)}', '${escapeJsStr(game.app_id || '')}', '${escapeJsStr(game.platform || '')}')" title="Iniciar juego directamente">
          <svg width="11" height="11" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>
          <span>JUGAR</span>
        </button>
        ${hasAnyBackup ? `
          <button class="btn-matrix btn-matrix-outline" style="height:26px; padding:0 10px; font-size:9px;" onclick="restoreAllInGame('${escapeJsStr(game.install_path)}')">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/></svg>
            <span>REVERTIR TODOS</span>
          </button>
        ` : ''}
        <button class="btn-matrix btn-matrix-primary" style="height:26px; padding:0 10px; font-size:9px;" onclick="swapAllInGame('${escapeJsStr(game.install_path)}')">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2"/></svg>
          <span>ACTUALIZAR TODOS</span>
        </button>
        <button class="btn-matrix btn-matrix-outline" style="height:26px; padding:0 10px; font-size:9px;" onclick="openGameFolder('${escapeJsStr(game.install_path)}')">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
          <span>CARPETA</span>
        </button>
      </div>
    `;

    dom.dlssGamesGrid.appendChild(card);
  });
}

// 3. Carga y purga de Shader Caches
async function loadShaderCaches() {
  try {
    if (window.pywebview) {
      const data = await window.pywebview.api.scan_shader_caches();
      appState.shaderData = data;
      renderShaderData(data);
    }
  } catch (err) {
    console.error("Error al escanear shaders:", err);
  }
}

function renderShaderData(data) {
  if (!data) return;

  dom.shaderHeroTotal.textContent = data.total_size_str;
  dom.shaderHeroFiles.textContent = `${data.total_files} archivos analizados`;
  dom.tabCacheSize.textContent = data.total_size_str;
  dom.telemCacheTotal.textContent = data.total_size_str;
  dom.telemLifetimeReclaimed.textContent = data.lifetime_reclaimed_str;
  dom.telemCardTotalReclaimed.textContent = data.lifetime_reclaimed_str;

  dom.shaderCategoriesContainer.innerHTML = "";

  (data.categories || []).forEach(cat => {
    const card = document.createElement("div");
    card.className = "shader-card";
    card.innerHTML = `
      <div class="shader-card-head">
        <div>
          <div class="card-tag">${escapeHtml(cat.category)}</div>
          <div class="shader-card-title">${escapeHtml(cat.label)}</div>
        </div>
        <div class="shader-card-size">${escapeHtml(cat.size_str)}</div>
      </div>
      <div class="shader-card-desc">${escapeHtml(cat.description)}</div>
      <div class="shader-card-path">${escapeHtml(cat.path)}</div>
      <div class="shader-card-footer">
        <span class="shader-card-stats">${cat.file_count} archivos</span>
        <div style="display:flex; gap:8px;">
          <button class="btn-matrix btn-matrix-outline" style="height:26px; padding:0 8px; font-size:9px;" onclick="openGameFolder('${escapeJsStr(cat.path)}')">
            VER
          </button>
          <button class="btn-matrix btn-matrix-primary" style="height:26px; padding:0 10px; font-size:9px;" onclick="purgeShaders(['${cat.id}'])" ${cat.file_count === 0 ? 'disabled' : ''}>
            PURGAR
          </button>
        </div>
      </div>
    `;
    dom.shaderCategoriesContainer.appendChild(card);
  });
}

async function purgeShaders(targetIds) {
  showToast("Iniciando purga de shaders...", "info");
  try {
    if (window.pywebview) {
      const res = await window.pywebview.api.purge_caches(targetIds, 0);
      if (res && res.success) {
        showToast(res.message, "success");
        loadShaderCaches();
        loadTelemetry();
      } else {
        showToast(res.error || "Ocurrió un error al purgar.", "error");
      }
    }
  } catch (err) {
    showToast("Error ejecutando la purga: " + err, "error");
  }
}

// 4. Telemetría GPU
async function loadTelemetry() {
  try {
    if (window.pywebview) {
      const data = await window.pywebview.api.get_system_telemetry();
      appState.telemetryData = data;
      renderTelemetry(data);
    }
  } catch (err) {
    console.error("Error al cargar telemetría:", err);
  }
}

function renderTelemetry(data) {
  if (!data || !data.primary_gpu) return;
  const gpu = data.primary_gpu;

  dom.telemGpuName.textContent = gpu.name;
  dom.telemGpuDriver.textContent = `v${gpu.commercial_driver || gpu.driver_version}`;

  dom.telemCardName.textContent = gpu.name;
  dom.telemCardVram.textContent = gpu.vram_gb ? `${gpu.vram_gb} GB GDDR` : "Compartida";
  dom.telemCardDriver.textContent = `v${gpu.commercial_driver} (${gpu.driver_version})`;
  dom.telemCardDlssSupport.textContent = gpu.supports_dlss_sr ? "SOPORTADO (NVIDIA RTX/GTX)" : "FSR / XeSS Compatible";
  dom.telemCardFgSupport.textContent = gpu.supports_dlss_fg ? "SOPORTADO NATIVAMENTE" : "No soportado (Requiere RTX 40/50)";
}

// 5. Modal de Swapping
window.openSwapModal = function(gameTitle, targetPath, dllName, currentVer, techType, techLabel) {
  appState.selectedTargetDll = targetPath;
  appState.selectedTargetTech = techType || "dlss_sr";
  appState.selectedTargetTechLabel = techLabel || dllName;
  appState.selectedReplacementPath = null;

  dom.swapModalGameTitle.textContent = gameTitle;
  dom.modalTargetDllName.textContent = dllName;
  dom.modalTargetCurrVer.textContent = `v${currentVer}`;
  dom.modalTargetPath.textContent = targetPath;

  renderModalVersions();
  dom.swapModal.classList.remove("hidden");
};

function closeSwapModal() {
  dom.swapModal.classList.add("hidden");
}

function renderModalVersions() {
  dom.modalVersionsList.innerHTML = "";
  dom.btnConfirmSwap.disabled = true;

  if (appState.libraryVersions.length === 0) {
    dom.modalVersionsList.innerHTML = `
      <div style="padding:16px; color:var(--color-text-dim); text-align:center; font-size:11px;">
        No hay librerías en la bóveda aún. Usa "DESCARGAR OFICIAL NVIDIA" o "IMPORTAR DLL".
      </div>
    `;
    return;
  }

  // Filtrar versiones compatibles con la tecnología seleccionada (evitar cruzar DLSS con FSR)
  const targetTech = appState.selectedTargetTech;
  let compatibleVersions = appState.libraryVersions.filter(v => v.tech_type === targetTech);

  if (compatibleVersions.length === 0) {
    dom.modalVersionsList.innerHTML = `
      <div style="padding:16px; color:var(--color-text-dim); text-align:center; font-size:11px; line-height:1.5;">
        <div style="color:var(--color-accent-orange); font-weight:700; margin-bottom:4px;">No hay versiones de ${escapeHtml(appState.selectedTargetTechLabel || targetTech)} en la bóveda.</div>
        <div>Las versiones de NVIDIA DLSS solo son compatibles con archivos DLSS. Puedes importar una versión de esta tecnología con "IMPORTAR DLL".</div>
      </div>
    `;
    return;
  }

  compatibleVersions.forEach(ver => {
    const item = document.createElement("div");
    item.className = "version-option";
    item.innerHTML = `
      <div>
        <div class="ver-opt-title">${escapeHtml(ver.filename)} (v${escapeHtml(ver.version)})</div>
        <div class="ver-opt-date">Tamaño: ${escapeHtml(ver.size_str)}</div>
      </div>
      <span class="tech-badge badge-${ver.tech_type}">BÓVEDA</span>
    `;

    item.addEventListener("click", () => {
      document.querySelectorAll(".version-option").forEach(i => i.classList.remove("selected"));
      item.classList.add("selected");
      appState.selectedReplacementPath = ver.path;
      dom.btnConfirmSwap.disabled = false;
    });

    dom.modalVersionsList.appendChild(item);
  });
}

async function executeSwap() {
  if (!appState.selectedTargetDll || !appState.selectedReplacementPath) return;

  try {
    if (window.pywebview) {
      const res = await window.pywebview.api.swap_dll(appState.selectedTargetDll, appState.selectedReplacementPath);
      if (res && res.success) {
        showToast(res.message, "success");
        closeSwapModal();
        loadGamesAndUpscalers();
      } else {
        showToast(res.error || "Fallo en el swap", "error");
      }
    }
  } catch (err) {
    showToast("Error: " + err, "error");
  }
}

window.restoreDll = async function(targetPath) {
  if (!confirm("¿Deseas restaurar la versión original (.bak) de esta DLL?")) return;

  try {
    if (window.pywebview) {
      const res = await window.pywebview.api.restore_dll(targetPath);
      if (res && res.success) {
        showToast(res.message, "success");
        loadGamesAndUpscalers();
      } else {
        showToast(res.error || "Fallo al restaurar", "error");
      }
    }
  } catch (err) {
    showToast("Error: " + err, "error");
  }
};

window.swapAllInGame = async function(gamePath) {
  showToast("Actualizando todas las librerías del juego con versiones de la bóveda...", "info");
  try {
    if (window.pywebview) {
      const res = await window.pywebview.api.swap_all_in_game(gamePath);
      if (res && res.success) {
        showToast(res.message, "success");
        loadGamesAndUpscalers();
      } else {
        showToast(res.error || "No se pudieron actualizar los archivos", "error");
      }
    }
  } catch (err) {
    showToast("Error en actualización masiva: " + err, "error");
  }
};

window.restoreAllInGame = async function(gamePath) {
  if (!confirm("¿Deseas revertir todas las DLLs modificadas de este juego a su estado original?")) return;
  showToast("Restaurando archivos originales...", "info");
  try {
    if (window.pywebview) {
      const res = await window.pywebview.api.restore_all_in_game(gamePath);
      if (res && res.success) {
        showToast(res.message, "success");
        loadGamesAndUpscalers();
      } else {
        showToast(res.error || "No se pudieron restaurar los archivos", "error");
      }
    }
  } catch (err) {
    showToast("Error al revertir: " + err, "error");
  }
};

window.openGameFolder = function(path) {
  if (window.pywebview) {
    window.pywebview.api.open_folder(path);
  }
};

window.launchGame = async function(installPath, appId, platform) {
  showToast("Iniciando juego...", "info");
  try {
    if (window.pywebview) {
      const res = await window.pywebview.api.launch_game(installPath, appId, platform);
      if (res && res.success) {
        showToast(res.message || "Juego iniciado", "success");
      } else {
        showToast(res.error || "No se pudo iniciar el juego", "error");
      }
    } else {
      showToast("Lanzador disponible en la versión de escritorio.", "info");
    }
  } catch (err) {
    showToast("Error al iniciar juego: " + err, "error");
  }
};

window.removeCustomFolder = async function(installPath) {
  if (!confirm("¿Deseas desvincular esta carpeta de ApexMatrix?\n(No se eliminará ningún archivo de tu disco)")) return;
  try {
    if (window.pywebview) {
      const res = await window.pywebview.api.remove_custom_game_folder(installPath);
      if (res && res.success) {
        showToast("Carpeta desvinculada de la matriz", "success");
        loadGamesAndUpscalers();
      } else {
        showToast(res.error || "Error al desvincular carpeta", "error");
      }
    }
  } catch (err) {
    showToast("Error: " + err, "error");
  }
};

window.openCatalogModal = async function() {
  if (dom.catalogModal) {
    dom.catalogModal.classList.remove("hidden");
    await loadCatalogItems();
  }
};

window.closeCatalogModal = function() {
  if (dom.catalogModal) {
    dom.catalogModal.classList.add("hidden");
  }
};

async function loadCatalogItems() {
  if (!dom.catalogItemsList) return;
  dom.catalogItemsList.innerHTML = `
    <div style="padding:20px; text-align:center; color:var(--color-text-dim); font-size:11px;">
      Cargando catálogo oficial de NVIDIA SDK...
    </div>
  `;
  try {
    if (window.pywebview) {
      appState.catalogItems = await window.pywebview.api.get_dlss_catalog();
    } else {
      appState.catalogItems = [
        { id: "dlss_3_7_20", name: "NVIDIA DLSS v3.7.20", version: "3.7.20.0", category: "Super Resolution", tag: "MÁXIMA NITIDEZ", description: "Última versión optimizada con Preset E. Gran reducción de ghosting y artefactos en movimiento.", is_downloaded: false },
        { id: "dlss_3_7_10", name: "NVIDIA DLSS v3.7.10", version: "3.7.10.0", category: "Super Resolution", tag: "OFICIAL SDK", description: "Versión oficial del SDK de NVIDIA. Muy alta estabilidad en títulos Unreal Engine 5.", is_downloaded: true },
        { id: "dlss_fg_3_7_10", name: "NVIDIA DLSS 3 Frame Generation", version: "3.7.10.0", category: "Frame Generation", tag: "RTX 40/50 SERIES", description: "Librería oficial de generación de fotogramas por hardware para duplicar los FPS.", is_downloaded: false }
      ];
    }
    renderCatalogItems();
  } catch (err) {
    dom.catalogItemsList.innerHTML = `
      <div style="padding:20px; text-align:center; color:var(--color-accent-orange); font-size:11px;">
        Error al cargar catálogo: ${escapeHtml(err)}
      </div>
    `;
  }
}

function renderCatalogItems() {
  if (!dom.catalogItemsList) return;
  dom.catalogItemsList.innerHTML = "";

  (appState.catalogItems || []).forEach(item => {
    const card = document.createElement("div");
    card.className = "catalog-card";
    card.innerHTML = `
      <div class="catalog-card-info">
        <div class="catalog-card-header">
          <span class="catalog-card-title">${escapeHtml(item.name)}</span>
          <span class="catalog-card-tag">${escapeHtml(item.tag || item.category)}</span>
        </div>
        <div class="catalog-card-desc">${escapeHtml(item.description)}</div>
      </div>
      <div class="catalog-card-actions">
        ${item.is_downloaded ? `
          <span class="status-badge status-updated" style="font-size:9px; padding:5px 8px;">EN BÓVEDA</span>
        ` : `
          <button class="btn-matrix btn-matrix-primary" id="btn-dl-${item.id}" style="height:28px; padding:0 12px; font-size:10px;" onclick="downloadCatalogItem('${escapeJsStr(item.id)}')">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
            <span>DESCARGAR</span>
          </button>
        `}
      </div>
    `;
    dom.catalogItemsList.appendChild(card);
  });
}

window.downloadCatalogItem = async function(itemId) {
  const btn = document.getElementById(`btn-dl-${itemId}`);
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<span>DESCARGANDO...</span>`;
  }
  showToast("Descargando versión oficial a la bóveda...", "info");

  try {
    if (window.pywebview) {
      const res = await window.pywebview.api.download_catalog_item(itemId);
      if (res && res.success) {
        showToast(res.message, "success");
        appState.libraryVersions = await window.pywebview.api.get_library_versions();
        await loadCatalogItems();
        updateDlssCounters();
        renderDlssGames();
      } else {
        showToast(res.error || "Fallo al descargar", "error");
        if (btn) btn.disabled = false;
      }
    } else {
      showToast("Descarga completada (Modo Demostración)", "success");
    }
  } catch (err) {
    showToast("Error en descarga: " + err, "error");
    if (btn) btn.disabled = false;
  }
};

// 6. Toast Utilities
function showToast(message, type = "info") {
  const toast = document.createElement("div");
  toast.className = `toast ${type === "error" ? "toast-error" : ""}`;
  toast.textContent = message;

  dom.toastContainer.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function escapeJsStr(str) {
  if (!str) return "";
  return String(str).replace(/\\/g, "\\\\").replace(/'/g, "\\'");
}

// 7. Mock Data para visualización en navegador
function initMockData() {
  renderTelemetry({
    primary_gpu: {
      name: "NVIDIA GeForce RTX 4070 SUPER",
      driver_version: "32.0.15.6070",
      commercial_driver: "560.70",
      vram_gb: 12.0,
      supports_dlss_sr: true,
      supports_dlss_fg: true
    }
  });

  renderShaderData({
    total_bytes: 4120000000,
    total_files: 184,
    total_size_str: "3.84 GB",
    lifetime_reclaimed_str: "14.20 GB",
    categories: [
      { id: "nvidia_dx", label: "NVIDIA DirectX Shader Cache", category: "NVIDIA", size_str: "2.83 GB", file_count: 18, path: "C:\\Users\\Anima\\AppData\\Local\\NVIDIA\\DXCache", description: "Caché de compilación de shaders DirectX 11/12 para GPUs NVIDIA GeForce RTX/GTX." },
      { id: "d3ds_cache", label: "DirectX D3DSCache", category: "DirectX", size_str: "874.00 MB", file_count: 149, path: "C:\\Users\\Anima\\AppData\\Local\\D3DSCache", description: "Almacén general de shaders compilados del subsistema de gráficos de Windows." },
      { id: "crash_dumps", label: "Windows Crash Dumps", category: "Crash Logs", size_str: "136.70 MB", file_count: 10, path: "C:\\Users\\Anima\\AppData\\Local\\CrashDumps", description: "Volcados pesados de memoria generados cuando un juego o app sufre un crash." }
    ]
  });

  appState.games = [
    {
      game_name: "Cyberpunk 2077",
      platform: "Steam",
      install_path: "C:\\Games\\Steam\\steamapps\\common\\Cyberpunk 2077",
      dlls: [
        { tech_type: "dlss_sr", filename: "nvngx_dlss.dll", version: "3.5.10.0", has_backup: true, full_path: "C:\\Games\\Cyberpunk 2077\\bin\\x64\\nvngx_dlss.dll" },
        { tech_type: "dlss_fg", filename: "nvngx_dlssg.dll", version: "3.5.0.0", has_backup: false, full_path: "C:\\Games\\Cyberpunk 2077\\bin\\x64\\nvngx_dlssg.dll" },
        { tech_type: "dlss_rr", filename: "nvngx_dlssd.dll", version: "3.5.0.0", has_backup: false, full_path: "C:\\Games\\Cyberpunk 2077\\bin\\x64\\nvngx_dlssd.dll" }
      ]
    },
    {
      game_name: "Black Myth: Wukong",
      platform: "Steam",
      install_path: "C:\\Games\\Steam\\steamapps\\common\\BlackMythWukong",
      dlls: [
        { tech_type: "dlss_sr", filename: "nvngx_dlss.dll", version: "3.7.10.0", has_backup: false, full_path: "C:\\Games\\BlackMythWukong\\b1\\Binaries\\Win64\\nvngx_dlss.dll" },
        { tech_type: "dlss_fg", filename: "nvngx_dlssg.dll", version: "3.7.0.0", has_backup: false, full_path: "C:\\Games\\BlackMythWukong\\b1\\Binaries\\Win64\\nvngx_dlssg.dll" }
      ]
    }
  ];
  updateDlssCounters();
  renderDlssGames();
}
