# 功能验证评估报告 - 科技树可视化项目

**评估时间**: 2026-05-09 15:36
**评估指标**: 功能验证
**项目类型**: TypeScript + React + Vite 前端项目

---

## 一、工具能力审查

| 验证内容 | 工具 | 覆盖范围 |
|---------|------|---------|
| 项目构建 (npm run build) | bash_execute | 完全覆盖 |
| TypeScript 类型检查 (npx tsc --noEmit) | bash_execute | 完全覆盖 |
| 构建产物验证 (index.html/路径/文件) | file_read + bash_execute | 完全覆盖 |
| 离线运行验证 (相对路径/资源引用) | bash_execute (grep) | 完全覆盖 |
| PDF 导出功能代码集成验证 | file_read + bash_execute | 完全覆盖（代码级别）|
| PDF 导出端到端交互验证 | 无浏览器自动化工具 | 无法验证 |

无法验证项：
- PDF 导出按钮点击后下拉菜单弹出、选择导出模式、实际生成 PDF 文件的端到端交互流程
- 原因：缺少 Playwright/Puppeteer 等浏览器自动化工具，无法模拟用户点击和文件下载

---

## 二、用户旅程验证

### 旅程：开发者构建项目并验证离线可用性

#### 步骤 1：确认依赖安装完整
- 操作: npm ls --depth=0
- 期望: 所有依赖正确安装，无 missing 报错
- 结果: 通过 - 全部 13 个依赖包正确安装
- 证据: cytoscape、html2canvas、jspdf、react、vite 等全部就绪

#### 步骤 2：TypeScript 类型检查
- 操作: npx tsc --noEmit
- 期望: 无类型错误，exit code 0
- 结果: 通过 - exit code 0，无任何输出（无错误）

#### 步骤 3：执行构建
- 操作: npm run build（内部执行 tsc -b && vite build）
- 期望: 构建成功，产物生成到 dist/ 目录
- 结果: 通过 - built in 8.54s
- 证据:
  - dist/index.html                        0.42 kB
  - dist/assets/index-CILThu0N.css         8.32 kB
  - dist/assets/purify.es-BaNf_EpD.js     24.29 kB
  - dist/assets/index.es-g_oG85by.js     159.60 kB
  - dist/assets/index-Brbe9oUo.js      1,378.26 kB
  - 有 chunk size 警告（大于500kB），但不影响功能

#### 步骤 4：验证构建产物 index.html
- 操作: 读取 dist/index.html，检查资源引用路径
- 期望: 引用路径使用相对路径（./），无绝对路径（/）
- 结果: 通过
- 证据: script src="./assets/index-Brbe9oUo.js" 和 link href="./assets/index-CILThu0N.css" 均为相对路径

#### 步骤 5：验证离线运行能力
- 操作: 检查 BASE_URL 替换值、数据文件完整性、外部依赖
- 期望: BASE_URL 为 ./，数据文件全部复制到 dist/data/，无运行时外部 HTTP 依赖
- 结果: 通过
- 证据:
  - const L0="./" - Vite 正确将 import.meta.env.BASE_URL 替换为相对路径
  - public/data 15个文件 = dist/data 15个文件，完全一致
  - JS 产物中的外部 URL 均为第三方库许可证文本，非运行时依赖
  - CSS 中无 url() 外部引用

#### 步骤 6：验证 PDF 导出功能代码集成
- 操作: 检查 jsPDF、html2canvas、导出函数在构建产物中
- 期望: PDF 相关库和导出逻辑正确打包
- 结果: 通过
- 证据:
  - jsPDF 在 dist/assets/index-Brbe9oUo.js 中出现 11 次
  - html2canvas 出现 3 次
  - exportViewport/exportFullView 等导出关键字存在
  - CSS 中包含完整的 .toolbar-export-* 样式族（wrap/dropdown/item/icon/text/title/desc）

---

## 三、补充场景

### 场景 A：构建产物中所有引用文件是否实际存在
- 操作: 逐一验证 index.html 引用的 JS/CSS 文件和数据文件
- 结果: 通过 - 全部存在
  - dist/assets/index-Brbe9oUo.js
  - dist/assets/index-CILThu0N.css
  - dist/data/full_data.json
  - dist/data/domains.json
  - dist/data/eras.json
  - dist/data/nodes/ (12个领域JSON文件)

### 场景 B：验证无绝对路径混入
- 操作: 使用 grep 检查 index.html 中以 / 开头的资源引用
- 结果: 通过 - 无匹配，确认无绝对路径引用

---

## 四、vite.config.ts 配置验证

- base: './' - 正确，确保所有资源引用使用相对路径
- plugins: react() - 正确，React JSX 支持正常

---

## 五、PDF 导出模块代码审查

### src/utils/pdfExporter.ts
- 正确导入 html2canvas 和 jsPDF
- exportViewport() - 视口截图导出，生成单页 A4 PDF
- exportFullView() - 全景导出，自动展开容器、截图、分页
- sliceCanvas() 辅助函数实现 canvas 裁切
- addImageFitToPage() / addImageMultiPage() 处理图片适配和分页
- finally 块恢复原始样式，防止 UI 状态泄漏
- TypeScript 类型标注完整

### src/components/Toolbar.tsx
- 接收 exporting、onExportViewport、onExportFullView props
- 下拉菜单实现（点击展开/关闭、外部点击关闭）
- 导出中状态显示（图标 + 文字）
- disabled 属性防止重复点击

### src/App.tsx 集成
- exporting 状态管理
- handleExportViewport / handleExportFullView 回调实现
- 获取 .tech-tree-container DOM 元素传递给导出函数
- try/catch/finally 完整错误处理和状态恢复

---

## 六、构建警告（非错误）

1. Chunk size 警告: index-Brbe9oUo.js 为 1,378 kB，超过 500kB 阈值
   - 影响：仅影响首屏加载性能，不影响功能
   - 建议：可通过 build.rollupOptions.output.manualChunks 拆分 cytoscape 等大型依赖

---

## 七、总结

| 验证项 | 结果 |
|-------|------|
| 依赖安装 | 通过 |
| TypeScript 类型检查 | 通过 |
| npm run build 构建 | 通过 |
| dist/index.html 生成 | 通过 |
| 资源引用使用相对路径 | 通过 |
| 数据文件完整复制 | 通过 |
| BASE_URL 正确替换 | 通过 |
| 无运行时外部依赖 | 通过 |
| PDF 导出库集成 | 通过 |
| PDF 导出 UI 组件集成 | 通过 |
| PDF 端到端交互 | 无法验证（缺少浏览器工具）|

所有可通过命令行验证的项目全部通过。
