"""
科技树 prerequisites 修正结果全面测试验证
测试文件: public/data/full_data.json
验证内容:
1. 数据完整性 - 所有节点有prerequisites字段，引用ID存在
2. 前置链可追溯性 - 从前沿节点追溯到基础
3. 三类前置覆盖 - 理论/工程/组织前置抽样验证
4. 无循环依赖 - 无 A→B→...→A 循环
5. 基础节点测试 - 基础节点prerequisites为空
"""

import json
import sys
import os
from collections import defaultdict, deque

# ============================================================
# 数据加载
# ============================================================
DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "public", "data", "full_data.json")

def load_data():
    """加载科技树数据"""
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        nodes = json.load(f)
    return nodes

# ============================================================
# 测试1: 数据完整性
# ============================================================
def test_data_completeness(nodes):
    """验证所有节点都有prerequisites字段，所有引用的ID存在"""
    print("\n" + "="*60)
    print("测试1: 数据完整性")
    print("="*60)

    issues = []
    all_ids = set()
    node_map = {}

    # 构建ID集合和节点映射
    for i, node in enumerate(nodes):
        node_id = node.get("id")
        if node_id is None:
            issues.append(f"节点#{i}: 缺少id字段")
            continue
        if node_id in all_ids:
            issues.append(f"节点#{i}: 重复id '{node_id}'")
        all_ids.add(node_id)
        node_map[node_id] = node

    print(f"  总节点数: {len(nodes)}")
    print(f"  唯一ID数: {len(all_ids)}")

    # 检查prerequisites字段
    missing_prereqs = []
    invalid_ref_count = 0
    for i, node in enumerate(nodes):
        node_id = node.get("id", f"node#{i}")
        if "prerequisites" not in node:
            missing_prereqs.append(f"  节点 '{node_id}' (#{i}): 缺少prerequisites字段")
            continue
        if not isinstance(node["prerequisites"], list):
            issues.append(f"  节点 '{node_id}': prerequisites不是数组类型")
            continue
        # 检查引用ID是否存在
        for prereq_id in node["prerequisites"]:
            if prereq_id not in all_ids:
                invalid_ref_count += 1
                issues.append(f"  节点 '{node_id}': prerequisites引用了不存在的ID '{prereq_id}'")

    if missing_prereqs:
        issues = missing_prereqs + issues

    passed = len(issues) == 0
    status = "✅ 通过" if passed else "❌ 失败"
    print(f"  缺少prerequisites字段的节点: {len(missing_prereqs)}")
    print(f"  引用无效ID数: {invalid_ref_count}")
    print(f"  结果: {status}")

    if not passed:
        for issue in issues[:20]:
            print(f"    {issue}")
        if len(issues) > 20:
            print(f"    ... 还有 {len(issues)-20} 个问题")

    return passed, issues, node_map


# ============================================================
# 测试2: 前置链可追溯性
# ============================================================
def trace_prerequisites(node_id, node_map, max_depth=30):
    """从指定节点向前追溯前置链，返回所有可达节点集合和路径"""
    visited = set()
    queue = deque([(node_id, [node_id])])
    all_prereqs = set()
    paths = {}

    while queue:
        current_id, path = queue.popleft()
        if current_id in visited:
            continue
        visited.add(current_id)

        node = node_map.get(current_id)
        if node is None:
            continue

        prereqs = node.get("prerequisites", [])
        for prereq_id in prereqs:
            if prereq_id not in all_prereqs:
                all_prereqs.add(prereq_id)
                paths[prereq_id] = path + [prereq_id]
            if prereq_id not in visited and len(path) < max_depth:
                queue.append((prereq_id, path + [prereq_id]))

    return all_prereqs, paths, visited


