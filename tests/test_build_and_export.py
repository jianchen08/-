"""
科技树可视化项目 - 构建与导出功能测试验证。

测试范围：
1. 构建测试：npm run build 成功，产物在 dist/ 目录
2. TypeScript 类型检查：tsc --noEmit 无错误
3. 构建产物验证：dist/index.html 存在，引用路径为相对路径
4. 离线运行验证：构建产物资源引用使用相对路径，可直接打开 index.html 运行
"""
from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

import pytest

# 项目根目录（tests/ 的上一级）
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DIST_DIR = PROJECT_ROOT / "dist"
SRC_DIR = PROJECT_ROOT / "src"


# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------


def _run_cmd(cmd: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    """在项目根目录执行命令并返回结果。"""
    return subprocess.run(
        cmd,
        shell=True,
        cwd=cwd or PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=180,
    )


def _find_js_files(dist_dir: Path) -> list[Path]:
    """查找 dist/assets/ 下所有 JS 文件。"""
    assets_dir = dist_dir / "assets"
    if not assets_dir.exists():
        return []
    return list(assets_dir.glob("*.js"))


# ---------------------------------------------------------------------------
# 1. 构建测试
# ---------------------------------------------------------------------------


class TestBuild:
    """构建相关测试。"""

    def test_npm_build_succeeds(self) -> None:
        """验证 npm run build 构建成功且无错误。"""
        result = _run_cmd("npm run build")
        assert result.returncode == 0, (
            f"构建失败，退出码: {result.returncode}\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )
        # 确认构建日志中包含成功标识
        assert "built in" in result.stdout, f"构建输出中未找到 'built in' 标识:\n{result.stdout}"

    def test_dist_directory_exists(self) -> None:
        """验证构建后 dist/ 目录存在。"""
        assert DIST_DIR.exists(), f"构建产物目录不存在: {DIST_DIR}"

    def test_dist_index_html_exists(self) -> None:
        """验证 dist/index.html 存在。"""
        index_html = DIST_DIR / "index.html"
        assert index_html.exists(), f"构建产物 index.html 不存在: {index_html}"

    def test_dist_assets_exist(self) -> None:
        """验证 dist/assets/ 目录中有 JS 和 CSS 文件。"""
        assets_dir = DIST_DIR / "assets"
        assert assets_dir.exists(), f"assets 目录不存在: {assets_dir}"

        js_files = list(assets_dir.glob("*.js"))
        css_files = list(assets_dir.glob("*.css"))

        assert len(js_files) > 0, "assets 目录中没有 JS 文件"
        assert len(css_files) > 0, "assets 目录中没有 CSS 文件"

    def test_dist_data_directory_exists(self) -> None:
        """验证 dist/data/ 目录存在（数据文件被正确复制）。"""
        data_dir = DIST_DIR / "data"
        assert data_dir.exists(), f"data 目录不存在: {data_dir}"

        # 验证关键数据文件存在
        expected_files = ["full_data.json", "domains.json", "eras.json"]
        for fname in expected_files:
            fpath = data_dir / fname
            assert fpath.exists(), f"数据文件不存在: {fpath}"


# ---------------------------------------------------------------------------
# 2. TypeScript 类型检查
# ---------------------------------------------------------------------------


class TestTypeCheck:
    """TypeScript 类型检查测试。"""

    def test_tsc_no_errors(self) -> None:
        """验证 tsc --noEmit 无类型错误。"""
        result = _run_cmd("npx tsc --noEmit")
        assert result.returncode == 0, (
            f"TypeScript 类型检查失败，退出码: {result.returncode}\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )
        # 类型检查成功时应该没有输出
        assert result.stdout.strip() == "", (
            f"类型检查有输出（可能有错误）:\n{result.stdout}"
        )


# ---------------------------------------------------------------------------
# 3. 构建产物路径验证
# ---------------------------------------------------------------------------


class TestBuildArtifacts:
    """构建产物路径和内容验证。"""

    def test_index_html_uses_relative_paths(self) -> None:
        """验证 dist/index.html 中的资源引用使用相对路径（./）。"""
        index_html = DIST_DIR / "index.html"
        content = index_html.read_text(encoding="utf-8")

        # 检查 script 标签的 src 属性
        script_matches = re.findall(r'<script[^>]+src="([^"]+)"', content)
        assert len(script_matches) > 0, "index.html 中未找到 script 标签"
        for src in script_matches:
            assert src.startswith("./"), (
                f"script src 不是相对路径: {src}（应以 './' 开头）"
            )
            # 绝对路径检查：不应以 / 开头（除非是 ./）
            assert not src.startswith("/"), (
                f"script src 使用了绝对路径: {src}"
            )

        # 检查 link 标签的 href 属性
        link_matches = re.findall(r'<link[^>]+href="([^"]+)"', content)
        assert len(link_matches) > 0, "index.html 中未找到 link 标签"
        for href in link_matches:
            assert href.startswith("./"), (
                f"link href 不是相对路径: {href}（应以 './' 开头）"
            )
            assert not href.startswith("/"), (
                f"link href 使用了绝对路径: {href}"
            )

    def test_no_absolute_paths_in_index_html(self) -> None:
        """验证 index.html 中不包含以 / 开头的绝对路径引用。"""
        index_html = DIST_DIR / "index.html"
        content = index_html.read_text(encoding="utf-8")

        # 查找所有 src= 和 href= 中的路径
        all_paths = re.findall(r'(?:src|href)="([^"]+)"', content)
        for path in all_paths:
            # 允许 ./ 开头的相对路径，不允许 / 开头的绝对路径
            if path.startswith("/"):
                pytest.fail(f"发现绝对路径引用: {path}")

    def test_js_data_paths_are_relative(self) -> None:
        """验证 JS 构建产物中数据文件路径使用相对路径（不包含绝对 /data/）。"""
        js_files = _find_js_files(DIST_DIR)
        assert len(js_files) > 0, "未找到 JS 构建产物"

        for js_file in js_files:
            content = js_file.read_text(encoding="utf-8")

            # 查找数据文件路径引用
            # 不应出现 "/data/xxx.json"（绝对路径），应该是 "./data/xxx.json" 或 "data/xxx.json"
            absolute_data_refs = re.findall(r'"/data/(?:full_data|domains|eras)\.json"', content)
            assert len(absolute_data_refs) == 0, (
                f"JS 文件 {js_file.name} 中发现绝对路径数据引用: {absolute_data_refs}\n"
                f"应使用相对路径（如 ./data/xxx.json）以确保离线可用"
            )

    def test_data_files_valid_json(self) -> None:
        """验证 dist/data/ 中的 JSON 数据文件格式正确。"""
        data_dir = DIST_DIR / "data"
        json_files = ["full_data.json", "domains.json", "eras.json"]

        for fname in json_files:
            fpath = data_dir / fname
            assert fpath.exists(), f"数据文件不存在: {fpath}"
            content = fpath.read_text(encoding="utf-8")
            try:
                json.loads(content)
            except json.JSONDecodeError as e:
                pytest.fail(f"数据文件 {fname} JSON 格式错误: {e}")


# ---------------------------------------------------------------------------
# 4. 离线运行验证
# ---------------------------------------------------------------------------


class TestOfflineCapability:
    """离线运行能力验证。"""

    def test_all_resource_references_are_relative(self) -> None:
        """验证所有资源引用均为相对路径，确保可直接打开 index.html 运行。"""
        index_html = DIST_DIR / "index.html"
        content = index_html.read_text(encoding="utf-8")

        # 所有外部资源引用
        resource_refs = re.findall(r'(?:src|href)="([^"]+)"', content)

        for ref in resource_refs:
            # 必须以 ./ 开头（相对路径）
            assert ref.startswith("./"), (
                f"资源引用不是相对路径: {ref}，离线打开时将无法加载"
            )
            # 不应包含 http:// 或 https://（外部 CDN 依赖）
            assert not ref.startswith("http://") and not ref.startswith("https://"), (
                f"资源引用指向外部 URL: {ref}，离线时无法访问"
            )

    def test_no_external_cdn_dependencies(self) -> None:
        """验证构建产物不依赖外部 CDN。"""
        index_html = DIST_DIR / "index.html"
        content = index_html.read_text(encoding="utf-8")

        # 检查是否有外部 URL 引用
        external_urls = re.findall(r'https?://[^\s"]+', content)
        assert len(external_urls) == 0, (
            f"index.html 引用了外部资源，离线时无法访问: {external_urls}"
        )

    def test_dist_is_self_contained(self) -> None:
        """验证 dist/ 目录是自包含的：index.html 引用的所有文件都存在于 dist/ 内。"""
        index_html = DIST_DIR / "index.html"
        content = index_html.read_text(encoding="utf-8")

        # 提取所有相对路径引用
        resource_refs = re.findall(r'(?:src|href)="(\./[^"]+)"', content)

        for ref in resource_refs:
            # 将 ./ 映射到 dist/ 目录
            relative_path = ref.lstrip("./")
            full_path = DIST_DIR / relative_path
            assert full_path.exists(), (
                f"index.html 引用的文件在 dist/ 中不存在: {ref} -> {full_path}"
            )

    def test_js_bundle_contains_base_url(self) -> None:
        """验证 JS 产物中使用了 BASE_URL（值为 './'）构建数据路径。"""
        js_files = _find_js_files(DIST_DIR)
        main_js = None
        for f in js_files:
            if f.stat().st_size > 100_000:
                main_js = f
                break

        assert main_js is not None, "未找到主 JS bundle 文件"
        content = main_js.read_text(encoding="utf-8")

        # 验证使用了 BASE_URL 变量构建路径（Vite 会将 import.meta.env.BASE_URL 编译为 "./"）
        # 构建产物中应该包含 "./data/" 的路径模式
        assert re.search(r'"\./"[\s+,;].*data/', content) is not None or \
               re.search(r'data/(?:full_data|domains|eras)\.json', content) is not None, (
            "JS bundle 中未找到使用 BASE_URL 构建的数据路径，离线时可能无法加载数据"
        )


# ---------------------------------------------------------------------------
# 5. 源码验证
# ---------------------------------------------------------------------------


class TestSourceCode:
    """源代码结构和配置验证。"""

    def test_vite_config_has_relative_base(self) -> None:
        """验证 vite.config.ts 配置了相对路径 base: './'。"""
        config_path = PROJECT_ROOT / "vite.config.ts"
        assert config_path.exists(), f"vite.config.ts 不存在: {config_path}"

        content = config_path.read_text(encoding="utf-8")
        assert "base:" in content or "base :" in content, (
            "vite.config.ts 中未配置 base 属性"
        )
        assert "'./'" in content or '"./"' in content, (
            "vite.config.ts 中 base 未设置为 './'（相对路径）"
        )

    def test_dataloader_uses_base_url(self) -> None:
        """验证 dataLoader.ts 使用 import.meta.env.BASE_URL 构建路径。"""
        loader_path = SRC_DIR / "utils" / "dataLoader.ts"
        assert loader_path.exists(), f"dataLoader.ts 不存在: {loader_path}"

        content = loader_path.read_text(encoding="utf-8")
        assert "import.meta.env.BASE_URL" in content, (
            "dataLoader.ts 未使用 import.meta.env.BASE_URL，离线时可能无法加载数据"
        )

    def test_pdf_exporter_exists(self) -> None:
        """验证 PDF 导出工具模块存在。"""
        exporter_path = SRC_DIR / "utils" / "pdfExporter.ts"
        assert exporter_path.exists(), f"pdfExporter.ts 不存在: {exporter_path}"

    def test_pdf_exporter_exports_functions(self) -> None:
        """验证 pdfExporter.ts 导出了视口导出和全景导出函数。"""
        exporter_path = SRC_DIR / "utils" / "pdfExporter.ts"
        content = exporter_path.read_text(encoding="utf-8")

        assert "export async function exportViewport" in content, (
            "pdfExporter.ts 未导出 exportViewport 函数"
        )
        assert "export async function exportFullView" in content, (
            "pdfExporter.ts 未导出 exportFullView 函数"
        )

    def test_toolbar_component_has_export_props(self) -> None:
        """验证 Toolbar 组件包含导出相关的 props。"""
        toolbar_path = SRC_DIR / "components" / "Toolbar.tsx"
        assert toolbar_path.exists(), f"Toolbar.tsx 不存在: {toolbar_path}"

        content = toolbar_path.read_text(encoding="utf-8")
        assert "onExportViewport" in content, "Toolbar 组件未包含 onExportViewport prop"
        assert "onExportFullView" in content, "Toolbar 组件未包含 onExportFullView prop"
        assert "exporting" in content, "Toolbar 组件未包含 exporting prop"

    def test_app_integrates_export(self) -> None:
        """验证 App.tsx 集成了导出功能。"""
        app_path = SRC_DIR / "App.tsx"
        assert app_path.exists(), f"App.tsx 不存在: {app_path}"

        content = app_path.read_text(encoding="utf-8")
        assert "exportViewport" in content, "App.tsx 未导入或使用 exportViewport"
        assert "exportFullView" in content, "App.tsx 未导入或使用 exportFullView"
        assert "handleExportViewport" in content or "onExportViewport" in content, (
            "App.tsx 未集成视口导出处理"
        )
        assert "handleExportFullView" in content or "onExportFullView" in content, (
            "App.tsx 未集全景导出处理"
        )

    def test_vite_env_d_exists(self) -> None:
        """验证 vite-env.d.ts 类型声明文件存在。"""
        env_d_path = SRC_DIR / "vite-env.d.ts"
        assert env_d_path.exists(), (
            f"vite-env.d.ts 不存在: {env_d_path}，"
            f"TypeScript 无法识别 import.meta.env 类型"
        )
