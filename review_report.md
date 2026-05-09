# 代码审查报告：PDF 导出功能 + 构建配置 + README

## 1. 概述

- **审查范围**：`src/utils/pdfExporter.ts`、`src/components/Toolbar.tsx`（新增导出部分）、`src/App.tsx`（导出集成）、`vite.config.ts`、`README.md`
- **代码类型**：前端（React + TypeScript）
- **审查维度**：Google 八大维度 + 前端专项规则
- **审查日期**：2026-05-09
- **变更概述**：新增 PDF 导出功能（视口导出 + 全景导出），修改 Toolbar 组件集成导出按钮，更新 vite.config.ts 支持离线部署，更新 README 文档

---

## 2. 静态扫描指标

| 检查项 | 工具 | 结果 | 状态 |
|--------|------|------|------|
| TypeScript 类型检查 | `tsc --noEmit --strict` | 0 错误 / 0 警告 | ✅ 通过 |
| 未使用变量/参数检查 | `tsc --noUnusedLocals --noUnusedParameters` | 0 错误 / 0 警告 | ✅ 通过 |
| ESLint 代码规范 | ESLint | ⚠️ 项目未配置 ESLint | ⚠️ 缺失 |
| 生产构建 | `vite build` | 构建成功，1 个 chunk 大小警告 | ⚠️ 部分通过 |
| 单元测试 | — | 项目无测试文件 | ❌ 缺失 |

### 构建产物分析

| 产物 | 大小 | Gzip | 备注 |
|------|------|------|------|
| `index-DmNtU9Xs.js` | 1,378 KB | 427 KB | ⚠️ 超过 500KB 警告阈值 |
| `index.es-BEthgigX.js` | 160 KB | 54 KB | Cytoscape 核心库 |
| `purify.es-BaNf_EpD.js` | 24 KB | 9 KB | DOMPurify |
| `index-CILThu0N.css` | 8 KB | 2 KB | 样式 |
| `index.html` | 0.4 KB | 0.3 KB | ✅ 使用相对路径 |

### 量化指标汇总

| 指标 | 值 | 评级 |
|------|------|------|
| TypeScript 严格模式错误数 | 0 | 良好 |
| 类型注解覆盖度 | 100%（公共接口） | 良好 |
| 主 JS Chunk 大小 | 1,378 KB | 差 |
| 代码规范工具配置 | 未配置 | 差 |
| 测试覆盖率 | 0% | 差 |

---

## 3. 维度审查发现的问题

### 3.1 Design（设计）

**架构合理性** ✅ 良好

`pdfExporter.ts` 作为独立 utils 模块，职责单一，只负责 PDF 生成逻辑。Toolbar 组件只负责 UI 展示和用户交互，App.tsx 负责状态管理和胶水代码。三层分离清晰。

**接口设计** ✅ 良好

公共接口仅暴露 `exportViewport` 和 `exportFullView` 两个函数，参数简洁（element + fileName），内部函数 `sliceCanvas`、`addImageFitToPage`、`addImageMultiPage` 均为模块私有。

### 3.2 Functionality（功能）

#### 问题 F-1：`sliceCanvas` 中 `getContext('2d')` 返回 null 时静默失败

- **文件**：`src/utils/pdfExporter.ts` 第 54-57 行
- **级别**：Must Fix
- **描述**：当 `getContext('2d')` 返回 `null`（如 canvas 已被其他上下文占用）时，函数返回一个空白 canvas，不会抛出错误。这会导致 PDF 中出现空白页，用户无法得知原因。
- **修复建议**：

```typescript
function sliceCanvas(...): HTMLCanvasElement {
  const sliced = document.createElement('canvas');
  sliced.width = width;
  sliced.height = height;
  const ctx = sliced.getContext('2d');
  if (!ctx) {
    throw new Error('无法创建 Canvas 2D 上下文，PDF 分页切片失败');
  }
  ctx.drawImage(source, startX, startY, width, height, 0, 0, width, height);
  return sliced;
}
```

#### 问题 F-2：导出失败时用户无反馈

- **文件**：`src/App.tsx` 第 104-105 行、第 118-119 行
- **级别**：Should Fix
- **描述**：`handleExportViewport` 和 `handleExportFullView` 的 catch 块仅使用 `console.error` 输出错误，用户在界面上看不到任何提示。导出失败后，按钮恢复可点击状态，但用户不知道发生了什么。
- **修复建议**：添加一个错误状态（如 `exportError`），在 UI 中显示 toast 或内联错误提示。