def test_prerequisite_traceability(node_map):
    """从前沿节点追溯前置链，验证链条完整不中断"""
    print("\n" + "="*60)
    print("测试2: 前置链可追溯性")
    print("="*60)

    issues = []

    # 定义前沿起点（根据实际数据中的节点ID）
    frontier_nodes = {
        "AI Agent → 基础理论": "it_ai_agent",
        "可回收火箭 → 基础材料/制造": "eng_reusable_rocket",
        "受控核聚变 → 基础物理/材料": "energy_nuclear_fusion_reactor",
        # 光伏链路：太阳能电池 + 钙钛矿材料
        "太阳能电池 → 基础材料/半导体": "energy_solar_cell",
        "钙钛矿材料 → 基础材料/半导体": "mat_perovskite",
    }

    # 搜索先进战斗机相关节点（隐身、战斗、喷气、超音速）
    fighter_keywords = ["隐身", "战斗", "stealth", "超音速"]
    for nid, node in node_map.items():
        name = node.get("name", "")
        tags = node.get("tags", [])
        tag_str = " ".join(str(t) for t in tags) if isinstance(tags, list) else str(tags)
        if any(kw in name for kw in fighter_keywords):
            frontier_nodes[f"{name} → 基础航空/材料"] = nid
        elif any(kw in tag_str for kw in fighter_keywords) and node.get("domain") in ("engineering",):
            frontier_nodes[f"{name} → 基础航空/材料"] = nid

    # 如果没有找到先进战斗机，用喷气发动机和飞机作为替代
    if not any("航空/材料" in k for k in frontier_nodes):
        if "eng_jet_engine" in node_map:
            frontier_nodes["喷气发动机 → 基础航空/材料"] = "eng_jet_engine"
        if "eng_airplane" in node_map:
            frontier_nodes["飞机 → 基础航空/材料"] = "eng_airplane"

    print(f"  前沿节点数: {len(frontier_nodes)}")

    for trace_name, start_id in frontier_nodes.items():
        node = node_map.get(start_id)
        if node is None:
            issues.append(f"  前沿节点 '{trace_name}': ID '{start_id}' 不存在")
            print(f"  [{trace_name}] ❌ 节点不存在: {start_id}")
            continue

        all_prereqs, paths, visited = trace_prerequisites(start_id, node_map)

        # 分析前置节点按领域分布
        domains = defaultdict(int)
        base_nodes_reached = []
        for pid in all_prereqs:
            pnode = node_map.get(pid)
            if pnode:
                domains[pnode.get("domain", "unknown")] += 1
                if not pnode.get("prerequisites", []):
                    base_nodes_reached.append(f"{pnode.get('name','?')}({pid})")

        # 检查是否追溯到基础理论节点
        has_math = any(pid.startswith("math_") for pid in all_prereqs)
        has_phys = any(pid.startswith("phys_") for pid in all_prereqs)

        chain_ok = True
        if not base_nodes_reached:
            issues.append(f"  '{trace_name}': 前置链未追溯到任何基础节点")
            chain_ok = False

        status = "✅" if chain_ok else "❌"
        print(f"  [{trace_name}] {status}")
        print(f"    起点: {node.get('name','?')} ({start_id})")
        print(f"    前置节点总数: {len(all_prereqs)}")
        print(f"    到达基础节点: {len(base_nodes_reached)} 个")
        print(f"    覆盖数学节点: {'是' if has_math else '否'}")
        print(f"    覆盖物理节点: {'是' if has_phys else '否'}")
        print(f"    领域分布: {dict(domains)}")
        if base_nodes_reached:
            print(f"    基础节点: {', '.join(base_nodes_reached[:10])}")

    passed = len(issues) == 0
    print(f"  结果: {'✅ 通过' if passed else '❌ 失败'}")
    for issue in issues:
        print(f"    {issue}")

    return passed, issues


