"""
科技树 prerequisites 修正结果全面验证脚本
直接运行: python tests/verify_prerequisites.py
"""
import json
import sys
import os
from collections import defaultdict, deque

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "public", "data", "full_data.json")

def load_data():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

# ============================================================
# 测试1: 数据完整性
# ============================================================
def test_data_completeness(nodes):
    print("\n" + "=" * 70)
    print("测试1: 数据完整性 — 所有节点有prerequisites字段，引用ID存在")
    print("=" * 70)

    issues = []
    all_ids = set()
    node_map = {}
    dup_ids = []

    for i, node in enumerate(nodes):
        nid = node.get("id")
        if nid is None:
            issues.append(f"public/data/full_data.json:行约{1+i*22} — 节点#{i}缺少id字段")
            continue
        if nid in all_ids:
            dup_ids.append(nid)
        all_ids.add(nid)
        node_map[nid] = node

    print(f"  总节点数: {len(nodes)}")
    print(f"  唯一ID数: {len(all_ids)}")
    if dup_ids:
        for d in dup_ids:
            issues.append(f"public/data/full_data.json — 重复id '{d}'")

    missing_prereqs = []
    invalid_refs = []
    for i, node in enumerate(nodes):
        nid = node.get("id", f"node#{i}")
        if "prerequisites" not in node:
            missing_prereqs.append(nid)
            issues.append(f"public/data/full_data.json — 节点 '{nid}' 缺少prerequisites字段")
            continue
        if not isinstance(node["prerequisites"], list):
            issues.append(f"public/data/full_data.json — 节点 '{nid}' prerequisites不是数组")
            continue
        for pid in node["prerequisites"]:
            if pid not in all_ids:
                invalid_refs.append((nid, pid))
                issues.append(f"public/data/full_data.json — 节点 '{nid}' 引用了不存在的ID '{pid}'")

    print(f"  缺少prerequisites字段: {len(missing_prereqs)}个")
    print(f"  引用无效ID: {len(invalid_refs)}个")
    if invalid_refs:
        for nid, pid in invalid_refs[:20]:
            print(f"    ❌ {nid} → {pid}")
    if missing_prereqs:
        for nid in missing_prereqs[:20]:
            print(f"    ❌ {nid} 缺少prerequisites")

    passed = len(issues) == 0
    print(f"  结果: {'✅ 通过' if passed else '❌ 失败'}")
    return passed, issues, node_map


# ============================================================
# 测试2: 前置链可追溯性
# ============================================================
def trace_prerequisites(start_id, node_map, max_depth=50):
    """BFS从start_id往回追溯所有前置，返回所有可达节点和路径"""
    visited = set()
    queue = deque([(start_id, [start_id])])
    all_prereqs = set()
    leaf_nodes = []  # prerequisites为空的节点

    while queue:
        current_id, path = queue.popleft()
        if current_id in visited:
            continue
        visited.add(current_id)

        node = node_map.get(current_id)
        if node is None:
            continue

        prereqs = node.get("prerequisites", [])
        if not prereqs:
            leaf_nodes.append((current_id, path))

        for pid in prereqs:
            all_prereqs.add(pid)
            if pid not in visited and len(path) < max_depth:
                queue.append((pid, path + [pid]))

    return all_prereqs, visited, leaf_nodes


