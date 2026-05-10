# 科技树可视化项目 — 功能验证报告

**验证日期**: 2026-05-09  
**项目**: tech-tree-visualizer v1.0.0  
**验证人**: 自动化功能验证

---

## 一、验证总览

| 功能模块 | 验证结果 | 备注 |
|---------|---------|------|
| 项目可构建性 | ✅ 通过 | npm install & build 均成功 |
| 核心可视化组件 | ✅ 通过 | 有轻微偏差，见详细分析 |
| 数据加载 | ✅ 通过 | 完整实现 |
| 枢纽值计算 | ✅ 通过 | 逻辑正确 |
| TypeScript 类型定义 | ✅ 通过 | 类型完整 |
| 应用入口 | ✅ 通过 | 正确挂载 |

**整体验证结论**: ✅ **通过** — 所有核心功能点均已正确实现，项目可正常构建和运行。发现 1 个轻微偏差（hubScore≥60 枢纽节点光晕效果使用边框近似实现），不影响功能可用性。

---

## 二、逐项详细验证

### 1. 项目可构建性 — ✅ 通过

| 验证项 | 结果 | 说明 |
|-------|------|------|
| `npm install` | ✅ 成功 | 0 vulnerabilities，依赖安装正常 |
| `npm run build` | ✅ 成功 | tsc + vite build，4.79s 完成构建 |
| `dist/` 目录存在 | ✅ 通过 | 包含 index.html、assets/、data/ |
| 数据文件复制到 dist | ✅ 通过 | full_data.json (279.1KB)、domains.json (3.6KB)、eras.json (3.7KB) 均存在于 dist/data/ |

**构建产物**:
- `dist/index.html` (0.42 KB)
- `dist/assets/index-si_dMFfm.css` (0.53 KB)
- `dist/assets/index-DRqASOov.js` (687.70 KB)

> ⚠️ **提示**: JS chunk 超过 500KB，建议后续考虑代码分割优化（非功能性问题）。

---

### 2. 核心可视化组件 (src/components/TechTree.tsx) — ✅ 通过

#### 2.1 使用 Cytoscape.js 渲染科技树 — ✅ 通过

- **代码证据** (第2行): `import cytoscape from 'cytoscape';`
- **实例创建** (第79-87行): 使用 `cytoscape({ container, elements, style, layout })` 创建实例
- **依赖声明** (package.json): `"cytoscape": "^3.31.0"`

#### 2.2 使用 dagre 布局，方向从左到右 — ✅ 通过

- **代码证据** (第3行): `import dagre from 'cytoscape-dagre';`
- **注册插件** (第8行): `cytoscape.use(dagre);`
- **布局配置** (第70-77行):
  ```typescript
  {
    name: 'dagre',
    rankDir: 'LR',       // 左到右方向 ✅
    spacingFactor: 1.2,
    nodeSep: 30,
    rankSep: 80,
    animate: false,
  }
  ```

#### 2.3 节点大小根据枢纽值映射到 20-50px — ✅ 通过

- **代码证据** (第20-23行):
  ```typescript
  function hubToSize(hubScore: number): number {
    return 20 + (hubScore / 100) * 30;  // hubScore 0→20px, 100→50px ✅
  }
  ```
- **样式应用** (第181-182行): `width: 'data(nodeSize)', height: 'data(nodeSize)'`

#### 2.4 节点颜色根据枢纽值调整亮度 — ✅ 通过

- **代码证据** (第25-35行): `adjustBrightness()` 函数
  - factor 范围: `0.4 + (hubScore / 100) * 0.6` → 0.4~1.0
  - 对 hex 颜色 RGB 各通道乘以 factor，实现亮度调节
- **调用位置** (第136行): `const displayColor = adjustBrightness(baseColor, hubScore);`
- **样式应用** (第183行): `'background-color': 'data(displayColor)'`

#### 2.5 hubScore≥60 枢纽节点有光晕效果 — ⚠️ 轻微偏差

- **代码证据** (第194-201行，`isTop20` 为布尔属性，当 hubScore≥60 时为 true):
  ```typescript
  {
    selector: 'node[?isTop20]',
    style: {
      'border-width': 3,
      'border-color': '#FFD700',   // 金色边框
      'border-opacity': 0.8,
    },
  }
  ```
- **分析**: 使用 3px 金色边框（#FFD700）模拟光晕效果，而非真正的发光/阴影效果。在 Cytoscape.js 中实现真正的 glow 效果需要额外的自定义渲染。当前边框方案在视觉上能区分 hubScore≥60 枢纽节点，是合理的工程折中方案。

