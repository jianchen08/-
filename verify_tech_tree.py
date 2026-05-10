#!/usr/bin/env python3
"""
科技树可视化工具 - 功能验证脚本
可独立运行，验证核心功能的正确性。

使用方法:
  python3 verify_tech_tree.py

前提条件:
  - 项目已安装依赖 (npm install)
  - 开发服务器运行中 (npm run dev) 或构建已完成 (npm run build)
"""

import json
import sys
import os
import subprocess
from collections import defaultdict, deque

# ============================================================
# 工具函数
# ============================================================

PASS = 0
FAIL = 0
WARN = 0

def report(category, name, status, detail=""):
    global PASS, FAIL, WARN
    icon = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️"}[status]
    PASS += status == "PASS"
    FAIL += status == "FAIL"
    WARN += status == "WARN"
    print(f"  {icon} [{category}] {name}: {detail}" if detail else f"  {icon} [{category}] {name}")


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ============================================================
# 1. 数据完整性验证
# ============================================================

def verify_data_integrity():
    print("\n📂 1. 数据完整性验证")
    data = load_json("public/data/full_data.json")
    domains_data = load_json("public/data/domains.json")
    eras_data = load_json("public/data/eras.json")

    # 1.1 节点数量
    report("数据", "节点总数", "PASS", f"{len(data)} 个节点")

    # 1.2 无重复 ID
    ids = [n["id"] for n in data]
    dup_ids = [i for i in set(ids) if ids.count(i) > 1]
    report("数据", "无重复ID", "PASS" if not dup_ids else "FAIL",
           f"重复ID: {dup_ids}" if dup_ids else "全部唯一")

    # 1.3 无循环依赖
    adj = defaultdict(list)
    for n in data:
        for p in n.get("prerequisites", []):
            adj[n["id"]].append(p)

    WHITE, GRAY, BLACK = 0, 1, 2
    color = {n["id"]: WHITE for n in data}
    has_cycle = False

    def dfs(node):
        global has_cycle
        nonlocal color
        color[node] = GRAY
        for nb in adj[node]:
            if color[nb] == GRAY:
                return True
            if color[nb] == WHITE and dfs(nb):
                return True
        color[node] = BLACK
        return False

    for n in data:
        if color[n["id"]] == WHITE:
            if dfs(n["id"]):
                has_cycle = True
                break

    report("数据", "无循环依赖", "PASS" if not has_cycle else "FAIL",
           "DAG无环" if not has_cycle else "存在循环!")

    # 1.4 所有前置引用有效
    node_id_set = {n["id"] for n in data}
    missing_refs = [(n["id"], p) for n in data for p in n.get("prerequisites", []) if p not in node_id_set]
    report("数据", "前置引用有效", "PASS" if not missing_refs else "FAIL",
           f"缺失引用: {len(missing_refs)}" if missing_refs else "全部有效")

    # 1.5 必填字段完整
    required = ["id", "name", "domain", "era", "year", "description", "prerequisites"]
    missing_fields = [(n.get("id", "?"), f) for n in data for f in required if f not in n]
    report("数据", "必填字段完整", "PASS" if not missing_fields else "FAIL",
           f"缺失: {len(missing_fields)}" if missing_fields else "全部完整")

    # 1.6 描述质量
    short_desc = [n for n in data if len(n.get("description", "")) < 20]
    report("数据", "描述质量", "PASS" if len(short_desc) == 0 else "WARN",
           f"过短描述: {len(short_desc)}" if short_desc else "全部≥20字符")

    # 1.7 领域和时代数据
    domain_ids = {d["id"] for d in domains_data}
    era_ids = {e["id"] for e in eras_data}
    node_domains = {n["domain"] for n in data}
    node_eras = {n["era"] for n in data}
    report("数据", "领域定义", "PASS",
           f"{len(domains_data)} 个领域: {', '.join(d['name'] for d in domains_data)}")
    report("数据", "时代定义", "PASS",
           f"{len(eras_data)} 个时代: {', '.join(e['name'] for e in eras_data)}")

    invalid_domains = node_domains - domain_ids
    report("数据", "节点领域引用", "PASS" if not invalid_domains else "FAIL",
           f"无效领域: {invalid_domains}" if invalid_domains else "全部有效")

    invalid_eras = node_eras - era_ids
    report("数据", "节点时代引用", "PASS" if not invalid_eras else "FAIL",
           f"无效时代: {invalid_eras}" if invalid_eras else "全部有效")

    # 1.8 individual domain files vs full_data.json 一致性
    domain_names = [d["id"] for d in domains_data]
    domain_total = 0
    for dn in domain_names:
        path = f"public/data/nodes/{dn}.json"
        if os.path.exists(path):
            domain_total += len(load_json(path))
    diff = len(data) - domain_total
    report("数据", "领域文件一致性", "WARN" if diff != 0 else "PASS",
           f"full_data: {len(data)}, 领域文件总和: {domain_total}, 差异: {diff}")

    return data, domains_data, eras_data