#### 问题 F-3：大尺寸 Canvas 可能导致内存溢出

- **文件**：`src/utils/pdfExporter.ts` 第 29 行
- **级别**：Should Fix
- **描述**：`CAPTURE_SCALE = 2` 固定缩放 2 倍。对于全景导出，如果完整科技树实际尺寸为 5000×8000 像素，截图将生成 10000×16000 像素的 Canvas（约 640MB 内存），可能导致浏览器崩溃。`html2canvas` 没有内建的上限保护。
- **修复建议**：根据元素尺寸动态调整 scale，或设置最大 canvas 像素面积上限：

```typescript
function getSafeScale(width: number, height: number): number {
  const MAX_PIXELS = 16_000_000; // 约 64MB RGBA
  const totalPixels = width * height;
  if (totalPixels * 4 > MAX_PIXELS) {
    return Math.max(1, Math.floor(Math.sqrt(MAX_PIXELS / totalPixels)));
  }
  return CAPTURE_SCALE;
}
```

#### 问题 F-4：`exportFullView` 修改 DOM 样式时用户可见

- **文件**：`src/utils/pdfExporter.ts` 第 110-114 行
- **级别**：Should Fix
- **描述**：`exportFullView` 在截图前临时修改容器的 `overflow`、`width`、`height` 样式。如果 `html2canvas` 耗时较长（全景截图通常需要数秒），用户会看到布局突然变化再恢复，体验不佳。
- **修复建议**：在修改样式前先将容器设为不可见（如 `visibility: hidden` 或覆盖一个 loading 遮罩），截图完成后恢复。或者使用 `cloneNode` 克隆 DOM 再截图（html2canvas 不支持 clone，需要自行处理）。

### 3.3 Complexity（复杂度）

**可读性** ✅ 良好

代码组织清晰，函数职责单一：
- `sliceCanvas`：纯函数，负责 canvas 裁切
- `addImageFitToPage`：负责单页图片适配
- `addImageMultiPage`：负责多页分页逻辑
- `exportViewport` / `exportFullView`：高层导出入口

数学计算部分（px/mm 转换、分页计算）注释充分，易于理解。

### 3.4 Tests（测试）

#### 问题 T-1：完全缺失测试

- **文件**：项目根目录无 `tests/` 目录或 `*.test.ts` 文件
- **级别**：Must Fix
- **描述**：PDF 导出功能没有对应的单元测试或集成测试。关键逻辑（分页计算、canvas 切片、图片适配）都应该有测试覆盖。
- **修复建议**：至少添加以下测试：
  1. `sliceCanvas` 裁切正确性
  2. `addImageFitToPage` 宽高比适配逻辑（宽图、高图、正方形）
  3. `addImageMultiPage` 分页数量计算（单页、多页、边界值）
  4. `exportViewport` / `exportFullView` 的集成测试（mock html2canvas 和 jsPDF）

### 3.5 Naming（命名）

**命名清晰** ✅ 良好

- 常量命名：`A4_WIDTH_MM`、`CONTENT_HEIGHT_MM`、`CAPTURE_SCALE` —— 含义明确，含单位
- 函数命名：`exportViewport`、`exportFullView`、`sliceCanvas`、`addImageFitToPage` —— 动词开头，表达意图
- 变量命名：`pxPerMm`、`totalPages`、`sliceHeightMm` —— 简洁准确

### 3.6 Comments（注释）

**注释质量** ✅ 良好

- 模块级 JSDoc 说明功能和使用方式
- 每个 exported 函数有完整的 `@param` 和功能说明
- 关键计算步骤有行内注释（如 "计算按宽度适配时的高度"、"如果高度超出，则按高度适配"）
- 魔法数字全部提取为命名常量

### 3.7 Style（风格）

**风格一致性** ✅ 良好

- TypeScript 严格模式通过，类型注解完整
- 代码格式统一（2 空格缩进、一致的空行分隔）
- 但项目缺少 ESLint/Prettier 配置，建议补充

### 3.8 Documentation（文档）

**README 更新** ✅ 良好

