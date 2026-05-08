/**
 * 人类科技树全景图 - 类型定义
 */

/** 技术时代划分 */
export enum Era {
  /** 史前时代（-3000年以前） */
  Prehistoric = 'prehistoric',
  /** 古代（-3000 ~ 500年） */
  Ancient = 'ancient',
  /** 中世纪（500 ~ 1500年） */
  Medieval = 'medieval',
  /** 文艺复兴 / 近代早期（1500 ~ 1750年） */
  Renaissance = 'renaissance',
  /** 工业革命（1750 ~ 1900年） */
  Industrial = 'industrial',
  /** 现代（1900 ~ 2000年） */
  Modern = 'modern',
  /** 信息时代（2000年 ~ 至今） */
  Information = 'information',
  /** 未来展望 */
  Future = 'future',
}

/** 时代显示信息 */
export interface EraInfo {
  id: Era;
  name: string;
  nameEn: string;
  startYear: number;
  endYear: number;
  description: string;
  color: string;
}

/** 技术领域 */
export enum Domain {
  /** 数学与逻辑 */
  Mathematics = 'mathematics',
  /** 物理学 */
  Physics = 'physics',
  /** 化学 */
  Chemistry = 'chemistry',
  /** 生物学 */
  Biology = 'biology',
  /** 医学 */
  Medicine = 'medicine',
  /** 天文学 */
  Astronomy = 'astronomy',
  /** 地球科学 */
  EarthScience = 'earth-science',
  /** 材料科学 */
  Materials = 'materials',
  /** 能源 */
  Energy = 'energy',
  /** 信息技术 */
  InformationTechnology = 'information-technology',
  /** 电子与电气 */
  Electronics = 'electronics',
  /** 机械工程 */
  MechanicalEngineering = 'mechanical-engineering',
  /** 土木与建筑 */
  CivilEngineering = 'civil-engineering',
  /** 航空航天 */
  Aerospace = 'aerospace',
  /** 交通运输 */
  Transportation = 'transportation',
  /** 通信 */
  Communication = 'communication',
  /** 农业与食品 */
  Agriculture = 'agriculture',
  /** 环境科学 */
  EnvironmentalScience = 'environmental-science',
  /** 纳米技术 */
  Nanotechnology = 'nanotechnology',
  /** 生物技术 */
  Biotechnology = 'biotechnology',
  /** 人工智能 */
  ArtificialIntelligence = 'artificial-intelligence',
}

/** 技术领域显示信息 */
export interface DomainInfo {
  id: Domain;
  name: string;
  nameEn: string;
  icon?: string;
  color: string;
  description: string;
}

/** 技术节点重要程度 */
export enum Importance {
  /** 关键突破 - 改变人类历史进程的重大发现 */
  Breakthrough = 'breakthrough',
  /** 重要 - 重要技术进步 */
  Major = 'major',
  /** 一般 - 常规技术发展 */
  Normal = 'normal',
  /** 次要 - 辅助性或渐进性改进 */
  Minor = 'minor',
}

/** 技术节点状态 */
export enum TechStatus {
  /** 已确立 - 被广泛验证和应用 */
  Established = 'established',
  /** 发展中 - 正在快速发展 */
  Developing = 'developing',
  /** 理论阶段 - 仅有理论框架 */
  Theoretical = 'theoretical',
  /** 已淘汰 - 被更先进技术取代 */
  Obsolete = 'obsolete',
}

/** 技术节点（核心数据结构） */
export interface TechNode {
  /** 唯一标识 */
  id: string;
  /** 技术名称 */
  name: string;
  /** 英文名称 */
  nameEn: string;
  /** 简要描述 */
  description: string;
  /** 详细说明 */
  detail?: string;
  /** 所属时代 */
  era: Era;
  /** 所属领域 */
  domain: Domain;
  /** 前置技术（依赖） */
  prerequisites: string[];
  /** 后续技术（衍生） */
  successors: string[];
  /** 相关技术（关联） */
  relatedTo: string[];
  /** 重要程度 */
  importance: Importance;
  /** 技术状态 */
  status: TechStatus;
  /** 出现年份（负数表示公元前） */
  year?: number;
  /** 关键人物 */
  keyFigures?: string[];
  /** 参考链接 */
  references?: string[];
  /** 标签 */
  tags?: string[];
  /** 自定义元数据 */
  metadata?: Record<string, unknown>;
}

/** Cytoscape 节点数据 */
export interface CytoscapeNodeData {
  id: string;
  label: string;
  era: Era;
  domain: Domain;
  importance: Importance;
  status: TechStatus;
  year?: number;
}

/** Cytoscape 边数据 */
export interface CytoscapeEdgeData {
  id: string;
  source: string;
  target: string;
  type: 'prerequisite' | 'related';
}

/** Cytoscape 元素定义 */
export interface CytoscapeElements {
  nodes: Array<{
    data: CytoscapeNodeData;
    position?: { x: number; y: number };
  }>;
  edges: Array<{
    data: CytoscapeEdgeData;
  }>;
}

/** 布局类型 */
export type LayoutType = 'dagre' | 'cose-bilkent' | 'breadthfirst' | 'circle' | 'concentric' | 'grid';

/** 视图筛选条件 */
export interface ViewFilter {
  eras: Era[];
  domains: Domain[];
  importanceLevels: Importance[];
  searchQuery: string;
  showObsolete: boolean;
}

/** 视图配置 */
export interface ViewConfig {
  layout: LayoutType;
  filter: ViewFilter;
  showLabels: boolean;
  showMinimap: boolean;
  animate: boolean;
  theme: 'light' | 'dark';
}

/** 导出选项 */
export interface ExportOptions {
  format: 'png' | 'jpg' | 'pdf' | 'svg';
  width?: number;
  height?: number;
  quality?: number;
  background?: string;
  filename?: string;
}

/** 数据分类定义文件 */
export interface CategoryDefinition {
  version: string;
  eras: EraInfo[];
  domains: DomainInfo[];
}