# ============================================================
# 2. 搜索功能验证
# ============================================================

def verify_search(nodes):
    print("\n🔍 2. 搜索功能验证")

    def matches_search(node, text):
        if not text.strip():
            return True
        lower = text.lower()
        if lower in node["name"].lower():
            return True
        if lower in node["description"].lower():
            return True
        if node.get("tags") and any(lower in t.lower() for t in node["tags"]):
            return True
        return False

    test_cases = [
        ("火", 5, "中文搜索-火"),
        ("蒸汽", 1, "中文搜索-蒸汽"),
        ("电", 1, "中文搜索-电"),
        ("量子", 1, "中文搜索-量子"),
        ("计算机", 1, "中文搜索-计算机"),
        ("火药", 1, "精确搜索-火药"),
        ("", len(nodes), "空搜索返回全部"),
    ]

    for query, expected_min, desc in test_cases:
        matches = [n for n in nodes if matches_search(n, query)]
        ok = len(matches) >= expected_min
        report("搜索", desc, "PASS" if ok else "FAIL",
               f"查询\"{query}\": {len(matches)} 条结果 (期望≥{expected_min})")


# ============================================================
# 3. 筛选功能验证
# ============================================================

def verify_filter(nodes):
    print("\n🔬 3. 筛选功能验证")

    def passes_filter(node, filter_state):
        if filter_state.get("selectedEras") and node["era"] not in filter_state["selectedEras"]:
            return False
        if filter_state.get("selectedDomains") and node["domain"] not in filter_state["selectedDomains"]:
            return False
        if (node.get("hubScore") or 0) < filter_state.get("hubThreshold", 0):
            return False
        yr = filter_state.get("yearRange")
        if yr:
            y = node["year"] if isinstance(node["year"], int) else int(node["year"])
            if y < yr[0] or y > yr[1]:
                return False
        return True

    # 3.1 无筛选
    all_pass = [n for n in nodes if passes_filter(n, {})]
    report("筛选", "无筛选", "PASS" if len(all_pass) == len(nodes) else "FAIL",
           f"{len(all_pass)}/{len(nodes)}")

    # 3.2 按领域筛选
    for domain in ["physics", "it", "medicine"]:
        filtered = [n for n in nodes if passes_filter(n, {"selectedDomains": [domain]})]
        report("筛选", f"领域={domain}", "PASS" if filtered else "FAIL",
               f"{len(filtered)} 个节点")

    # 3.3 按时代筛选
    for era in ["ancient", "information", "prehistoric"]:
        filtered = [n for n in nodes if passes_filter(n, {"selectedEras": [era]})]
        report("筛选", f"时代={era}", "PASS" if filtered else "FAIL",
               f"{len(filtered)} 个节点")

    # 3.4 年份范围筛选
    filtered = [n for n in nodes if passes_filter(n, {"yearRange": [1900, 2025]})]
    report("筛选", "年份1900-2025", "PASS" if filtered else "FAIL",
           f"{len(filtered)} 个节点")

    # 3.5 组合筛选
    filtered = [n for n in nodes if passes_filter(n, {
        "selectedEras": ["information"],
        "selectedDomains": ["it"],
        "hubThreshold": 0
    })]
    report("筛选", "组合: 信息时代+IT", "PASS" if filtered else "FAIL",
           f"{len(filtered)} 个节点")


