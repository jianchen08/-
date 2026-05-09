# 🌳 科技树可视化工具

人类科技树全景可视化项目——交互式展示人类从远古到现代的科技发展脉络，支持多维度筛选、搜索和 PDF 导出。

## ✨ 功能特性

- **交互式图谱**：基于 Cytoscape.js 的科技树可视化，支持缩放、拖拽、节点点击
- **多种布局**：层次布局（Dagre）、力导向布局（CoSE-Bilkent）、时间轴布局
- **多维筛选**：按时代、领域、枢纽值筛选科技节点
- **全文搜索**：支持按名称、描述、标签搜索科技节点
- **节点详情**：点击节点查看详细信息、前置技术和关联节点
- **PDF 导出**：
  - 🖼️ **视口导出**：导出当前可见区域为 PDF
  - 🗺️ **全景导出**：导出完整科技树（自动分页）

## 🛠️ 技术栈

| 技术 | 用途 |
|------|------|
| TypeScript | 类型安全的开发语言 |
| React 18 | UI 框架 |
| Vite 6 | 构建工具 |
| Cytoscape.js | 图可视化引擎 |
| html2canvas | DOM 截图 |
| jsPDF | PDF 生成 |

## 📦 安装

```bash
# 克隆项目
git clone <repository-url>
cd tech-tree-visualizer

# 安装依赖
npm install
```

## 🚀 运行

```bash
# 启动开发服务器
npm run dev
```

启动后访问 http://localhost:5173 即可查看。

## 📦 构建

```bash
# 构建生产版本
npm run build
```

构建产物输出到 `dist/` 目录。

## 🌐 部署

`dist/` 目录为纯静态文件，可直接部署到任意静态服务器：

```bash
# 方式一：本地预览
npm run preview

# 方式二：直接用浏览器打开
# dist/index.html 使用相对路径，可直接双击打开（离线可用）

# 方式三：部署到 Nginx / Apache / GitHub Pages / Vercel 等
# 将 dist/ 目录内容复制到 Web 服务器的根目录即可
```

## 📂 项目结构

```
tech-tree-visualizer/
├── public/
│   └── data/                  # 科技树数据集
│       ├── domains.json       # 领域定义（12 个领域）
│       ├── eras.json          # 时代定义
│       ├── full_data.json     # 完整数据
│       └── nodes/             # 各领域节点数据
│           ├── agriculture.json
│           ├── astronomy.json
│           ├── biology.json
│           ├── chemistry.json
│           ├── energy.json
│           ├── engineering.json
│           ├── it.json
│           ├── materials.json
│           ├── math.json
│           ├── medicine.json
│           ├── physics.json
│           └── social.json
├── src/
│   ├── components/
│   │   ├── FilterPanel.tsx    # 筛选面板（时代/领域/枢纽值）
│   │   ├── Legend.tsx         # 图例组件
│   │   ├── NodeDetail.tsx    # 节点详情面板
│   │   ├── SearchPanel.tsx   # 搜索面板
│   │   ├── TechTree.tsx      # 科技树主组件（Cytoscape）
│   │   └── Toolbar.tsx       # 工具栏（布局切换/导出）
│   ├── types/
│   │   └── index.ts          # TypeScript 类型定义
│   ├── utils/
│   │   ├── dataLoader.ts     # 数据加载器
│   │   ├── hubCalculator.ts  # 枢纽值计算
│   │   └── pdfExporter.ts    # PDF 导出工具
│   ├── App.tsx               # 应用主组件
│   ├── App.css               # 全局样式
│   └── main.tsx              # 入口文件
├── index.html                # HTML 入口
├── vite.config.ts            # Vite 构建配置
├── tsconfig.json             # TypeScript 配置
└── package.json              # 项目依赖
```

## 📄 License

MIT
