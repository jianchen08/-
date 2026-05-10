#!/usr/bin/env python3
"""科技树可视化应用 - 构建产物功能验证脚本

验证项目：
1. dist 目录结构完整性
2. dist/index.html 资源路径验证
3. standalone.html 完整性验证
4. standalone.html 资源独立性
5. Cytoscape.js 库可用性
6. 科技树数据正确性

运行方式: python3 verify_build.py
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(ROOT, "dist")
STANDALONE = os.path.join(ROOT, "standalone.html")

results = []


def check(name, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    results.append({"name": name, "passed": passed, "detail": detail})
    icon = "✅" if passed else "❌"
    print(f"  {icon} [{status}] {name}")
    if detail:
        print(f"      {detail}")
    return passed


def verify_dist_structure():
    """验证1: dist目录结构完整性"""
    print("\n=== 验证1: dist目录结构完整性 ===")

    # dist 目录存在
    check("dist目录存在", os.path.isdir(DIST))

    # dist/index.html 存在
    index_html = os.path.join(DIST, "index.html")
    check("dist/index.html存在", os.path.isfile(index_html))

    # assets 子目录存在
    assets_dir = os.path.join(DIST, "assets")
    check("dist/assets目录存在", os.path.isdir(assets_dir))

    # JS 文件存在
    js_files = [f for f in os.listdir(assets_dir) if f.endswith(".js")] if os.path.isdir(assets_dir) else []
    check("dist/assets包含JS文件", len(js_files) > 0, f"找到 {len(js_files)} 个JS文件: {', '.join(js_files)}")

    # CSS 文件存在
    css_files = [f for f in os.listdir(assets_dir) if f.endswith(".css")] if os.path.isdir(assets_dir) else []
    check("dist/assets包含CSS文件", len(css_files) > 0, f"找到 {len(css_files)} 个CSS文件: {', '.join(css_files)}")

    # data 目录存在
    data_dir = os.path.join(DIST, "data")
    check("dist/data目录存在", os.path.isdir(data_dir))

    # 数据文件存在
    for fname in ["full_data.json", "domains.json", "eras.json"]:
        fpath = os.path.join(data_dir, fname)
        check(f"dist/data/{fname}存在", os.path.isfile(fpath))


def verify_dist_resource_paths():
    """验证2: dist/index.html 资源路径验证"""
    print("\n=== 验证2: dist/index.html资源路径验证 ===")

    index_html = os.path.join(DIST, "index.html")
    if not os.path.isfile(index_html):
        check("dist/index.html可读", False, "文件不存在")
        return

    with open(index_html, "r", encoding="utf-8") as f:
        content = f.read()

    import re

    # 提取所有 src/href 属性值
    src_paths = re.findall(r'src="([^"]+)"', content)
    href_paths = re.findall(r'href="([^"]+)"', content)
    all_paths = src_paths + href_paths

    check("包含JS引用", len(src_paths) > 0, f"JS引用: {src_paths}")
    check("包含CSS引用", len(href_paths) > 0, f"CSS引用: {href_paths}")

    # 所有路径必须为相对路径
    absolute_paths = [p for p in all_paths if p.startswith("/")]
    check("无绝对路径（以/开头）", len(absolute_paths) == 0,
          f"绝对路径: {absolute_paths}" if absolute_paths else "全部为相对路径")

    # 不能包含 /@vite/ 等开发服务器路径
    vite_paths = [p for p in all_paths if "/@vite/" in p or "/@fs/" in p]
    check("无/@vite/开发路径", len(vite_paths) == 0,
          f"Vite路径: {vite_paths}" if vite_paths else "无开发服务器专属路径")

    # 路径应以 ./ 开头
    relative_paths = [p for p in all_paths if p.startswith("./")]
    check("资源路径以./开头", len(relative_paths) == len(all_paths),
          f"相对路径: {relative_paths}" if len(relative_paths) == len(all_paths) else f"非./路径: {[p for p in all_paths if not p.startswith('./')]}")


def verify_standalone_completeness():
    """验证3: standalone.html完整性验证"""
    print("\n=== 验证3: standalone.html完整性验证 ===")

    check("standalone.html存在", os.path.isfile(STANDALONE))

    if not os.path.isfile(STANDALONE):
        return

    with open(STANDALONE, "r", encoding="utf-8") as f:
        content = f.read()

    size_mb = os.path.getsize(STANDALONE) / (1024 * 1024)
    check("standalone.html大小合理", size_mb > 0.5,
          f"文件大小: {size_mb:.2f} MB")

    # HTML 结构完整性
    check("包含DOCTYPE", "<!DOCTYPE html>" in content or "<!doctype html>" in content)
    check("包含html标签", "<html" in content and "</html>" in content)
    check("包含head标签", "<head>" in content and "</head>" in content)
    check("包含body标签", "<body>" in content and "</body>" in content)
    check("包含root div", 'id="root"' in content)

    # 包含科技树可视化代码
    check("包含CSS样式", "<style>" in content and "app-loading" in content)
    check("包含JS代码", "<script>" in content)
    check("包含Cytoscape代码", "cytoscape" in content.lower())
    check("包含节点数据", "mat_stone_tools" in content)
    check("包含领域数据", "materials" in content and "energy" in content)
    check("包含时代数据", "prehistoric" in content)


def verify_standalone_independence():
    """验证4: standalone.html资源独立性"""
    print("\n=== 验证4: standalone.html资源独立性 ===")

    if not os.path.isfile(STANDALONE):
        check("standalone.html可读", False, "文件不存在")
        return

    with open(STANDALONE, "r", encoding="utf-8") as f:
        content = f.read()

    import re

    # CSS 应全部内联
    css_links = re.findall(r'<link[^>]*href="([^"]+\.css)"[^>]*>', content)
    check("CSS已内联（无外部CSS链接）", len(css_links) == 0,
          f"外部CSS引用: {css_links}" if css_links else "所有CSS内联在<style>标签中")

    # JS 应全部内联（无外部src引用）
    js_srcs = re.findall(r'<script[^>]*src="([^"]+)"[^>]*>', content)
    check("JS已内联（无外部JS引用）", len(js_srcs) == 0,
          f"外部JS引用: {js_srcs}" if js_srcs else "所有JS内联在<script>标签中")

    # Fetch 拦截器
    check("包含Fetch拦截器", "__originalFetch" in content or "window.fetch" in content,
          "内联数据通过fetch拦截器提供")

    # 数据文件内联
    check("节点数据内联", "full_data.json" in content)
    check("领域数据内联", "domains.json" in content)
    check("时代数据内联", "eras.json" in content)

    # 无外部HTTP服务器依赖（排除W3C命名空间URI）
    external_urls = re.findall(r'https?://[^"\'>\s]+', content)
    real_deps = [u for u in external_urls if "w3.org" not in u]
    check("无外部HTTP依赖", len(real_deps) == 0,
          f"外部URL: {real_deps}" if real_deps else "无外部HTTP依赖（W3C命名空间URI除外）")


def verify_cytoscape_availability():
    """验证5: Cytoscape.js库可用性"""
    print("\n=== 验证5: Cytoscape.js库可用性 ===")

    # 检查 dist 构建产物中是否包含 cytoscape
    main_js = os.path.join(DIST, "assets", "index-Cxi9b8Hp.js")
    if not os.path.isfile(main_js):
        # 查找主 JS 文件
        assets_dir = os.path.join(DIST, "assets")
        if os.path.isdir(assets_dir):
            js_files = [f for f in os.listdir(assets_dir) if f.endswith(".js") and f.startswith("index-")]
            if js_files:
                main_js = os.path.join(assets_dir, js_files[0])

    if os.path.isfile(main_js):
        with open(main_js, "r", encoding="utf-8") as f:
            js_content = f.read()

        check("Cytoscape库已打包到JS中", "cytoscape" in js_content.lower(),
              f"在 {os.path.basename(main_js)} 中找到 cytoscape 引用")
        check("Cytoscape dagre布局可用", "dagre" in js_content.lower(),
              "dagre 布局引擎已包含")
        check("Cytoscape cose-bilkent布局可用", "cose-bilkent" in js_content.lower() or "coseBilkent" in js_content,
              "cose-bilkent 布局引擎已包含")

    # 检查 standalone.html 中
    if os.path.isfile(STANDALONE):
        with open(STANDALONE, "r", encoding="utf-8") as f:
            sa_content = f.read()
        check("standalone.html包含Cytoscape", "cytoscape" in sa_content.lower())


def verify_tech_tree_data():
    """验证6: 科技树数据正确性"""
    print("\n=== 验证6: 科技树数据正确性 ===")

    data_dir = os.path.join(DIST, "data")

    # 验证 full_data.json
    nodes_path = os.path.join(data_dir, "full_data.json")
    if os.path.isfile(nodes_path):
        try:
            nodes = json.load(open(nodes_path, encoding="utf-8"))
            check("full_data.json可解析", True)
            check("节点数量合理", len(nodes) > 100,
                  f"共 {len(nodes)} 个科技节点")

            # 验证节点结构
            required_keys = {"id", "name", "year", "era", "domain", "prerequisites"}
            if nodes:
                node_keys = set(nodes[0].keys())
                check("节点包含必要字段", required_keys.issubset(node_keys),
                      f"节点字段: {sorted(node_keys)}")

            # 验证连接关系
            conn_count = sum(len(n.get("prerequisites", [])) for n in nodes)
            check("节点间有连接关系", conn_count > 50,
                  f"共 {conn_count} 条前置依赖关系")

            # 验证所有前置引用的节点都存在
            node_ids = {n["id"] for n in nodes}
            broken_refs = []
            for n in nodes:
                for pre in n.get("prerequisites", []):
                    if pre not in node_ids:
                        broken_refs.append((n["id"], pre))
            check("前置引用完整（无悬空引用）", len(broken_refs) == 0,
                  f"悬空引用: {broken_refs[:5]}..." if broken_refs else "所有前置引用都指向有效节点")
        except json.JSONDecodeError as e:
            check("full_data.json可解析", False, str(e))
    else:
        check("full_data.json存在", False)

    # 验证 domains.json
    domains_path = os.path.join(data_dir, "domains.json")
    if os.path.isfile(domains_path):
        try:
            domains = json.load(open(domains_path, encoding="utf-8"))
            check("domains.json可解析", True)
            check("领域数量合理", len(domains) >= 8,
                  f"共 {len(domains)} 个科技领域")
            # 每个领域有颜色
            has_colors = all("color" in d for d in domains)
            check("每个领域有颜色定义", has_colors,
                  f"领域颜色: {[d.get('color','?') for d in domains[:3]]}")
        except json.JSONDecodeError as e:
            check("domains.json可解析", False, str(e))

    # 验证 eras.json
    eras_path = os.path.join(data_dir, "eras.json")
    if os.path.isfile(eras_path):
        try:
            eras = json.load(open(eras_path, encoding="utf-8"))
            check("eras.json可解析", True)
            check("时代数量合理", len(eras) >= 5,
                  f"共 {len(eras)} 个科技时代")
        except json.JSONDecodeError as e:
            check("eras.json可解析", False, str(e))


def main():
    print("=" * 60)
    print("科技树可视化应用 - 构建产物功能验证")
    print("=" * 60)

    verify_dist_structure()
    verify_dist_resource_paths()
    verify_standalone_completeness()
    verify_standalone_independence()
    verify_cytoscape_availability()
    verify_tech_tree_data()

    # 汇总
    print("\n" + "=" * 60)
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    failed = total - passed
    print(f"验证完成: {passed}/{total} 项通过, {failed} 项失败")
    print("=" * 60)

    if failed > 0:
        print("\n失败项详情:")
        for r in results:
            if not r["passed"]:
                print(f"  ❌ {r['name']}: {r['detail']}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