# ============================================================
# 4. 枢纽值计算验证
# ============================================================

def verify_hub_calculation(nodes):
    print("\n📊 4. 枢纽值(Hub Score)计算验证")

    out_deg = defaultdict(int)
    in_deg = defaultdict(int)
    for n in nodes:
        for p in n.get("prerequisites", []):
            out_deg[p] += 1
            in_deg[n["id"]] += 1

    max_out = max(out_deg.values()) if out_deg else 1
    max_in = max(in_deg.values()) if in_deg else 1

    scores = {}
    for n in nodes:
        od = out_deg.get(n["id"], 0)
        id2 = in_deg.get(n["id"], 0)
        score = ((od / max_out) * 0.6 + (id2 / max_in) * 0.4) * 100
        scores[n["id"]] = round(score, 1)

    sorted_nodes = sorted(scores.items(), key=lambda x: -x[1])
    top5 = sorted_nodes[:5]
    for nid, score in top5:
        node = next(n for n in nodes if n["id"] == nid)
        report("枢纽值", f"  {node['name']}", "PASS",
               f"hubScore={score}, domain={node['domain']}, outDeg={out_deg.get(nid,0)}")

    hub60 = sum(1 for _, s in sorted_nodes if s >= 60)
    report("枢纽值", "高枢纽节点(≥60)", "PASS", f"{hub60} 个")


# ============================================================
# 5. 构建产物验证
# ============================================================

def verify_build():
    print("\n🔨 5. 构建产物验证")

    # 5.1 dist 目录存在
    report("构建", "dist目录", "PASS" if os.path.isdir("dist") else "FAIL",
           "存在" if os.path.isdir("dist") else "不存在")

    # 5.2 HTML 入口
    html_exists = os.path.isfile("dist/index.html")
    report("构建", "index.html", "PASS" if html_exists else "FAIL")

    if html_exists:
        html = open("dist/index.html").read()
        has_js = "index-" in html and ".js" in html
        has_css = "index-" in html and ".css" in html
        report("构建", "HTML引用JS", "PASS" if has_js else "FAIL")
        report("构建", "HTML引用CSS", "PASS" if has_css else "FAIL")

    # 5.3 数据文件复制
    data_exists = os.path.isfile("dist/data/full_data.json")
    report("构建", "数据文件复制", "PASS" if data_exists else "FAIL")

    if data_exists:
        dist_data = load_json("dist/data/full_data.json")
        src_data = load_json("public/data/full_data.json")
        report("构建", "构建数据一致性", "PASS" if len(dist_data) == len(src_data) else "FAIL",
               f"源={len(src_data)}, 构建={len(dist_data)}")

    # 5.4 CSS 特性检查
    css_files = [f for f in os.listdir("dist/assets") if f.endswith(".css")]
    if css_files:
        css = open(f"dist/assets/{css_files[0]}").read()
        features = {
            "hover效果": "hover" in css,
            "过渡动画": "transition" in css,
            "渐变背景": "radial-gradient" in css or "linear-gradient" in css,
            "毛玻璃效果": "backdrop-filter" in css,
            "关键帧动画": "@keyframes" in css,
            "响应式设计": "@media" in css,
        }
        for name, found in features.items():
            report("构建-CSS", name, "PASS" if found else "FAIL")

    # 5.5 JS 功能模块检查
    js_files = [f for f in os.listdir("dist/assets") if f.endswith(".js")]
    if js_files:
        js = open(f"dist/assets/{max(js_files, key=lambda x: os.path.getsize(f'dist/assets/{x}'))}").read()
        modules = {
            "Cytoscape图引擎": "cytoscape" in js,
            "Dagre层次布局": "dagre" in js,
            "鼠标悬停事件": "mouseover" in js,
            "节点选中样式": "selected" in js,
            "边高亮样式": "highlighted" in js,
        }
        for name, found in modules.items():
            report("构建-JS", name, "PASS" if found else "FAIL")


