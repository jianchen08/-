#!/usr/bin/env python3
"""
科技树数据集 DAG 校验脚本
功能：
  1. 检测循环依赖
  2. 检测孤立节点（无入边且无出边的节点）
  3. 检测前置引用缺失（引用了不存在的节点ID）
  4. 检测字段完整性
  5. 统计跨领域前置关系
  6. 验证追溯性（信息时代节点能否追溯到远古）
  7. 输出详细校验报告

用法：python scripts/validate_dag.py [--data-dir public/data/nodes] [--verbose]
"""

import json
import os
import sys
import glob
from collections import defaultdict, deque


def load_all_nodes(data_dir):
    """加载所有领域的节点数据"""
    all_nodes = {}
    domain_stats = defaultdict(lambda: {"count": 0, "eras": defaultdict(int)})
    
    for filepath in sorted(glob.glob(os.path.join(data_dir, "*.json"))):
        domain = os.path.basename(filepath).replace(".json", "")
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                nodes = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"  ❌ 无法加载 {filepath}: {e}")
            continue
        
        for node in nodes:
            nid = node.get("id", "")
            if nid in all_nodes:
                print(f"  ⚠️ 重复节点ID: {nid}")
            all_nodes[nid] = node
            domain_stats[domain]["count"] += 1
            era = node.get("era", "unknown")
            domain_stats[domain]["eras"][era] += 1
    
    return all_nodes, domain_stats


def check_field_completeness(all_nodes):
    """检查节点字段完整性"""
    required_fields = ["id", "name", "year", "yearRange", "era", "domain", "prerequisites", "description", "importance", "tags"]
    issues = []
    
    for nid, node in all_nodes.items():
        for field in required_fields:
            if field not in node or node[field] is None:
                issues.append(f"  {nid}: 缺失字段 '{field}'")
            elif field == "tags" and not isinstance(node[field], list):
                issues.append(f"  {nid}: tags 字段应为数组")
            elif field == "prerequisites" and not isinstance(node[field], list):
                issues.append(f"  {nid}: prerequisites 字段应为数组")
    
    return issues


def check_missing_references(all_nodes):
    """检查前置引用缺失"""
    issues = []
    for nid, node in all_nodes.items():
        for prereq in node.get("prerequisites", []):
            if prereq not in all_nodes:
                issues.append(f"  {nid} -> {prereq} (不存在)")
    return issues