README.md 已包含：
- ✅ 项目简介和功能特性（含 PDF 导出说明）
- ✅ 技术栈（含 html2canvas 和 jsPDF）
- ✅ 安装步骤
- ✅ 运行命令
- ✅ 构建命令
- ✅ 部署方式（本地预览 / 浏览器直接打开 / 静态服务器）
- ✅ 项目结构（含 pdfExporter.ts）

#### 问题 D-1：README 缺少 Node.js 版本要求

- **文件**：`README.md`
- **级别**：Should Fix
- **描述**：未说明 Node.js 最低版本要求。项目使用了 Vite 6 和 TypeScript 5.6，对 Node.js 版本有最低要求（Vite 5+ 需要 Node.js 18+）。
- **修复建议**：在"安装"章节添加 Node.js 版本要求说明。

### 3.9 前端专项：组件设计

**Toolbar 集成** ✅ 良好

对比 `Toolbar.tsx.bak`，新增部分仅限于：
- 新增 3 个可选 Props：`exporting`、`onExportViewport`、`onExportFullView`
- 新增导出按钮下拉菜单的 UI 和逻辑
- 原有的布局切换按钮和重置按钮完全未改动 ✅

Props 接口使用可选属性（`exporting?`、`onExportViewport?`），向后兼容。

### 3.10 前端专项：交互完整性

#### 问题 I-1：导出下拉菜单无键盘可访问性

- **文件**：`src/components/Toolbar.tsx` 第 86-116 行
- **级别**：Should Fix
- **描述**：导出下拉菜单不支持键盘操作：
  - 缺少 `aria-expanded`、`aria-haspopup` 属性
  - 无 Escape 键关闭菜单的处理
  - 无 Arrow 键导航菜单项
  - 菜单项无 `role="menuitem"`
- **修复建议**：

```tsx
<button
  className="toolbar-btn toolbar-export"
  onClick={toggleExportMenu}
  disabled={exporting}
  aria-haspopup="true"
  aria-expanded={exportMenuOpen}
  title="导出PDF"
>
```

并添加 `onKeyDown` 处理 Escape 关闭。

### 3.11 前端专项：用户体验

#### 问题 U-1：全景导出无进度反馈

- **文件**：`src/utils/pdfExporter.ts`、`src/App.tsx`
- **级别**：Should Fix
- **描述**：全景导出可能耗时数秒（取决于图大小），但只显示"导出中..."的静态文字，没有进度信息。用户可能以为程序卡死了。
- **修复建议**：可以考虑在多页导出时回调进度（当前页/总页数），或者至少在导出中遮罩界面避免用户误操作。

### 3.12 构建配置审查

#### 问题 B-1：缺少代码分割配置

- **文件**：`vite.config.ts`
- **级别**：Should Fix
- **描述**：构建产物 `index-DmNtU9Xs.js` 高达 1,378 KB（gzip 后 427 KB），触发 Vite 的 chunk 大小警告。所有依赖（React、Cytoscape、html2canvas、jsPDF）打包在一个 chunk 中。`base: './'` 配置正确（构建产物使用相对路径），支持离线运行 ✅。
- **修复建议**：

```typescript
export default defineConfig({
  plugins: [react()],
  base: './',
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor-react': ['react', 'react-dom'],
          'vendor-cytoscape': ['cytoscape', 'cytoscape-cose-bilkent', 'cytoscape-dagre'],
          'vendor-pdf': ['html2canvas', 'jspdf'],
        },
      },
    },
  },
});
```

---

## 4. 细节清单核对结果

