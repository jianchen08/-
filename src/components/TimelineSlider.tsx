import { useCallback } from 'react';
import type { Era, FilterState } from '../types';

interface TimelineSliderProps {
  eras: Era[];
  filter: FilterState;
  onFilterChange: (filter: FilterState) => void;
}

export default function TimelineSlider({ eras, filter, onFilterChange }: TimelineSliderProps) {
  // 单击时代块：只选该时代，再次点击则全选
  const handleEraClick = useCallback(
    (eraId: string) => {
      if (filter.selectedEras.length === 1 && filter.selectedEras[0] === eraId) {
        // 已单独选中该时代 → 恢复全选
        onFilterChange({ ...filter, selectedEras: eras.map((e) => e.id) });
      } else {
        onFilterChange({ ...filter, selectedEras: [eraId] });
      }
    },
    [filter, eras, onFilterChange]
  );

  // 滑块拖动：根据滑块值选中对应时代
  const handleSliderChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const idx = parseInt(e.target.value, 10);
      if (idx === 0) {
        onFilterChange({ ...filter, selectedEras: eras.map((e) => e.id) });
      } else {
        const era = eras[idx - 1];
        if (era) {
          onFilterChange({ ...filter, selectedEras: [era.id] });
        }
      }
    },
    [filter, eras, onFilterChange]
  );

  // 求滑块当前值
  const sliderValue =
    filter.selectedEras.length === 1
      ? eras.findIndex((e) => e.id === filter.selectedEras[0]) + 1
      : 0;

  // 计算各时代节点数比例（等分即可，数据由 eras 长度决定）
  const segmentCount = eras.length;

  return (
    <div className="timeline-slider">
      <div className="timeline-labels">
        <span className="timeline-title">⏳ 时间轴</span>
        <span className="timeline-hint">
          {sliderValue === 0 ? '全部时代' : eras[sliderValue - 1]?.name ?? ''}
        </span>
      </div>

      <div className="timeline-bar-container">
        <div className="timeline-segments">
          {eras.map((era) => {
            const isActive =
              filter.selectedEras.length === 0 ||
              filter.selectedEras.includes(era.id);
            const isSolo = filter.selectedEras.length === 1 && filter.selectedEras.includes(era.id);
            return (
              <button
                key={era.id}
                className={`timeline-segment ${isActive ? 'active' : ''} ${isSolo ? 'solo' : ''}`}
                style={{ width: `${100 / segmentCount}%` }}
                onClick={() => handleEraClick(era.id)}
                title={`${era.name} (${era.yearRange[0]} ~ ${era.yearRange[1]})`}
              >
                <span className="timeline-segment-name">{era.name}</span>
              </button>
            );
          })}
        </div>

        <input
          type="range"
          className="timeline-range"
          min={0}
          max={eras.length}
          step={1}
          value={sliderValue}
          onChange={handleSliderChange}
        />
      </div>
    </div>
  );
}