def test_prerequisite_traceability(node_map):
    print("\n" + "=" * 70)
    print("测试2: 前置链可追溯性 — 从前沿起点追溯到基础")
    print("=" * 70)

    issues = []

    # 动态搜索所有相关前沿节点
    frontier_targets = {}

    # 硬编码已知前沿节点
    known_frontier = {
        "AI Agent → 基础理论": "it_ai_agent",
        "可回收火箭 → 基础材料/制造": "eng_reusable_rocket",
        "受控核聚变 → 基础物理/材料": "energy_nuclear_fusion_reactor",
    }

    for label, nid in known_frontier.items():
        if nid in node_map:
            frontier_targets[label] = nid
        else:
            issues.append(f"public/data/full_data.json — 前沿节点 '{nid}'({label}) 不存在")

    # 动态搜索隐身/战斗机相关
    for nid, node in node_map.items():
        name = node.get("name", "")
        if "隐身" in name:
            frontier_targets[f"{name} → 基础航空/材料"] = nid
        if "超材料" in name and "隐身" in str(node.get("tags", [])):
            frontier_targets[f"{name} → 基础材料"] = nid

    # 动态搜索光伏相关
    for nid, node in node_map.items():
        name = node.get("name", "")
        if "钙钛矿" in name:
            frontier_targets[f"{name} → 基础材料/半导体"] = nid
        if "太阳能电池" in name or "光伏发电" in name:
            frontier_targets[f"{name} → 基础材料/半导体"] = nid

    print(f"  找到前沿节点: {len(frontier_targets)}个")

    for label, start_id in frontier_targets.items():
        node = node_map.get(start_id)
        if node is None:
            print(f"  [{label}] ❌ 节点不存在: {start_id}")
            continue

        all_prereqs, visited, leaf_nodes = trace_prerequisites(start_id, node_map)

        # 按领域统计
        domains = defaultdict(int)
        base_names = []
        for pid in all_prereqs:
            pnode = node_map.get(pid)
            if pnode:
                domains[pnode.get("domain", "?")] += 1
                if not pnode.get("prerequisites", []):
                    base_names.append(f"{pnode.get('name', '?')}({pid})")

        has_math = any(pid.startswith("math_") for pid in all_prereqs)
        has_phys = any(pid.startswith("phys_") for pid in all_prereqs)
        has_mat = any(pid.startswith("mat_") for pid in all_prereqs)

        chain_ok = True
        if not leaf_nodes:
            issues.append(f"public/data/full_data.json — '{label}': 前置链未追溯到任何基础节点")
            chain_ok = False

        status = "✅" if chain_ok else "❌"
        print(f"\n  [{label}] {status}")
        print(f"    起点节点: {node.get('name', '?')} ({start_id})")
        print(f"    前置节点总数: {len(all_prereqs)}")
        print(f"    到达基础节点: {len(leaf_nodes)}个")
        print(f"    覆盖数学(math_): {'是' if has_math else '否'}")
        print(f"    覆盖物理(phys_): {'是' if has_phys else '否'}")
        print(f"    覆盖材料(mat_): {'是' if has_mat else '否'}")
        if base_names:
            print(f"    基础节点: {', '.join(base_names[:8])}")

    passed = len(issues) == 0
    print(f"\n  结果: {'✅ 通过' if passed else '❌ 失败'}")
    for issue in issues:
        print(f"    {issue}")
    return passed, issues


# ============================================================
# 测试3: 三类前置覆盖（抽样验证）
# ============================================================
def test_three_category_coverage(node_map):
    print("\n" + "=" * 70)
    print("测试3: 三类前置覆盖 — 理论/工程/组织前置抽样验证")
    print("=" * 70)

    issues = []
    theory_prefixes = ("math_", "phys_")
    engineering_prefixes = ("eng_", "mat_", "energy_", "chem_", "it_", "astro_")
    social_prefixes = ("org_", "soc_", "bio_", "med_", "ag_")

    # 抽样重要节点
    target_ids = [
        "it_ai_agent",
        "eng_reusable_rocket",
        "energy_nuclear_fusion_reactor",
        "phys_quantum_computing",
        "it_deep_learning",
    ]

    sampled = []
    for tid in target_ids:
        if tid in node_map:
            sampled.append(node_map[tid])

    # 补充高importance节点
    extras = [n for n in node_map.values()
              if n.get("importance", 0) >= 4
              and n.get("id") not in target_ids
              and n.get("prerequisites")]
    sampled.extend(extras[:15])

    print(f"  抽样节点数: {len(sampled)}")

    cat_counts = {"理论前置": 0, "工程前置": 0, "组织/社会前置": 0, "跨域(≥2类)": 0, "单域": 0}

    for node in sampled:
        nid = node.get("id", "?")
        name = node.get("name", "?")
        prereqs = node.get("prerequisites", [])

        has_theory = any(pid.startswith(theory_prefixes) for pid in prereqs)
        has_eng = any(pid.startswith(engineering_prefixes) for pid in prereqs)
        has_soc = any(pid.startswith(social_prefixes) for pid in prereqs)

        types_count = sum([has_theory, has_eng, has_soc])
        if has_theory: cat_counts["理论前置"] += 1
        if has_eng: cat_counts["工程前置"] += 1
        if has_soc: cat_counts["组织/社会前置"] += 1
        if types_count >= 2:
            cat_counts["跨域(≥2类)"] += 1
        else:
            cat_counts["单域"] += 1

        # 检查无效引用
        for pid in prereqs:
            if pid not in node_map:
                issues.append(f"public/data/full_data.json — 节点 '{nid}'({name}) 引用不存在ID '{pid}'")

    print(f"  类别统计: {cat_counts}")
    print(f"  前10个抽样节点详情:")
    for node in sampled[:10]:
        nid = node.get("id", "?")
        name = node.get("name", "?")
        prereqs = node.get("prerequisites", [])
        types = []
        for pid in prereqs:
            if pid.startswith(theory_prefixes): types.append("理论")
            elif pid.startswith(engineering_prefixes): types.append("工程")
            elif pid.startswith(social_prefixes): types.append("社会")
        unique_types = sorted(set(types))
        print(f"    {name}({nid}): {len(prereqs)}个前置 [{', '.join(unique_types) if unique_types else '无分类'}]")

    passed = len(issues) == 0
    print(f"  结果: {'✅ 通过' if passed else '❌ 失败'}")
    return passed, issues


