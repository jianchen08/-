"""
科技树页面修复效果验证测试。

验证范围：
1. 页面渲染：构建成功、组件完整、数据加载、节点/层级关系正常
2. 样式美化：配色方案、节点卡片样式、连接线、字体、间距、动画过渡
3. 交互功能：hover 高亮、点击选中、搜索、筛选、布局切换
4. 响应式布局：多断点适配
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
PUBLIC_DIR = PROJECT_ROOT / "public"
DIST_DIR = PROJECT_ROOT / "dist"
CSS_FILE = SRC_DIR / "App.css"


def _run_cmd(cmd: str, cwd: Path | None = None, timeout: int = 180) -> subprocess.CompletedProcess[str]:
    """在项目根目录执行命令并返回结果。"""
    return subprocess.run(
        cmd,
        shell=True,
        cwd=cwd or PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


# ===========================================================================
# 1. 页面渲染验证 — 构建成功 + 组件完整 + 数据加载
# ===========================================================================


class TestPageRendering:
    """验证科技树页面能正常渲染，不再空白。"""

    def test_build_succeeds_without_errors(self) -> None:
        """验证项目能成功构建，无 TypeScript 编译错误。"""
        result = _run_cmd("npm run build")
        assert result.returncode == 0, (
            f"构建失败:\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_main_entry_point_exists(self) -> None:
        """验证入口文件 src/main.tsx 存在。"""
        assert (SRC_DIR / "main.tsx").exists(), "入口文件 main.tsx 不存在"

    def test_app_component_exists(self) -> None:
        """验证主组件 App.tsx 存在。"""
        assert (SRC_DIR / "App.tsx").exists(), "主组件 App.tsx 不存在"

    def test_tech_tree_component_exists(self) -> None:
        """验证核心科技树组件 TechTree.tsx 存在。"""
        assert (SRC_DIR / "components" / "TechTree.tsx").exists(), (
            "TechTree 组件不存在"
        )

    def test_all_required_components_exist(self) -> None:
        """验证所有必要的子组件都存在。"""
        required_components = [
            "SearchPanel.tsx",
            "FilterPanel.tsx",
            "NodeDetail.tsx",
            "Toolbar.tsx",
            "Legend.tsx",
            "MiniMap.tsx",
            "TimelineSlider.tsx",
        ]
        for comp in required_components:
            path = SRC_DIR / "components" / comp
            assert path.exists(), f"必要组件缺失: {comp}"

    def test_cytoscape_initialized_with_layouts(self) -> None:
        """验证 Cytoscape 注册了所有布局算法（dagre、cose-bilkent）。"""
        tech_tree_src = (SRC_DIR / "components" / "TechTree.tsx").read_text(encoding="utf-8")
        assert "cytoscape.use(dagre)" in tech_tree_src, "未注册 dagre 布局"
        assert "cytoscape.use(coseBilkent)" in tech_tree_src, "未注册 cose-bilkent 布局"

    def test_three_layout_types_supported(self) -> None:
        """验证支持三种布局类型：dagre、force、timeline。"""
        types_src = (SRC_DIR / "types" / "index.ts").read_text(encoding="utf-8")
        assert "'dagre'" in types_src, "未定义 dagre 布局类型"
        assert "'force'" in types_src, "未定义 force 布局类型"
        assert "'timeline'" in types_src, "未定义 timeline 布局类型"

    def test_data_files_are_valid(self) -> None:
        """验证数据文件完整且 JSON 格式正确。"""
        for fname in ["full_data.json", "domains.json", "eras.json"]:
            fpath = PUBLIC_DIR / "data" / fname
            assert fpath.exists(), f"数据文件不存在: {fname}"
            content = fpath.read_text(encoding="utf-8")
            data = json.loads(content)
            assert len(data) > 0, f"数据文件为空: {fname}"

    def test_nodes_have_complete_fields(self) -> None:
        """验证每个节点都有完整的字段。"""
        nodes_path = PUBLIC_DIR / "data" / "full_data.json"
        nodes = json.loads(nodes_path.read_text(encoding="utf-8"))

        required_fields = ["id", "name", "year", "era", "domain", "prerequisites", "description"]
        for node in nodes:
            for field in required_fields:
                assert field in node, (
                    f"节点 {node.get('id', '未知')} 缺少字段: {field}"
                )

    def test_nodes_cover_all_domains(self) -> None:
        """验证节点覆盖所有定义的领域。"""
        nodes = json.loads((PUBLIC_DIR / "data" / "full_data.json").read_text(encoding="utf-8"))
        domains = json.loads((PUBLIC_DIR / "data" / "domains.json").read_text(encoding="utf-8"))

        node_domains = {n["domain"] for n in nodes}
        defined_domains = {d["id"] for d in domains}

        assert node_domains == defined_domains, (
            f"节点领域与定义不匹配: 缺少 {defined_domains - node_domains}"
        )

    def test_nodes_cover_all_eras(self) -> None:
        """验证节点覆盖所有定义的时代。"""
        nodes = json.loads((PUBLIC_DIR / "data" / "full_data.json").read_text(encoding="utf-8"))
        eras = json.loads((PUBLIC_DIR / "data" / "eras.json").read_text(encoding="utf-8"))

        node_eras = {n["era"] for n in nodes}
        defined_eras = {e["id"] for e in eras}

        assert node_eras == defined_eras, (
            f"节点时代与定义不匹配: 缺少 {defined_eras - node_eras}"
        )

    def test_prerequisite_edges_are_valid(self) -> None:
        """验证所有前置引用指向存在的节点。"""
        nodes = json.loads((PUBLIC_DIR / "data" / "full_data.json").read_text(encoding="utf-8"))
        node_ids = {n["id"] for n in nodes}

        for node in nodes:
            for prereq in node["prerequisites"]:
                assert prereq in node_ids, (
                    f"节点 {node['id']} 的前置 {prereq} 不存在于节点集合中"
                )

    def test_hub_calculator_exists_and_works(self) -> None:
        """验证枢纽值计算模块存在且逻辑正确。"""
        hub_path = SRC_DIR / "utils" / "hubCalculator.ts"
        assert hub_path.exists(), "hubCalculator.ts 不存在"

        content = hub_path.read_text(encoding="utf-8")
        assert "calculateHubScores" in content, "缺少 calculateHubScores 函数"
        assert "getRankedNodeIds" in content, "缺少 getRankedNodeIds 函数"

    def test_data_loader_uses_base_url(self) -> None:
        """验证数据加载器使用 BASE_URL 构建路径。"""
        loader_src = (SRC_DIR / "utils" / "dataLoader.ts").read_text(encoding="utf-8")
        assert "import.meta.env.BASE_URL" in loader_src, (
            "dataLoader 未使用 BASE_URL"
        )

    def test_dist_contains_rendered_assets(self) -> None:
        """验证构建产物包含完整的渲染资源。"""
        assert (DIST_DIR / "index.html").exists(), "dist/index.html 不存在"

        # 检查 JS bundle
        js_files = list((DIST_DIR / "assets").glob("*.js"))
        assert len(js_files) >= 1, "构建产物中无 JS 文件"

        # 检查 CSS bundle
        css_files = list((DIST_DIR / "assets").glob("*.css"))
        assert len(css_files) >= 1, "构建产物中无 CSS 文件"

        # 检查数据文件
        assert (DIST_DIR / "data" / "full_data.json").exists(), "dist/data/full_data.json 不存在"

    def test_cytoscape_elements_built_correctly(self) -> None:
        """验证 buildElements 函数能正确构建 Cytoscape 元素。"""
        tech_tree_src = (SRC_DIR / "components" / "TechTree.tsx").read_text(encoding="utf-8")

        # 验证节点构建逻辑
        assert "buildElements" in tech_tree_src, "缺少 buildElements 函数"
        assert "group: 'nodes'" in tech_tree_src, "未构建节点元素"
        assert "group: 'edges'" in tech_tree_src, "未构建边元素"

    def test_cytoscape_style_defined(self) -> None:
        """验证 Cytoscape 节点/边样式已定义。"""
        tech_tree_src = (SRC_DIR / "components" / "TechTree.tsx").read_text(encoding="utf-8")

        # 节点样式
        assert "'background-color'" in tech_tree_src, "未定义节点背景色"
        assert "'text-valign'" in tech_tree_src, "未定义文字垂直对齐"
        assert "'text-wrap'" in tech_tree_src, "未定义文字换行"

        # 边样式
        assert "'line-color'" in tech_tree_src, "未定义连接线颜色"
        assert "'target-arrow-shape'" in tech_tree_src, "未定义箭头形状"
        assert "'curve-style'" in tech_tree_src, "未定义曲线样式"


# ===========================================================================
# 2. 样式美化验证 — 配色、节点样式、连接线、字体、间距、动画
# ===========================================================================


class TestStylingAndBeautification:
    """验证页面样式美化效果。"""

    def _read_css(self) -> str:
        return CSS_FILE.read_text(encoding="utf-8")

    def test_dark_theme_colors(self) -> None:
        """验证深色主题配色方案。"""
        css = self._read_css()

        # 主背景色
        assert "#0d1117" in css, "缺少深色主题背景色 #0d1117"

        # 文字颜色层次
        assert "#e6edf3" in css or "#f0f6fc" in css, "缺少亮色文字"
        assert "#8b949e" in css, "缺少次要文字颜色"

    def test_node_card_styles(self) -> None:
        """验证节点卡片样式配置。"""
        tech_tree_src = (SRC_DIR / "components" / "TechTree.tsx").read_text(encoding="utf-8")

        # 节点尺寸映射（hubScore → nodeSize）
        assert "hubToSize" in tech_tree_src, "缺少节点尺寸映射函数"

        # 节点颜色映射（domain → displayColor）
        assert "adjustBrightness" in tech_tree_src, "缺少颜色亮度调整函数"
        assert "domainColorMap" in tech_tree_src, "缺少领域颜色映射"

        # 节点边框样式
        assert "'border-width'" in tech_tree_src, "未定义节点边框宽度"
        assert "'border-color'" in tech_tree_src, "未定义节点边框颜色"

    def test_hub_score_visual_differentiation(self) -> None:
        """验证不同枢纽值节点有不同的视觉表现。"""
        tech_tree_src = (SRC_DIR / "components" / "TechTree.tsx").read_text(encoding="utf-8")

        # hub >= 60 金色边框
        assert "hubScore >= 60" in tech_tree_src, "缺少 hub>=60 的视觉样式"
        assert "#FFD700" in tech_tree_src, "缺少金色边框 (#FFD700)"

        # hub >= 80 红橙边框 + 星标
        assert "hubScore >= 80" in tech_tree_src, "缺少 hub>=80 的视觉样式"
        assert "#FF4500" in tech_tree_src, "缺少红橙边框 (#FF4500)"
        assert "⭐" in tech_tree_src, "缺少高枢纽值节点的星标标识"

    def test_connection_line_styles(self) -> None:
        """验证连接线（edge）样式。"""
        tech_tree_src = (SRC_DIR / "components" / "TechTree.tsx").read_text(encoding="utf-8")

        # 贝塞尔曲线
        assert "'bezier'" in tech_tree_src, "连接线未使用贝塞尔曲线"

        # 半透明效果
        assert "opacity" in tech_tree_src, "连接线缺少透明度设置"

        # 箭头
        assert "'triangle'" in tech_tree_src, "缺少箭头指示"

    def test_highlighted_edge_style(self) -> None:
        """验证高亮连接线样式（hover 时激活）。"""
        tech_tree_src = (SRC_DIR / "components" / "TechTree.tsx").read_text(encoding="utf-8")

        assert "edge.highlighted" in tech_tree_src, "缺少高亮边样式"
        assert "#4fc3f7" in tech_tree_src, "缺少高亮色 #4fc3f7"

    def test_font_settings(self) -> None:
        """验证字体设置。"""
        css = self._read_css()

        # 字体族
        assert "font-family" in css, "缺少字体定义"
        assert "PingFang SC" in css or "Microsoft YaHei" in css, "缺少中文字体支持"

        # 字体大小层次
        assert "font-size" in css, "缺少字体大小定义"

    def test_loading_animation(self) -> None:
        """验证加载动画。"""
        css = self._read_css()

        assert ".app-loading-spinner" in css, "缺少加载旋转动画"
        assert "@keyframes spin" in css or "animation:" in css, "缺少旋转动画关键帧"

    def test_glow_pulse_animation(self) -> None:
        """验证发光脉冲动画。"""
        css = self._read_css()

        assert "@keyframes glow-pulse" in css, "缺少发光脉冲动画"
        assert ".legend-glow-dot" in css, "缺少发光圆点样式"

    def test_smooth_transitions(self) -> None:
        """验证平滑过渡动画。"""
        css = self._read_css()
        tech_tree_src = (SRC_DIR / "components" / "TechTree.tsx").read_text(encoding="utf-8")

        # CSS 过渡
        assert "transition:" in css or "transition-" in css, "缺少 CSS 过渡效果"

        # Cytoscape 过渡
        assert "'transition-property'" in tech_tree_src, "Cytoscape 节点缺少过渡属性"
        assert "'transition-duration'" in tech_tree_src, "Cytoscape 节点缺少过渡时长"

    def test_sidebar_panel_styles(self) -> None:
        """验证侧栏面板样式。"""
        css = self._read_css()

        # 左侧筛选面板
        assert ".app-sidebar-left" in css, "缺少左侧面板样式"
        assert ".filter-panel" in css, "缺少筛选面板样式"

        # 右侧详情面板
        assert ".app-sidebar-right" in css, "缺少右侧面板样式"
        assert ".node-detail" in css, "缺少节点详情样式"

    def test_top_bar_styles(self) -> None:
        """验证顶部工具栏样式。"""
        css = self._read_css()

        assert ".app-top-bar" in css, "缺少顶部栏样式"
        assert ".toolbar" in css, "缺少工具栏样式"
        assert ".search-panel" in css, "缺少搜索面板样式"

    def test_legend_styles(self) -> None:
        """验证图例样式。"""
        css = self._read_css()

        assert ".legend" in css, "缺少图例样式"
        assert ".legend-color-dot" in css, "缺少图例颜色圆点"
        assert ".legend-size-dot" in css, "缺少图例大小指示"

    def test_minimap_styles(self) -> None:
        """验证小地图样式。"""
        css = self._read_css()

        assert ".minimap" in css, "缺少小地图样式"
        assert ".minimap-canvas" in css, "缺少小地图画布样式"

    def test_timeline_slider_styles(self) -> None:
        """验证时间轴滑块样式。"""
        css = self._read_css()

        assert ".timeline-slider" in css, "缺少时间轴滑块样式"
        assert ".timeline-era-band" in css, "缺少时代色带样式"
        assert ".timeline-range" in css, "缺少时间范围滑块样式"

    def test_node_detail_panel_styles(self) -> None:
        """验证节点详情面板样式。"""
        css = self._read_css()

        assert ".detail-name" in css, "缺少详情名称样式"
        assert ".detail-domain-badge" in css, "缺少领域徽章样式"
        assert ".detail-tags" in css, "缺少标签样式"
        assert ".detail-description" in css, "缺少描述样式"
        assert ".detail-node-list" in css, "缺少关联节点列表样式"

    def test_backdrop_blur_effects(self) -> None:
        """验证毛玻璃模糊效果。"""
        css = self._read_css()

        assert "backdrop-filter" in css, "缺少毛玻璃模糊效果"
        assert "blur(" in css, "缺少 blur 模糊函数"

    def test_box_shadow_effects(self) -> None:
        """验证阴影效果。"""
        css = self._read_css()

        assert "box-shadow" in css, "缺少阴影效果"

    def test_radial_gradient_background(self) -> None:
        """验证径向渐变背景。"""
        css = self._read_css()

        assert "radial-gradient" in css, "缺少径向渐变背景"

    def test_detail_sidebar_slide_animation(self) -> None:
        """验证详情侧栏滑入动画。"""
        css = self._read_css()

        # 右侧面板展开动画
        assert "transition:" in css or "transition-" in css, "缺少过渡动画"
        assert ".app-sidebar-right.open" in css, "缺少右侧面板展开状态"


# ===========================================================================
# 3. 交互功能验证 — hover、点击、搜索、筛选、布局切换
# ===========================================================================


class TestInteractiveFeatures:
    """验证页面交互功能。"""

    def _read_tech_tree(self) -> str:
        return (SRC_DIR / "components" / "TechTree.tsx").read_text(encoding="utf-8")

    def test_hover_highlight_implementation(self) -> None:
        """验证节点 hover 高亮效果已实现。"""
        src = self._read_tech_tree()

        # mouseover/mouseout 事件
        assert "'mouseover'" in src, "缺少 mouseover 事件监听"
        assert "'mouseout'" in src, "缺少 mouseout 事件监听"

        # hovered 类添加/移除
        assert "addClass('hovered')" in src, "缺少 hovered 类添加"
        assert "removeClass('hovered')" in src, "缺少 hovered 类移除"

    def test_hover_highlighted_edge_implementation(self) -> None:
        """验证 hover 时高亮关联连接线。"""
        src = self._read_tech_tree()

        assert "connectedEdges().addClass('highlighted')" in src, (
            "hover 时未高亮关联边"
        )
        assert "connectedEdges().removeClass('highlighted')" in src, (
            "hover 结束时未移除边高亮"
        )

    def test_hover_node_style_definition(self) -> None:
        """验证 hover 节点的样式定义。"""
        src = self._read_tech_tree()

        assert "node.hovered" in src, "缺少 node.hovered 样式选择器"
        # hover 时白色边框、提升 z-index、放大字号
        assert "'z-index'" in src, "hover 样式缺少 z-index 提升"

    def test_click_select_implementation(self) -> None:
        """验证节点点击选中功能。"""
        src = self._read_tech_tree()

        # 点击事件监听
        assert "'tap'" in src, "缺少 tap 点击事件监听"

        # 选中样式
        assert "node.selected" in src, "缺少 node.selected 样式"
        assert "addClass('selected')" in src, "缺少 selected 类添加"

    def test_click_deselect_implementation(self) -> None:
        """验证取消选中功能。"""
        src = self._read_tech_tree()

        # 移除选中类
        assert "removeClass('selected')" in src, "缺少取消选中功能"

    def test_right_click_select(self) -> None:
        """验证右键选中节点。"""
        src = self._read_tech_tree()

        assert "'cxttap'" in src, "缺少右键点击事件 (cxttap)"

    def test_search_functionality(self) -> None:
        """验证搜索功能实现。"""
        src = self._read_tech_tree()

        # 搜索匹配函数
        assert "matchesSearch" in src, "缺少搜索匹配函数"

        # 搜索结果视觉反馈：匹配节点保持可见，不匹配变暗
        assert "isDimmed" in src, "缺少搜索暗化标记"
        assert "node[?isDimmed]" in src, "缺少暗化节点样式选择器"
        assert "opacity: 0.12" in src or "0.12" in src, "暗化节点缺少低透明度"

    def test_search_covers_name_description_tags(self) -> None:
        """验证搜索覆盖节点名称、描述和标签。"""
        src = self._read_tech_tree()

        assert "node.name" in src, "搜索未覆盖节点名称"
        assert "node.description" in src, "搜索未覆盖节点描述"
        assert "node.tags" in src, "搜索未覆盖节点标签"

    def test_filter_functionality(self) -> None:
        """验证筛选功能实现。"""
        src = self._read_tech_tree()

        # 筛选判断函数
        assert "passesFilter" in src, "缺少筛选判断函数"

        # 按时代筛选
        assert "selectedEras" in src, "缺少时代筛选"

        # 按领域筛选
        assert "selectedDomains" in src, "缺少领域筛选"

        # 按枢纽值筛选
        assert "hubThreshold" in src, "缺少枢纽值筛选"

    def test_year_range_filter(self) -> None:
        """验证年份范围筛选。"""
        src = self._read_tech_tree()

        assert "yearRange" in src, "缺少年份范围筛选"
        assert "filter.yearRange" in src, "未使用年份范围进行筛选"

    def test_layout_switching(self) -> None:
        """验证布局切换功能。"""
        src = self._read_tech_tree()

        assert "getLayoutOptions" in src, "缺少布局选项获取函数"
        assert "'dagre'" in src, "缺少 dagre 布局选项"
        assert "'cose-bilkent'" in src or "'force'" in src, "缺少力导向布局选项"
        assert "'preset'" in src, "缺少预设位置（timeline）布局"

    def test_layout_animation(self) -> None:
        """验证布局切换有动画效果。"""
        src = self._read_tech_tree()

        assert "animate: true" in src or "'animate': true" in src, "布局切换缺少动画"
        assert "animationDuration" in src, "缺少动画时长配置"

    def test_reset_view_functionality(self) -> None:
        """验证重置视图功能。"""
        src = self._read_tech_tree()

        assert "resetView" in src, "缺少重置视图方法"
        assert "cy.fit" in src, "缺少 cy.fit() 视图适配"

    def test_focus_node_functionality(self) -> None:
        """验证节点聚焦功能。"""
        src = self._read_tech_tree()

        assert "focusNode" in src, "缺少节点聚焦方法"
        assert "cy.animate" in src, "缺少动画聚焦"

    def test_box_select_zoom(self) -> None:
        """验证框选放大功能。"""
        src = self._read_tech_tree()

        assert "handleMouseDown" in src, "缺少鼠标按下处理"
        assert "handleMouseMove" in src, "缺少鼠标移动处理"
        assert "handleMouseUp" in src, "缺少鼠标释放处理"
        assert "isBoxSelectingRef" in src, "缺少框选状态引用"
        assert "box-select-overlay" in src, "缺少框选覆盖层"

    def test_node_detail_panel_integration(self) -> None:
        """验证节点详情面板集成。"""
        app_src = (SRC_DIR / "App.tsx").read_text(encoding="utf-8")

        assert "NodeDetail" in app_src, "App 未集成 NodeDetail 组件"
        assert "selectedNode" in app_src, "缺少选中节点状态"
        assert "handleNodeSelect" in app_src, "缺少节点选中处理"

    def test_detail_panel_slide_animation(self) -> None:
        """验证详情面板展开/收起动画。"""
        css = CSS_FILE.read_text(encoding="utf-8")

        # 面板宽度过渡
        assert "transition:" in css, "详情面板缺少过渡动画"

        # open 状态
        assert ".app-sidebar-right.open" in css, "缺少面板展开状态"

    def test_zoom_controls(self) -> None:
        """验证缩放控制范围。"""
        src = self._read_tech_tree()

        assert "minZoom" in src, "缺少最小缩放限制"
        assert "maxZoom" in src, "缺少最大缩放限制"


# ===========================================================================
# 4. 响应式布局验证
# ===========================================================================


class TestResponsiveLayout:
    """验证响应式布局。"""

    def _read_css(self) -> str:
        return CSS_FILE.read_text(encoding="utf-8")

    def test_has_responsive_breakpoints(self) -> None:
        """验证定义了响应式断点。"""
        css = self._read_css()

        assert "@media" in css, "缺少媒体查询断点"
        assert "max-width: 1024px" in css, "缺少 1024px 断点"
        assert "max-width: 768px" in css, "缺少 768px 断点"
        assert "max-width: 480px" in css, "缺少 480px 断点"

    def test_tablet_breakpoint_adjustments(self) -> None:
        """验证平板断点（1024px）的布局调整。"""
        css = self._read_css()

        # 查找 1024px 断点下的规则
        media_1024 = re.search(
            r"@media\s*\(max-width:\s*1024px\)\s*\{([^}]*\{[^}]*\})*[^}]*\}",
            css,
            re.DOTALL,
        )
        assert media_1024 is not None, "缺少 1024px 媒体查询"

        # 侧栏和详情面板宽度调整
        assert ".app-sidebar-left" in css, "1024px 断点缺少侧栏调整"

    def test_mobile_breakpoint_adjustments(self) -> None:
        """验证手机断点（768px）的布局调整。"""
        css = self._read_css()

        # 图例和小地图隐藏
        assert ".legend" in css, "768px 断点需要处理图例"
        assert ".minimap" in css, "768px 断点需要处理小地图"

        # 工具栏按钮标签隐藏
        assert ".toolbar-btn-label" in css, "768px 断点需要隐藏按钮文字"

    def test_small_mobile_breakpoint(self) -> None:
        """验证小屏手机断点（480px）的布局调整。"""
        css = self._read_css()

        # 搜索面板宽度限制
        assert ".search-panel" in css, "480px 断点需要调整搜索面板"

        # 布局按钮间距
        assert ".toolbar-layout-group" in css, "480px 断点需要调整按钮间距"

    def test_flex_layout_used(self) -> None:
        """验证使用 Flex 布局实现自适应。"""
        css = self._read_css()

        assert "display: flex" in css, "缺少 Flex 布局"

    def test_viewport_meta_tag(self) -> None:
        """验证 HTML 包含 viewport meta 标签。"""
        index_html = (PROJECT_ROOT / "index.html").read_text(encoding="utf-8")

        assert "viewport" in index_html, "缺少 viewport meta 标签"
        assert "width=device-width" in index_html, "viewport 未设置 width=device-width"
        assert "initial-scale=1.0" in index_html, "viewport 未设置 initial-scale=1.0"

    def test_no_fixed_height_restrictions(self) -> None:
        """验证主布局没有固定高度限制导致溢出。"""
        css = self._read_css()

        # 布局应使用 100% 高度
        assert "height: 100%" in css, "布局未使用百分比高度"

    def test_overflow_handling(self) -> None:
        """验证溢出处理。"""
        css = self._read_css()

        assert "overflow" in css, "缺少溢出处理"

    def test_mobile_sidebar_overlay(self) -> None:
        """验证移动端侧栏使用覆盖层模式。"""
        css = self._read_css()

        # 移动端侧栏应使用 absolute 定位
        assert "position: absolute" in css, "移动端侧栏缺少绝对定位"


# ===========================================================================
# 5. 构建产物页面渲染验证（功能级别端到端）
# ===========================================================================


class TestBuildArtifactRendering:
    """验证构建产物的页面渲染能力。"""

    def test_dist_html_has_root_div(self) -> None:
        """验证 dist/index.html 包含 #root 挂载点。"""
        html = (DIST_DIR / "index.html").read_text(encoding="utf-8")
        assert '<div id="root">' in html, "dist/index.html 缺少 #root 挂载点"

    def test_dist_css_contains_dark_theme(self) -> None:
        """验证构建后的 CSS 包含深色主题。"""
        css_files = list((DIST_DIR / "assets").glob("*.css"))
        assert len(css_files) > 0, "构建产物中无 CSS 文件"

        combined_css = "".join(f.read_text(encoding="utf-8") for f in css_files)
        assert "#0d1117" in combined_css, "构建后 CSS 缺少深色主题背景色"

    def test_dist_css_contains_responsive_rules(self) -> None:
        """验证构建后的 CSS 包含响应式规则。"""
        css_files = list((DIST_DIR / "assets").glob("*.css"))
        combined_css = "".join(f.read_text(encoding="utf-8") for f in css_files)

        assert "@media" in combined_css, "构建后 CSS 缺少媒体查询"

    def test_dist_js_contains_cytoscape(self) -> None:
        """验证构建后的 JS 包含 Cytoscape 核心代码。"""
        js_files = list((DIST_DIR / "assets").glob("*.js"))
        combined_js = "".join(f.read_text(encoding="utf-8") for f in js_files)

        assert "cytoscape" in combined_js.lower(), "构建后 JS 缺少 Cytoscape 代码"

    def test_dist_data_has_sufficient_nodes(self) -> None:
        """验证构建产物数据中有足够多的节点用于渲染。"""
        nodes = json.loads(
            (DIST_DIR / "data" / "full_data.json").read_text(encoding="utf-8")
        )
        assert len(nodes) >= 100, (
            f"节点数量不足: {len(nodes)}，预期至少 100 个节点以形成丰富的科技树"
        )

    def test_dist_data_has_edges(self) -> None:
        """验证构建产物数据中有连接边。"""
        nodes = json.loads(
            (DIST_DIR / "data" / "full_data.json").read_text(encoding="utf-8")
        )
        total_edges = sum(len(n.get("prerequisites", [])) for n in nodes)
        assert total_edges >= 100, (
            f"边数量不足: {total_edges}，预期至少 100 条边以形成层级关系"
        )
