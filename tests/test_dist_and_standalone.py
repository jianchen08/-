"""
科技树可视化项目 - dist构建产物与standalone.html正确性验证。

测试范围：
1. dist目录结构完整性
2. dist/index.html资源路径验证（相对路径，无绝对路径）
3. standalone.html完整性验证
4. standalone.html资源独立性（无外部依赖）
5. Cytoscape.js库可用性验证
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DIST_DIR = PROJECT_ROOT / "dist"
STANDALONE_HTML = PROJECT_ROOT / "standalone.html"


# ---------------------------------------------------------------------------
# 1. dist 目录结构完整性
# ---------------------------------------------------------------------------


class TestDistStructure:
    """验证 dist/ 目录结构的完整性。"""

    def test_dist_directory_exists(self) -> None:
        """dist/ 目录存在。"""
        assert DIST_DIR.exists(), f"构建产物目录不存在: {DIST_DIR}"
        assert DIST_DIR.is_dir(), f"dist 不是目录: {DIST_DIR}"

    def test_dist_index_html_exists(self) -> None:
        """dist/index.html 存在且非空。"""
        index_html = DIST_DIR / "index.html"
        assert index_html.exists(), "dist/index.html 不存在"
        assert index_html.stat().st_size > 0, "dist/index.html 为空文件"

    def test_dist_assets_directory_exists(self) -> None:
        """dist/assets/ 目录存在且包含 JS 和 CSS 文件。"""
        assets_dir = DIST_DIR / "assets"
        assert assets_dir.exists(), "dist/assets/ 目录不存在"

        js_files = list(assets_dir.glob("*.js"))
        css_files = list(assets_dir.glob("*.css"))

        assert len(js_files) > 0, "dist/assets/ 中没有 JS 文件"
        assert len(css_files) > 0, "dist/assets/ 中没有 CSS 文件"

    def test_dist_index_html_references_js_and_css(self) -> None:
        """dist/index.html 引用了 JS 和 CSS 资源文件。"""
        index_html = DIST_DIR / "index.html"
        content = index_html.read_text(encoding="utf-8")

        # 检查 script 引用
        script_refs = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', content)
        assert len(script_refs) > 0, "index.html 未引用任何 JS 文件"

        # 检查 link stylesheet 引用
        link_refs = re.findall(r'<link[^>]+href=["\']([^"\']+)["\']', content)
        assert len(link_refs) > 0, "index.html 未引用任何 CSS 文件"

    def test_dist_data_directory_exists(self) -> None:
        """dist/data/ 目录存在，包含完整数据文件。"""
        data_dir = DIST_DIR / "data"
        assert data_dir.exists(), "dist/data/ 目录不存在"

        expected_data_files = ["full_data.json", "domains.json", "eras.json"]
        for fname in expected_data_files:
            fpath = data_dir / fname
            assert fpath.exists(), f"数据文件不存在: {fpath}"

    def test_dist_data_nodes_directory_exists(self) -> None:
        """dist/data/nodes/ 目录存在，包含各学科 JSON 数据。"""
        nodes_dir = DIST_DIR / "data" / "nodes"
        assert nodes_dir.exists(), "dist/data/nodes/ 目录不存在"

        expected_domains = [
            "agriculture", "astronomy", "biology", "chemistry",
            "energy", "engineering", "it", "materials", "math",
            "medicine", "physics", "social",
        ]
        for domain in expected_domains:
            fpath = nodes_dir / f"{domain}.json"
            assert fpath.exists(), f"学科数据文件不存在: {fpath}"


# ---------------------------------------------------------------------------
# 2. dist/index.html 资源路径验证
# ---------------------------------------------------------------------------


class TestDistResourcePaths:
    """验证 dist/index.html 中所有资源路径为相对路径。"""

    def _read_index_html(self) -> str:
        index_html = DIST_DIR / "index.html"
        return index_html.read_text(encoding="utf-8")

    def test_all_resource_paths_are_relative(self) -> None:
        """所有资源路径以 ./ 开头（相对路径）。"""
        content = self._read_index_html()
        resource_refs = re.findall(r'(?:src|href)=["\']([^"\']+)["\']', content)

        assert len(resource_refs) > 0, "未找到任何资源引用"
        for ref in resource_refs:
            assert ref.startswith("./"), (
                f"资源路径不是相对路径: {ref}（应以 './' 开头）"
            )

    def test_no_absolute_paths(self) -> None:
        """资源路径不以 / 开头（非绝对路径）。"""
        content = self._read_index_html()
        resource_refs = re.findall(r'(?:src|href)=["\']([^"\']+)["\']', content)

        for ref in resource_refs:
            assert not ref.startswith("/"), (
                f"发现绝对路径引用: {ref}（不应以 '/' 开头）"
            )

    def test_no_vite_dev_paths(self) -> None:
        """资源路径不包含 /@vite/ 等开发服务器专属路径。"""
        content = self._read_index_html()
        dev_patterns = ["/@vite/", "/@id/", "/@fs/", "/src/"]
        for pattern in dev_patterns:
            assert pattern not in content, (
                f"index.html 包含开发服务器路径: {pattern}"
            )

    def test_no_external_urls(self) -> None:
        """资源路径不引用外部 HTTP/HTTPS URL。"""
        content = self._read_index_html()
        resource_refs = re.findall(r'(?:src|href)=["\']([^"\']+)["\']', content)

        for ref in resource_refs:
            assert not ref.startswith("http://") and not ref.startswith("https://"), (
                f"资源引用指向外部 URL: {ref}，离线时无法访问"
            )

    def test_referenced_files_exist_in_dist(self) -> None:
        """index.html 引用的所有文件都在 dist/ 目录中存在。"""
        content = self._read_index_html()
        resource_refs = re.findall(r'(?:src|href)=["\'](\./[^"\']+)["\']', content)

        for ref in resource_refs:
            relative_path = ref.lstrip("./")
            full_path = DIST_DIR / relative_path
            assert full_path.exists(), (
                f"index.html 引用的文件在 dist/ 中不存在: {ref} -> {full_path}"
            )


# ---------------------------------------------------------------------------
# 3. standalone.html 完整性验证
# ---------------------------------------------------------------------------


class TestStandaloneCompleteness:
    """验证 standalone.html 包含科技树可视化所需的全部代码。"""

    def _read_standalone(self) -> str:
        assert STANDALONE_HTML.exists(), f"standalone.html 不存在: {STANDALONE_HTML}"
        return STANDALONE_HTML.read_text(encoding="utf-8")

    def test_standalone_html_exists(self) -> None:
        """standalone.html 存在于项目根目录。"""
        assert STANDALONE_HTML.exists(), f"standalone.html 不存在: {STANDALONE_HTML}"
        assert STANDALONE_HTML.is_file(), f"standalone.html 不是文件: {STANDALONE_HTML}"

    def test_standalone_html_not_empty(self) -> None:
        """standalone.html 非空且有足够大小（应包含完整应用代码）。"""
        size = STANDALONE_HTML.stat().st_size
        # standalone.html 应该是一个较大的文件（内联了所有JS/CSS/数据）
        assert size > 100_000, (
            f"standalone.html 文件过小: {size} 字节，"
            f"可能未包含完整的应用代码和数据"
        )

    def test_standalone_has_html_structure(self) -> None:
        """standalone.html 包含完整的 HTML 结构。"""
        content = self._read_standalone()
        content_lower = content.lower()

        assert "<!doctype html>" in content_lower, "缺少 <!doctype html> 声明"
        assert "<html" in content_lower, "缺少 <html> 标签"
        assert "<head>" in content_lower, "缺少 <head> 标签"
        assert "<body>" in content_lower, "缺少 <body> 标签"
        assert "</html>" in content_lower, "缺少 </html> 结束标签"

    def test_standalone_has_root_div(self) -> None:
        """standalone.html 包含 React 挂载点 <div id="root">。"""
        content = self._read_standalone()
        assert 'id="root"' in content, '缺少 React 挂载点: <div id="root">'

    def test_standalone_has_inline_data(self) -> None:
        """standalone.html 包含内联的科技树数据。"""
        content = self._read_standalone()
        # 检查全局数据对象
        assert "window.__TECH_TREE_DATA__" in content, (
            "standalone.html 未包含内联数据（window.__TECH_TREE_DATA__）"
        )
        # 检查关键数据文件是否被内联
        assert '"data/full_data.json"' in content, (
            "standalone.html 未包含 full_data.json 数据"
        )
        assert '"data/domains.json"' in content, (
            "standalone.html 未包含 domains.json 数据"
        )
        assert '"data/eras.json"' in content, (
            "standalone.html 未包含 eras.json 数据"
        )

    def test_standalone_has_fetch_interceptor(self) -> None:
        """standalone.html 包含 fetch 拦截器，将数据请求重定向到内联数据。"""
        content = self._read_standalone()
        # 检查 fetch 拦截逻辑
        assert "window.fetch" in content, "缺少 window.fetch 拦截"
        assert "originalFetch" in content or "original fetch" in content.lower(), (
            "缺少 originalFetch 保存原始 fetch 的代码"
        )


# ---------------------------------------------------------------------------
# 4. standalone.html 资源独立性
# ---------------------------------------------------------------------------


class TestStandaloneIndependence:
    """验证 standalone.html 不依赖任何外部 HTTP 服务器或网络资源。"""

    def _read_standalone(self) -> str:
        return STANDALONE_HTML.read_text(encoding="utf-8")

    def test_no_external_script_src(self) -> None:
        """standalone.html 没有 <script src="..."> 外部脚本引用。"""
        content = self._read_standalone()
        external_scripts = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', content)
        assert len(external_scripts) == 0, (
            f"standalone.html 引用了外部脚本文件: {external_scripts}，"
            f"所有 JS 应内联在 HTML 中"
        )

    def test_no_external_link_href(self) -> None:
        """standalone.html 没有 <link href="..."> 外部样式引用。"""
        content = self._read_standalone()
        external_links = re.findall(r'<link[^>]+href=["\']([^"\']+)["\']', content)
        assert len(external_links) == 0, (
            f"standalone.html 引用了外部样式文件: {external_links}，"
            f"所有 CSS 应内联在 HTML 中"
        )

    def test_no_local_file_references(self) -> None:
        """standalone.html 不引用本地文件路径（如 ./assets/ 或 data/）。"""
        content = self._read_standalone()

        # 查找所有 script src 和 link href 引用（应该没有）
        script_srcs = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', content)
        link_hrefs = re.findall(r'<link[^>]+href=["\']([^"\']+)["\']', content)

        local_refs = [
            r for r in script_srcs + link_hrefs
            if r.startswith("./") or r.startswith("/") or r.startswith("assets/")
        ]
        assert len(local_refs) == 0, (
            f"standalone.html 引用了本地文件路径: {local_refs}，"
            f"在 file:// 协议下可能无法正常工作"
        )

    def test_no_http_resource_dependencies(self) -> None:
        """standalone.html 不依赖 HTTP 资源加载（核心功能不依赖网络）。"""
        content = self._read_standalone()

        # 检查是否有 CDN 引用
        cdn_patterns = [
            r'<script[^>]+src=["\']https?://',
            r'<link[^>]+href=["\']https?://',
        ]
        for pattern in cdn_patterns:
            matches = re.findall(pattern, content)
            assert len(matches) == 0, (
                f"standalone.html 依赖 CDN 资源: {matches}，"
                f"离线时将无法使用"
            )


# ---------------------------------------------------------------------------
# 5. Cytoscape.js 库可用性验证
# ---------------------------------------------------------------------------


class TestCytoscapeAvailability:
    """验证 Cytoscape.js 被正确引入且科技树数据可加载。"""

    def _read_standalone(self) -> str:
        return STANDALONE_HTML.read_text(encoding="utf-8")

    def test_cytoscape_in_standalone(self) -> None:
        """standalone.html 包含 Cytoscape.js 库代码（内联）。"""
        content = self._read_standalone()
        # Cytoscape.js 核心标识
        assert "cytoscape" in content.lower(), (
            "standalone.html 未包含 Cytoscape.js 代码"
        )
        # 检查 Cytoscape.js 的关键 API
        assert "core(" in content or "container(" in content, (
            "standalone.html 中的 Cytoscape.js 可能不完整（缺少核心 API）"
        )

    def test_cytoscape_layout_in_standalone(self) -> None:
        """standalone.html 包含 Cytoscape.js 布局算法（cose-bilkent 或 dagre）。"""
        content = self._read_standalone()
        has_layout = (
            "cose-bilkent" in content
            or "coseBilkent" in content
            or "dagre" in content
        )
        assert has_layout, (
            "standalone.html 未包含任何 Cytoscape.js 布局算法"
        )

    def test_cytoscape_in_dist_bundle(self) -> None:
        """dist 构建产物中包含 Cytoscape.js 库代码。"""
        assets_dir = DIST_DIR / "assets"
        js_files = list(assets_dir.glob("*.js"))
        assert len(js_files) > 0, "dist/assets/ 中没有 JS 文件"

        found_cytoscape = False
        for js_file in js_files:
            content = js_file.read_text(encoding="utf-8")
            if "cytoscape" in content.lower():
                found_cytoscape = True
                break

        assert found_cytoscape, (
            "dist 构建产物中未找到 Cytoscape.js 代码"
        )

    def test_standalone_data_loadable(self) -> None:
        """standalone.html 中内联的科技树数据可以被正确解析。"""
        content = self._read_standalone()

        # 验证关键科技节点存在
        assert '"id"' in content, "standalone.html 数据中缺少节点 id 字段"

        # 查找基础科技节点名称
        basic_tech_patterns = ["stone_tools", "fire", "wheel"]
        found_count = sum(1 for p in basic_tech_patterns if p in content)
        assert found_count >= 1, (
            f"standalone.html 数据中未找到基础科技节点: {basic_tech_patterns}"
        )

    def test_dist_data_files_valid_json(self) -> None:
        """dist/data/ 中的 JSON 数据文件格式正确。"""
        data_dir = DIST_DIR / "data"
        json_files = ["full_data.json", "domains.json", "eras.json"]

        for fname in json_files:
            fpath = data_dir / fname
            assert fpath.exists(), f"数据文件不存在: {fpath}"
            content = fpath.read_text(encoding="utf-8")
            try:
                data = json.loads(content)
                assert isinstance(data, list) or isinstance(data, dict), (
                    f"{fname} 顶层结构应为 list 或 dict"
                )
            except json.JSONDecodeError as e:
                pytest.fail(f"数据文件 {fname} JSON 格式错误: {e}")

    def test_standalone_uses_iife_format(self) -> None:
        """standalone.html 使用 IIFE 格式（而非 ES module），兼容 file:// 协议。"""
        content = self._read_standalone()

        # 确保没有 type="module" 的 script 标签（file:// 协议下 ES module 不工作）
        module_scripts = re.findall(
            r'<script[^>]+type=["\']module["\']', content
        )
        assert len(module_scripts) == 0, (
            f"standalone.html 包含 ES module script 标签: {module_scripts}，"
            f"file:// 协议下 ES module 会被浏览器拦截"
        )