# ============================================================
# 测试4: 无循环依赖
# ============================================================
def test_no_circular_dependencies(node_map):
    print("\n" + "=" * 70)
    print("测试4: 无循环依赖 — 检测A→B→...→A循环")
    print("=" * 70)

    issues = []
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {nid: WHITE for nid in node_map}
    cycles = []

    sys.setrecursionlimit(5000)

    def dfs(node_id, path):
        color[node_id] = GRAY
        node = node_map.get(node_id)
        if node is None:
            color[node_id] = BLACK
            return
        for prereq_id in node.get("prerequisites", []):
            if prereq_id not in color:
                continue
            if color[prereq_id] == GRAY:
                idx = path.index(prereq_id) if prereq_id in path else 0
                cycle_path = path[idx:] + [prereq_id]
                cycles.append(cycle_path)
            elif color[prereq_id] == WHITE:
                dfs(prereq_id, path + [prereq_id])
        color[node_id] = BLACK

    for nid in node_map:
        if color[nid] == WHITE:
            dfs(nid, [nid])

    if cycles:
        for cycle in cycles:
            cycle_str = " → ".join(cycle)
            issues.append(f"public/data/full_data.json — 循环依赖: {cycle_str}")
            print(f"  ❌ 循环依赖: {cycle_str}")

    print(f"  检测节点数: {len(node_map)}")
    print(f"  发现循环数: {len(cycles)}")
    passed = len(issues) == 0
    print(f"  结果: {'✅ 通过' if passed else '❌ 失败'}")
    return passed, issues


