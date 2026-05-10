import { useEffect, useRef, useCallback, useState, forwardRef, useImperativeHandle } from 'react';
import cytoscape from 'cytoscape';
import dagre from 'cytoscape-dagre';
import coseBilkent from 'cytoscape-cose-bilkent';
import type cytoscapeType from 'cytoscape';
import type { TechNode, Domain, Era, LayoutType, FilterState } from '../types';

cytoscape.use(dagre);
cytoscape.use(coseBilkent);

interface TechTreeProps {
  nodes: TechNode[];
  domains: Domain[];
  eras: Era[];
  searchText: string;
  filter: FilterState;
  layout: LayoutType;
  selectedNodeId: string | null;
  onNodeSelect: (nodeId: string) => void;
  onCyReady?: (cy: cytoscapeType.Core | null) => void;
}

/** hubScore (0-100) → 节点大小 (20-50px) */
function hubToSize(hubScore: number): number {
  return 20 + (hubScore / 100) * 30;
}

/** 根据枢纽值调整颜色亮度 */
function adjustBrightness(hex: string, hubScore: number): string {
  const factor = 0.4 + (hubScore / 100) * 0.6;
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  const nr = Math.min(255, Math.round(r * factor));
  const ng = Math.min(255, Math.round(g * factor));
  const nb = Math.min(255, Math.round(b * factor));
  return `#${nr.toString(16).padStart(2, '0')}${ng.toString(16).padStart(2, '0')}${nb.toString(16).padStart(2, '0')}`;
}

/** 搜索匹配判断 */
function matchesSearch(node: TechNode, text: string): boolean {
  if (!text.trim()) return true;
  const lower = text.toLowerCase();
  if (node.name.toLowerCase().includes(lower)) return true;
  if (node.description.toLowerCase().includes(lower)) return true;
  if (node.tags?.some((t) => t.toLowerCase().includes(lower))) return true;
  return false;
}

/** 筛选判断（含年份范围检查） */
function passesFilter(node: TechNode, filter: FilterState): boolean {
  if (filter.selectedEras.length > 0 && !filter.selectedEras.includes(node.era)) return false;
  if (filter.selectedDomains.length > 0 && !filter.selectedDomains.includes(node.domain)) return false;
  if ((node.hubScore ?? 0) < filter.hubThreshold) return false;
  // 年份范围检查
  const nodeYear = typeof node.year === 'string' ? parseInt(node.year, 10) : node.year;
  if (filter.yearRange) {
    if (nodeYear < filter.yearRange[0] || nodeYear > filter.yearRange[1]) return false;
  }
  return true;
}

/** 构建 cytoscape elements */
function buildElements(
  nodes: TechNode[],
  domainColorMap: Map<string, string>,
  searchText: string,
  filter: FilterState,
) {
  const elements: cytoscape.ElementDefinition[] = [];
  const visibleIds = new Set<string>();

  // 筛选可见节点，并按年份升序排序（影响 dagre 布局中同层级节点的排列）
  const visibleNodes = nodes
    .filter((n) => passesFilter(n, filter))
    .sort((a, b) => {
      const yearA = typeof a.year === 'string' ? parseInt(a.year, 10) : a.year;
      const yearB = typeof b.year === 'string' ? parseInt(b.year, 10) : b.year;
      return yearA - yearB;
    });
  for (const n of visibleNodes) {
    visibleIds.add(n.id);
  }

  // 搜索匹配的节点集合
  const searchLower = searchText.toLowerCase().trim();
  const matchedIds = new Set<string>();
  if (searchLower) {
    for (const n of visibleNodes) {
      if (matchesSearch(n, searchText)) {
        matchedIds.add(n.id);
      }
    }
  }

  for (const node of visibleNodes) {
    const hubScore = node.hubScore ?? 0;
    const baseColor = domainColorMap.get(node.domain) ?? '#888888';
    const displayColor = adjustBrightness(baseColor, hubScore);
    const size = hubToSize(hubScore);
    const isMatched = searchLower ? matchedIds.has(node.id) : true;
    const isDimmed = searchLower ? !matchedIds.has(node.id) : false;

    elements.push({
      group: 'nodes',
      data: {
        id: node.id,
        name: hubScore >= 80 ? `⭐ ${node.name}` : node.name,
        domain: node.domain,
        hubScore,
        era: node.era,
        year: node.year,
        nodeSize: size,
        displayColor,
        isMatched,
        isDimmed,
      },
    });
  }

  // 只添加两端都可见的边，根据源节点枢纽值设置边宽度（1-4px分级）
  for (const node of visibleNodes) {
    for (const prereq of node.prerequisites) {
      if (visibleIds.has(prereq)) {
        const prereqNode = nodes.find((n) => n.id === prereq);
        const prereqHub = prereqNode?.hubScore ?? 0;
        const edgeWidth = prereqHub >= 80 ? 4 : prereqHub >= 60 ? 3 : prereqHub >= 30 ? 2 : 1.5;
        elements.push({
          group: 'edges',
          data: {
            id: `${prereq}->${node.id}`,
            source: prereq,
            target: node.id,
            edgeWidth,
          },
        });
      }
    }
  }

  return { elements, matchedIds };
}