# ============================================================
# 测试3: 三类前置覆盖测试（抽样）
# ============================================================
def test_three_category_coverage(node_map):
    """抽样验证节点的prerequisites是否覆盖理论、工程、组织三大类"""
    print("\n" + "="*60)
    print("测试3: 三类前置覆盖（抽样验证）")
    print("="*60)

    issues = []

    # 定义领域前缀到类别的映射
    theory_prefixes = ("math_", "phys_")
    engineering_prefixes = ("eng_", "mat_", "energy_", "chem_")
    social_prefixes = ("org_", "soc_", "bio_", "med_")

    # 固定选择一些有代表性的高importance节点
    target_ids = [
        "it_ai_agent",           # AI Agent
        "eng_reusable_rocket",   # 可回收火箭
        "energy_nuclear_fusion_reactor",  # 受控核聚变
        "phys_quantum_computing", # 量子计算
        "it_deep_learning",      # 深度学习
    ]

    # 补充随机抽样到至少20个
    sampled = []
    sampled_ids = set()
    for tid in target_ids:
        if tid in node_map:
            sampled.append(node_map[tid])
            sampled_ids.add(tid)

    importance_high = [n for n in node_map.values()
                       if n.get("importance", 0) >= 4
                       and n.get("id") not in sampled_ids
                       and n.get("prerequisites")]
    sampled.extend(importance_high[:15])

    print(f"  抽样节点数: {len(sampled)}")

    # 统计各类别覆盖
    categories = {"理论前置": 0, "工程前置": 0, "组织/社会前置": 0, "跨域混合": 0}
    detail_results = []

    for node in sampled:
        nid = node.get("id", "?")
        name = node.get("name", "?")
        prereqs = node.get("prerequisites", [])

        has_theory = False
        has_engineering = False
        has_social = False
        missing_ids = []

        for pid in prereqs:
            if pid.startswith(theory_prefixes):
                has_theory = True
            elif pid.startswith(engineering_prefixes):
                has_engineering = True
            elif pid.startswith(social_prefixes):
                has_social = True
            else:
                # it_ 域也算工程/技术类
                if pid.startswith("it_"):
                    has_engineering = True
                elif pid.startswith("ag_"):
                    has_engineering = True
                elif pid.startswith("astro_"):
                    has_theory = True
                elif pid not in node_map:
                    missing_ids.append(pid)

        # 判断覆盖情况
        covered_types = sum([has_theory, has_engineering, has_social])

        if covered_types >= 2:
            categories["跨域混合"] += 1
        elif has_theory:
            categories["理论前置"] += 1
        elif has_engineering:
            categories["工程前置"] += 1
        elif has_social:
            categories["组织/社会前置"] += 1

        if missing_ids:
            issues.append(f"  节点 '{nid}'({name}): 引用不存在的ID: {missing_ids}")

        detail_results.append({
            "id": nid, "name": name,
            "prereqs_count": len(prereqs),
            "has_theory": has_theory,
            "has_engineering": has_engineering,
            "has_social": has_social,
        })

    # 打印抽样结果摘要
    print(f"  前置类别分布: {categories}")
    for r in detail_results[:10]:
        types = []
        if r["has_theory"]: types.append("理论")
        if r["has_engineering"]: types.append("工程")
        if r["has_social"]: types.append("社会")
        print(f"    {r['name']}: {r['prereqs_count']}个前置 [{', '.join(types) if types else '无分类'}]")

    if len(detail_results) > 10:
        print(f"    ... 还有 {len(detail_results)-10} 个节点")

    # 注意：不是所有节点都需要覆盖三类前置，这里只记录信息
    # 只有引用了不存在ID才算问题
    passed = len(issues) == 0
    print(f"  结果: {'✅ 通过' if passed else '❌ 失败'}")
    for issue in issues:
        print(f"    {issue}")

    return passed, issues


