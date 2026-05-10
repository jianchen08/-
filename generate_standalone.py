#!/usr/bin/env python3
"""Generate standalone.html for the tech tree visualizer."""
import json

def main():
    # Read JSON data files
    with open('public/data/full_data.json', 'r', encoding='utf-8') as f:
        full_data = f.read()
    with open('public/data/domains.json', 'r', encoding='utf-8') as f:
        domains = f.read()
    with open('public/data/eras.json', 'r', encoding='utf-8') as f:
        eras = f.read()

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>科技树可视化</title>
<style>
/* ========== Global Reset & Base ========== */
*, *::before, *::after {{ margin: 0; padding: 0; box-sizing: border-box; }}
html, body {{ width: 100%; height: 100%; overflow: hidden; background: #0d1117; color: #e6edf3; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', Roboto, sans-serif; font-size: 14px; }}
::-webkit-scrollbar {{ width: 6px; height: 6px; }}
::-webkit-scrollbar-track {{ background: rgba(255,255,255,0.03); }}
::-webkit-scrollbar-thumb {{ background: rgba(255,255,255,0.12); border-radius: 3px; }}
::-webkit-scrollbar-thumb:hover {{ background: rgba(255,255,255,0.22); }}

/* ========== Loading ========== */
.app-loading {{ width:100%; height:100%; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:20px; background:radial-gradient(ellipse at center,#111927 0%,#0d1117 70%); color:#8b949e; font-size:16px; }}
.app-loading-spinner {{ width:48px; height:48px; border:3px solid rgba(79,195,247,0.15); border-top-color:#58a6ff; border-radius:50%; animation:spin 0.8s linear infinite; }}
@keyframes spin {{ to {{ transform:rotate(360deg); }} }}

/* ========== Layout ========== */
.app-layout {{ width:100%; height:100%; display:flex; overflow:hidden; background:#0d1117; }}

/* ========== Left Sidebar ========== */
.app-sidebar-left {{ width:240px; min-width:240px; height:100%; background:rgba(13,17,23,0.98); border-right:1px solid rgba(48,54,61,0.6); overflow-y:auto; display:flex; flex-direction:column; }}
.app-sidebar-title {{ padding:16px; font-size:15px; font-weight:600; color:#f0f6fc; border-bottom:1px solid rgba(48,54,61,0.6); background:linear-gradient(180deg,rgba(88,166,255,0.06) 0%,transparent 100%); }}

/* ========== Main Area ========== */
.app-main {{ flex:1; height:100%; display:flex; flex-direction:column; position:relative; overflow:hidden; background:#0d1117; }}
.app-top-bar {{ display:flex; align-items:center; gap:12px; padding:8px 16px; background:rgba(13,17,23,0.95); border-bottom:1px solid rgba(48,54,61,0.6); z-index:10; backdrop-filter:blur(12px); }}

/* ========== Right Sidebar ========== */
.app-sidebar-right {{ width:0; overflow:hidden; height:100%; background:rgba(13,17,23,0.98); border-left:1px solid rgba(48,54,61,0.6); transition:width 0.3s cubic-bezier(0.4,0,0.2,1); flex-shrink:0; }}
.app-sidebar-right.open {{ width:340px; }}

/* ========== Search ========== */
.search-panel {{ flex:1; max-width:400px; }}
.search-input-wrap {{ display:flex; align-items:center; background:rgba(22,27,34,0.8); border:1px solid rgba(48,54,61,0.6); border-radius:8px; padding:0 10px; transition:border-color 0.2s,box-shadow 0.2s; }}
.search-input-wrap:focus-within {{ border-color:#58a6ff; box-shadow:0 0 0 3px rgba(88,166,255,0.15); }}
.search-icon {{ font-size:14px; margin-right:6px; flex-shrink:0; }}
.search-input {{ flex:1; background:none; border:none; outline:none; color:#e6edf3; font-size:13px; padding:8px 0; font-family:inherit; }}
.search-input::placeholder {{ color:rgba(139,148,158,0.6); }}
.search-clear {{ background:none; border:none; color:rgba(139,148,158,0.6); cursor:pointer; font-size:12px; padding:4px; line-height:1; transition:color 0.15s; }}
.search-clear:hover {{ color:#f0f6fc; }}

/* ========== Toolbar ========== */
.toolbar {{ display:flex; align-items:center; gap:8px; }}
.toolbar-layout-group {{ display:flex; gap:4px; }}
.toolbar-btn {{ display:flex; align-items:center; gap:4px; padding:6px 10px; background:rgba(22,27,34,0.6); border:1px solid rgba(48,54,61,0.6); border-radius:6px; color:#8b949e; font-size:12px; cursor:pointer; transition:all 0.2s ease; white-space:nowrap; font-family:inherit; }}
.toolbar-btn:hover {{ background:rgba(88,166,255,0.1); border-color:rgba(88,166,255,0.3); color:#f0f6fc; }}
.toolbar-btn.active {{ background:rgba(88,166,255,0.15); border-color:#58a6ff; color:#58a6ff; box-shadow:0 0 8px rgba(88,166,255,0.15); }}
.toolbar-btn-icon {{ font-size:14px; }}
.toolbar-btn-label {{ font-size:12px; }}
.toolbar-reset {{ margin-left:4px; }}

/* ========== Filter Panel ========== */
.filter-panel {{ padding:12px; display:flex; flex-direction:column; gap:16px; }}
.filter-section {{ display:flex; flex-direction:column; gap:8px; }}
.filter-header {{ display:flex; align-items:center; justify-content:space-between; }}
.filter-title {{ font-size:13px; font-weight:600; color:#e6edf3; }}
.filter-value {{ font-size:12px; color:#58a6ff; font-weight:600; min-width:24px; text-align:right; }}
.filter-actions {{ display:flex; gap:4px; }}
.filter-btn {{ background:none; border:1px solid rgba(48,54,61,0.6); border-radius:4px; color:#8b949e; font-size:11px; padding:2px 6px; cursor:pointer; transition:all 0.2s; font-family:inherit; }}
.filter-btn:hover {{ border-color:rgba(88,166,255,0.4); color:#58a6ff; background:rgba(88,166,255,0.08); }}
.filter-checkboxes {{ display:flex; flex-direction:column; gap:4px; }}
.filter-checkbox-label {{ display:flex; align-items:center; gap:6px; cursor:pointer; padding:3px 4px; border-radius:4px; transition:background 0.15s; }}
.filter-checkbox-label:hover {{ background:rgba(88,166,255,0.06); }}
.filter-checkbox-label input[type="checkbox"] {{ accent-color:#58a6ff; width:14px; height:14px; flex-shrink:0; }}
.filter-color-dot {{ width:10px; height:10px; border-radius:50%; flex-shrink:0; box-shadow:0 0 4px rgba(0,0,0,0.3); }}
.filter-checkbox-text {{ font-size:12px; color:#c9d1d9; }}
.filter-slider {{ width:100%; accent-color:#58a6ff; height:4px; cursor:pointer; }}
.filter-slider-labels {{ display:flex; justify-content:space-between; font-size:10px; color:#484f58; }}

/* ========== TechTree Container ========== */
.tech-tree-wrapper {{ flex:1; position:relative; overflow:hidden; background:radial-gradient(ellipse at 30% 20%,rgba(88,166,255,0.03) 0%,transparent 50%),radial-gradient(ellipse at 70% 80%,rgba(139,92,246,0.02) 0%,transparent 50%),#0d1117; }}
.tech-tree-container {{ width:100%; height:100%; }}

/* ========== Node Detail ========== */
.node-detail {{ width:340px; height:100%; overflow-y:auto; display:flex; flex-direction:column; }}
.detail-header {{ display:flex; justify-content:flex-end; padding:12px 16px 0; }}
.detail-close {{ background:none; border:1px solid rgba(48,54,61,0.6); border-radius:6px; color:#8b949e; cursor:pointer; font-size:14px; padding:4px 8px; transition:all 0.2s; }}
.detail-close:hover {{ border-color:#f85149; color:#f85149; background:rgba(248,81,73,0.08); }}
.detail-body {{ padding:12px 16px 24px; display:flex; flex-direction:column; gap:14px; }}
.detail-name {{ font-size:20px; font-weight:700; color:#f0f6fc; line-height:1.3; }}
.detail-meta {{ display:flex; flex-wrap:wrap; gap:8px; align-items:center; }}
.detail-domain-badge {{ display:inline-block; padding:3px 10px; border-radius:12px; font-size:12px; font-weight:600; color:#fff; box-shadow:0 2px 6px rgba(0,0,0,0.3); }}
.detail-year {{ font-size:12px; color:#8b949e; }}
.detail-hub {{ font-size:12px; color:#d29922; }}
.detail-description {{ font-size:13px; line-height:1.7; color:#c9d1d9; }}
.detail-section {{ display:flex; flex-direction:column; gap:8px; }}
.detail-section-title {{ font-size:13px; font-weight:600; color:#e6edf3; padding-bottom:4px; border-bottom:1px solid rgba(48,54,61,0.4); }}
.detail-tags {{ display:flex; flex-wrap:wrap; gap:6px; }}
.detail-tag {{ padding:2px 8px; border-radius:10px; background:rgba(88,166,255,0.1); color:#58a6ff; font-size:11px; border:1px solid rgba(88,166,255,0.15); }}
.detail-node-list {{ display:flex; flex-direction:column; gap:4px; }}
.detail-node-item {{ display:flex; align-items:center; justify-content:space-between; padding:8px 12px; background:rgba(22,27,34,0.6); border:none; border-left:3px solid #484f58; border-radius:4px; cursor:pointer; transition:all 0.15s ease; text-align:left; font-family:inherit; color:#c9d1d9; }}
.detail-node-item:hover {{ background:rgba(88,166,255,0.08); color:#f0f6fc; border-left-color:#58a6ff; transform:translateX(2px); }}
.detail-node-name {{ font-size:12px; }}
.detail-node-year {{ font-size:11px; color:#484f58; flex-shrink:0; }}

/* ========== Legend ========== */
.legend {{ position:absolute; left:12px; bottom:100px; background:rgba(13,17,23,0.94); border:1px solid rgba(48,54,61,0.5); border-radius:10px; padding:12px 16px; z-index:5; backdrop-filter:blur(12px); max-width:220px; box-shadow:0 4px 16px rgba(0,0,0,0.3); }}
.legend-title {{ font-size:13px; font-weight:600; color:#f0f6fc; margin-bottom:10px; }}
.legend-section {{ margin-bottom:10px; }}
.legend-section:last-child {{ margin-bottom:0; }}
.legend-subtitle {{ font-size:11px; color:#8b949e; margin-bottom:6px; text-transform:uppercase; letter-spacing:0.5px; }}
.legend-items {{ display:flex; flex-direction:column; gap:4px; }}
.legend-item {{ display:flex; align-items:center; gap:8px; }}
.legend-color-dot {{ width:10px; height:10px; border-radius:50%; flex-shrink:0; box-shadow:0 0 4px rgba(0,0,0,0.2); }}
.legend-item-text {{ font-size:11px; color:#8b949e; }}
.legend-size-items {{ flex-direction:row; gap:12px; flex-wrap:wrap; }}
.legend-size-dot {{ display:inline-block; border-radius:50%; background:#58a6ff; }}
.legend-size-dot.small {{ width:8px; height:8px; }}
.legend-size-dot.medium {{ width:14px; height:14px; }}
.legend-size-dot.large {{ width:22px; height:22px; }}
.legend-glow-dot {{ display:inline-block; width:14px; height:14px; border-radius:50%; background:#f0883e; box-shadow:0 0 6px 2px rgba(240,136,62,0.5); animation:glow-pulse 2s ease-in-out infinite; }}
@keyframes glow-pulse {{ 0%,100% {{ box-shadow:0 0 4px 1px rgba(240,136,62,0.3); }} 50% {{ box-shadow:0 0 8px 3px rgba(240,136,62,0.6); }} }}

/* ========== MiniMap ========== */
.minimap {{ position:absolute; right:12px; bottom:12px; background:rgba(13,17,23,0.94); border:1px solid rgba(48,54,61,0.5); border-radius:10px; padding:8px; z-index:5; backdrop-filter:blur(12px); box-shadow:0 4px 16px rgba(0,0,0,0.3); }}
.minimap-title {{ font-size:13px; font-weight:600; color:#f0f6fc; margin-bottom:6px; }}
.minimap-canvas {{ display:block; border-radius:4px; cursor:pointer; background:rgba(10,10,30,0.9); }}

/* ========== Timeline Slider ========== */
.timeline-slider {{ position:absolute; left:12px; bottom:12px; right:240px; background:rgba(13,17,23,0.94); border:1px solid rgba(48,54,61,0.5); border-radius:10px; padding:10px 16px 14px; z-index:5; backdrop-filter:blur(12px); box-shadow:0 4px 16px rgba(0,0,0,0.3); }}
.timeline-labels {{ display:flex; align-items:center; justify-content:space-between; margin-bottom:8px; }}
.timeline-title {{ font-size:13px; font-weight:600; color:#f0f6fc; }}
.timeline-hint {{ font-size:12px; color:#58a6ff; font-weight:600; }}
.timeline-bar-container {{ position:relative; }}
.timeline-era-band {{ display:flex; height:20px; border-radius:4px; overflow:hidden; margin-bottom:4px; }}
.timeline-era-segment {{ display:flex; align-items:center; justify-content:center; font-size:9px; color:rgba(255,255,255,0.8); overflow:hidden; text-overflow:ellipsis; white-space:nowrap; transition:opacity 0.2s; }}
.timeline-era-segment.dimmed {{ opacity:0.3; }}
.timeline-era-segment-name {{ overflow:hidden; text-overflow:ellipsis; }}
.timeline-year-labels {{ position:relative; height:18px; margin-top:2px; font-size:10px; color:#484f58; }}
.timeline-year-label {{ white-space:nowrap; }}
.timeline-track {{ position:relative; width:100%; height:6px; background:rgba(255,255,255,0.04); border-radius:3px; margin-bottom:4px; }}
.timeline-track-fill {{ position:absolute; top:0; height:100%; background:linear-gradient(90deg,#58a6ff,#79c0ff); border-radius:3px; transition:left 0.15s,width 0.15s; pointer-events:none; }}
.timeline-range {{ position:absolute; width:100%; height:30px; top:0; left:0; margin:0; padding:0; -webkit-appearance:none; appearance:none; background:transparent; pointer-events:none; z-index:2; }}
.timeline-range::-webkit-slider-thumb {{ -webkit-appearance:none; appearance:none; width:16px; height:16px; border-radius:50%; background:#58a6ff; border:2px solid #f0f6fc; cursor:grab; pointer-events:auto; box-shadow:0 1px 4px rgba(0,0,0,0.4); transition:transform 0.15s,box-shadow 0.15s; }}
.timeline-range::-webkit-slider-thumb:hover {{ transform:scale(1.2); box-shadow:0 0 8px rgba(88,166,255,0.4); }}
.timeline-range::-webkit-slider-thumb:active {{ cursor:grabbing; transform:scale(1.3); background:#79c0ff; }}
.timeline-range::-moz-range-thumb {{ width:16px; height:16px; border-radius:50%; background:#58a6ff; border:2px solid #f0f6fc; cursor:grab; pointer-events:auto; box-shadow:0 1px 4px rgba(0,0,0,0.4); }}
.timeline-range-start {{ z-index:3; }}
.timeline-range-end {{ z-index:4; }}

/* ========== Box Select ========== */
.box-select-overlay {{ position:absolute; border:2px dashed #58a6ff; background-color:rgba(88,166,255,0.08); pointer-events:none; z-index:10; border-radius:2px; }}

/* ========== Responsive ========== */
@media (max-width:1024px) {{
  .app-sidebar-left {{ width:200px; min-width:200px; }}
  .app-sidebar-right.open {{ width:280px; }}
  .node-detail {{ width:280px; }}
  .timeline-slider {{ right:200px; }}
}}
@media (max-width:768px) {{
  .app-sidebar-left {{ position:absolute; left:0; top:0; z-index:20; width:0; min-width:0; overflow:hidden; transition:width 0.3s ease; box-shadow:4px 0 16px rgba(0,0,0,0.4); }}
  .app-sidebar-left.mobile-open {{ width:240px; min-width:240px; }}
  .app-sidebar-right.open {{ width:100%; max-width:340px; }}
  .timeline-slider {{ left:8px; right:8px; bottom:8px; }}
  .legend {{ display:none; }}
  .minimap {{ display:none; }}
  .toolbar-btn-label {{ display:none; }}
  .toolbar-btn {{ padding:6px 8px; }}
  .app-top-bar {{ padding:6px 8px; gap:6px; }}
  .search-panel {{ max-width:200px; }}
}}
@media (max-width:480px) {{
  .search-panel {{ max-width:140px; }}
  .toolbar-layout-group {{ gap:2px; }}
}}
</style>
</head>
<body>
<!-- Loading Screen -->
<div id="loading" class="app-loading">
  <div class="app-loading-spinner"></div>
  <p>正在加载科技树数据...</p>
</div>

<!-- Main App Layout (hidden until data loads) -->
<div id="app" class="app-layout" style="display:none;">
  <!-- Left Sidebar: Filters -->
  <aside id="sidebar-left" class="app-sidebar-left">
    <div class="app-sidebar-title">⚙️ 筛选</div>
    <div class="filter-panel">
      <!-- Era Filter -->
      <div class="filter-section">
        <div class="filter-header">
          <span class="filter-title">⏳ 时代</span>
          <div class="filter-actions">
            <button class="filter-btn" onclick="selectAllEras()">全选</button>
            <button class="filter-btn" onclick="clearAllEras()">清空</button>
          </div>
        </div>
        <div id="era-checkboxes" class="filter-checkboxes"></div>
      </div>
      <!-- Domain Filter -->
      <div class="filter-section">
        <div class="filter-header">
          <span class="filter-title">🔬 领域</span>
          <div class="filter-actions">
            <button class="filter-btn" onclick="selectAllDomains()">全选</button>
            <button class="filter-btn" onclick="clearAllDomains()">清空</button>
          </div>
        </div>
        <div id="domain-checkboxes" class="filter-checkboxes"></div>
      </div>
      <!-- Hub Threshold -->
      <div class="filter-section">
        <div class="filter-header">
          <span class="filter-title">🔗 枢纽值阈值</span>
          <span id="hub-value" class="filter-value">0</span>
        </div>
        <input type="range" min="0" max="100" step="5" value="0" class="filter-slider" id="hub-slider" oninput="onHubChange(this.value)">
        <div class="filter-slider-labels"><span>0</span><span>100</span></div>
      </div>
    </div>
  </aside>

  <!-- Main Area -->
  <main class="app-main">
    <!-- Top Bar: Search + Toolbar -->
    <div class="app-top-bar">
      <div class="search-panel">
        <div class="search-input-wrap">
          <span class="search-icon">🔍</span>
          <input type="text" class="search-input" id="search-input" placeholder="搜索节点名称、描述、标签..." oninput="onSearchChange(this.value)">
          <button class="search-clear" id="search-clear" style="display:none" onclick="clearSearch()">✕</button>
        </div>
      </div>
      <div class="toolbar">
        <div class="toolbar-layout-group">
          <button class="toolbar-btn" data-layout="dagre" onclick="setLayout('dagre')" title="层次布局">
            <span class="toolbar-btn-icon">📐</span><span class="toolbar-btn-label">层次布局</span>
          </button>
          <button class="toolbar-btn" data-layout="force" onclick="setLayout('force')" title="力导向">
            <span class="toolbar-btn-icon">🌐</span><span class="toolbar-btn-label">力导向</span>
          </button>
          <button class="toolbar-btn active" data-layout="timeline" onclick="setLayout('timeline')" title="时间轴">
            <span class="toolbar-btn-icon">⏰</span><span class="toolbar-btn-label">时间轴</span>
          </button>
        </div>
        <button class="toolbar-btn toolbar-reset" onclick="resetView()" title="重置视图">
          <span class="toolbar-btn-icon">🔄</span><span class="toolbar-btn-label">重置</span>
        </button>
      </div>
    </div>

    <!-- Tech Tree Area -->
    <div class="tech-tree-wrapper" id="tree-wrapper">
      <div class="tech-tree-container" id="cy-container"></div>
      <div id="box-select-overlay" class="box-select-overlay" style="display:none;"></div>
    </div>

    <!-- Legend -->
    <div id="legend" class="legend"></div>

    <!-- MiniMap -->
    <div class="minimap">
      <div class="minimap-title">🗺️ 导航</div>
      <canvas id="minimap-canvas" class="minimap-canvas" width="200" height="150"></canvas>
    </div>

    <!-- Timeline Slider -->
    <div id="timeline-slider" class="timeline-slider"></div>
  </main>

  <!-- Right Sidebar: Node Detail -->
  <aside id="sidebar-right" class="app-sidebar-right">
    <div id="node-detail" class="node-detail"></div>
  </aside>
</div>

<!-- CDN Scripts -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.31.0/cytoscape.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape-dagre/2.5.0/cytoscape-dagre.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape-cose-bilkent/4.1.0/cytoscape-cose-bilkent.min.js"></script>

<script>
// ========== Inline Data ==========
const INLINE_NODES = {full_data};
const INLINE_DOMAINS = {domains};
const INLINE_ERAS = {eras};

// ========== State ==========
let allNodes = [];
let allDomains = [];
let allEras = [];
let domainColorMap = new Map();
let state = {{
  searchText: '',
  selectedEras: [],
  selectedDomains: [],
  hubThreshold: 0,
  yearRange: [-3000000, 2025],
  layout: 'timeline',
  selectedNodeId: null,
  minYear: -3000000,
  maxYear: 2025,
}};
let cy = null;
let minimapRAF = 0;
let boxSelecting = false;
let boxStart = null;

// ========== Data Loading ==========
function loadData() {{
  try {{
    allNodes = INLINE_NODES;
    allDomains = INLINE_DOMAINS;
    allEras = INLINE_ERAS;

    // Ensure years are numbers
    for (const n of allNodes) {{
      if (typeof n.year === 'string') n.year = parseInt(n.year, 10);
    }}

    // Calculate hub scores
    const refCount = new Map();
    for (const n of allNodes) refCount.set(n.id, 0);
    for (const n of allNodes) {{
      for (const p of n.prerequisites) {{
        const c = refCount.get(p);
        if (c !== undefined) refCount.set(p, c + 1);
      }}
    }}
    let maxCount = 0;
    for (const c of refCount.values()) if (c > maxCount) maxCount = c;
    for (const n of allNodes) {{
      n.hubScore = maxCount > 0 ? Math.round((refCount.get(n.id) / maxCount) * 100) : 0;
    }}

    // Build domain color map
    for (const d of allDomains) domainColorMap.set(d.id, d.color);

    // Calculate year range
    const years = allNodes.map(n => n.year);
    state.minYear = Math.min(...years);
    state.maxYear = Math.max(...years);
    state.yearRange = [state.minYear, state.maxYear];
    state.selectedEras = allEras.map(e => e.id);
    state.selectedDomains = allDomains.map(d => d.id);

    return true;
  }} catch (err) {{
    console.error('Data loading failed:', err);
    return false;
  }}
}}

// ========== Utility Functions ==========
function hubToSize(hubScore) {{ return 20 + (hubScore / 100) * 30; }}

function adjustBrightness(hex, hubScore) {{
  const factor = 0.4 + (hubScore / 100) * 0.6;
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  const nr = Math.min(255, Math.round(r * factor));
  const ng = Math.min(255, Math.round(g * factor));
  const nb = Math.min(255, Math.round(b * factor));
  return '#' + nr.toString(16).padStart(2,'0') + ng.toString(16).padStart(2,'0') + nb.toString(16).padStart(2,'0');
}}

function matchesSearch(node, text) {{
  if (!text.trim()) return true;
  const lower = text.toLowerCase();
  if (node.name.toLowerCase().includes(lower)) return true;
  if (node.description.toLowerCase().includes(lower)) return true;
  if (node.tags && node.tags.some(t => t.toLowerCase().includes(lower))) return true;
  return false;
}}

function passesFilter(node) {{
  if (state.selectedEras.length > 0 && !state.selectedEras.includes(node.era)) return false;
  if (state.selectedDomains.length > 0 && !state.selectedDomains.includes(node.domain)) return false;
  if ((node.hubScore || 0) < state.hubThreshold) return false;
  if (state.yearRange) {{
    if (node.year < state.yearRange[0] || node.year > state.yearRange[1]) return false;
  }}
  return true;
}}

function buildElements() {{
  const elements = [];
  const visibleIds = new Set();

  const visibleNodes = allNodes
    .filter(n => passesFilter(n))
    .sort((a, b) => a.year - b.year);
  for (const n of visibleNodes) visibleIds.add(n.id);

  const searchLower = state.searchText.toLowerCase().trim();
  const matchedIds = new Set();
  if (searchLower) {{
    for (const n of visibleNodes) {{
      if (matchesSearch(n, state.searchText)) matchedIds.add(n.id);
    }}
  }}

  for (const node of visibleNodes) {{
    const hubScore = node.hubScore || 0;
    const baseColor = domainColorMap.get(node.domain) || '#888888';
    const displayColor = adjustBrightness(baseColor, hubScore);
    const size = hubToSize(hubScore);
    const isMatched = searchLower ? matchedIds.has(node.id) : true;
    const isDimmed = searchLower ? !matchedIds.has(node.id) : false;

    elements.push({{
      group: 'nodes',
      data: {{
        id: node.id,
        name: hubScore >= 80 ? '⭐ ' + node.name : node.name,
        domain: node.domain,
        hubScore: hubScore,
        era: node.era,
        year: node.year,
        nodeSize: size,
        displayColor: displayColor,
        isMatched: isMatched,
        isDimmed: isDimmed,
      }},
    }});
  }}

  for (const node of visibleNodes) {{
    for (const prereq of node.prerequisites) {{
      if (visibleIds.has(prereq)) {{
        elements.push({{
          group: 'edges',
          data: {{
            id: prereq + '->' + node.id,
            source: prereq,
            target: node.id,
          }},
        }});
      }}
    }}
  }}
  return elements;
}}

function getLayoutOptions() {{
  const layout = state.layout;
  if (layout === 'dagre') {{
    return {{ name:'dagre', rankDir:'LR', spacingFactor:1.2, nodeSep:30, rankSep:80, animate:true, animationDuration:500 }};
  }} else if (layout === 'force') {{
    return {{ name:'cose-bilkent', animate:true, animationDuration:800, nodeRepulsion:80000, idealEdgeLength:80, gravity:0.3, randomize:true }};
  }} else {{
    // timeline layout
    const eraWeights = [0.08, 0.10, 0.10, 0.10, 0.12, 0.15, 0.35];
    const domainMap = new Map(allDomains.map((d, i) => [d.id, i]));
    const positions = {{}};
    const visibleNodes = allNodes.filter(n => passesFilter(n));
    for (const node of visibleNodes) {{
      const year = node.year;
      let xPos = 0;
      for (let i = 0; i < allEras.length; i++) {{
        const era = allEras[i];
        const weight = eraWeights[i] || 0.1;
        const segmentWidth = weight * 5000;
        const [eraStart, eraEnd] = era.yearRange;
        if (year <= eraStart) break;
        if (year >= eraEnd) {{
          xPos += segmentWidth;
        }} else {{
          const t = (year - eraStart) / (eraEnd - eraStart);
          xPos += t * segmentWidth;
          break;
        }}
      }}
      const domainIdx = domainMap.get(node.domain) || 0;
      const yBase = domainIdx * 120;
      let hash = 0;
      for (let i = 0; i < node.id.length; i++) {{
        hash = ((hash << 5) - hash) + node.id.charCodeAt(i);
        hash |= 0;
      }}
      const jitter = (Math.abs(hash) % 60) - 30;
      positions[node.id] = {{ x: xPos + jitter * 0.3, y: yBase + jitter }};
    }}
    return {{
      name: 'preset',
      positions: function(ele) {{ return positions[ele.id()] || {{ x: 0, y: 0 }}; }},
      animate: true,
      animationDuration: 500,
    }};
  }}
}}

function getCyStyle() {{
  return [
    {{
      selector: 'node',
      style: {{
        'label': 'data(name)',
        'width': 'data(nodeSize)',
        'height': 'data(nodeSize)',
        'background-color': 'data(displayColor)',
        'text-valign': 'center',
        'text-halign': 'center',
        'font-size': '8px',
        'color': '#fff',
        'text-outline-width': 1,
        'text-outline-color': '#000',
        'text-wrap': 'wrap',
        'text-max-width': '60px',
        'opacity': 1,
        'transition-property': 'background-color, border-color, border-width, opacity, text-outline-width, font-size',
        'transition-duration': 150,
      }},
    }},
    {{
      selector: 'node[?isDimmed]',
      style: {{ 'opacity': 0.12 }},
    }},
    {{
      selector: 'node[hubScore >= 60]',
      style: {{ 'border-width': 3, 'border-color': '#FFD700', 'border-opacity': 0.7 }},
    }},
    {{
      selector: 'node[hubScore >= 80]',
      style: {{ 'border-width': 4, 'border-color': '#FF4500', 'border-opacity': 1 }},
    }},
    {{
      selector: 'node.selected',
      style: {{ 'border-width': 5, 'border-color': '#00FFFF', 'border-opacity': 1, 'font-size': '10px' }},
    }},
    {{
      selector: 'node.hovered',
      style: {{ 'border-width': 4, 'border-color': '#ffffff', 'border-opacity': 0.9, 'z-index': 999, 'font-size': '10px', 'text-outline-width': 2, 'opacity': 1 }},
    }},
    {{
      selector: 'edge',
      style: {{
        'width': 1.5,
        'line-color': 'rgba(100, 140, 180, 0.35)',
        'target-arrow-color': 'rgba(100, 140, 180, 0.35)',
        'target-arrow-shape': 'triangle',
        'arrow-scale': 0.6,
        'curve-style': 'bezier',
        'opacity': 0.5,
        'transition-property': 'line-color, target-arrow-color, width, opacity',
        'transition-duration': 200,
      }},
    }},
    {{
      selector: 'edge.highlighted',
      style: {{ 'width': 3, 'line-color': '#4fc3f7', 'target-arrow-color': '#4fc3f7', 'opacity': 1 }},
    }},
  ];
}}

// ========== Cytoscape Initialization ==========
function initCy() {{
  const container = document.getElementById('cy-container');
  const elements = buildElements();
  const layoutOpts = getLayoutOptions();

  cy = cytoscape({{
    container: container,
    elements: elements,
    style: getCyStyle(),
    layout: layoutOpts,
    minZoom: 0.1,
    maxZoom: 3,
  }});

  // Node click
  cy.on('tap', 'node', function(evt) {{
    const nodeId = evt.target.id();
    onNodeSelect(nodeId);
  }});

  // Right-click select
  cy.on('cxttap', 'node', function(evt) {{
    onNodeSelect(evt.target.id());
  }});

  // Hover highlight
  cy.on('mouseover', 'node', function(evt) {{
    const node = evt.target;
    node.addClass('hovered');
    node.connectedEdges().addClass('highlighted');
  }});
  cy.on('mouseout', 'node', function(evt) {{
    const node = evt.target;
    node.removeClass('hovered');
    node.connectedEdges().removeClass('highlighted');
  }});

  // Fit view after layout
  cy.one('layoutstop', function() {{
    setTimeout(function() {{ cy.fit(undefined, 50); }}, 100);
  }});
  setTimeout(function() {{ if (cy) cy.fit(undefined, 50); }}, 800);

  // Minimap updates
  cy.on('pan zoom layoutstop', scheduleMinimapDraw);
  drawMinimap();
}}

function updateCy() {{
  if (!cy) return;
  const elements = buildElements();
  cy.elements().remove();
  cy.add(elements);
  const layoutOpts = getLayoutOptions();
  const layoutInst = cy.layout(layoutOpts);
  layoutInst.one('layoutstop', function() {{
    setTimeout(function() {{ cy.fit(undefined, 50); }}, 100);
  }});
  layoutInst.run();

  // Re-apply selected state
  if (state.selectedNodeId) {{
    const sn = cy.getElementById(state.selectedNodeId);
    if (sn.length > 0) sn.addClass('selected');
  }}
}}

// ========== UI Rendering ==========
function renderEraCheckboxes() {{
  const container = document.getElementById('era-checkboxes');
  container.innerHTML = allEras.map(function(era) {{
    const checked = state.selectedEras.includes(era.id) ? 'checked' : '';
    return '<label class="filter-checkbox-label">' +
      '<input type="checkbox" ' + checked + ' onchange="toggleEra(\\'' + era.id + '\\')">' +
      '<span class="filter-checkbox-text">' + era.name + '</span>' +
      '</label>';
  }}).join('');
}}

function renderDomainCheckboxes() {{
  const container = document.getElementById('domain-checkboxes');
  container.innerHTML = allDomains.map(function(d) {{
    const checked = state.selectedDomains.includes(d.id) ? 'checked' : '';
    return '<label class="filter-checkbox-label">' +
      '<input type="checkbox" ' + checked + ' onchange="toggleDomain(\\'' + d.id + '\\')">' +
      '<span class="filter-color-dot" style="background-color:' + d.color + '"></span>' +
      '<span class="filter-checkbox-text">' + d.name + '</span>' +
      '</label>';
  }}).join('');
}}

function renderLegend() {{
  const el = document.getElementById('legend');
  el.innerHTML =
    '<div class="legend-title">🗺️ 图例</div>' +
    '<div class="legend-section">' +
      '<div class="legend-subtitle">领域颜色</div>' +
      '<div class="legend-items">' +
        allDomains.map(function(d) {{
          return '<div class="legend-item"><span class="legend-color-dot" style="background-color:' + d.color + '"></span><span class="legend-item-text">' + d.name + '</span></div>';
        }}).join('') +
      '</div>' +
    '</div>' +
    '<div class="legend-section">' +
      '<div class="legend-subtitle">节点大小</div>' +
      '<div class="legend-items legend-size-items">' +
        '<div class="legend-item"><span class="legend-size-dot small"></span><span class="legend-item-text">低枢纽值</span></div>' +
        '<div class="legend-item"><span class="legend-size-dot medium"></span><span class="legend-item-text">中枢纽值</span></div>' +
        '<div class="legend-item"><span class="legend-size-dot large"></span><span class="legend-item-text">高枢纽值</span></div>' +
      '</div>' +
    '</div>' +
    '<div class="legend-section">' +
      '<div class="legend-subtitle">光晕动画</div>' +
      '<div class="legend-items">' +
        '<div class="legend-item"><span class="legend-glow-dot"></span><span class="legend-item-text">Top 10 枢纽节点</span></div>' +
      '</div>' +
    '</div>';
}}

// ========== Timeline Slider ==========
const ERA_WEIGHTS = [0.08, 0.10, 0.10, 0.10, 0.12, 0.15, 0.35];
const ERA_COLORS = ['#8B4513','#DAA520','#708090','#CD853F','#A0522D','#4682B4','#1E90FF'];
const SLIDER_MAX = 10000;

function yearToPosition(year) {{
  let position = 0;
  for (let i = 0; i < allEras.length && i < ERA_WEIGHTS.length; i++) {{
    const era = allEras[i];
    const segW = ERA_WEIGHTS[i] * SLIDER_MAX;
    if (year <= era.yearRange[0]) break;
    if (year >= era.yearRange[1]) {{
      position += segW;
    }} else {{
      const t = (year - era.yearRange[0]) / (era.yearRange[1] - era.yearRange[0]);
      position += t * segW;
      break;
    }}
  }}
  return Math.round(position);
}}

function positionToYear(position) {{
  let remaining = position;
  for (let i = 0; i < allEras.length && i < ERA_WEIGHTS.length; i++) {{
    const segW = ERA_WEIGHTS[i] * SLIDER_MAX;
    if (remaining <= segW) {{
      const t = remaining / segW;
      const era = allEras[i];
      return Math.round(era.yearRange[0] + t * (era.yearRange[1] - era.yearRange[0]));
    }}
    remaining -= segW;
  }}
  const lastEra = allEras[allEras.length - 1];
  return lastEra ? lastEra.yearRange[1] : 2025;
}}

function formatYear(year) {{
  if (year <= -1000000) return Math.round(year / -10000) + '万年前';
  if (year <= -10000) return Math.round(-year / 1000) + '千年前';
  if (year < 0) return '公元前' + Math.abs(year) + '年';
  return year + '年';
}}

function renderTimeline() {{
  const el = document.getElementById('timeline-slider');
  const [startYear, endYear] = state.yearRange;
  const startPos = yearToPosition(startYear);
  const endPos = yearToPosition(endYear);
  const isAll = startYear <= state.minYear && endYear >= state.maxYear;

  // Year labels
  const yearLabels = [];
  for (const era of allEras) {{
    yearLabels.push({{ year: era.yearRange[0], position: yearToPosition(era.yearRange[0]) }});
  }}
  const lastEra = allEras[allEras.length - 1];
  if (lastEra) yearLabels.push({{ year: lastEra.yearRange[1], position: yearToPosition(lastEra.yearRange[1]) }});

  el.innerHTML =
    '<div class="timeline-labels">' +
      '<span class="timeline-title">时间轴</span>' +
      '<span class="timeline-hint">' + (isAll ? '全部年份' : (formatYear(startYear) + ' → ' + formatYear(endYear))) + '</span>' +
    '</div>' +
    '<div class="timeline-bar-container">' +
      '<div class="timeline-era-band">' +
        allEras.map(function(era, idx) {{
          const segStart = yearToPosition(era.yearRange[0]);
          const segEnd = yearToPosition(era.yearRange[1]);
          const segWidth = ((segEnd - segStart) / SLIDER_MAX) * 100;
          const overlapStart = Math.max(era.yearRange[0], startYear);
          const overlapEnd = Math.min(era.yearRange[1], endYear);
          const isDimmed = overlapStart >= overlapEnd ? ' dimmed' : '';
          return '<div class="timeline-era-segment' + isDimmed + '" style="width:' + segWidth + '%;background-color:' + (ERA_COLORS[idx] || '#888') + '" title="' + era.name + ' (' + formatYear(era.yearRange[0]) + ' ~ ' + formatYear(era.yearRange[1]) + ')">' +
            '<span class="timeline-era-segment-name">' + era.name + '</span></div>';
        }}).join('') +
      '</div>' +
      '<div class="timeline-track">' +
        '<div class="timeline-track-fill" style="left:' + (startPos / SLIDER_MAX * 100) + '%;width:' + ((endPos - startPos) / SLIDER_MAX * 100) + '%"></div>' +
      '</div>' +
      '<input type="range" class="timeline-range timeline-range-start" min="0" max="' + SLIDER_MAX + '" step="1" value="' + startPos + '" oninput="onTimelineStart(this.value)" aria-label="起始年份">' +
      '<input type="range" class="timeline-range timeline-range-end" min="0" max="' + SLIDER_MAX + '" step="1" value="' + endPos + '" oninput="onTimelineEnd(this.value)" aria-label="结束年份">' +
      '<div class="timeline-year-labels">' +
        yearLabels.map(function(l) {{
          return '<span class="timeline-year-label" style="position:absolute;left:' + (l.position / SLIDER_MAX * 100) + '%;transform:translateX(-50%)">' + formatYear(l.year) + '</span>';
        }}).join('') +
      '</div>' +
    '</div>';
}}

// ========== MiniMap ==========
function drawMinimap() {{
  const canvas = document.getElementById('minimap-canvas');
  if (!canvas || !cy) return;
  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  const MINI_W = 200, MINI_H = 150;
  const dpr = window.devicePixelRatio || 1;
  canvas.width = MINI_W * dpr;
  canvas.height = MINI_H * dpr;
  canvas.style.width = MINI_W + 'px';
  canvas.style.height = MINI_H + 'px';
  ctx.scale(dpr, dpr);

  ctx.fillStyle = 'rgba(10, 10, 30, 0.9)';
  ctx.fillRect(0, 0, MINI_W, MINI_H);

  const nodes = cy.nodes();
  if (nodes.length === 0) return;

  const bbox = nodes.boundingBox({{}});
  const pad = 30;
  const bx = bbox.x1 - pad, by = bbox.y1 - pad;
  const bw = Math.max(bbox.w + pad * 2, 1);
  const bh = Math.max(bbox.h + pad * 2, 1);

  ctx.globalAlpha = 0.7;
  for (const node of nodes) {{
    const p = node.position();
    const x = ((p.x - bx) / bw) * MINI_W;
    const y = ((p.y - by) / bh) * MINI_H;
    const domain = node.data('domain');
    ctx.fillStyle = domainColorMap.get(domain) || '#888888';
    ctx.beginPath();
    ctx.arc(x, y, 1.5, 0, Math.PI * 2);
    ctx.fill();
  }}

  const vp = cy.extent();
  const vx1 = ((vp.x1 - bx) / bw) * MINI_W;
  const vy1 = ((vp.y1 - by) / bh) * MINI_H;
  const vx2 = ((vp.x2 - bx) / bw) * MINI_W;
  const vy2 = ((vp.y2 - by) / bh) * MINI_H;

  ctx.globalAlpha = 0.12;
  ctx.fillStyle = '#4fc3f7';
  ctx.fillRect(vx1, vy1, vx2 - vx1, vy2 - vy1);
  ctx.globalAlpha = 0.9;
  ctx.strokeStyle = '#4fc3f7';
  ctx.lineWidth = 1.5;
  ctx.strokeRect(vx1, vy1, vx2 - vx1, vy2 - vy1);
  ctx.globalAlpha = 1;
}}

function scheduleMinimapDraw() {{
  cancelAnimationFrame(minimapRAF);
  minimapRAF = requestAnimationFrame(drawMinimap);
}}

// ========== Node Detail ==========
function renderNodeDetail() {{
  const sidebar = document.getElementById('sidebar-right');
  const container = document.getElementById('node-detail');

  if (!state.selectedNodeId) {{
    sidebar.classList.remove('open');
    return;
  }}

  const node = allNodes.find(function(n) {{ return n.id === state.selectedNodeId; }});
  if (!node) {{
    sidebar.classList.remove('open');
    return;
  }}

  sidebar.classList.add('open');
  const domainInfo = allDomains.find(function(d) {{ return d.id === node.domain; }});
  const domainName = domainInfo ? domainInfo.name : node.domain;
  const domainColor = domainInfo ? domainInfo.color : '#888';

  // Prerequisites
  const prereqNodes = node.prerequisites
    .map(function(id) {{ return allNodes.find(function(n) {{ return n.id === id; }}); }})
    .filter(function(n) {{ return n !== undefined; }});

  // Successors
  const successorNodes = allNodes.filter(function(n) {{ return n.prerequisites.includes(node.id); }});

  function nodeListHTML(title, nodes, icon) {{
    if (nodes.length === 0) return '';
    return '<div class="detail-section">' +
      '<h4 class="detail-section-title">' + icon + ' ' + title + '</h4>' +
      '<div class="detail-node-list">' +
        nodes.map(function(n) {{
          const di = allDomains.find(function(d) {{ return d.id === n.domain; }});
          return '<button class="detail-node-item" style="border-left-color:' + (di ? di.color : '#888') + '" onclick="focusNode(\\'' + n.id + '\\')">' +
            '<span class="detail-node-name">' + n.name + '</span>' +
            '<span class="detail-node-year">' + n.year + '</span></button>';
        }}).join('') +
      '</div></div>';
  }}

  container.innerHTML =
    '<div class="detail-header"><button class="detail-close" onclick="closeDetail()" title="关闭">✕</button></div>' +
    '<div class="detail-body">' +
      '<h2 class="detail-name">' + node.name + '</h2>' +
      '<div class="detail-meta">' +
        '<span class="detail-domain-badge" style="background-color:' + domainColor + '">' + domainName + '</span>' +
        '<span class="detail-year">📅 ' + node.year + '</span>' +
        '<span class="detail-hub">⭐ 枢纽值 ' + (node.hubScore || 0) + '</span>' +
      '</div>' +
      '<div class="detail-section"><p class="detail-description">' + node.description + '</p></div>' +
      (node.tags && node.tags.length > 0 ?
        '<div class="detail-section"><div class="detail-tags">' +
          node.tags.map(function(t) {{ return '<span class="detail-tag">' + t + '</span>'; }}).join('') +
        '</div></div>' : '') +
      nodeListHTML('前置技术', prereqNodes, '⬅️') +
      nodeListHTML('后继技术', successorNodes, '➡️') +
    '</div>';
}}

// ========== Event Handlers ==========
function onSearchChange(value) {{
  state.searchText = value;
  document.getElementById('search-clear').style.display = value ? 'block' : 'none';
  updateCy();
}}

function clearSearch() {{
  state.searchText = '';
  document.getElementById('search-input').value = '';
  document.getElementById('search-clear').style.display = 'none';
  updateCy();
}}

function toggleEra(eraId) {{
  const idx = state.selectedEras.indexOf(eraId);
  if (idx >= 0) state.selectedEras.splice(idx, 1);
  else state.selectedEras.push(eraId);
  updateCy();
}}

function selectAllEras() {{
  state.selectedEras = allEras.map(function(e) {{ return e.id; }});
  renderEraCheckboxes();
  updateCy();
}}

function clearAllEras() {{
  state.selectedEras = [];
  renderEraCheckboxes();
  updateCy();
}}

function toggleDomain(domainId) {{
  const idx = state.selectedDomains.indexOf(domainId);
  if (idx >= 0) state.selectedDomains.splice(idx, 1);
  else state.selectedDomains.push(domainId);
  updateCy();
}}

function selectAllDomains() {{
  state.selectedDomains = allDomains.map(function(d) {{ return d.id; }});
  renderDomainCheckboxes();
  updateCy();
}}

function clearAllDomains() {{
  state.selectedDomains = [];
  renderDomainCheckboxes();
  updateCy();
}}

function onHubChange(value) {{
  state.hubThreshold = parseFloat(value);
  document.getElementById('hub-value').textContent = value;
  updateCy();
}}

function setLayout(layout) {{
  state.layout = layout;
  // Update active button
  document.querySelectorAll('.toolbar-layout-group .toolbar-btn').forEach(function(btn) {{
    btn.classList.toggle('active', btn.getAttribute('data-layout') === layout);
  }});
  updateCy();
}}

function resetView() {{
  if (cy) cy.fit(undefined, 50);
}}

function onNodeSelect(nodeId) {{
  if (state.selectedNodeId === nodeId) {{
    state.selectedNodeId = null;
    if (cy) cy.nodes().removeClass('selected');
  }} else {{
    state.selectedNodeId = nodeId;
    if (cy) {{
      cy.nodes().removeClass('selected');
      const sn = cy.getElementById(nodeId);
      if (sn.length > 0) sn.addClass('selected');
    }}
  }}
  renderNodeDetail();
}}

function closeDetail() {{
  state.selectedNodeId = null;
  if (cy) cy.nodes().removeClass('selected');
  renderNodeDetail();
}}

function focusNode(nodeId) {{
  state.selectedNodeId = nodeId;
  renderNodeDetail();
  if (cy) {{
    const node = cy.getElementById(nodeId);
    if (node.length > 0) {{
      cy.nodes().removeClass('selected');
      node.addClass('selected');
      cy.animate({{ fit: {{ eles: node, padding: 100 }}, duration: 500 }});
    }}
  }}
}}

function onTimelineStart(value) {{
  const newYear = positionToYear(parseInt(value, 10));
  if (newYear <= state.yearRange[1]) {{
    state.yearRange = [newYear, state.yearRange[1]];
    renderTimeline();
    updateCy();
  }}
}}

function onTimelineEnd(value) {{
  const newYear = positionToYear(parseInt(value, 10));
  if (newYear >= state.yearRange[0]) {{
    state.yearRange = [state.yearRange[0], newYear];
    renderTimeline();
    updateCy();
  }}
}}

// ========== Box Select (Right-click drag to zoom) ==========
function initBoxSelect() {{
  const wrapper = document.getElementById('tree-wrapper');

  wrapper.addEventListener('contextmenu', function(e) {{ e.preventDefault(); }});

  wrapper.addEventListener('mousedown', function(e) {{
    if (e.button !== 2) return;
    const rect = wrapper.getBoundingClientRect();
    boxSelecting = true;
    boxStart = {{ x: e.clientX - rect.left, y: e.clientY - rect.top }};
    const overlay = document.getElementById('box-select-overlay');
    overlay.style.display = 'none';
    e.preventDefault();
  }});

  wrapper.addEventListener('mousemove', function(e) {{
    if (!boxSelecting || !boxStart) return;
    const rect = wrapper.getBoundingClientRect();
    const ex = e.clientX - rect.left;
    const ey = e.clientY - rect.top;
    const overlay = document.getElementById('box-select-overlay');
    overlay.style.display = 'block';
    overlay.style.left = Math.min(boxStart.x, ex) + 'px';
    overlay.style.top = Math.min(boxStart.y, ey) + 'px';
    overlay.style.width = Math.abs(ex - boxStart.x) + 'px';
    overlay.style.height = Math.abs(ey - boxStart.y) + 'px';
  }});

  wrapper.addEventListener('mouseup', function(e) {{
    if (!boxSelecting || !boxStart) return;
    boxSelecting = false;
    const overlay = document.getElementById('box-select-overlay');
    overlay.style.display = 'none';

    const rect = wrapper.getBoundingClientRect();
    const ex = e.clientX - rect.left;
    const ey = e.clientY - rect.top;
    const x1 = Math.min(boxStart.x, ex);
    const y1 = Math.min(boxStart.y, ey);
    const x2 = Math.max(boxStart.x, ex);
    const y2 = Math.max(boxStart.y, ey);

    boxStart = null;
    if (x2 - x1 < 10 || y2 - y1 < 10) return;
    if (!cy) return;

    const container = document.getElementById('cy-container');
    const wrapperRect = wrapper.getBoundingClientRect();
    const containerRect = container.getBoundingClientRect();
    const cx1 = x1 - (containerRect.left - wrapperRect.left);
    const cy1 = y1 - (containerRect.top - wrapperRect.top);
    const cx2 = x2 - (containerRect.left - wrapperRect.left);
    const cy2 = y2 - (containerRect.top - wrapperRect.top);

    const pan = cy.pan();
    const zoom = cy.zoom();
    const modelX1 = (cx1 - pan.x) / zoom;
    const modelY1 = (cy1 - pan.y) / zoom;
    const modelX2 = (cx2 - pan.x) / zoom;
    const modelY2 = (cy2 - pan.y) / zoom;

    const boxedNodes = cy.nodes().filter(function(node) {{
      const p = node.position();
      return p.x >= modelX1 && p.x <= modelX2 && p.y >= modelY1 && p.y <= modelY2;
    }});

    if (boxedNodes.length > 0) {{
      cy.animate({{ fit: {{ eles: boxedNodes, padding: 30 }}, duration: 400 }});
    }} else {{
      const centerX = (modelX1 + modelX2) / 2;
      const centerY = (modelY1 + modelY2) / 2;
      const cW = container.clientWidth;
      const cH = container.clientHeight;
      const newZoom = Math.min(cW / (modelX2 - modelX1), cH / (modelY2 - modelY1)) * 0.9;
      const clampedZoom = Math.max(0.1, Math.min(3, newZoom));
      cy.animate({{
        pan: {{ x: cW / 2 - centerX * clampedZoom, y: cH / 2 - centerY * clampedZoom }},
        zoom: clampedZoom,
        duration: 400,
      }});
    }}
  }});
}}

// ========== Minimap Click Navigation ==========
document.getElementById('minimap-canvas').addEventListener('click', function(e) {{
  if (!cy) return;
  const canvas = this;
  const rect = canvas.getBoundingClientRect();
  const rx = (e.clientX - rect.left) / rect.width;
  const ry = (e.clientY - rect.top) / rect.height;

  const nodes = cy.nodes();
  if (nodes.length === 0) return;

  const bbox = nodes.boundingBox({{}});
  const pad = 30;
  const bx = bbox.x1 - pad, by = bbox.y1 - pad;
  const bw = Math.max(bbox.w + pad * 2, 1);
  const bh = Math.max(bbox.h + pad * 2, 1);

  const tx = bx + rx * bw;
  const ty = by + ry * bh;
  const z = cy.zoom();

  cy.animate({{
    pan: {{ x: cy.width() / 2 - tx * z, y: cy.height() / 2 - ty * z }},
    duration: 300,
  }});
}});

// ========== Initialization ==========
function init() {{
  const success = loadData();
  if (!success) {{
    document.getElementById('loading').innerHTML =
      '<div style="text-align:center;color:#f85149;"><h2>加载失败</h2><p>无法读取科技树数据</p></div>';
    return;
  }}

  // Hide loading, show app
  document.getElementById('loading').style.display = 'none';
  document.getElementById('app').style.display = 'flex';

  // Render UI
  renderEraCheckboxes();
  renderDomainCheckboxes();
  renderLegend();
  renderTimeline();

  // Init Cytoscape
  initCy();
  initBoxSelect();
}}

// Start
init();
</script>
</body>
</html>'''

    with open('standalone.html', 'w', encoding='utf-8') as f:
        f.write(html)

    import os
    size = os.path.getsize('standalone.html')
    print(f'standalone.html generated: {size:,} bytes ({size/1024:.1f} KB)')

if __name__ == '__main__':
    main()