/** 获取布局配置 */
function getLayoutOptions(
  layout: LayoutType,
  nodes?: TechNode[],
  domains?: Domain[],
  eras?: Era[],
) {
  switch (layout) {
    case 'dagre':
      return {
        name: 'dagre',
        rankDir: 'LR' as const,
        spacingFactor: 1.2,
        nodeSep: 30,
        rankSep: 80,
        animate: true,
        animationDuration: 500,
      };
    case 'force':
      return {
        name: 'cose-bilkent',
        animate: true,
        animationDuration: 800,
        nodeRepulsion: 80000,
        idealEdgeLength: 80,
        gravity: 0.3,
        randomize: true,
      };
    case 'timeline': {
      if (!nodes || !domains || !eras) {
        return { name: 'circle', animate: true, animationDuration: 500 };
      }
      const eraWeights = [0.08, 0.10, 0.10, 0.10, 0.12, 0.15, 0.35];
      const domainMap = new Map(domains.map((d, i) => [d.id, i]));
      const positions: Record<string, { x: number; y: number }> = {};
      for (const node of nodes) {
        const year = typeof node.year === 'string' ? parseInt(node.year, 10) : node.year;
        let xPos = 0;
        for (let i = 0; i < eras.length; i++) {
          const era = eras[i];
          const weight = eraWeights[i] ?? 0.1;
          if (!era) break;
          const [eraStart, eraEnd] = era.yearRange;
          const segmentWidth = weight * 5000;
          if (year <= eraStart) break;
          if (year >= eraEnd) {
            xPos += segmentWidth;
          } else {
            const t = (year - eraStart) / (eraEnd - eraStart);
            xPos += t * segmentWidth;
            break;
          }
        }
        const domainIdx = domainMap.get(node.domain) ?? 0;
        const yBase = domainIdx * 120;
        let hash = 0;
        for (let i = 0; i < node.id.length; i++) {
          hash = ((hash << 5) - hash) + node.id.charCodeAt(i);
          hash |= 0;
        }
        const jitter = (Math.abs(hash) % 60) - 30;
        positions[node.id] = { x: xPos + jitter * 0.3, y: yBase + jitter };
      }
      return {
        name: 'preset',
        positions: (ele: cytoscape.NodeSingular) => positions[ele.id()] ?? { x: 0, y: 0 },
        animate: true,
        animationDuration: 500,
      };
    }
    default:
      return { name: 'dagre', animate: true };
  }
}

/** TechTree 暴露给父组件的方法 */
export interface TechTreeHandle {
  resetView: () => void;
  focusNode: (nodeId: string) => void;
}