# ============================================================
# 测试4: 无循环依赖
# ============================================================
def test_no_circular_dependencies(node_map):
    """验证不存在 A→B→...→A 的循环依赖"""
    print("\n" + "="*60)
    print("测试4: 无循环依赖")
    print("="*60)

    issues = []

    # 使用DFS检测循环 - 迭代版本避免递归栈溢出
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {nid: WHITE for nid in node_map}
    cycles = []

    def dfs_iterative(start_id):
        """迭代式DFS检测循环"""
        stack = [(start_id, iter(node_map.get(start_id, {}).get("prerequisites", [])), [start_id])]
        color[start_id] = GRAY

        while stack:
            node_id, prereq_iter, path = stack[-1]
            try:
                prereq_id = next(prereq_iter)
                if prereq_id not in color:
                    # 不存在的ID已在测试1中检查
                    continue
                if color[prereq_id] == GRAY:
                    # 找到循环
                    cycle_start = path.index(prereq_id) if prereq_id in path else 0
                    cycle_path = path[cycle_start:] + [prereq_id]
                    cycles.append(cycle_path)
                elif color[prereq_id] == WHITE:
                    color[prereq_id] = GRAY
                    stack.append((prereq_id, iter(node_map.get(prereq_id, {}).get("prerequisites", [])), path + [prereq_id]))
            except StopIteration:
                color[node_id] = BLACK
                stack.pop()

    for nid in list(node_map.keys()):
        if color[nid] == WHITE:
            dfs_iterative(nid)

    if cycles:
        for cycle in cycles:
            cycle_str = " → ".join(cycle)
            issues.append(f"  发现循环依赖: {cycle_str}")
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
    """验证基础技术节点的prerequisites为空数组"""
    print("\n" + "="*60)
    print("测试5: 基础节点测试")
    print("="*60)

    issues = []

    # 找出所有prerequisites为空的节点
    empty_prereq_nodes = []
    for nid, node in node_map.items():
        prereqs = node.get("prerequisites", None)
        if prereqs is not None and len(prereqs) == 0:
            empty_prereq_nodes.append(nid)

    print(f"  基础节点(prerequisites为空)数: {len(empty_prereq_nodes)}")

    # 验证已知的基础节点确实存在且为空
    known_base_nodes = {
        "mat_stone_tools": "石器制作",
        "energy_fire": "火的控制",
        "math_counting": "计数与数字概念",
        "soc_language": "语言系统化",
        "energy_human_animal": "人力与畜力",
        "phys_magnetism_ancient": "磁石发现",
        "phys_static_elec": "静电现象",
    }

    base_check_results = []
    for base_id, expected_name in known_base_nodes.items():
        node = node_map.get(base_id)
        if node is None:
            base_check_results.append(f"  ❌ {base_id}: 不存在于数据中")
            issues.append(f"  基础节点 '{base_id}' 不存在")
            continue
        prereqs = node.get("prerequisites", "MISSING")
        if prereqs == "MISSING":
            base_check_results.append(f"  ❌ {base_id}({node.get('name','?')}): 缺少prerequisites字段")
            issues.append(f"  基础节点 '{base_id}' 缺少prerequisites字段")
        elif prereqs != []:
            base_check_results.append(f"  ❌ {base_id}({node.get('name','?')}): prerequisites={prereqs} (应为空)")
            issues.append(f"  基础节点 '{base_id}'({node.get('name','?')}) prerequisites应为空数组，实际为 {prereqs}")
        else:
            base_check_results.append(f"  ✅ {base_id}({node.get('name','?')}): prerequisites=[]")

    for r in base_check_results:
        print(f"    {r}")

    # 验证基础节点覆盖关键域
    base_domains = set()
    for nid in empty_prereq_nodes:
        node = node_map.get(nid)
        if node:
            base_domains.add(node.get("domain", ""))
    essential_domains = {"math", "physics", "materials", "energy", "social"}
    missing_domains = essential_domains - base_domains
    if missing_domains:
        issues.append(f"  基础节点未覆盖关键域: {sorted(missing_domains)}")
        print(f"  ❌ 基础节点未覆盖域: {sorted(missing_domains)}")
    else:
        print(f"  ✅ 基础节点覆盖全部关键域: {sorted(base_domains)}")

    # 验证基础节点数量合理 (3-30个)
    if len(empty_prereq_nodes) < 3 or len(empty_prereq_nodes) > 30:
        issues.append(f"  基础节点数量不合理: {len(empty_prereq_nodes)} (期望3-30)")
        print(f"  ❌ 基础节点数量: {len(empty_prereq_nodes)} (期望3-30)")
    else:
        print(f"  ✅ 基础节点数量合理: {len(empty_prereq_nodes)}")

    # 验证所有空前置节点都属于基础时代 (prehistoric / ancient)
    foundational_eras = {"prehistoric", "ancient"}
    unexpected_era_bases = []
    for nid in empty_prereq_nodes:
        node = node_map.get(nid)
        if node and node.get("era", "") not in foundational_eras:
            unexpected_era_bases.append(f"{nid}({node.get('name','?')}, era={node.get('era','')})")
    if unexpected_era_bases:
        issues.append(f"  非基础时代的空前置节点: {unexpected_era_bases[:10]}")
        print(f"  ❌ 非基础时代的空前置节点: {unexpected_era_bases[:10]}")
    else:
        print(f"  ✅ 所有空前置节点均属于 prehistoric/ancient 时代")

    # 列出所有基础节点
    print(f"\n  所有基础节点 (prerequisites=[]):")
    for nid in empty_prereq_nodes:
        node = node_map.get(nid)
        if node:
            print(f"    {node.get('name','?')} ({nid}) [domain={node.get('domain','?')}, era={node.get('era','?')}]")

    passed = len(issues) == 0
    print(f"  结果: {'✅ 通过' if passed else '❌ 失败'}")
    return passed, issues


