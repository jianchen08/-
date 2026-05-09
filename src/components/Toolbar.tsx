import type { LayoutType } from '../types';

interface ToolbarProps {
  layout: LayoutType;
  onLayoutChange: (layout: LayoutType) => void;
  onResetView: () => void;
}

const layoutOptions: { value: LayoutType; label: string; icon: string }[] = [
  { value: 'dagre', label: '层次布局', icon: '📐' },
  { value: 'force', label: '力导向', icon: '🌐' },
  { value: 'timeline', label: '时间轴', icon: '⏰' },
];

export default function Toolbar({ layout, onLayoutChange, onResetView }: ToolbarProps) {
  return (
    <div className="toolbar">
      <div className="toolbar-layout-group">
        {layoutOptions.map((opt) => (
          <button
            key={opt.value}
            className={`toolbar-btn ${layout === opt.value ? 'active' : ''}`}
            onClick={() => onLayoutChange(opt.value)}
            title={opt.label}
          >
            <span className="toolbar-btn-icon">{opt.icon}</span>
            <span className="toolbar-btn-label">{opt.label}</span>
          </button>
        ))}
      </div>
      <button className="toolbar-btn toolbar-reset" onClick={onResetView} title="重置视图">
        <span className="toolbar-btn-icon">🔄</span>
        <span className="toolbar-btn-label">重置</span>
      </button>
    </div>
  );
}
