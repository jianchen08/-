import type { TechNode, Domain } from '../types';

interface NodeDetailProps {
  node: TechNode | null;
  domains: Domain[];
  allNodes: TechNode[];
  onClose: () => void;
  onNodeClick: (nodeId: string) => void;
}

export default function NodeDetail({
  node,
  domains,
  allNodes,
  onClose,
  onNodeClick,
}: NodeDetailProps) {
  if (!node) return null;

  const domainInfo = domains.find((d) => d.id === node.domain);
  const domainName = domainInfo?.name ?? node.domain;
  const domainColor = domainInfo?.color ?? '#888';

  // 前置节点
  const prereqNodes = node.prerequisites
    .map((id) => allNodes.find((n) => n.id === id))
    .filter((n): n is TechNode => n !== undefined);

  // 后继节点
  const successorNodes = allNodes.filter((n) =>
    n.prerequisites.includes(node.id),
  );

  const renderNodeList = (
    title: string,
    nodes: TechNode[],
    icon: string,
  ) => {
    if (nodes.length === 0) return null;
    return (
      <div className="detail-section">
        <h4 className="detail-section-title">
          {icon} {title}
        </h4>
        <div className="detail-node-list">
          {nodes.map((n) => {
            const dInfo = domains.find((d) => d.id === n.domain);
            return (
              <button
                key={n.id}
                className="detail-node-item"
                onClick={() => onNodeClick(n.id)}
                style={{ borderLeftColor: dInfo?.color ?? '#888' }}
              >
                <span className="detail-node-name">{n.name}</span>
                <span className="detail-node-year">{n.year}</span>
              </button>
            );
          })}
        </div>
      </div>
    );
  };

  return (
    <div className="node-detail">
      <div className="detail-header">
        <button className="detail-close" onClick={onClose} title="关闭">
          ✕
        </button>
      </div>

      <div className="detail-body">
        {/* 名称 */}
        <h2 className="detail-name">{node.name}</h2>

        {/* 元信息 */}
        <div className="detail-meta">
          <span
            className="detail-domain-badge"
            style={{ backgroundColor: domainColor }}
          >
            {domainName}
          </span>
          <span className="detail-year">📅 {node.year}</span>
          <span className="detail-hub">⭐ 枢纽值 {node.hubScore ?? 0}</span>
        </div>

        {/* 描述 */}
        <div className="detail-section">
          <p className="detail-description">{node.description}</p>
        </div>

        {/* 标签 */}
        {node.tags && node.tags.length > 0 && (
          <div className="detail-section">
            <div className="detail-tags">
              {node.tags.map((tag) => (
                <span key={tag} className="detail-tag">
                  {tag}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* 前置节点 */}
        {renderNodeList('前置技术', prereqNodes, '⬅️')}

        {/* 后继节点 */}
        {renderNodeList('后继技术', successorNodes, '➡️')}
      </div>
    </div>
  );
}