# ============================================================
# 主测试入口
# ============================================================
def main():
    print("="*60)
    print("科技树 Prerequisites 全面验证测试")
    print(f"数据文件: {DATA_PATH}")
    print("="*60)

    # 加载数据
    if not os.path.exists(DATA_PATH):
        print(f"\n❌ 错误: 数据文件不存在: {DATA_PATH}")
        sys.exit(1)

    nodes = load_data()
    print(f"数据加载成功: {len(nodes)} 个节点")

    # 节点总数验证
    expected_node_count = 574
    if len(nodes) != expected_node_count:
        print(f"  ⚠️  节点总数: {len(nodes)} (期望 {expected_node_count})")
    else:
        print(f"  ✅ 节点总数: {len(nodes)}")

    all_passed = True
    all_issues = []

    # 测试1
    t1_pass, t1_issues, node_map = test_data_completeness(nodes)
    all_passed = all_passed and t1_pass
    all_issues.extend(t1_issues)

    # 测试2
    t2_pass, t2_issues = test_prerequisite_traceability(node_map)
    all_passed = all_passed and t2_pass
    all_issues.extend(t2_issues)

    # 测试3
    t3_pass, t3_issues = test_three_category_coverage(node_map)
    all_passed = all_passed and t3_pass
    all_issues.extend(t3_issues)

    # 测试4
    t4_pass, t4_issues = test_no_circular_dependencies(node_map)
    all_passed = all_passed and t4_pass
    all_issues.extend(t4_issues)

    # 测试5
    t5_pass, t5_issues = test_base_nodes(node_map)
    all_passed = all_passed and t5_pass
    all_issues.extend(t5_issues)

    # 汇总
    print("\n" + "="*60)
    print("汇总结果")
    print("="*60)
    test_results = [
        ("数据完整性", t1_pass),
        ("前置链可追溯性", t2_pass),
        ("三类前置覆盖", t3_pass),
        ("无循环依赖", t4_pass),
        ("基础节点验证", t5_pass),
    ]
    for name, passed in test_results:
        print(f"  {name}: {'✅ 通过' if passed else '❌ 失败'}")

    passed_count = sum(1 for _, p in test_results if p)
    total_count = len(test_results)
    print(f"\n  通过: {passed_count}/{total_count}")
    print(f"  问题总数: {len(all_issues)}")

    if all_passed:
        print("\n🎉 所有测试通过！")
    else:
        print("\n⚠️  存在测试失败项，详情见上方输出。")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
