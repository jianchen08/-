#!/usr/bin/env python3
"""
科技树前置条件修正结果 - 全面验证脚本
验证 full_data.json 中所有节点的 prerequisites 数据质量
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

DATA_FILE = Path("public/data/full_data.json")

# ===========================================================================
# 加载数据
# ===========================================================================
def load_data():
    assert DATA_FILE.exists(), f"数据文件不存在: {DATA_FILE}"
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert isinstance(data, list), "数据文件顶层应为 JSON 数组"
    assert len(data) > 0, "数据文件为空"
    return data

def build_node_map(nodes):
    mapping = {}
    for node in nodes:
        assert node["id"] not in mapping, f"存在重复节点 ID: {node['id']}"
        mapping[node["id"]] = node
    return mapping

# ===========================================================================
# 1. 数据完整性测试
# ===========================================================================
def test_data_integrity(nodes, node_map, all_ids):
    print("\n" + "="*70)
    print("【测试1】数据完整性测试")
    print("="*70)
    passed = True
    issues = []

    # 1.1 所有节点都有 prerequisites 字段
    missing_field = [n["id"] for n in nodes if "prerequisites" not in n]
    if missing_field:
        msg = f"以下节点缺少 prerequisites 字段: {missing_field}"
        print(f"  ✗ {msg}")
        issues.append(msg)
        passed = False
    else:
        print(f"  ✓ 所有 {len(nodes)} 个节点都有 prerequisites 字段")

    # 1.2 prerequisites 是列表类型
    bad_type = [n["id"] for n in nodes if not isinstance(n.get("prerequisites"), list)]
    if bad_type:
        msg = f"以下节点的 prerequisites 不是列表: {bad_type}"
        print(f"  ✗ {msg}")
        issues.append(msg)
        passed = False
    else:
        print(f"  ✓ 所有节点的 prerequisites 都是列表类型")

    # 1.3 prerequisites 元素都是字符串
    bad_elem = []
    for node in nodes:
        for p in node["prerequisites"]:
            if not isinstance(p, str):
                bad_elem.append(f"{node['id']}[{node['prerequisites'].index(p)}]")
    if bad_elem:
        msg = f"以下节点 prerequisites 中有非字符串元素: {bad_elem}"
        print(f"  ✗ {msg}")
        issues.append(msg)
        passed = False
    else:
        print(f"  ✓ 所有 prerequisites 元素都是字符串")

    # 1.4 没有空字符串
    empty_str_nodes = []
    for node in nodes:
        for p in node["prerequisites"]:
            if isinstance(p, str) and p.strip() == "":
                empty_str_nodes.append(node["id"])
                break
    if empty_str_nodes:
        msg = f"以下节点 prerequisites 中有空字符串: {empty_str_nodes}"
        print(f"  ✗ {msg}")
        issues.append(msg)
        passed = False
    else:
        print(f"  ✓ 所有 prerequisites 中没有空字符串")

    # 1.5 所有引用的 ID 存在
    missing_refs = {}
    for node in nodes:
        for p in node["prerequisites"]:
            if p not in all_ids:
                missing_refs.setdefault(node["id"], []).append(p)
    if missing_refs:
        lines = []
        for nid, refs in missing_refs.items():
            lines.append(f"  {nid} -> {refs}")
        msg = f"以下节点引用了不存在的 ID:\n" + "\n".join(lines)
        print(f"  ✗ {msg}")
        issues.append(msg)
        passed = False
    else:
        print(f"  ✓ 所有引用的 ID 在数据文件中均存在")

    # 1.6 没有自引用
    self_refs = [n["id"] for n in nodes if n["id"] in n.get("prerequisites", [])]
    if self_refs:
        msg = f"以下节点自引用: {self_refs}"
        print(f"  ✗ {msg}")
        issues.append(msg)
        passed = False
    else:
        print(f"  ✓ 没有节点自引用")

    # 1.7 没有重复项
    duped = []
    for node in nodes:
        prereqs = node["prerequisites"]
        if len(prereqs) != len(set(prereqs)):
            duped.append(node["id"])
    if duped:
        msg = f"以下节点 prerequisites 中有重复项: {duped}"
        print(f"  ✗ {msg}")
        issues.append(msg)
        passed = False
    else:
        print(f"  ✓ 所有 prerequisites 列表无重复项")

    status = "通过" if passed else "失败"
    print(f"  >>> 数据完整性测试: {status}")
    return passed, issues

# ===========================================================================
# 2. 前置链可追溯性测试
# ===========================================================================
def trace_chain(start_id, node_map, all_ids):
    """BFS 从 start_id 往回追溯全部前置链"""
    visited = []
    reachable = set()
    queue = [start_id]
    parent_map = {start_id: None}

    while queue:
        current = queue.pop(0)
        if current in reachable:
            continue
        reachable.add(current)
        visited.append(current)
        node = node_map.get(current)
        if node is None:
            continue
        for p in node["prerequisites"]:
            if p not in reachable:
                queue.append(p)
                if p not in parent_map:
                    parent_map[p] = current

    # 沿第一条前置链到根
    path = []
    cur = start_id
    while cur is not None:
        path.append(cur)
        node = node_map.get(cur)
        if node is None or not node["prerequisites"]:
            break
        cur = node["prerequisites"][0]

    return visited, reachable, path

def test_chain(start_id, label, node_map, all_ids, expected_domains=None):
    """测试单条前置链"""
    print(f"\n  --- {label} ({start_id}) ---")
    visited, reachable, path = trace_chain(start_id, node_map, all_ids)

    passed = True
    issues = []

    # 链条中每个节点必须存在
    for nid in visited:
        if nid not in all_ids:
            msg = f"{label}: 链条中引用了不存在的节点: {nid}"
            print(f"    ✗ {msg}")
            issues.append(msg)
            passed = False

    # 必须能追溯到基础节点
    root_nodes = [nid for nid in reachable if not node_map[nid]["prerequisites"]]
    if not root_nodes:
        msg = f"{label}: 前置链未能追溯到任何基础节点"
        print(f"    ✗ {msg}")
        issues.append(msg)
        passed = False
    else:
        print(f"    ✓ 追溯到 {len(root_nodes)} 个基础节点: {root_nodes}")

    # 链深度
    print(f"    ✓ 链深度: {len(path)} 层")
    print(f"    ✓ 可达节点数: {len(reachable)}")
    print(f"    ✓ 主链路: {' → '.join(path[:6])}{'...' if len(path) > 6 else ''}")

    # 验证跨域
    domains_reached = {node_map[nid]["domain"] for nid in reachable}
    print(f"    ✓ 涉及域: {domains_reached}")

    if expected_domains:
        for dom in expected_domains:
            if dom not in domains_reached:
                msg = f"{label}: 前置链应包含 {dom} 域，实际: {domains_reached}"
                print(f"    ✗ {msg}")
                issues.append(msg)
                passed = False
            else:
                print(f"    ✓ 包含期望域: {dom}")

    # 链深度至少4层
    if len(path) < 4:
        msg = f"{label}: 前置链深度不足 ({len(path)} 层 < 4)"
        print(f"    ✗ {msg}")
        issues.append(msg)
        passed = False

    status = "通过" if passed else "失败"
    print(f"    >>> {label}: {status}")
    return passed, issues

def test_prerequisite_chain_traceability(node_map, all_ids):
    print("\n" + "="*70)
    print("【测试2】前置链可追溯性测试")
    print("="*70)
    all_passed = True
    all_issues = []

    chains = [
        ("it_ai_agent", "AI Agent → 基础理论", None),
        ("eng_reusable_rocket", "可回收火箭 → 基础材料/制造", ["materials"]),
        ("eng_jet_engine", "先进战斗机(喷气发动机) → 基础航空/材料", ["materials"]),
        ("energy_nuclear_fusion_reactor", "可控核聚变 → 基础物理/材料", ["physics", "materials"]),
        ("energy_solar_cell", "高效光伏(太阳能电池) → 基础材料/半导体", ["materials"]),
    ]

    for start_id, label, expected_domains in chains:
        p, iss = test_chain(start_id, label, node_map, all_ids, expected_domains)
        if not p:
            all_passed = False
            all_issues.extend(iss)

    status = "通过" if all_passed else "失败"
    print(f"\n  >>> 前置链可追溯性测试: {status}")
    return all_passed, all_issues

# ===========================================================================
# 3. 三类前置覆盖测试
# ===========================================================================
def get_domains_of_prereqs(node, node_map):
    domains = set()
    for pid in node["prerequisites"]:
        pnode = node_map.get(pid)
        if pnode:
            domains.add(pnode["domain"])
    return domains

def test_three_category_coverage(nodes, node_map):
    print("\n" + "="*70)
    print("【测试3】三类前置覆盖测试（理论/工程/组织-社会）")
    print("="*70)
    all_passed = True
    all_issues = []

    # 3.1 AI Agent 应有跨域前置
    node = node_map.get("it_ai_agent")
    if node:
        prereq_domains = get_domains_of_prereqs(node, node_map)
        print(f"  AI Agent 前置域: {prereq_domains}")
        if len(prereq_domains) < 1:
            msg = "AI Agent 前置域过于单一"
            print(f"  ✗ {msg}")
            all_issues.append(msg)
            all_passed = False
        else:
            print(f"  ✓ AI Agent 前置覆盖 {len(prereq_domains)} 个域")

    # 3.2 可控核聚变应涵盖物理理论、工程、材料
    node = node_map.get("energy_nuclear_fusion_reactor")
    if node:
        prereq_domains = get_domains_of_prereqs(node, node_map)
        print(f"  可控核聚变 前置域: {prereq_domains}")
        if len(prereq_domains) < 2:
            msg = f"可控核聚变前置域过于单一 (期望>=2): {prereq_domains}"
            print(f"  ✗ {msg}")
            all_issues.append(msg)
            all_passed = False
        if "physics" not in prereq_domains:
            msg = f"可控核聚变应有物理理论前置: {prereq_domains}"
            print(f"  ✗ {msg}")
            all_issues.append(msg)
            all_passed = False
        else:
            print(f"  ✓ 可控核聚变涵盖物理域")

    # 3.3 可回收火箭应涵盖工程和材料
    node = node_map.get("eng_reusable_rocket")
    if node:
        prereq_domains = get_domains_of_prereqs(node, node_map)
        print(f"  可回收火箭 前置域: {prereq_domains}")
        if len(prereq_domains) < 2:
            msg = f"可回收火箭前置域过于单一 (期望>=2): {prereq_domains}"
            print(f"  ✗ {msg}")
            all_issues.append(msg)
            all_passed = False
        if "materials" not in prereq_domains:
            msg = f"可回收火箭应有材料类前置: {prereq_domains}"
            print(f"  ✗ {msg}")
            all_issues.append(msg)
            all_passed = False
        else:
            print(f"  ✓ 可回收火箭涵盖材料域")

    # 3.4 太阳能电池应有材料或物理前置
    node = node_map.get("energy_solar_cell")
    if node:
        prereq_domains = get_domains_of_prereqs(node, node_map)
        print(f"  太阳能电池 前置域: {prereq_domains}")
        if "materials" not in prereq_domains and "physics" not in prereq_domains:
            msg = f"太阳能电池应有材料或物理前置: {prereq_domains}"
            print(f"  ✗ {msg}")
            all_issues.append(msg)
            all_passed = False
        else:
            print(f"  ✓ 太阳能电池涵盖材料/物理域")

    # 3.5 无人机应有 IT 通信前置
    node = node_map.get("eng_drone")
    if node:
        prereq_domains = get_domains_of_prereqs(node, node_map)
        print(f"  无人机 前置域: {prereq_domains}")
        if "it" not in prereq_domains:
            msg = f"无人机技术应有 IT 通信前置: {prereq_domains}"
            print(f"  ✗ {msg}")
            all_issues.append(msg)
            all_passed = False
        else:
            print(f"  ✓ 无人机涵盖 IT 域")

    # 3.6 跨域前置总体占比
    cross_domain_count = 0
    for node in nodes:
        prereq_domains = get_domains_of_prereqs(node, node_map)
        other_domains = prereq_domains - {node["domain"]}
        if other_domains:
            cross_domain_count += 1
    ratio = cross_domain_count / len(nodes)
    print(f"\n  跨域前置节点: {cross_domain_count}/{len(nodes)} ({ratio:.1%})")
    if ratio < 0.15:
        msg = f"跨域前置节点占比 {ratio:.1%} 过低 (< 15%)"
        print(f"  ✗ {msg}")
        all_issues.append(msg)
        all_passed = False
    else:
        print(f"  ✓ 跨域前置占比达标 (>= 15%)")

    status = "通过" if all_passed else "失败"
    print(f"\n  >>> 三类前置覆盖测试: {status}")
    return all_passed, all_issues

# ===========================================================================
# 4. 无循环依赖测试
# ===========================================================================
def test_no_circular_dependencies(nodes, node_map):
    print("\n" + "="*70)
    print("【测试4】无循环依赖测试")
    print("="*70)
    all_passed = True
    all_issues = []

    # 4.1 DFS 检测环
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {n["id"]: WHITE for n in nodes}

    def dfs(node_id, path):
        color[node_id] = GRAY
        path.append(node_id)
        node = node_map.get(node_id)
        if node:
            for p in node["prerequisites"]:
                if p in color:
                    if color[p] == GRAY:
                        cycle_start = path.index(p)
                        return path[cycle_start:] + [p]
                    if color[p] == WHITE:
                        result = dfs(p, path)
                        if result is not None:
                            return result
        path.pop()
        color[node_id] = BLACK
        return None

    for node in nodes:
        if color[node["id"]] == WHITE:
            cycle = dfs(node["id"], [])
            if cycle is not None:
                msg = f"发现循环依赖: {' -> '.join(cycle)}"
                print(f"  ✗ {msg}")
                all_issues.append(msg)
                all_passed = False

    if all_passed:
        print(f"  ✓ DFS 检测: 无循环依赖")

    # 4.2 Kahn 算法 (拓扑排序) 验证
    in_degree = {}
    for node in nodes:
        in_degree[node["id"]] = len(node["prerequisites"])

    queue = [nid for nid, deg in in_degree.items() if deg == 0]
    processed = 0

    while queue:
        current = queue.pop(0)
        processed += 1
        for node in nodes:
            if current in node["prerequisites"]:
                in_degree[node["id"]] -= 1
                if in_degree[node["id"]] == 0:
                    queue.append(node["id"])

    if processed != len(nodes):
        msg = f"拓扑排序只处理了 {processed}/{len(nodes)} 个节点，存在 {len(nodes) - processed} 个节点在循环依赖中"
        print(f"  ✗ {msg}")
        all_issues.append(msg)
        all_passed = False
    else:
        print(f"  ✓ Kahn 拓扑排序验证: {processed}/{len(nodes)} 个节点全部处理，无环")

    status = "通过" if all_passed else "失败"
    print(f"\n  >>> 无循环依赖测试: {status}")
    return all_passed, all_issues

# ===========================================================================
# 5. 基础节点测试
# ===========================================================================
def test_basic_nodes(nodes, node_map):
    print("\n" + "="*70)
    print("【测试5】基础节点测试")
    print("="*70)
    all_passed = True
    all_issues = []

    # 5.1 已知基础节点的 prerequisites 为空
    basic_nodes = {
        "mat_stone_tools": "石器制作",
        "energy_fire": "火的控制",
        "math_counting": "计数与数字概念",
        "soc_language": "语言系统化",
        "energy_human_animal": "人力与畜力",
        "phys_magnetism_ancient": "磁石发现",
        "phys_static_elec": "静电现象",
    }
    for nid, name in basic_nodes.items():
        if nid not in node_map:
            msg = f"基础节点不存在: {nid} ({name})"
            print(f"  ✗ {msg}")
            all_issues.append(msg)
            all_passed = False
        elif node_map[nid]["prerequisites"] != []:
            msg = f"基础节点 {nid} ({name}) 的 prerequisites 应为空，实际: {node_map[nid]['prerequisites']}"
            print(f"  ✗ {msg}")
            all_issues.append(msg)
            all_passed = False
        else:
            print(f"  ✓ 基础节点 {nid} ({name}): prerequisites=[]")

    # 5.2 所有空前置节点属于基础时代
    foundational_eras = {"prehistoric", "ancient"}
    empty_prereq_nodes = [n for n in nodes if not n["prerequisites"]]
    print(f"\n  空前置节点共 {len(empty_prereq_nodes)} 个")
    for node in empty_prereq_nodes:
        if node["era"] not in foundational_eras:
            msg = f"节点 {node['id']} ({node['name']}) prerequisites 为空，但 era 为 '{node['era']}'，应为 prehistoric 或 ancient"
            print(f"  ✗ {msg}")
            all_issues.append(msg)
            all_passed = False

    if all_passed:
        print(f"  ✓ 所有空前置节点均属于基础时代 (prehistoric/ancient)")

    # 5.3 基础节点数量合理
    if len(empty_prereq_nodes) < 3:
        msg = f"基础节点只有 {len(empty_prereq_nodes)} 个，太少"
        print(f"  ✗ {msg}")
        all_issues.append(msg)
        all_passed = False
    elif len(empty_prereq_nodes) > 30:
        msg = f"基础节点有 {len(empty_prereq_nodes)} 个，太多"
        print(f"  ✗ {msg}")
        all_issues.append(msg)
        all_passed = False
    else:
        print(f"  ✓ 基础节点数量合理: {len(empty_prereq_nodes)} 个")

    # 5.4 现代节点没有空前置
    modern_eras = {"modern", "information", "nuclear"}
    for node in nodes:
        if node["era"] in modern_eras and len(node["prerequisites"]) == 0:
            msg = f"现代节点 {node['id']} ({node['name']}, era={node['era']}) 的 prerequisites 为空"
            print(f"  ✗ {msg}")
            all_issues.append(msg)
            all_passed = False

    modern_nodes = [n for n in nodes if n["era"] in modern_eras]
    print(f"  ✓ 所有 {len(modern_nodes)} 个现代节点均有前置条件")

    # 打印基础节点列表
    print(f"\n  所有基础节点:")
    for n in empty_prereq_nodes:
        print(f"    - {n['id']} ({n['name']}, era={n['era']}, domain={n['domain']})")

    status = "通过" if all_passed else "失败"
    print(f"\n  >>> 基础节点测试: {status}")
    return all_passed, all_issues

# ===========================================================================
# 主函数
# ===========================================================================
def main():
    print("="*70)
    print("科技树前置条件修正结果 - 全面验证")
    print("="*70)

    # 加载数据
    nodes = load_data()
    node_map = build_node_map(nodes)
    all_ids = set(node_map.keys())
    print(f"数据加载完成: {len(nodes)} 个节点, {len(all_ids)} 个唯一 ID")

    results = {}
    all_issues = []

    # 执行5大类测试
    p1, i1 = test_data_integrity(nodes, node_map, all_ids)
    results["数据完整性"] = p1
    all_issues.extend(i1)

    p2, i2 = test_prerequisite_chain_traceability(node_map, all_ids)
    results["前置链可追溯性"] = p2
    all_issues.extend(i2)

    p3, i3 = test_three_category_coverage(nodes, node_map)
    results["三类前置覆盖"] = p3
    all_issues.extend(i3)

    p4, i4 = test_no_circular_dependencies(nodes, node_map)
    results["无循环依赖"] = p4
    all_issues.extend(i4)

    p5, i5 = test_basic_nodes(nodes, node_map)
    results["基础节点"] = p5
    all_issues.extend(i5)

    # 汇总
    print("\n" + "="*70)
    print("测试汇总")
    print("="*70)
    total = len(results)
    passed_count = sum(1 for v in results.values() if v)
    for name, p in results.items():
        status = "✓ 通过" if p else "✗ 失败"
        print(f"  {status}: {name}")

    overall = passed_count == total
    print(f"\n  总计: {passed_count}/{total} 类测试通过")
    if all_issues:
        print(f"\n  发现 {len(all_issues)} 个问题:")
        for i, issue in enumerate(all_issues, 1):
            print(f"    {i}. {issue}")
    else:
        print(f"\n  未发现问题!")

    if overall:
        print("\n★★★ 整体评估: 全部通过 ★★★")
    else:
        print("\n★★★ 整体评估: 存在失败项 ★★★")

    return overall, all_issues, results

if __name__ == "__main__":
    overall, issues, results = main()
    sys.exit(0 if overall else 1)