| # | 检查项 | 级别 | 结果 | 说明 |
|---|--------|------|------|------|
| **Design（设计）** |||||
| 1 | 架构合理性 | [error] | ✅ | pdfExporter 独立模块，职责清晰 |
| 2 | 模块划分 | [error] | ✅ | PDF逻辑与UI分离，Toolbar仅负责交互 |
| 3 | 扩展性 | [warning] | ✅ | 函数参数化，易于扩展 |
| 4 | 接口设计 | [warning] | ✅ | 公共接口最小化（2个导出函数） |
| **Functionality（功能）** |||||
| 5 | 行为正确性 | [error] | ✅ | exportViewport/exportFullView 实现完整 |
| 6 | 边界情况 | [error] | ❌ | sliceCanvas ctx=null 静默失败（F-1） |
| 7 | 用户价值 | [warning] | ✅ | PDF导出对用户有明确价值 |
| 8 | 副作用处理 | [error] | ✅ | try/finally 正确恢复DOM样式 |
| **Complexity（复杂度）** |||||
| 9 | 可读性 | [error] | ✅ | 函数职责单一，注释充分 |
| 10 | 过度设计 | [warning] | ✅ | 无过度设计 |
| 11 | 抽象层次 | [warning] | ✅ | 辅助函数抽象层次恰当 |
| **Tests（测试）** |||||
| 12 | 测试覆盖 | [error] | ❌ | 无任何测试文件（T-1） |
| 13 | 测试质量 | [error] | ❌ | N/A，无测试 |
| 14 | 测试命名 | [warning] | — | N/A |
| 15 | 缺失测试 | [warning] | ❌ | 缺少边界条件和集成测试 |
| **Naming（命名）** |||||
| 16 | 命名清晰 | [error] | ✅ | 常量含单位，函数动宾结构 |
| 17 | 命名一致 | [warning] | ✅ | 风格统一 |
| 18 | 命名规范 | [warning] | ✅ | 遵循 TypeScript 约定 |
| **Comments（注释）** |||||
| 19 | 注释必要性 | [warning] | ✅ | JSDoc 完整 |
| 20 | 注释准确性 | [error] | ✅ | 注释与代码一致 |
| 21 | 自文档化 | [warning] | ✅ | 命名清晰减少注释依赖 |
| **Style（风格）** |||||
| 22 | 风格一致性 | [warning] | ⚠️ | 代码一致但缺 ESLint 配置 |
| 23 | 格式规范 | [warning] | ✅ | 缩进、空行统一 |
| **Documentation（文档）** |||||
| 24 | 文档更新 | [warning] | ✅ | README 含 PDF 导出说明 |
| 25 | 接口文档 | [error] | ✅ | JSDoc 参数文档完整 |
| **前端专项** |||||
| 26 | 组件职责 | [error] | ✅ | Toolbar 职责单一 |
| 27 | 组件复用性 | [warning] | ✅ | Props 接口通用 |
| 28 | 错误反馈 | [error] | ❌ | 导出失败无用户提示（F-2） |
| 29 | 加载状态 | [warning] | ✅ | 导出中有 loading 状态 |
| 30 | 渲染优化 | [error] | ❌ | 大 canvas 内存风险（F-3） |
| 31 | 内存泄漏 | [error] | ⚠️ | 大 canvas 对象未释放（GC处理） |
| 32 | 键盘导航 | [error] | ❌ | 下拉菜单不支持键盘（I-1） |
| 33 | 屏幕阅读器 | [warning] | ❌ | 缺少 ARIA 属性（I-1） |
| **安全与健壮性** |||||
| 34 | 输入验证 | [error] | ✅ | fileName 有默认值 |
| 35 | 权限控制 | [error] | ✅ | N/A，纯前端无权限 |
| 36 | 资源清理 | [warning] | ✅ | useEffect 正确清理事件监听 |
| **构建配置** |||||
| 37 | base 配置 | — | ✅ | `./` 正确支持离线运行 |
| 38 | 代码分割 | [warning] | ❌ | 缺少 manualChunks（B-1） |
| 39 | 无安全漏洞 | [error] | ✅ | 依赖版本较新 |

### 通过统计

| 级别 | 总数 | ✅ 通过 | ❌ 未通过 | ⚠️ 部分通过 | 通过率 |
|------|------|---------|-----------|-------------|--------|
| [error] 必须项 | 16 | 11 | 5 | 0 | **68.8%** |
| [warning] 建议项 | 16 | 11 | 4 | 1 | **68.8%** |
| **合计** | **39** | **25** | **10** | **2** | **64.1%** |

---

## 5. 验收标准核对结果

基于任务描述中的审查要点逐条核对：

