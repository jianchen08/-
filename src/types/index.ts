/** 科技节点 */
export interface TechNode {
  id: string;
  name: string;
  year: number;
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