# ---------------------------------------------------------------------------
# 6. 端到端完整性（综合验证）
# ---------------------------------------------------------------------------


class TestEndToEndIntegrity:
    """综合验证：dist 和 standalone 的一致性和完整性。"""

    def _read_standalone(self) -> str:
        return STANDALONE_HTML.read_text(encoding="utf-8")

    def test_dist_and_standalone_both_exist(self) -> None:
        """dist 目录和 standalone.html 同时存在。"""
        assert DIST_DIR.exists(), "dist/ 目录不存在"
        assert STANDALONE_HTML.exists(), "standalone.html 不存在"

    def test_standalone_contains_all_domain_data(self) -> None:
        """standalone.html 包含所有学科领域的节点数据。"""
        content = self._read_standalone()

        # standalone 使用 full_data.json 统一存储所有节点，节点通过 domain 字段区分学科
        assert '"data/full_data.json"' in content, (
            "standalone.html 未包含 full_data.json 数据"
        )
        expected_domains = [
            "agriculture", "astronomy", "biology", "chemistry",
            "energy", "engineering", "materials", "math",
            "medicine", "physics", "social",
        ]
        for domain in expected_domains:
            assert f'"domain": "{domain}"' in content, (
                f"standalone.html 中缺少 {domain} 学科的节点数据"
            )

    def test_vite_config_uses_relative_base(self) -> None:
        """验证 vite.config.ts 配置了相对路径 base: './'。"""
        config_path = PROJECT_ROOT / "vite.config.ts"
        assert config_path.exists(), "vite.config.ts 不存在"

        content = config_path.read_text(encoding="utf-8")
        assert "base" in content, "vite.config.ts 未配置 base 属性"
        assert "'./'" in content or '"./"' in content, (
            "vite.config.ts 中 base 未设置为 './'（相对路径）"
        )