#### 2.6 hubScore≥80 枢纽节点有星标标记 — ✅ 通过

- **代码证据** (第108行): `name: hubScore >= 80 ? \`⭐ ${node.name}\` : node.name,`（枢纽值≥80时添加⭐星标前缀）
- **枢纽值≥80 边框增强** (第252-258行): 4px 橙红色边框（#FF4500），opacity 1.0，比枢纽值≥60更醒目

#### 2.7 支持鼠标滚轮缩放和拖拽平移 — ✅ 通过

- **Cytoscape.js 内置支持**: 默认启用鼠标滚轮缩放和拖拽平移
- **缩放配置** (第84-86行):
  ```typescript
  minZoom: 0.1,         // 最小缩放 10%
  maxZoom: 3,           // 最大缩放 300%
  wheelSensitivity: 0.3, // 滚轮灵敏度
  ```

---

### 3. 数据加载 (src/utils/dataLoader.ts) — ✅ 通过

#### 3.1 使用 fetch 加载 /data/full_data.json — ✅ 通过

- **代码证据** (第19行): `fetchJson<TechNode[]>('/data/full_data.json')`
- **数据文件存在**: `public/data/full_data.json` (279.1KB, 11927行)

#### 3.2 使用 fetch 加载 /data/domains.json — ✅ 通过

- **代码证据** (第20行): `fetchJson<Domain[]>('/data/domains.json')`
- **数据文件存在**: `public/data/domains.json` (3.6KB, 98行)

#### 3.3 使用 fetch 加载 /data/eras.json — ✅ 通过

- **代码证据** (第21行): `fetchJson<Era[]>('/data/eras.json')`
- **数据文件存在**: `public/data/eras.json` (3.7KB, 51行)

#### 3.4 错误处理 — ✅ 通过

- **超时控制** (第4-5行): 使用 `AbortController` + `setTimeout(15000ms)` 实现请求超时
- **HTTP 状态检查** (第8-10行): `if (!response.ok)` 抛出含状态信息的 Error
- **组件级错误处理** (TechTree.tsx 第92-97行): try-catch 捕获异常并展示错误信息
- **组件卸载保护** (TechTree.tsx 第52-53行, 第67-68行): 使用 `cancelled` 标记防止卸载后更新状态

---

### 4. 枢纽值计算 (src/utils/hubCalculator.ts) — ✅ 通过

#### 4.1 从 prerequisites 反向统计每个节点被引用次数 — ✅ 通过

- **代码证据** (第10-22行):
  ```typescript
  // 初始化所有节点引用计数为 0
  const refCount = new Map<string, number>();
  for (const node of nodes) {
    refCount.set(node.id, 0);
  }
  // 遍历每个节点的 prerequisites，反向计数
  for (const node of nodes) {
    for (const prereq of node.prerequisites) {
      const count = refCount.get(prereq);
      if (count !== undefined) {
        refCount.set(prereq, count + 1);
      }
    }
  }
  ```
- **逻辑正确**: 遍历所有节点的 prerequisites 数组，对被引用的节点累加计数，实现了"被引用次数"的统计。

#### 4.2 归一化到 0-100 范围 — ✅ 通过

- **代码证据** (第24-37行):
  ```typescript
  // 找最大引用次数
  let maxCount = 0;
  for (const count of refCount.values()) {
    if (count > maxCount) maxCount = count;
  }
  // 归一化: (count / maxCount) * 100，四舍五入
  scoreMap.set(node.id, maxCount > 0 ? Math.round((count / maxCount) * 100) : 0);
  ```
- **边界处理**: maxCount 为 0 时（无引用关系），所有节点 hubScore 为 0 ✅

#### 4.3 将 hubScore 写入节点数据 — ✅ 通过

- **计算结果传递**: `calculateHubScores()` 返回 `Map<string, number>`
- **写入 cytoscape 节点数据** (TechTree.tsx 第132行): `const hubScore = scoreMap.get(node.id) ?? 0;`
- **存入节点数据** (TechTree.tsx 第146行): `hubScore` 作为 data 字段写入 cytoscape elements
- **注意**: hubScore 未直接写回原始 TechNode 数组（保持了不可变性设计），而是通过 Map 传递并在构建可视化元素时写入 cytoscape 节点数据。

---

### 5. TypeScript 类型定义 (src/types/index.ts) — ✅ 通过

#### 5.1 TechNode 类型 — ✅ 通过

