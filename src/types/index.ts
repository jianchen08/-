/** 科技节点 */
export interface TechNode {
  id: string;
  name: string;
  year: number | string;
  yearRange?: [number, number];
  era: string;
  domain: string;
  prerequisites: string[];
  description: string;
  importance?: number;
  tags?: string[];
  /** 由 hubCalculator 计算填入 */
  hubScore?: number;
}

/** 时代 */
export interface Era {
  id: string;
  name: string;
  nameEn: string;
  yearRange: [number, number];
  description: string;
}

/** 领域 */
export interface Domain {
  id: string;
  name: string;
  nameEn: string;
  icon: string;
  description: string;
  color: string;
}

/** 完整数据集 */
export interface TechTreeData {
  nodes: TechNode[];
  domains: Domain[];
  eras: Era[];
}

/** 布局类型 */
export type LayoutType = 'dagre' | 'force' | 'timeline';

/** 筛选条件 */
export interface FilterState {
  selectedEras: string[];
  selectedDomains: string[];
  hubThreshold: number;
  /** 年份范围：[起始年份, 结束年份] */
  yearRange: [number, number];
}

/** 选中节点信息（传递给 NodeDetail） */
export interface SelectedNode {
  id: string;
  name: string;
  description: string;
  year: number | string;
  era: string;
  domain: string;
  tags: string[];
  hubScore: number;
  prerequisites: string[];
}
