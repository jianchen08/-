"""科技树可视化项目 - 模块桥接文件。

本文件用于项目模块索引。实际功能代码位于 TypeScript 模块中：
- PDF 导出：src/utils/pdfExporter.ts
- 工具栏组件：src/components/Toolbar.tsx
- 构建配置：vite.config.ts
- 项目文档：README.md
"""

from __future__ import annotations

PROJECT_NAME: str = "tech-tree-visualizer"
VERSION: str = "1.0.0"
DESCRIPTION: str = "人类科技树全景可视化工具"


def get_project_info() -> dict[str, str]:
    """返回项目基本信息。

    Returns:
        包含项目名称、版本和描述的字典。
    """
    return {
        "name": PROJECT_NAME,
        "version": VERSION,
        "description": DESCRIPTION,
    }
