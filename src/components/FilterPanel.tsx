import type { Era, Domain, FilterState } from '../types';

interface FilterPanelProps {
  eras: Era[];
  domains: Domain[];
  filter: FilterState;
  onFilterChange: (filter: FilterState) => void;
}

export default function FilterPanel({
  eras,
  domains,
  filter,
  onFilterChange,
}: FilterPanelProps) {
  const toggleEra = (eraId: string) => {
    const next = filter.selectedEras.includes(eraId)
      ? filter.selectedEras.filter((e) => e !== eraId)
      : [...filter.selectedEras, eraId];
    onFilterChange({ ...filter, selectedEras: next });
  };

  const toggleDomain = (domainId: string) => {
    const next = filter.selectedDomains.includes(domainId)
      ? filter.selectedDomains.filter((d) => d !== domainId)
      : [...filter.selectedDomains, domainId];
    onFilterChange({ ...filter, selectedDomains: next });
  };

  const selectAllEras = () => {
    onFilterChange({ ...filter, selectedEras: eras.map((e) => e.id) });
  };

  const clearAllEras = () => {
    onFilterChange({ ...filter, selectedEras: [] });
  };

  const selectAllDomains = () => {
    onFilterChange({ ...filter, selectedDomains: domains.map((d) => d.id) });
  };

  const clearAllDomains = () => {
    onFilterChange({ ...filter, selectedDomains: [] });
  };

  const handleHubThreshold = (e: React.ChangeEvent<HTMLInputElement>) => {
    onFilterChange({ ...filter, hubThreshold: parseFloat(e.target.value) });
  };

  return (
    <div className="filter-panel">
      {/* 时代筛选 */}
      <div className="filter-section">
        <div className="filter-header">
          <span className="filter-title">⏳ 时代</span>
          <div className="filter-actions">
            <button className="filter-btn" onClick={selectAllEras}>全选</button>
            <button className="filter-btn" onClick={clearAllEras}>清空</button>
          </div>
        </div>
        <div className="filter-checkboxes">
          {eras.map((era) => (
            <label key={era.id} className="filter-checkbox-label">
              <input
                type="checkbox"
                checked={filter.selectedEras.includes(era.id)}
                onChange={() => toggleEra(era.id)}
              />
              <span className="filter-checkbox-text">{era.name}</span>
            </label>
          ))}
        </div>
      </div>

      {/* 领域筛选 */}
      <div className="filter-section">
        <div className="filter-header">
          <span className="filter-title">🔬 领域</span>
          <div className="filter-actions">
            <button className="filter-btn" onClick={selectAllDomains}>全选</button>
            <button className="filter-btn" onClick={clearAllDomains}>清空</button>
          </div>
        </div>
        <div className="filter-checkboxes">
          {domains.map((domain) => (
            <label key={domain.id} className="filter-checkbox-label">
              <input
                type="checkbox"
                checked={filter.selectedDomains.includes(domain.id)}
                onChange={() => toggleDomain(domain.id)}
              />
              <span
                className="filter-color-dot"
                style={{ backgroundColor: domain.color }}
              />
              <span className="filter-checkbox-text">{domain.name}</span>
            </label>
          ))}
        </div>
      </div>

      {/* 枢纽值阈值 */}
      <div className="filter-section">
        <div className="filter-header">
          <span className="filter-title">🔗 枢纽值阈值</span>
          <span className="filter-value">{filter.hubThreshold}</span>
        </div>
        <input
          type="range"
          min="0"
          max="100"
          step="5"
          value={filter.hubThreshold}
          onChange={handleHubThreshold}
          className="filter-slider"
        />
        <div className="filter-slider-labels">
          <span>0</span>
          <span>100</span>
        </div>
      </div>
    </div>
  );
}
