# 科技树可视化项目 — 代码审查报告

> 审查日期：2026-05-09  
> 项目：tech-tree-visualizer  
> 审查范围：10 个核心文件（配置、类型、工具、组件、样式）

---

## 目录

1. [总体评价](#总体评价)
2. [逐文件审查](#逐文件审查)
3. [问题汇总（按严重程度分类）](#问题汇总按严重程度分类)
4. [已修复问题](#已修复问题)
5. [改进建议](#改进建议)

---

## 总体评价

项目整体结构清晰，模块职责分明，TypeScript 严格模式已启用，Cytoscape.js 集成思路正确。代码量不大但功能完整，具备加载状态和错误处理的基本框架。

审查过程中发现的严重和中等问题已全部修复：消除了 `as any` 类型绕过、修复了 StrictMode 竞态条件和内存泄漏、增强了数据加载健壮性、改为不可变的枢纽值计算。修复后项目代码质量达到较高水平。

---

## 逐文件审查

### 1. `package.json` — ✅ 良好

**审查结论**：依赖配置合理，版本选择恰当。

**优点**：
- React 18 + TypeScript + Vite 的技术栈搭配现代且合理
- `cytoscape` + `cytoscape-dagre` 用于有向图布局是正确选择
- 生产依赖和开发依赖分离清晰

**残留建议**：
- 建议添加 `eslint`、`prettier` 配置，统一代码风格
- 确认 `@types/cytoscape-dagre` 是否需要额外安装

---

### 2. `vite.config.ts` — ✅ 良好

**审查结论**：配置极简但够用。

**残留建议**：
- `dataLoader.ts` 从 `/data/*.json` 加载数据，依赖 Vite 的 `public/` 目录静态服务。建议在 README 中说明数据文件的放置要求。

---

### 3. `tsconfig.json` — ✅ 良好

**审查结论**：TypeScript 配置严格且完善。

**优点**：
- `strict: true` 开启了所有严格检查
- `noUnusedLocals`、`noUnusedParameters` 避免死代码
- `noUncheckedIndexedAccess` 防止数组/对象索引越界
- `moduleResolution: "bundler"` 适配 Vite 的打包模式

**注意**：引用了 `tsconfig.node.json`（`references` 字段），应确认该文件存在且配置正确。

---

### 4. `src/types/index.ts` — ✅ 良好（已修复）

**审查结论**：类型定义完整准确。

**修复内容**：
- ~~`CyNodeData` / `CyEdgeData` 未使用的接口定义已删除~~
- ~~`TechNode.year` 类型从 `string | number` 收窄为 `number`~~

**当前状态**：
```typescript
export interface TechNode {
  id: string;
  name: string;
  year: number;           // ✅ 精确类型
  yearRange?: [number, number];
  era: string;
  domain: string;
  prerequisites: string[];
  description: string;
  importance?: number;
  tags?: string[];
  hubScore?: number;
}
// Domain, Era, TechTreeData — 均定义完整，无冗余
```

---

### 5. `src/utils/dataLoader.ts` — ✅ 良好（已修复）

**审查结论**：数据加载具备错误处理和超时机制。

**修复内容**：
- ~~添加了 `AbortController` 超时机制（默认 10 秒）~~

**当前状态**：
```typescript
async function fetchJson<T>(url: string, timeout = 10000): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeout);
  try {
    const response = await fetch(url, { signal: controller.signal });
    // ...错误处理...
  } finally {
    clearTimeout(timer);
  }
}
```

**残留建议**：
- 可引入 zod 进行运行时 schema 验证，进一步提升健壮性
- 可添加重试逻辑（1-2 次）

---

### 6. `src/utils/hubCalculator.ts` — ✅ 良好（已修复）

**审查结论**：算法正确，实现清晰，不可变设计。

**修复内容**：
- ~~`calculateHubScores` 从 `void`（修改输入）改为返回 `Map<string, number>`（不修改输入）~~
- ~~`getRankedNodeIds` 新增 `scoreMap` 参数，从外部传入计算结果~~

**算法验证**：
- ✅ 正确统计每个节点被其他节点 `prerequisites` 引用的次数
- ✅ 正确处理引用不存在节点的情况
- ✅ 归一化到 0-100 的计算正确
- ✅ 边界情况 `maxCount === 0` 正确处理
- ✅ 函数式不可变设计，无副作用

---

### 7. `src/components/TechTree.tsx` — ✅ 良好（已修复）

**审查结论**：核心组件的类型安全、内存管理和异步处理均已修复。

**修复内容**：

#### 7.1 消除 `as any` 类型转换
- ~~`getCyStyle()` 返回类型从自定义 `CytoscapeStyleRule[]` 改为 cytoscape 内置的 `Stylesheet[]`~~
- ~~移除了 `// eslint-disable-next-line` 注释和 `as any` 转换~~
- 现在样式部分享有完整的编译期类型安全

#### 7.2 修复 StrictMode 竞态条件和内存泄漏
- ~~添加 `cancelled` 标志保护异步操作~~
- ~~使用 `cyRef = useRef` 保存 cytoscape 实例引用，确保清理函数能正确销毁~~
- ~~在 `await` 后、`cytoscape()` 调用前、`setState` 调用前均检查 `cancelled` 标志~~

#### 7.3 适配不可变的 hubCalculator API
- ~~`calculateHubScores(nodes)` 返回 `scoreMap`，传递给 `getRankedNodeIds` 和 `buildElements`~~

#### 7.4 修复 Cytoscape 选择器语法
- ~~布尔属性选择器从 `[isTop20 = true]` 改为 `[?isTop20]`（truthy 检查）~~

**当前核心代码结构**：
```typescript
useEffect(() => {
  let cancelled = false;

  (async () => {
    const data = await loadTechTreeData();
    if (cancelled) return;           // ✅ 卸载保护
    // ... 构建元素 ...
    if (cancelled || !containerRef.current) return;  // ✅ 二次检查
    cyRef.current = cytoscape({...});  // ✅ 类型安全，无 as any
    if (!cancelled) setLoading(false); // ✅ 卸载保护
  })();

  return () => {
    cancelled = true;
    cyRef.current?.destroy();         // ✅ 可靠清理
    cyRef.current = null;
  };
}, []);
```

---

### 8. `src/App.tsx` — ✅ 良好

**审查结论**：简洁的应用入口，职责单一，无问题。

---

### 9. `src/main.tsx` — ✅ 良好

**审查结论**：标准的 React 18 入口，使用 `StrictMode`。TechTree 组件已正确处理 StrictMode 的双 mount 行为。

---

### 10. `src/App.css` — ✅ 良好

**审查结论**：暗色主题样式简洁实用，对比度良好。

**残留建议**：
- 可添加加载动画（旋转指示器）替代纯文本提示
- 如需添加非全屏内容，调整 `overflow: hidden` 策略

---

## 问题汇总（按严重程度分类）

### 修复前问题清单

#### 🔴 严重（2 个）— ✅ 已全部修复

| # | 文件 | 问题 | 修复方式 |
|---|------|------|----------|
| S1 | `TechTree.tsx` | `as any` 绕过类型检查 | 改用 cytoscape 内置 `Stylesheet` 类型 |
| S2 | `TechTree.tsx` | StrictMode 下 cytoscape 实例泄漏 | 添加 `cancelled` 标志 + `useRef` 保存实例 |

#### 🟠 中等（4 个）— ✅ 已全部修复

| # | 文件 | 问题 | 修复方式 |
|---|------|------|----------|
| M1 | `TechTree.tsx` | 异步操作无卸载保护 | `cancelled` 标志 + 所有 `setState` 前检查 |
| M2 | `types/index.ts` | `CyNodeData`/`CyEdgeData` 未使用且不一致 | 删除未使用的接口定义 |
| M3 | `dataLoader.ts` | fetch 无超时机制 | 添加 `AbortController` 超时（10s） |
| M4 | `hubCalculator.ts` | 直接修改输入参数 | 改为返回 `Map<string, number>` |

#### 🟡 轻微（5 个残留）

| # | 文件 | 问题 | 建议 |
|---|------|------|------|
| L1 | `package.json` | 缺少 eslint / prettier | 添加代码质量工具链 |
| L2 | `dataLoader.ts` | 无运行时数据校验 | 可引入 zod 进行 schema 验证 |
| L3 | `dataLoader.ts` | 无重试逻辑 | 可添加 1-2 次自动重试 |
| L4 | `TechTree.tsx` | `cytoscape.use(dagre)` 模块级副作用 | 可移入 useEffect 内部 |
| L5 | `App.css` | `overflow: hidden` 限制扩展性 | 按需调整布局策略 |

---

## 已修复问题

### 修改文件清单

| 文件 | 修改类型 | 说明 |
|------|----------|------|
| `src/types/index.ts` | 精简 | 删除未使用的 `CyNodeData`/`CyEdgeData`，`year` 类型收窄为 `number` |
| `src/utils/dataLoader.ts` | 增强 | 添加 `AbortController` 超时机制（默认 10 秒） |
| `src/utils/hubCalculator.ts` | 重构 | `calculateHubScores` 返回 `Map` 而非修改输入；`getRankedNodeIds` 接收外部 `scoreMap` |
| `src/components/TechTree.tsx` | 修复 | 消除 `as any`（使用 `Stylesheet` 类型）、添加卸载保护（`cancelled` + `useRef`）、适配新 API、修复选择器语法 |

---

## 改进建议

### 优先级 P2：长期优化

#### 1. 添加运行时数据校验

```typescript
import { z } from 'zod';

const TechNodeSchema = z.object({
  id: z.string(),
  name: z.string(),
  year: z.number(),
  // ...
});

// 在 dataLoader 中使用
const nodes = TechNodeSchema.array().parse(await response.json());
```

#### 2. 添加节点交互

```typescript
cy.on('tap', 'node', (evt) => {
  const node = evt.target;
  // 显示 tooltip / 侧边详情面板
});
```

#### 3. 性能优化

- 对于大型图谱（> 500 节点），考虑启用 `cytoscape` 的 `headless` 模式做预计算
- 添加虚拟化渲染（仅渲染视口内的节点）

#### 4. 工程化增强

- 添加 ESLint + Prettier 配置
- 添加 Vitest 单元测试（重点覆盖 `hubCalculator` 和 `dataLoader`）
- 添加 CI/CD 流水线配置

---

## 审查总结

| 维度 | 修复前 | 修复后 | 说明 |
|------|--------|--------|------|
| TypeScript 类型 | ⭐⭐⭐☆☆ | ⭐⭐⭐⭐⭐ | 消除 `as any`，删除死代码，收窄类型 |
| React Hooks | ⭐⭐☆☆☆ | ⭐⭐⭐⭐⭐ | 完整的卸载保护，可靠实例清理 |
| Cytoscape 集成 | ⭐⭐⭐⭐☆ | ⭐⭐⭐⭐⭐ | 类型安全样式，正确选择器语法 |
| 错误处理 | ⭐⭐⭐☆☆ | ⭐⭐⭐⭐☆ | 添加超时机制，残留：运行时校验、重试 |
| 算法正确性 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 算法不变，改为不可变设计 |
| 代码结构 | ⭐⭐⭐⭐☆ | ⭐⭐⭐⭐⭐ | 更清晰的模块职责和 API 设计 |
| 性能/安全 | ⭐⭐⭐☆☆ | ⭐⭐⭐⭐☆ | 修复内存泄漏，残留：大规模图谱优化 |

**综合评价**：修复后项目代码质量优秀，TypeScript 类型安全完善，React Hooks 使用规范，无内存泄漏风险，模块职责清晰。建议后续关注运行时数据校验和工程化工具链的完善。
