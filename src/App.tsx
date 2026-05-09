import { useState, useEffect, useRef, useCallback } from 'react';
import type cytoscape from 'cytoscape';
import type { TechTreeData, TechNode, FilterState, LayoutType } from './types';
import { loadTechTreeData } from './utils/dataLoader';
import { exportViewport, exportFullView } from './utils/pdfExporter';
import TechTree from './components/TechTree';
import SearchPanel from './components/SearchPanel';
import FilterPanel from './components/FilterPanel';
import NodeDetail from './components/NodeDetail';
import Toolbar from './components/Toolbar';
import Legend from './components/Legend';
import MiniMap from './components/MiniMap';
import TimelineSlider from './components/TimelineSlider';
import './App.css';

export default function App() {
  // 数据状态
  const [data, setData] = useState<TechTreeData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 交互状态
  const [searchText, setSearchText] = useState('');
  const [filter, setFilter] = useState<FilterState>({
    selectedEras: [],
    selectedDomains: [],
    hubThreshold: 0,
  });
  const [layout, setLayout] = useState<LayoutType>('dagre');
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);

  // 导出状态
  const [exporting, setExporting] = useState(false);

  // Cytoscape 实例引用（供 MiniMap 使用）
  const [cyInstance, setCyInstance] = useState<cytoscape.Core | null>(null);

  const handleCyReady = useCallback((cy: cytoscape.Core | null) => {
    setCyInstance(cy);
  }, []);

  // TechTree 容器 ref（用于调用 resetView/focusNode）
  const treeContainerRef = useRef<HTMLDivElement | null>(null);

  // 加载数据
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const result = await loadTechTreeData();
        if (!cancelled) {
          setData(result);
          // 初始化筛选：全选所有时代和领域
          setFilter({
            selectedEras: result.eras.map((e) => e.id),
            selectedDomains: result.domains.map((d) => d.id),
            hubThreshold: 0,
          });
          setLoading(false);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : '加载失败');
          setLoading(false);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  // 节点选中处理
  const handleNodeSelect = useCallback((nodeId: string) => {
    setSelectedNodeId((prev) => (prev === nodeId ? null : nodeId));
  }, []);

  // 详情面板中的节点跳转
  const handleDetailNodeClick = useCallback((nodeId: string) => {
    setSelectedNodeId(nodeId);
    // 聚焦到节点
    const container = treeContainerRef.current?.querySelector('.tech-tree-container');
    if (container) {
      const focusFn = (container as unknown as Record<string, unknown>)._focusNode;
      if (typeof focusFn === 'function') {
        (focusFn as (id: string) => void)(nodeId);
      }
    }
  }, []);

  // 关闭详情
  const handleCloseDetail = useCallback(() => {
    setSelectedNodeId(null);
  }, []);

  // 重置视图
  const handleResetView = useCallback(() => {
    const container = treeContainerRef.current?.querySelector('.tech-tree-container');
    if (container) {
      const resetFn = (container as unknown as Record<string, unknown>)._resetView;
      if (typeof resetFn === 'function') {
        (resetFn as () => void)();
      }
    }
  }, []);

  // 导出视口截图
  const handleExportViewport = useCallback(async () => {
    const container = treeContainerRef.current?.querySelector('.tech-tree-container');
    if (!container || exporting) return;
    setExporting(true);
    try {
      await exportViewport(container as HTMLElement);
    } catch (err) {
      console.error('视口导出失败:', err);
    } finally {
      setExporting(false);
    }
  }, [exporting]);

  // 导出全景
  const handleExportFullView = useCallback(async () => {
    const wrapper = treeContainerRef.current?.querySelector('.tech-tree-container');
    if (!wrapper || exporting) return;
    setExporting(true);
    try {
      await exportFullView(wrapper as HTMLElement);
    } catch (err) {
      console.error('全景导出失败:', err);
    } finally {
      setExporting(false);
    }
  }, [exporting]);

  // 获取选中的节点
  const selectedNode: TechNode | null = selectedNodeId && data
    ? data.nodes.find((n) => n.id === selectedNodeId) ?? null
    : null;

  if (error) {
    return (
      <div className="app-error">
        <div className="app-error-content">
          <h2>加载失败</h2>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  if (loading || !data) {
    return (
      <div className="app-loading">
        <div className="app-loading-spinner" />
        <p>正在加载科技树数据...</p>
      </div>
    );
  }

  return (
    <div className="app-layout">
      {/* 左侧：筛选面板 */}
      <aside className="app-sidebar-left">
        <div className="app-sidebar-title">⚙️ 筛选</div>
        <FilterPanel
          eras={data.eras}
          domains={data.domains}
          filter={filter}
          onFilterChange={setFilter}
        />
      </aside>

      {/* 中间：主区域 */}
      <main className="app-main" ref={treeContainerRef}>
        {/* 顶部栏：搜索 + 工具栏 */}
        <div className="app-top-bar">
          <SearchPanel searchText={searchText} onSearchChange={setSearchText} />
          <Toolbar
            layout={layout}
            onLayoutChange={setLayout}
            onResetView={handleResetView}
            exporting={exporting}
            onExportViewport={handleExportViewport}
            onExportFullView={handleExportFullView}
          />
        </div>

        {/* 图区域 */}
        <TechTree
          nodes={data.nodes}
          domains={data.domains}
          searchText={searchText}
          filter={filter}
          layout={layout}
          selectedNodeId={selectedNodeId}
          onNodeSelect={handleNodeSelect}
          onCyReady={handleCyReady}
        />

        {/* 左下图例 */}
        <Legend domains={data.domains} />

        {/* 右下小地图 */}
        <MiniMap domains={data.domains} cy={cyInstance} />

        {/* 底部时间轴 */}
        <TimelineSlider eras={data.eras} filter={filter} onFilterChange={setFilter} />
      </main>

      {/* 右侧：详情侧栏 */}
      <aside className={`app-sidebar-right ${selectedNode ? 'open' : ''}`}>
        <NodeDetail
          node={selectedNode}
          domains={data.domains}
          allNodes={data.nodes}
          onClose={handleCloseDetail}
          onNodeClick={handleDetailNodeClick}
        />
      </aside>
    </div>
  );
}