| AC# | 验收标准 | 状态 | 说明 |
|-----|----------|------|------|
| AC-1 | exportViewport 和 exportFullView 实现完整正确 | ✅ 已实现 | 两个函数逻辑完整，截图→适配→生成PDF→下载流程正确 |
| AC-2 | html2canvas 和 jsPDF 使用方式正确，类型安全 | ✅ 已实现 | TypeScript 严格模式无错误，API 使用方式正确 |
| AC-3 | html2canvas 和 jsPDF 使用类型安全 | ✅ 已实现 | `tsc --strict` 通过，无类型错误 |
| AC-4 | 大图分页处理逻辑合理 | ⚠️ 部分实现 | 分页数学逻辑正确，但存在内存风险和静默失败问题 |
| AC-5 | Toolbar 集成只添加了导出功能未改动已有逻辑 | ✅ 已实现 | 对比 .bak 文件，原有按钮和逻辑完全未变 |
| AC-6 | vite.config.ts 的 base: './' 配置正确支持离线 | ✅ 已实现 | 构建产物使用相对路径，dist/index.html 确认 |
| AC-7 | README 内容完整（简介/安装/运行/构建/部署） | ✅ 已实现 | 所有章节齐全，项目结构准确 |
| AC-8 | 代码质量：类型定义、错误处理、代码风格 | ⚠️ 部分实现 | 类型定义优秀，错误处理有遗漏，无 lint 配置 |
| AC-9 | 无安全隐患或性能问题 | ⚠️ 部分实现 | 无安全隐患，但存在大 canvas 内存性能问题 |

---

## 6. 改进建议

### Must Fix（必须修复，阻止合并）

| # | 问题 | 文件 | 建议 |
|---|------|------|------|
| 1 | sliceCanvas ctx=null 静默失败 | `pdfExporter.ts:54-57` | 抛出明确错误而非返回空白 canvas |
| 2 | 完全缺失测试 | 项目根目录 | 至少添加分页逻辑和 canvas 裁切的单元测试 |

### Should Fix（建议修复，不阻止合并但影响质量）

| # | 问题 | 文件 | 建议 |
|---|------|------|------|
| 3 | 导出失败无用户反馈 | `App.tsx:104-105` | 添加 toast 或错误状态提示 |
| 4 | 大 canvas 内存风险 | `pdfExporter.ts:29` | 动态调整 scale，设置像素上限 |
| 5 | 导出时 DOM 变化可见 | `pdfExporter.ts:110-114` | 截图前添加 loading 遮罩 |
| 6 | 导出下拉菜单无键盘支持 | `Toolbar.tsx:86-116` | 添加 ARIA 属性和键盘事件处理 |
| 7 | 构建产物过大（1378KB） | `vite.config.ts` | 配置 manualChunks 分割 vendor |
| 8 | 缺少 ESLint 配置 | 项目根目录 | 添加 eslint.config.js + prettier |
| 9 | README 缺 Node.js 版本要求 | `README.md` | 在安装章节说明版本要求 |

### Nit（可选改进）

| # | 问题 | 文件 | 建议 |
|---|------|------|------|
| 10 | useCORS: true 不必要 | `pdfExporter.ts:76` | 项目无跨域图片，可移除 |
| 11 | 全景导出无进度反馈 | `pdfExporter.ts` | 多页导出时回调进度信息 |
| 12 | 备份文件残留 | 多个 `.bak` 文件 | 清理 `.bak` 文件，使用 Git 管理版本 |

---

## 7. 总结

### 整体评价

本次 PDF 导出功能的实现**质量良好**，代码组织清晰、类型安全、文档完善。核心亮点包括：

1. **模块设计优秀**：pdfExporter 作为独立 utils 模块，公共接口简洁，内部函数职责单一
2. **类型安全**：TypeScript 严格模式零错误，类型注解覆盖完整
3. **Toolbar 集成干净**：仅新增导出相关代码，完全未影响已有功能
4. **构建配置正确**：`base: './'` 使 dist 可直接双击打开，支持离线运行
5. **README 完善**：涵盖所有必要章节，部署方式说明清晰

### 主要风险

1. **缺少测试**是最大的质量缺口，关键的分页计算和 canvas 操作应覆盖自动化测试
2. **大 canvas 内存风险**在全景导出时可能导致低端设备浏览器崩溃
3. **用户反馈不足**：导出失败时用户看不到任何提示

### 审查结论

| 结论 | 判定依据 |
|------|----------|
| **Request Changes** | 存在 2 个 Must Fix 级别问题（sliceCanvas 静默失败 + 缺失测试），[error] 项通过率 68.8% < 80% |

修复 Must Fix 问题后，建议重新提交审查。Should Fix 项可在后续迭代中逐步完善。
