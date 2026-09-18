// ==========================================================================
// APEX MATRIX // FRONTEND CONTROLLER V1.0
// NVIDIA Power Green Architecture — DLSS Swapper & ShaderPurge
// ==========================================================================

let appState = {
  activeTab: "dlss",
  currentFilter: "all",
  searchQuery: "",
  games: [],
  shaderData: null,
  telemetryData: null,
  libraryVersions: [],
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
  filterChips: document.querySelectorAll(".filter-chip"),
  dlssLoading: document.getElementById("dlss-loading"),
  dlssEmpty: document.getElementById("dlss-empty"),
  dlssGamesGrid: document.getElementById("dlss-games-grid"),
  btnDownloadDlss: document.getElementById("btn-download-dlss"),
  btnImportDll: document.getElementById("btn-import-dll"),
  btnOpenLibrary: document.getElementById("btn-open-library"),

  // Counters
  countAllDlss: document.getElementById("count-all-dlss"),
  countDlssSr: document.getElementById("count-dlss-sr"),
  countDlssFg: document.getElementById("count-dlss-fg"),
  countDlssRr: document.getElementById("count-dlss-rr"),
  countXess: document.getElementById("count-xess"),
  countFsr: document.getElementById("count-fsr"),

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

  // Acciones Modal
  dom.modalCloseBtn.addEventListener("click", closeSwapModal);
  dom.btnCancelSwap.addEventListener("click", closeSwapModal);
  dom.btnConfirmSwap.addEventListener("click", executeSwap);

  // Descargar DLSS Oficial desde NVIDIA
  if (dom.btnDownloadDlss) {
    dom.btnDownloadDlss.addEventListener("click", async () => {
      showToast("Conectando con NVIDIA GitHub y descargando última versión oficial...", "info");
      dom.btnDownloadDlss.disabled = true;
      try {
        if (window.pywebview) {
          const res = await window.pywebview.api.download_official_dlss();
          if (res && res.success) {
            showToast(res.message, "success");
            appState.libraryVersions = await window.pywebview.api.get_library_versions();
          } else {
            showToast(res.error || "Error al descargar", "error");
          }
        } else {
          showToast("Función disponible en la aplicación de escritorio.", "info");
        }
      } catch (err) {
        showToast("Error en descarga: " + err, "error");
      } finally {
        dom.btnDownloadDlss.disabled = false;
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

  appState.games.forEach(game => {
    counts.all++;
    const techs = new Set((game.dlls || []).map(d => d.tech_type));
    techs.forEach(t => {
      if (counts[t] !== undefined) counts[t]++;
    });
  });

  dom.countAllDlss.textContent = counts.all;
  dom.countDlssSr.textContent = counts.dlss_sr;
  dom.countDlssFg.textContent = counts.dlss_fg;
  dom.countDlssRr.textContent = counts.dlss_rr;
  dom.countXess.textContent = counts.xess;
  dom.countFsr.textContent = counts.fsr;
}

function renderDlssGames() {
  dom.dlssLoading.classList.add("hidden");

  const filtered = appState.games.filter(game => {
    // Filtro por tecnología
    if (appState.currentFilter !== "all") {
      const hasTech = (game.dlls || []).some(d => d.tech_type === appState.currentFilter);
      if (!hasTech) return false;
    }
    // Filtro por búsqueda
    if (appState.searchQuery) {
      const matchName = game.game_name.toLowerCase().includes(appState.searchQuery);
      const matchPath = game.install_path.toLowerCase().includes(appState.searchQuery);
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

    let dllsHtml = (game.dlls || []).map(dll => `
      <div class="dll-tech-item">
        <div class="tech-tag-group">
          <span class="tech-badge badge-${dll.tech_type}">${dll.filename}</span>
          <span class="ver-curr">v${dll.version}</span>
          ${dll.has_backup ? '<span class="badge-backup" title="Copia original inmutable presente">.BAK</span>' : ''}
        </div>
        <div class="tech-actions">
          ${dll.has_backup ? `
            <button class="btn-matrix btn-matrix-outline" style="height:24px; padding:0 8px; font-size:9px;" onclick="restoreDll('${escapeJsStr(dll.full_path)}')">
              REVERTIR
            </button>
          ` : ''}
          <button class="btn-matrix btn-matrix-primary" style="height:24px; padding:0 8px; font-size:9px;" onclick="openSwapModal('${escapeJsStr(game.game_name)}', '${escapeJsStr(dll.full_path)}', '${escapeJsStr(dll.filename)}', '${escapeJsStr(dll.version)}')">
            ACTUALIZAR
          </button>
        </div>
      </div>
    `).join("");

    card.innerHTML = `
      <div class="game-head">
        <div class="game-name">${escapeHtml(game.game_name)}</div>
        <span class="game-platform-badge">${escapeHtml(game.platform)}</span>
      </div>
      <div class="game-path-row" title="${escapeHtml(game.install_path)}">
        ${escapeHtml(game.install_path)}
      </div>
      <div class="dll-tech-list">
        ${dllsHtml}
      </div>
      <div class="game-card-actions">
        <button class="btn-matrix btn-matrix-outline" style="height:26px; padding:0 10px; font-size:9px;" onclick="openGameFolder('${escapeJsStr(game.install_path)}')">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
          <span>EXPLORADOR</span>
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
window.openSwapModal = function(gameTitle, targetPath, dllName, currentVer) {
  appState.selectedTargetDll = targetPath;
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
        No hay librerías en la bóveda aún. Usa "IMPORTAR DLL" para agregar una versión descargada.
      </div>
    `;
    return;
  }

  appState.libraryVersions.forEach(ver => {
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

window.openGameFolder = function(path) {
  if (window.pywebview) {
    window.pywebview.api.open_folder(path);
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