/** Cytoscape 样式 */
function getCyStyle(): cytoscape.StylesheetStyle[] {
  return [
    {
      selector: 'node',
      style: {
        label: 'data(name)',
        width: 'data(nodeSize)',
        height: 'data(nodeSize)',
        'background-color': 'data(displayColor)',
        'text-valign': 'center',
        'text-halign': 'center',
        'font-size': '8px',
        color: '#fff',
        'text-outline-width': 1,
        'text-outline-color': '#000',
        'text-wrap': 'wrap',
        'text-max-width': '60px',
        opacity: 1,
        'transition-property': 'background-color, border-color, border-width, opacity, text-outline-width, font-size',
        'transition-duration': 150,
      },
    },
    {
      selector: 'node[?isDimmed]',
      style: {
        opacity: 0.12,
      },
    },
    {
      selector: 'node[hubScore >= 60]',
      style: {
        'border-width': 3,
        'border-color': '#FFD700',
        'border-opacity': 0.7,
      },
    },
    {
      selector: 'node[hubScore >= 80]',
      style: {
        'border-width': 4,
        'border-color': '#FF4500',
        'border-opacity': 1,
      },
    },
    {
      selector: 'node.selected',
      style: {
        'border-width': 5,
        'border-color': '#00FFFF',
        'border-opacity': 1,
        'font-size': '10px',
      },
    },
    {
      selector: 'node.hovered',
      style: {
        'border-width': 4,
        'border-color': '#ffffff',
        'border-opacity': 0.9,
        'z-index': 999,
        'font-size': '10px',
        'text-outline-width': 2,
        opacity: 1,
      },
    },
    {
      selector: 'edge',
      style: {
        width: 'data(edgeWidth)',
        'line-color': 'rgba(100, 140, 180, 0.35)',
        'target-arrow-color': 'rgba(100, 140, 180, 0.35)',
        'target-arrow-shape': 'triangle',
        'arrow-scale': 0.6,
        'curve-style': 'bezier',
        opacity: 0.5,
        'transition-property': 'line-color, target-arrow-color, width, opacity',
        'transition-duration': 200,
      },
    },
    {
      selector: 'edge.highlighted',
      style: {
        width: 3,
        'line-color': '#4fc3f7',
        'target-arrow-color': '#4fc3f7',
        opacity: 1,
      },
    },
  ];
}

