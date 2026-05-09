import { useState, useRef, useEffect, useCallback } from 'react';
import type { LayoutType } from '../types';

interface ToolbarProps {
  layout: LayoutType;
  onLayoutChange: (layout: LayoutType) => void;
  onResetView: () => void;
  /** 是否正在导出 PDF */
  exporting?: boolean;
  /** 视口导出回调 */
  onExportViewport?: () => void;
  /** 全景导出回调 */
  onExportFullView?: () => void;
}

const layoutOptions: { value: LayoutType; label: string; icon: string }[] = [
  { value: 'dagre', label: '层次布局', icon: '📐' },
  { value: 'force', label: '力导向', icon: '🌐' },
  { value: 'timeline', label: '时间轴', icon: '⏰' },
];

export default function Toolbar({
  layout,
  onLayoutChange,
  onResetView,
  exporting = false,
  onExportViewport,
  onExportFullView,
}: ToolbarProps) {
  const [exportMenuOpen, setExportMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // 点击外部关闭下拉菜单
  const handleClickOutside = useCallback((e: MouseEvent) => {
    if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
      setExportMenuOpen(false);
    }
  }, []);

  useEffect(() => {
    if (exportMenuOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [exportMenuOpen, handleClickOutside]);

  const handleExportViewport = () => {
    setExportMenuOpen(false);
    onExportViewport?.();
  };

  const handleExportFullView = () => {
    setExportMenuOpen(false);
    onExportFullView?.();
  };

  const toggleExportMenu = () => {
    if (!exporting) {
      setExportMenuOpen((prev) => !prev);
    }
  };

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

      {/* 导出按钮 */}
      <div className="toolbar-export-wrap" ref={menuRef}>
        <button
          className={`toolbar-btn toolbar-export ${exportMenuOpen ? 'active' : ''}`}
          onClick={toggleExportMenu}
          disabled={exporting}
          title="导出PDF"
        >
          <span className="toolbar-btn-icon">{exporting ? '⏳' : '📄'}</span>
          <span className="toolbar-btn-label">{exporting ? '导出中...' : '导出'}</span>
          {!exporting && <span className="toolbar-btn-arrow">▾</span>}
        </button>

        {exportMenuOpen && !exporting && (
          <div className="toolbar-export-dropdown">
            <button className="toolbar-export-item" onClick={handleExportViewport}>
              <span className="toolbar-export-icon">🖼️</span>
              <div className="toolbar-export-text">
                <div className="toolbar-export-title">视口导出</div>
                <div className="toolbar-export-desc">导出当前可见区域</div>
              </div>
            </button>
            <button className="toolbar-export-item" onClick={handleExportFullView}>
              <span className="toolbar-export-icon">🗺️</span>
              <div className="toolbar-export-text">
                <div className="toolbar-export-title">全景导出</div>
                <div className="toolbar-export-desc">导出完整科技树（多页）</div>
              </div>
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
