import { useEffect, useRef, useCallback } from 'react';
import cytoscape from 'cytoscape';
import dagre from 'cytoscape-dagre';
import coseBilkent from 'cytoscape-cose-bilkent';
import type cytoscapeType from 'cytoscape';
import type { TechNode, Domain, LayoutType, FilterState } from '../types';

cytoscape.use(dagre);
cytoscape.use(coseBilkent);

interface TechTreeProps {
  nodes: TechNode[];
  domains: Domain[];
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

/** 筛选判断 */
function passesFilter(node: TechNode, filter: FilterState): boolean {
  if (filter.selectedEras.length > 0 && !filter.selectedEras.includes(node.era)) return false;
  if (filter.selectedDomains.length > 0 && !filter.selectedDomains.includes(node.domain)) return false;
  if ((node.hubScore ?? 0) < filter.hubThreshold) return false;
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

  // 筛选可见节点
  const visibleNodes = nodes.filter((n) => passesFilter(n, filter));
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

  // 只添加两端都可见的边
  for (const node of visibleNodes) {
    for (const prereq of node.prerequisites) {
      if (visibleIds.has(prereq)) {
        elements.push({
          group: 'edges',
          data: {
            id: `${prereq}->${node.id}`,
            source: prereq,
            target: node.id,
          },
        });
      }
    }
  }

  return { elements, matchedIds };
}

/** 获取布局配置 */
function getLayoutOptions(layout: LayoutType) {
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
    case 'timeline':
      return {
        name: 'circle',
        animate: true,
        animationDuration: 500,
      };
    default:
      return { name: 'dagre', animate: true };
  }
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
      },
    },
    {
      selector: 'edge',
      style: {
        width: 1,
        'line-color': '#555',
        'target-arrow-color': '#555',
        'target-arrow-shape': 'triangle',
        'arrow-scale': 0.6,
        'curve-style': 'bezier',
        opacity: 0.5,
      },
    },
  ];
}

export default function TechTree({
  nodes,
  domains,
  searchText,
  filter,
  layout,
  selectedNodeId,
  onNodeSelect,
  onCyReady,
}: TechTreeProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);
  const domainColorMapRef = useRef<Map<string, string>>(new Map());
  const isFirstRenderRef = useRef(true);

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

    const domainColorMap = domainColorMapRef.current;
    const { elements } = buildElements(nodes, domainColorMap, searchText, filter);

    // 销毁旧实例
    if (cyRef.current) {
      cyRef.current.destroy();
      cyRef.current = null;
    }

    const layoutOpts = getLayoutOptions(layout);

    const cy = cytoscape({
      container: containerRef.current,
      elements,
      style: getCyStyle(),
      layout: layoutOpts as cytoscape.LayoutOptions,
      minZoom: 0.1,
      maxZoom: 3,
      wheelSensitivity: 0.3,
    });

    // 节点点击事件
    cy.on('tap', 'node', (evt) => {
      const nodeId = evt.target.id();
      onNodeSelect(nodeId);
    });

    // 点击空白区域取消选中
    cy.on('tap', (evt) => {
      if (evt.target === cy) {
        // 点击了画布空白区域，不做什么，保留选中状态
      }
    });

    cyRef.current = cy;
    isFirstRenderRef.current = false;
    onCyReady?.(cy);

    return () => {
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
    const layoutOpts = getLayoutOptions(layout);
    cy.layout(layoutOpts as cytoscape.LayoutOptions).run();

    // 重新应用选中状态
    if (selectedNodeId) {
      const selectedNode = cy.getElementById(selectedNodeId);
      if (selectedNode.length > 0) {
        selectedNode.addClass('selected');
      }
    }
  }, [searchText, filter, nodes, layout, selectedNodeId]);

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
  // 通过 DOM data 属性传递（简化方案）
  useEffect(() => {
    if (containerRef.current) {
      (containerRef.current as unknown as Record<string, unknown>)._resetView = resetView;
      (containerRef.current as unknown as Record<string, unknown>)._focusNode = focusNode;
    }
  }, [resetView, focusNode]);

  return (
    <div className="tech-tree-wrapper">
      <div ref={containerRef} className="tech-tree-container" />
    </div>
  );
}