const TechTree = forwardRef<TechTreeHandle, TechTreeProps>(function TechTree({
  nodes,
  domains,
  eras,
  searchText,
  filter,
  layout,
  selectedNodeId,
  onNodeSelect,
  onCyReady,
}, ref) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);
  const domainColorMapRef = useRef<Map<string, string>>(new Map());
  const isFirstRenderRef = useRef(true);
  const isBoxSelectingRef = useRef(false);
  const [boxSelect, setBoxSelect] = useState<{
    startX: number;
    startY: number;
    endX: number;
    endY: number;
  } | null>(null);

  // 初始化 domainColorMap
  useEffect(() => {
    const map = new Map<string, string>();
    for (const d of domains) {
      map.set(d.id, d.color);
    }
    domainColorMapRef.current = map;
  }, [domains]);

  // 初始化 cytoscape 实例
  useEffect(() => {
    if (!containerRef.current || nodes.length === 0) return;

    // 禁用浏览器默认右键菜单
    const container = containerRef.current;
    const preventContextMenu = (e: MouseEvent) => e.preventDefault();
    container.addEventListener('contextmenu', preventContextMenu);

    const domainColorMap = domainColorMapRef.current;
    const { elements } = buildElements(nodes, domainColorMap, searchText, filter);

    // 销毁旧实例
    if (cyRef.current) {
      cyRef.current.destroy();
      cyRef.current = null;
    }

    const layoutOpts = getLayoutOptions(layout, nodes, domains, eras);

    const cy = cytoscape({
      container: containerRef.current,
      elements,
      style: getCyStyle(),
      layout: layoutOpts as cytoscape.LayoutOptions,
      minZoom: 0.1,
      maxZoom: 3,
    });

    // 节点点击事件
    cy.on('tap', 'node', (evt) => {
      const nodeId = evt.target.id();
      onNodeSelect(nodeId);
    });

    // 右键选中节点
    cy.on('cxttap', 'node', (evt) => {
      const nodeId = evt.target.id();
      onNodeSelect(nodeId);
    });

    // 点击空白区域取消选中
    cy.on('tap', (evt) => {
      if (evt.target === cy) {
        // 点击了画布空白区域，不做什么，保留选中状态
      }
    });

    // 节点 hover 高亮：显示关联边和邻居节点
    cy.on('mouseover', 'node', (evt) => {
      const node = evt.target;
      node.addClass('hovered');
      // 高亮所有连接边
      node.connectedEdges().addClass('highlighted');
    });

    cy.on('mouseout', 'node', (evt) => {
      const node = evt.target;
      node.removeClass('hovered');
      node.connectedEdges().removeClass('highlighted');
    });

    cyRef.current = cy;

    // 确保布局完成后 fit 视图
    cy.one('layoutstop', () => {
      setTimeout(() => {
        cy.fit(undefined, 50);
      }, 100);
    });

    // 备用：如果布局在超时内没触发 layoutstop，也做 fit
    setTimeout(() => {
      if (cyRef.current === cy) {
        cy.fit(undefined, 50);
      }
    }, 800);
    isFirstRenderRef.current = false;
    onCyReady?.(cy);

    return () => {
      container.removeEventListener('contextmenu', preventContextMenu);
      cy.destroy();
      cyRef.current = null;
      onCyReady?.(null);
    };
    // 只在 nodes 和 domains 变化时重建实例
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nodes, domains]);

  // 搜索和筛选更新：更新元素
  useEffect(() => {
    const cy = cyRef.current;
    if (!cy || nodes.length === 0) return;

    const domainColorMap = domainColorMapRef.current;
    const { elements } = buildElements(nodes, domainColorMap, searchText, filter);

    cy.elements().remove();
    cy.add(elements);

    // 重新布局
    const layoutOpts = getLayoutOptions(layout, nodes, domains, eras);
    const layoutInstance = cy.layout(layoutOpts as cytoscape.LayoutOptions);

    // 布局完成后 fit 视图
    layoutInstance.one('layoutstop', () => {
      setTimeout(() => {
        cy.fit(undefined, 50);
      }, 100);
    });

    layoutInstance.run();

    // 重新应用选中状态
    if (selectedNodeId) {
      const selectedNode = cy.getElementById(selectedNodeId);
      if (selectedNode.length > 0) {
        selectedNode.addClass('selected');
      }
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchText, filter, nodes, layout]);

  // 选中节点高亮
  useEffect(() => {
    const cy = cyRef.current;
    if (!cy) return;

    cy.nodes().removeClass('selected');
    if (selectedNodeId) {
      const selectedNode = cy.getElementById(selectedNodeId);
      if (selectedNode.length > 0) {
        selectedNode.addClass('selected');
      }
    }
  }, [selectedNodeId]);

  /** 框选开始：右键拖拽 */
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (e.button !== 2) return;
    const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
    isBoxSelectingRef.current = true;
    setBoxSelect({
      startX: e.clientX - rect.left,
      startY: e.clientY - rect.top,
      endX: e.clientX - rect.left,
      endY: e.clientY - rect.top,
    });
    e.preventDefault();
  }, []);

  /** 框选移动 */
  const handleMouseMove = useCallback(
    (e: React.MouseEvent) => {
      if (!isBoxSelectingRef.current || !boxSelect) return;
      const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
      setBoxSelect({
        ...boxSelect,
        endX: e.clientX - rect.left,
        endY: e.clientY - rect.top,
      });
    },
    [boxSelect],
  );

  /** 框选结束：放大到选中区域 */
  const handleMouseUp = useCallback(
    (_e: React.MouseEvent) => {
      if (!isBoxSelectingRef.current || !boxSelect) return;
      isBoxSelectingRef.current = false;

      const cy = cyRef.current;
      if (!cy) {
        setBoxSelect(null);
        return;
      }

      const wrapper = _e.currentTarget as HTMLElement;
      const container = containerRef.current;
      if (!container) {
        setBoxSelect(null);
        return;
      }

      const x1 = Math.min(boxSelect.startX, boxSelect.endX);
      const y1 = Math.min(boxSelect.startY, boxSelect.endY);
      const x2 = Math.max(boxSelect.startX, boxSelect.endX);
      const y2 = Math.max(boxSelect.startY, boxSelect.endY);

      // 选框太小则忽略
      if (x2 - x1 < 10 || y2 - y1 < 10) {
        setBoxSelect(null);
        return;
      }

      // 获取 cytoscape 容器在 wrapper 中的偏移
      const wrapperRect = wrapper.getBoundingClientRect();
      const containerRect = container.getBoundingClientRect();
      const cx1 = x1 - (containerRect.left - wrapperRect.left);
      const cy1 = y1 - (containerRect.top - wrapperRect.top);
      const cx2 = x2 - (containerRect.left - wrapperRect.left);
      const cy2 = y2 - (containerRect.top - wrapperRect.top);

      // 将渲染坐标转换为模型坐标
      const pan = cy.pan();
      const zoom = cy.zoom();
      const modelX1 = (cx1 - pan.x) / zoom;
      const modelY1 = (cy1 - pan.y) / zoom;
      const modelX2 = (cx2 - pan.x) / zoom;
      const modelY2 = (cy2 - pan.y) / zoom;

      // 找到在框内的节点
      const boxedNodes = cy.nodes().filter((node) => {
        const pos = node.position();
        return (
          pos.x >= modelX1 &&
          pos.x <= modelX2 &&
          pos.y >= modelY1 &&
          pos.y <= modelY2
        );
      });

      if (boxedNodes.length > 0) {
        cy.animate({
          fit: { eles: boxedNodes, padding: 30 },
          duration: 400,
        });
      } else {
        // 框内无节点时直接缩放到该区域
        const centerX = (modelX1 + modelX2) / 2;
        const centerY = (modelY1 + modelY2) / 2;
        const containerW = container.clientWidth;
        const containerH = container.clientHeight;
        const newZoom =
          Math.min(
            containerW / (modelX2 - modelX1),
            containerH / (modelY2 - modelY1),
          ) * 0.9;
        const clampedZoom = Math.max(
          cy.minZoom() ?? 0.1,
          Math.min(cy.maxZoom() ?? 3, newZoom),
        );
        cy.animate({
          pan: {
            x: containerW / 2 - centerX * clampedZoom,
            y: containerH / 2 - centerY * clampedZoom,
          },
          zoom: clampedZoom,
          duration: 400,
        });
      }

      setBoxSelect(null);
    },
    [boxSelect],
  );

  // 暴露重置视图方法
  const resetView = useCallback(() => {
    const cy = cyRef.current;
    if (!cy) return;
    cy.fit(undefined, 50);
  }, []);

  // 暴露 focusNode 方法
  const focusNode = useCallback((nodeId: string) => {
    const cy = cyRef.current;
    if (!cy) return;
    const node = cy.getElementById(nodeId);
    if (node.length > 0) {
      cy.animate({
        fit: { eles: node, padding: 100 },
        duration: 500,
      });
    }
  }, []);

  // 存储 resetView 和 focusNode 到 ref 供父组件使用
  // 通过 useImperativeHandle 暴露方法给父组件
  useImperativeHandle(ref, () => ({
    resetView,
    focusNode,
  }), [resetView, focusNode]);

  return (
    <div
      className="tech-tree-wrapper"
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
    >
      <div ref={containerRef} className="tech-tree-container" />
      {boxSelect && (
        <div
          className="box-select-overlay"
          style={{
            left: `${Math.min(boxSelect.startX, boxSelect.endX)}px`,
            top: `${Math.min(boxSelect.startY, boxSelect.endY)}px`,
            width: `${Math.abs(boxSelect.endX - boxSelect.startX)}px`,
            height: `${Math.abs(boxSelect.endY - boxSelect.startY)}px`,
          }}
        />
      )}
    </div>
  );
});

export default TechTree;