def check_circular_dependencies(all_nodes):
    """使用 Kahn 算法检测循环依赖（拓扑排序）"""
    # 构建邻接表和入度表
    in_degree = defaultdict(int)
    adj = defaultdict(list)  # prereq -> [nodes that depend on it]
    
    for nid in all_nodes:
        in_degree[nid] = in_degree.get(nid, 0)  # 确保所有节点都在图中
    
    for nid, node in all_nodes.items():
        for prereq in node.get("prerequisites", []):
            if prereq in all_nodes:  # 只处理有效引用
                adj[prereq].append(nid)
                in_degree[nid] += 1
    
    # Kahn 算法
    queue = deque([nid for nid in all_nodes if in_degree[nid] == 0])
    topo_order = []
    
    while queue:
        node = queue.popleft()
        topo_order.append(node)
        for neighbor in adj[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    
    # 如果拓扑排序没有包含所有节点，则存在环
    if len(topo_order) < len(all_nodes):
        cycle_nodes = set(all_nodes.keys()) - set(topo_order)
        # 尝试找出具体的循环路径
        cycles = find_cycles(all_nodes, cycle_nodes)
        return False, cycle_nodes, cycles
    
    return True, set(), []


def find_cycles(all_nodes, suspect_nodes):
    """在疑似有环节点中查找具体的循环路径"""
    cycles = []
    visited = set()
    
    def dfs(node_id, path, path_set):
        if node_id in path_set:
            # 找到环
            cycle_start = path.index(node_id)
            cycle = path[cycle_start:] + [node_id]
            cycles.append(cycle)
            return
        if node_id in visited:
            return
        if node_id not in all_nodes:
            return
        
        path.append(node_id)
        path_set.add(node_id)
        
        for prereq in all_nodes[node_id].get("prerequisites", []):
            if prereq in suspect_nodes or prereq in path_set:
                dfs(prereq, path, path_set)
        
        path.pop()
        path_set.discard(node_id)
        visited.add(node_id)
    
    for nid in suspect_nodes:
        if nid not in visited:
            dfs(nid, [], set())
    
    return cycles


def check_orphan_nodes(all_nodes):
    """检测孤立节点（没有入边也没有出边的节点，排除远古根节点）"""
    has_incoming = set()
    has_outgoing = set()
    
    for nid, node in all_nodes.items():
        for prereq in node.get("prerequisites", []):
            if prereq in all_nodes:
                has_incoming.add(nid)
                has_outgoing.add(prereq)
    
    orphans = []
    for nid, node in all_nodes.items():
        if nid not in has_incoming and nid not in has_outgoing:
            orphans.append(nid)
    
    return orphans


def check_traceability(all_nodes):
    """验证追溯性：信息时代节点能否追溯到远古基础节点"""
    def trace_back(node_id, visited=None):
        if visited is None:
            visited = set()
        if node_id in visited or node_id not in all_nodes:
            return set()
        visited.add(node_id)
        eras = {all_nodes[node_id].get("era", "?")}
        for prereq in all_nodes[node_id].get("prerequisites", []):
            eras |= trace_back(prereq, visited)
        return eras
    
    info_nodes = [nid for nid, n in all_nodes.items() if n.get("era") == "information"]
    can_reach = 0
    cannot_reach = []
    
    for nid in info_nodes:
        eras = trace_back(nid)
        if "prehistoric" in eras:
            can_reach += 1
        else:
            cannot_reach.append(nid)
    
    return len(info_nodes), can_reach, cannot_reach


def count_cross_domain_prereqs(all_nodes):
    """统计跨领域前置关系"""
    cross_domain = []
    for nid, node in all_nodes.items():
        node_domain = node.get("domain", "")
        for prereq in node.get("prerequisites", []):
            if prereq in all_nodes:
                prereq_domain = all_nodes[prereq].get("domain", "")
                if prereq_domain != node_domain:
                    cross_domain.append((nid, node_domain, prereq, prereq_domain))
    return cross_domain


def main():
    import argparse
    parser = argparse.ArgumentParser(description="科技树数据集 DAG 校验")
    parser.add_argument("--data-dir", default="public/data/nodes", help="节点数据目录")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    args = parser.parse_args()
    
    print("=" * 60)
    print("  科技树数据集 DAG 校验报告")
    print("=" * 60)
    
    # 加载数据
    print(f"\n📁 数据目录: {args.data_dir}")
    all_nodes, domain_stats = load_all_nodes(args.data_dir)
    print(f"📊 总节点数: {len(all_nodes)}")
    
    # 1. 领域分布
    print(f"\n{'─' * 40}")
    print("📋 领域分布")
    print(f"{'─' * 40}")
    for domain, stats in sorted(domain_stats.items()):
        print(f"  {domain}: {stats['count']} 个节点")
    
    # 2. 时代分布
    print(f"\n{'─' * 40}")
    print("🗓️ 时代分布")
    print(f"{'─' * 40}")
    era_counts = defaultdict(int)
    for nid, node in all_nodes.items():
        era_counts[node.get("era", "unknown")] += 1
    for era, count in sorted(era_counts.items()):
        print(f"  {era}: {count} 个节点")
    
    # 3. 字段完整性检查
    print(f"\n{'─' * 40}")
    print("📝 字段完整性检查")
    print(f"{'─' * 40}")
    field_issues = check_field_completeness(all_nodes)
    if field_issues:
        print(f"  ❌ 发现 {len(field_issues)} 个问题:")
        for issue in field_issues[:20]:
            print(issue)
    else:
        print(f"  ✅ 所有节点字段完整")
    
    # 4. 前置引用缺失检查
    print(f"\n{'─' * 40}")
    print("🔗 前置引用缺失检查")
    print(f"{'─' * 40}")
    missing_refs = check_missing_references(all_nodes)
    if missing_refs:
        print(f"  ❌ 发现 {len(missing_refs)} 个缺失引用:")
        for ref in missing_refs:
            print(ref)
    else:
        print(f"  ✅ 所有前置引用均存在")
    
    # 5. 循环依赖检测
    print(f"\n{'─' * 40}")
    print("🔄 循环依赖检测 (DAG)")
    print(f"{'─' * 40}")
    is_dag, cycle_nodes, cycles = check_circular_dependencies(all_nodes)
    if is_dag:
        print(f"  ✅ 无循环依赖，DAG 校验通过")
    else:
        print(f"  ❌ 发现循环依赖！涉及 {len(cycle_nodes)} 个节点:")
        for cycle in cycles[:5]:
            print(f"    {' → '.join(cycle)}")
    
    # 6. 孤立节点检测
    print(f"\n{'─' * 40}")
    print("🏝️ 孤立节点检测")
    print(f"{'─' * 40}")
    orphans = check_orphan_nodes(all_nodes)
    if orphans:
        print(f"  ⚠️  发现 {len(orphans)} 个孤立节点:")
        for nid in orphans:
            node = all_nodes[nid]
            print(f"    {nid} ({node.get('name', '?')}, {node.get('era', '?')})")
    else:
        print(f"  ✅ 无孤立节点")
    
    # 7. 跨领域前置关系统计
    print(f"\n{'─' * 40}")
    print("🌐 跨领域前置关系统计")
    print(f"{'─' * 40}")
    cross_domain = count_cross_domain_prereqs(all_nodes)
    cross_pairs = defaultdict(int)
    for nid, nd, pid, pd in cross_domain:
        pair = tuple(sorted([nd, pd]))
        cross_pairs[pair] += 1
    print(f"  跨领域前置关系总数: {len(cross_domain)}")
    if args.verbose:
        for pair, count in sorted(cross_pairs.items(), key=lambda x: -x[1]):
            print(f"    {pair[0]} ↔ {pair[1]}: {count}")
    
    # 8. 追溯性验证
    print(f"\n{'─' * 40}")
    print("🔍 追溯性验证（信息时代 → 远古）")
    print(f"{'─' * 40}")
    total_info, can_reach, cannot_reach = check_traceability(all_nodes)
    print(f"  信息时代节点: {total_info}")
    print(f"  可追溯到远古: {can_reach}/{total_info}")
    if cannot_reach:
        print(f"  ⚠️  不可追溯的节点 ({len(cannot_reach)}):")
        for nid in cannot_reach[:10]:
            print(f"    {nid}")
    else:
        print(f"  ✅ 所有信息时代节点均可追溯到远古")
    
    # 9. 根节点统计
    print(f"\n{'─' * 40}")
    print("🌱 根节点（无前置）")
    print(f"{'─' * 40}")
    root_nodes = [nid for nid, n in all_nodes.items() if not n.get("prerequisites", [])]
    root_eras = defaultdict(int)
    for nid in root_nodes:
        root_eras[all_nodes[nid].get("era", "?")] += 1
    print(f"  根节点总数: {len(root_nodes)}")
    for era, count in sorted(root_eras.items()):
        print(f"    {era}: {count}")
    
    # 总结
    print(f"\n{'=' * 60}")
    print("  校验总结")
    print(f"{'=' * 60}")
    
    all_pass = True
    checks = [
        ("节点总数 ≥ 500", len(all_nodes) >= 500, f"{len(all_nodes)} 个"),
        ("所有领域覆盖", len(domain_stats) >= 12, f"{len(domain_stats)} 个领域"),
        ("字段完整性", len(field_issues) == 0, f"{len(field_issues)} 个问题" if field_issues else "通过"),
        ("无缺失引用", len(missing_refs) == 0, f"{len(missing_refs)} 个缺失" if missing_refs else "通过"),
        ("DAG校验通过", is_dag, "无环" if is_dag else f"{len(cycle_nodes)} 个节点成环"),
        ("跨领域前置 ≥ 100", len(cross_domain) >= 100, f"{len(cross_domain)} 条"),
        ("追溯性完整", len(cannot_reach) == 0, f"{can_reach}/{total_info}" if not cannot_reach else f"{len(cannot_reach)} 不可追溯"),
    ]
    
    for name, passed, detail in checks:
        status = "✅" if passed else "❌"
        print(f"  {status} {name}: {detail}")
        if not passed:
            all_pass = False
    
    print(f"\n{'=' * 60}")
    if all_pass:
        print("  🎉 所有校验项通过！")
    else:
        print("  ⚠️  存在未通过的校验项，请修复后重新校验")
    print(f"{'=' * 60}")
    
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