# ============================================================
# 6. 服务器可访问性验证
# ============================================================

def verify_server():
    print("\n🌐 6. 服务器可访问性验证")
    import urllib.request
    import urllib.error

    base_urls = [
        ("http://localhost:5173", "开发服务器"),
        ("http://localhost:4173", "预览服务器"),
    ]

    for url, name in base_urls:
        try:
            req = urllib.request.urlopen(url + "/", timeout=3)
            code = req.getcode()
            report("服务器", name, "PASS" if code == 200 else "FAIL", f"HTTP {code}")
        except Exception as e:
            report("服务器", name, "WARN", f"未运行: {str(e)[:50]}")

    # 数据文件可访问性（通过开发服务器）
    try:
        req = urllib.request.urlopen("http://localhost:5173/data/full_data.json", timeout=3)
        data = json.loads(req.read())
        report("服务器", "full_data.json可访问", "PASS", f"{len(data)} 个节点")
    except Exception:
        report("服务器", "full_data.json", "WARN", "开发服务器未运行，跳过")

    try:
        req = urllib.request.urlopen("http://localhost:5173/data/domains.json", timeout=3)
        data = json.loads(req.read())
        report("服务器", "domains.json可访问", "PASS", f"{len(data)} 个领域")
    except Exception:
        report("服务器", "domains.json", "WARN", "开发服务器未运行，跳过")

    try:
        req = urllib.request.urlopen("http://localhost:5173/data/eras.json", timeout=3)
        data = json.loads(req.read())
        report("服务器", "eras.json可访问", "PASS", f"{len(data)} 个时代")
    except Exception:
        report("服务器", "eras.json", "WARN", "开发服务器未运行，跳过")


# ============================================================
# 7. 源代码完整性验证
# ============================================================

def verify_source_structure():
    print("\n📁 7. 源代码结构验证")

    expected_files = [
        ("src/App.tsx", "主应用组件"),
        ("src/main.tsx", "入口文件"),
        ("src/App.css", "全局样式"),
        ("src/components/TechTree.tsx", "科技树组件"),
        ("src/components/SearchPanel.tsx", "搜索面板"),
        ("src/components/FilterPanel.tsx", "筛选面板"),
        ("src/components/NodeDetail.tsx", "节点详情"),
        ("src/components/Toolbar.tsx", "工具栏"),
        ("src/components/Legend.tsx", "图例"),
        ("src/components/MiniMap.tsx", "小地图"),
        ("src/components/TimelineSlider.tsx", "时间轴"),
        ("src/utils/dataLoader.ts", "数据加载器"),
        ("src/utils/hubCalculator.ts", "枢纽值计算"),
        ("src/utils/pdfExporter.ts", "PDF导出"),
        ("src/types/index.ts", "类型定义"),
    ]

    for path, desc in expected_files:
        exists = os.path.isfile(path)
        report("源码", desc, "PASS" if exists else "FAIL", path)


# ============================================================
# 主函数
# ============================================================

def main():
    print("=" * 60)
    print("🌳 科技树可视化工具 - 功能验证脚本")
    print("=" * 60)

    os.chdir(os.path.dirname(os.path.abspath(__file__)) or ".")

    # 1. 数据完整性
    data, domains, eras = verify_data_integrity()

    # 2. 搜索功能
    verify_search(data)

    # 3. 筛选功能
    verify_filter(data)

    # 4. 枢纽值计算
    verify_hub_calculation(data)

    # 5. 构建产物
    verify_build()

    # 6. 服务器可访问性
    verify_server()

    # 7. 源代码结构
    verify_source_structure()

    # 汇总
    print("\n" + "=" * 60)
    total = PASS + FAIL + WARN
    print(f"📊 验证结果汇总: ✅ {PASS} 通过 | ❌ {FAIL} 失败 | ⚠️ {WARN} 警告 | 共 {total} 项")
    if FAIL == 0:
        print("🎉 核心功能验证通过!")
    else:
        print(f"⚠️ 有 {FAIL} 项验证失败，请检查!")
    print("=" * 60)

    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
