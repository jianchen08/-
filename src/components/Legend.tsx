import type { Domain } from '../types';

interface LegendProps {
  domains: Domain[];
}

export default function Legend({ domains }: LegendProps) {
  return (
    <div className="legend">
      <div className="legend-title">🗺️ 图例</div>

      {/* 领域颜色 */}
      <div className="legend-section">
        <div className="legend-subtitle">领域颜色</div>
        <div className="legend-items">
          {domains.map((d) => (
            <div key={d.id} className="legend-item">
              <span
                className="legend-color-dot"
                style={{ backgroundColor: d.color }}
              />
              <span className="legend-item-text">{d.name}</span>
            </div>
          ))}
        </div>
      </div>

      {/* 节点大小 */}
      <div className="legend-section">
        <div className="legend-subtitle">节点大小</div>
        <div className="legend-items legend-size-items">
          <div className="legend-item">
            <span className="legend-size-dot small" />
            <span className="legend-item-text">低枢纽值</span>
          </div>
          <div className="legend-item">
            <span className="legend-size-dot medium" />
            <span className="legend-item-text">中枢纽值</span>
          </div>
          <div className="legend-item">
            <span className="legend-size-dot large" />
            <span className="legend-item-text">高枢纽值</span>
          </div>
        </div>
      </div>

      {/* 光晕动画 */}
      <div className="legend-section">
        <div className="legend-subtitle">光晕动画</div>
        <div className="legend-items">
          <div className="legend-item">
            <span className="legend-glow-dot" />
            <span className="legend-item-text">Top 10 枢纽节点</span>
          </div>
        </div>
      </div>
    </div>
  );
}