# ============================================================
# 测试5: 基础节点测试
# ============================================================
def test_base_nodes(node_map):
    print("\n" + "=" * 70)
    print("测试5: 基础节点测试 — 基础节点prerequisites为空")
    print("=" * 70)

    issues = []

    empty_prereq_nodes = []
    for nid, node in node_map.items():
        if not node.get("prerequisites", None) == []:
            continue
        empty_prereq_nodes.append(nid)

    print(f"  基础节点(prerequisites=[])数: {len(empty_prereq_nodes)}")

    # 验证已知基础节点
    known_bases = {
        "mat_stone_tools": "石器制作",
        "energy_fire": "火的控制",
        "math_counting": "计数与数字概念",
        "soc_language": "语言系统化",
        "energy_human_animal": "人力与畜力",
        "phys_magnetism_ancient": "磁石发现",
        "phys_static_elec": "静电现象",
    }

    for bid, bname in known_bases.items():
        node = node_map.get(bid)
        if node is None:
            issues.append(f"public/data/full_data.json — 基础节点 '{bid}'({bname}) 不存在")
            print(f"  ❌ {bid}({bname}): 不存在")
            continue
        prereqs = node.get("prerequisites", "MISSING")
        if prereqs != []:
            issues.append(f"public/data/full_data.json:{bid} — 基础节点prerequisites应为空，实际为 {prereqs}")
            print(f"  ❌ {bid}({bname}): prerequisites={prereqs} (应为[])")
        else:
            print(f"  ✅ {bid}({bname}): prerequisites=[]")

    # 检查基础节点覆盖关键域
    base_domains = set()
    for nid in empty_prereq_nodes:
        node = node_map.get(nid)
        if node:
            base_domains.add(node.get("domain", ""))

    essential = {"math", "physics", "materials", "energy", "social"}
    # 兼容实际域前缀
    actual_essentials = set()
    for nid in empty_prereq_nodes:
        node = node_map.get(nid)
        if node:
            dom = node.get("domain", "")
            for e in essential:
                if dom.startswith(e) or dom == e:
                    actual_essentials.add(e)

    missing = essential - actual_essentials
    if missing:
        issues.append(f"public/data/full_data.json — 基础节点未覆盖关键域: {sorted(missing)}")
        print(f"  ❌ 未覆盖域: {sorted(missing)}")
    else:
        print(f"  ✅ 覆盖全部关键域")

    # 基础节点数量合理性
    if len(empty_prereq_nodes) < 3 or len(empty_prereq_nodes) > 30:
        issues.append(f"public/data/full_data.json — 基础节点数量: {len(empty_prereq_nodes)} (期望3-30)")
        print(f"  ❌ 数量: {len(empty_prereq_nodes)}")
    else:
        print(f"  ✅ 基础节点数量合理: {len(empty_prereq_nodes)}")

    # 基础节点应属于远古/史前时代
    bad_era = []
    for nid in empty_prereq_nodes:
        node = node_map.get(nid)
        if node and node.get("era", "") not in ("prehistoric", "ancient"):
            bad_era.append(f"{nid}({node.get('name','?')}, era={node.get('era','')})")
    if bad_era:
        issues.append(f"public/data/full_data.json — 非远古基础节点: {bad_era[:10]}")
        print(f"  ❌ 非远古基础节点: {bad_era[:10]}")
    else:
        print(f"  ✅ 所有基础节点均属 prehistoric/ancient")

    # 列出所有基础节点
    print(f"\n  全部基础节点:")
    for nid in empty_prereq_nodes:
        node = node_map.get(nid)
        if node:
            print(f"    {node.get('name','?')} ({nid}) [{node.get('domain','')}, {node.get('era','')}]")

    passed = len(issues) == 0
    print(f"\n  结果: {'✅ 通过' if passed else '❌ 失败'}")
    return passed, issues


# ============================================================
# 主入口
# ============================================================
def main():
    print("=" * 70)
    print("科技树 Prerequisites 全面验证测试")
    print(f"数据文件: {DATA_PATH}")
    print(f"文件存在: {os.path.exists(DATA_PATH)}")
    print("=" * 70)

    if not os.path.exists(DATA_PATH):
        print(f"\n❌ 数据文件不存在: {DATA_PATH}")
        return 1

    nodes = load_data()
    print(f"数据加载成功: {len(nodes)} 个节点")

    # 期望574个节点
    if len(nodes) != 574:
        print(f"⚠️  节点数为 {len(nodes)}，期望 574")

    results = {}
    all_issues = []

    # 测试1
    t1p, t1i, node_map = test_data_completeness(nodes)
    results["数据完整性"] = t1p
    all_issues.extend(t1i)

    # 测试2（依赖node_map）
    t2p, t2i = test_prerequisite_traceability(node_map)
    results["前置链可追溯性"] = t2p
    all_issues.extend(t2i)

    # 测试3
    t3p, t3i = test_three_category_coverage(node_map)
    results["三类前置覆盖"] = t3p
    all_issues.extend(t3i)

    # 测试4
    t4p, t4i = test_no_circular_dependencies(node_map)
    results["无循环依赖"] = t4p
    all_issues.extend(t4i)

    # 测试5
    t5p, t5i = test_base_nodes(node_map)
    results["基础节点验证"] = t5p
    all_issues.extend(t5i)

    # 汇总
    print("\n" + "=" * 70)
    print("汇总结果")
    print("=" * 70)
    for name, passed in results.items():
        print(f"  {name}: {'✅ 通过' if passed else '❌ 失败'}")

    passed_count = sum(1 for p in results.values() if p)
    total_count = len(results)
    all_passed = all(results.values())
    print(f"\n  通过: {passed_count}/{total_count}")
    print(f"  问题总数: {len(all_issues)}")

    if all_passed:
        print("\n🎉 所有测试通过！")
    else:
        print("\n⚠️  存在失败项:")
        for issue in all_issues:
            print(f"    {issue}")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