```typescript
export interface TechNode {
  id: string;              // 唯一标识 ✅
  name: string;            // 名称 ✅
  year: number;            // 年份 ✅
  yearRange?: [number, number];  // 年份范围（可选）✅
  era: string;             // 时代 ✅
  domain: string;          // 领域 ✅
  prerequisites: string[]; // 前置技术 ✅
  description: string;     // 描述 ✅
  importance?: number;     // 重要性（可选）✅
  tags?: string[];         // 标签（可选）✅
  hubScore?: number;       // 枢纽值（由 hubCalculator 计算填入）✅
}
```

#### 5.2 Era 类型 — ✅ 通过

```typescript
export interface Era {
  id: string;                    // 唯一标识 ✅
  name: string;                  // 中文名称 ✅
  nameEn: string;                // 英文名称 ✅
  yearRange: [number, number];   // 年份范围 ✅
  description: string;           // 描述 ✅
}
```

#### 5.3 Domain 类型 — ✅ 通过

```typescript
export interface Domain {
  id: string;          // 唯一标识 ✅
  name: string;        // 中文名称 ✅
  nameEn: string;      // 英文名称 ✅
  icon: string;        // 图标 ✅
  description: string; // 描述 ✅
  color: string;       // 颜色 ✅
}
```

#### 5.4 额外类型 — ✅ 通过

```typescript
export interface TechTreeData {
  nodes: TechNode[];
  domains: Domain[];
  eras: Era[];
}
```

---

### 6. 应用入口 — ✅ 通过

#### 6.1 src/App.tsx 加载 TechTree 组件 — ✅ 通过

```typescript
import TechTree from './components/TechTree';
import './App.css';

export default function App() {
  return <TechTree />;
}
```
- 简洁明了，正确导入和渲染 TechTree 组件。

#### 6.2 src/main.tsx 正确挂载 React 应用 — ✅ 通过

```typescript
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';

const rootElement = document.getElementById('root');
if (!rootElement) {
  throw new Error('Root element not found...');
}
createRoot(rootElement).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
```
- 使用 React 18 `createRoot` API ✅
- 包含 StrictMode 包裹 ✅
- 有 root 元素不存在的容错检查 ✅
- 入口文件路径在 `index.html` 中正确引用: `<script type="module" src="/src/main.tsx">` ✅

#### 6.3 src/App.css 基础样式（全屏显示）— ✅ 通过

- **全屏设置**:
  ```css
  html, body, #root {
    width: 100%;
    height: 100%;
    overflow: hidden;
  }
  ```
- **科技树容器**: `.tech-tree-wrapper` 和 `.tech-tree-container` 均为 `width: 100%; height: 100%` ✅
- **深色主题**: `background-color: #1a1a2e` ✅
- **加载/错误状态样式**: 居中显示 ✅

---

## 三、发现的问题列表

| # | 严重程度 | 模块 | 问题描述 | 建议 |
|---|---------|------|---------|------|
| 1 | ⚠️ 轻微 | TechTree.tsx | hubScore≥60 光晕效果使用 border 边框（3px #FFD700）近似实现，非真正的发光效果 | 可考虑使用 Cytoscape.js 的 `underlay-*` 属性或多层节点模拟光晕 |
| 2 | 💡 建议 | 构建产物 | JS chunk (687KB) 超过 500KB 建议阈值 | 可使用动态 import() 或 manualChunks 进行代码分割 |
| 3 | 💡 建议 | hubCalculator.ts | hubScore 通过独立 Map 传递，未回写到 TechNode 数组 | 当前不可变性设计更优，仅为文档说明差异 |

> **无阻塞性问题、无功能性错误、无类型错误。**

---

## 四、验证结论

### ✅ 项目功能验证通过

科技树可视化项目所有核心功能点均已正确实现：

1. **构建系统完整**: npm install → npm run build → dist 产出全流程通过
2. **可视化核心正确**: Cytoscape.js + dagre (LR方向) 渲染引擎配置正确
3. **数据管道完整**: fetch 加载三个 JSON 数据源，含超时和 HTTP 错误处理
4. **枢纽值算法正确**: prerequisites 反向统计 → 归一化 0-100 → 写入节点数据
5. **视觉效果齐全**: 节点大小映射(20-50px)、亮度调节、枢纽值≥60边框高亮、枢纽值≥80星标+边框
6. **交互功能就绪**: 缩放(0.1x~3x) + 平移 + 滚轮灵敏度配置
7. **类型系统完善**: TechNode、Era、Domain、TechTreeData 四个接口定义完整
8. **应用入口正确**: React 18 + StrictMode + createRoot 标准挂载方式
