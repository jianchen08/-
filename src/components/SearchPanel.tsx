import { useState, useCallback } from 'react';

interface SearchPanelProps {
  searchText: string;
  onSearchChange: (text: string) => void;
}

export default function SearchPanel({ searchText, onSearchChange }: SearchPanelProps) {
  const [localText, setLocalText] = useState(searchText);

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const val = e.target.value;
      setLocalText(val);
      onSearchChange(val);
    },
    [onSearchChange],
  );

  const handleClear = useCallback(() => {
    setLocalText('');
    onSearchChange('');
  }, [onSearchChange]);

  return (
    <div className="search-panel">
      <div className="search-input-wrap">
        <span className="search-icon">🔍</span>
        <input
          type="text"
          className="search-input"
          placeholder="搜索节点名称、描述、标签..."
          value={localText}
          onChange={handleChange}
        />
        {localText && (
          <button className="search-clear" onClick={handleClear} title="清除">
            ✕
          </button>
        )}
      </div>
    </div>
  );
}
