import { useEffect, useRef, useState } from 'react';
import cytoscape from 'cytoscape';
import dagre from 'cytoscape-dagre';
import type { TechNode } from '../types';
import { loadTechTreeData } from '../utils/dataLoader';
import { calculateHubScores, getRankedNodeIds } from '../utils/hubCalculator';

cytoscape.use(dagre);

/** Dagre 布局选项（包含 cytoscape 基础属性和 dagre 扩展属性） */
interface DagreLayoutOptions {
  name: string;
  rankDir?: string;
  spacingFactor?: number;
  nodeSep?: number;
  rankSep?: number;
  animate?: boolean;
}

/** 将 hubScore (0-100) 映射到节点大小 (20-50px) */
function hubToSize(hubScore: number): number {
  return 20 + (hubScore / 100) * 30;
}

/** 调整颜色亮度：将 hex 颜色乘以 factor (0.4~1.0) */
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

export default function TechTree() {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    let cancelled = false;

    (async () => {
      try {
        const { nodes, domains } = await loadTechTreeData();

        // 组件已卸载，不再继续
        if (cancelled) return;

        const scoreMap = calculateHubScores(nodes);
        const rankedIds = getRankedNodeIds(nodes, scoreMap);
        const top20Set = new Set(rankedIds.slice(0, 20));
        const top10Set = new Set(rankedIds.slice(0, 10));

        const domainColorMap = new Map<string, string>();
        for (const d of domains) {
          domainColorMap.set(d.id, d.color);
        }

        const elements = buildElements(nodes, domainColorMap, top20Set, top10Set, scoreMap);

        // 再次检查是否已卸载（containerRef.current 可能在卸载后为 null）
        if (cancelled || !containerRef.current) return;

        const layoutOptions: DagreLayoutOptions = {
          name: 'dagre',
          rankDir: 'LR',
          spacingFactor: 1.2,
          nodeSep: 30,
          rankSep: 80,
          animate: false,
        };

        cyRef.current = cytoscape({
          container: containerRef.current,
          elements,
          style: getCyStyle(),
          layout: layoutOptions as cytoscape.LayoutOptions,
          minZoom: 0.1,
          maxZoom: 3,
          wheelSensitivity: 0.3,
        });

        if (!cancelled) {
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
      if (cyRef.current) {
        cyRef.current.destroy();
        cyRef.current = null;
      }
    };
  }, []);

  if (error) {
    return <div className="tech-tree-error">加载失败: {error}</div>;
  }

  return (
    <div className="tech-tree-wrapper">
      {loading && <div className="tech-tree-loading">加载科技树数据中...</div>}
      <div ref={containerRef} className="tech-tree-container" />
    </div>
  );
}

function buildElements(
  nodes: TechNode[],
  domainColorMap: Map<string, string>,
  top20Set: Set<string>,
  top10Set: Set<string>,
  scoreMap: Map<string, number>,
) {
  const nodeIds = new Set(nodes.map((n) => n.id));
  const elements: cytoscape.ElementDefinition[] = [];

  for (const node of nodes) {
    const hubScore = scoreMap.get(node.id) ?? 0;
    const isTop10 = top10Set.has(node.id);
    const isTop20 = top20Set.has(node.id);
    const baseColor = domainColorMap.get(node.domain) ?? '#888888';
    const displayColor = adjustBrightness(baseColor, hubScore);
    const size = hubToSize(hubScore);
    const displayLabel = isTop10 ? `☆ ${node.name}` : node.name;

    elements.push({
      group: 'nodes',
      data: {
        id: node.id,
        name: displayLabel,
        domain: node.domain,
        hubScore,
        isTop10,
        isTop20,
        era: node.era,
        year: node.year,
        nodeSize: size,
        displayColor,
      },
    });
  }

  for (const node of nodes) {
    for (const prereq of node.prerequisites) {
      if (nodeIds.has(prereq)) {
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

  return elements;
}

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
      },
    },
    {
      selector: 'node[?isTop20]',
      style: {
        'border-width': 3,
        'border-color': '#FFD700',
        'border-opacity': 0.8,
      },
    },
    {
      selector: 'node[?isTop10]',
      style: {
        'border-width': 4,
        'border-color': '#FF4500',
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
        opacity: 0.6,
      },
    },
  ];
}
