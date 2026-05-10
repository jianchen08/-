import { useCallback, useMemo } from 'react';
import type { Era, TechNode, FilterState } from '../types';

interface TimelineSliderProps {
  eras: Era[];
  nodes: TechNode[];
  filter: FilterState;
  onFilterChange: (filter: FilterState) => void;
}

/** 各时代在滑块上的宽度占比权重 */
const ERA_WEIGHTS = [0.08, 0.10, 0.10, 0.10, 0.12, 0.15, 0.35];

/** 时代色带颜色 */
const ERA_COLORS = [
  '#8B4513', // 远古 - 棕色
  '#DAA520', // 古代 - 金色
  '#708090', // 中世纪 - 灰蓝
  '#CD853F', // 文艺复兴 - 秘鲁色
  '#A0522D', // 工业革命 - 赭色
  '#4682B4', // 现代 - 钢蓝
  '#1E90FF', // 信息时代 - 道奇蓝
];

/** 滑块最大值 */
const SLIDER_MAX = 10000;

/** 年份到滑块位置的分段线性映射 */
function yearToPosition(year: number, eras: Era[]): number {
  let position = 0;
  for (let i = 0; i < eras.length && i < ERA_WEIGHTS.length; i++) {
    const era = eras[i]!;
    const [eraStart, eraEnd] = era!.yearRange;
    const segmentWidth = ERA_WEIGHTS[i]! * SLIDER_MAX;
    if (year <= eraStart) break;
    if (year >= eraEnd) {
      position += segmentWidth;
    } else {
      const t = (year - eraStart) / (eraEnd - eraStart);
      position += t * segmentWidth;
      break;
    }
  }
  return Math.round(position);
}

/** 滑块位置到年份的逆映射 */
function positionToYear(position: number, eras: Era[]): number {
  let remaining = position;
  for (let i = 0; i < eras.length && i < ERA_WEIGHTS.length; i++) {
    const segmentWidth = ERA_WEIGHTS[i]! * SLIDER_MAX;
    if (remaining <= segmentWidth) {
      const t = remaining / segmentWidth;
      const era = eras[i]!;
      const [eraStart, eraEnd] = era.yearRange;
      return Math.round(eraStart + t * (eraEnd - eraStart));
    }
    remaining -= segmentWidth;
  }
  const lastEra = eras[eras.length - 1];
  return lastEra ? lastEra.yearRange[1] : 2025;
}

/** 格式化年份显示 */
function formatYear(year: number): string {
  if (year <= -1000000) {
    return `${Math.round(year / -10000)}万年前`;
  }
  if (year <= -10000) {
    return `${Math.round(-year / 1000)}千年前`;
  }
  if (year < 0) {
    return `公元前${Math.abs(year)}年`;
  }
  return `${year}年`;
}

/**
 * 年份制时间轴双滑块组件
 * 使用分段线性缩放，支持年份范围选择
 */
export default function TimelineSlider({ eras, nodes, filter, onFilterChange }: TimelineSliderProps) {
  /** 计算节点数据的年份范围 */
  const { minYear, maxYear } = useMemo(() => {
    if (nodes.length === 0) return { minYear: -3000000, maxYear: 2025 };
    const years = nodes.map((n) => (typeof n.year === 'string' ? parseInt(n.year, 10) : n.year));
    return {
      minYear: Math.min(...years),
      maxYear: Math.max(...years),
    };
  }, [nodes]);

  /** 当前选中年份范围 */
  const [startYear, endYear] = filter.yearRange;

  /** 年份对应的滑块位置 */
  const startPos = yearToPosition(startYear, eras);
  const endPos = yearToPosition(endYear, eras);

  /** 起始滑块变化处理 */
  const handleStartChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const pos = parseInt(e.target.value, 10);
      const newYear = positionToYear(pos, eras);
      if (newYear <= endYear) {
        onFilterChange({ ...filter, yearRange: [newYear, endYear] });
      }
    },
    [filter, eras, endYear, onFilterChange],
  );

  /** 结束滑块变化处理 */
  const handleEndChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const pos = parseInt(e.target.value, 10);
      const newYear = positionToYear(pos, eras);
      if (newYear >= startYear) {
        onFilterChange({ ...filter, yearRange: [startYear, newYear] });
      }
    },
    [filter, eras, startYear, onFilterChange],
  );

  /** 判断是否为全选状态 */
  const isAllSelected = startYear <= minYear && endYear >= maxYear;

  /** 年份标签：在关键位置显示年份 */
  const yearLabels = useMemo(() => {
    const labels: { year: number; position: number }[] = [];
    // 各时代起始年份
    for (const era of eras) {
      labels.push({ year: era.yearRange[0], position: yearToPosition(era.yearRange[0], eras) });
    }
    // 最后一个时代的结束年份
    const lastEra = eras[eras.length - 1];
    if (lastEra) {
      labels.push({ year: lastEra.yearRange[1], position: yearToPosition(lastEra.yearRange[1], eras) });
    }
    return labels;
  }, [eras]);

  return (
    <div className="timeline-slider">
      <div className="timeline-labels">
        <span className="timeline-title">时间轴</span>
        <span className="timeline-hint">
          {isAllSelected
            ? '全部年份'
            : `${formatYear(startYear)} → ${formatYear(endYear)}`}
        </span>
      </div>

      <div className="timeline-bar-container">
        {/* 时代色带 */}
        <div className="timeline-era-band">
          {eras.map((era, idx) => {
            const [eraStart, eraEnd] = era.yearRange;
            const segStart = yearToPosition(eraStart, eras);
            const segEnd = yearToPosition(eraEnd, eras);
            const segWidth = ((segEnd - segStart) / SLIDER_MAX) * 100;

            // 判断该色段是否在选中范围内
            const overlapStart = Math.max(eraStart, startYear);
            const overlapEnd = Math.min(eraEnd, endYear);
            const isDimmed = overlapStart >= overlapEnd;

            return (
              <div
                key={era.id}
                className={`timeline-era-segment ${isDimmed ? 'dimmed' : ''}`}
                style={{
                  width: `${segWidth}%`,
                  backgroundColor: ERA_COLORS[idx] || '#888',
                }}
                title={`${era.name} (${formatYear(eraStart)} ~ ${formatYear(eraEnd)})`}
              >
                <span className="timeline-era-segment-name">{era.name}</span>
              </div>
            );
          })}
        </div>

        {/* 选区高亮条 */}
        <div className="timeline-track">
          <div
            className="timeline-track-fill"
            style={{
              left: `${(startPos / SLIDER_MAX) * 100}%`,
              width: `${((endPos - startPos) / SLIDER_MAX) * 100}%`,
            }}
          />
        </div>

        {/* 双滑块 */}
        <input
          type="range"
          className="timeline-range timeline-range-start"
          min={0}
          max={SLIDER_MAX}
          step={1}
          value={startPos}
          onChange={handleStartChange}
          aria-label="起始年份"
        />
        <input
          type="range"
          className="timeline-range timeline-range-end"
          min={0}
          max={SLIDER_MAX}
          step={1}
          value={endPos}
          onChange={handleEndChange}
          aria-label="结束年份"
        />

        {/* 年份标签行 */}
        <div className="timeline-year-labels">
          {yearLabels.map((label) => (
            <span
              key={label.year}
              className="timeline-year-label"
              style={{
                position: 'absolute',
                left: `${(label.position / SLIDER_MAX) * 100}%`,
                transform: 'translateX(-50%)',
              }}
            >
              {formatYear(label.year)}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
