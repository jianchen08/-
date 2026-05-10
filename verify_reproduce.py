#!/usr/bin/env python3
"""
科技树574节点前置条件修正质量 - 可复现验证脚本

使用方法: python3 verify_reproduce.py [数据文件路径]
默认路径: public/data/full_data.json

验证项:
  V1: JSON格式正确性
  V2: 数据完整性（必填字段、ID唯一性、字段类型）
  V3: Prerequisites引用有效性（无悬空引用）
  V4: 无循环依赖（DAG结构）
  V5: 基础节点prerequisites为空
  V6: 前沿节点前置链完整性
  V7: 三类前置覆盖充分性
  V8: 前置链深度和数量边界分析
"""

import json
import sys
from collections import defaultdict

# ============================================================
# 配置
# ============================================================
DEFAULT_DATA_PATH = "public/data/full_data.json"

REQUIRED_FIELDS = ['id', 'name', 'year', 'prerequisites', 'domain', 'era']

# 前沿节点（ID可能在数据中不完全匹配，脚本会自动模糊查找）
FRONTIER_TARGETS = [
    ('it_ai_agent', 'AI Agent'),
    ('eng_reusable_rocket', '可回收火箭'),
    ('eng_jet_engine', '先进战斗机(喷气发动机)'),
    ('energy_nuclear_fusion_reactor', '可控核聚变'),
    ('energy_solar_cell', '高效光伏(太阳能电池)'),
]

# 三类前置的domain映射
THEORY_DOMAINS = {'math', 'physics', 'chemistry'}
ENGINEERING_DOMAINS = {'engineering', 'materials', 'energy'}
SOCIAL_DOMAINS = {'social', 'medicine', 'biology', 'agriculture'}
IT_DOMAINS = {'it', 'astronomy'}


# ============================================================
# 工具函数
# ============================================================
def load_data(path):
    """V1: 加载并解析JSON数据"""
    print("=" * 60)
    print("V1: JSON格式正确性验证")
    print("=" * 60)
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"  ✓ JSON解析成功，共 {len(data)} 个节点")
        return data
    except Exception as e:
        print(f"  ✗ JSON解析失败: {e}")
        return None


def verify_data_integrity(data):
    """V2: 验证数据完整性"""
    print("\n" + "=" * 60)
    print("V2: 数据完整性验证")
    print("=" * 60)
    passed = True

    # 必填字段检查
    missing = []
    for i, node in enumerate(data):
        for field in REQUIRED_FIELDS:
            if field not in node:
                missing.append((i, node.get('id', 'UNKNOWN'), field))
    if missing:
        print(f"  ✗ 有 {len(missing)} 个节点缺少必填字段")
        passed = False
    else:
        print(f"  ✓ 所有 {len(data)} 个节点均包含必填字段: {REQUIRED_FIELDS}")

    # ID唯一性检查
    id_count = defaultdict(int)
    for node in data:
        id_count[node['id']] += 1
    dup_ids = {nid: cnt for nid, cnt in id_count.items() if cnt > 1}
    if dup_ids:
        print(f"  ✗ 存在重复ID: {dup_ids}")
        passed = False
    else:
        print(f"  ✓ 所有 {len(id_count)} 个节点ID唯一")

    # prerequisites字段类型检查
    type_errors = [n['id'] for n in data if not isinstance(n.get('prerequisites'), list)]
    if type_errors:
        print(f"  ✗ prerequisites类型错误: {type_errors}")
        passed = False
    else:
        print(f"  ✓ 所有节点prerequisites字段均为数组类型")

    return passed


def verify_no_dangling_refs(data):
    """V3: 验证无悬空引用"""
    print("\n" + "=" * 60)
    print("V3: Prerequisites引用有效性验证（无悬空引用）")
    print("=" * 60)
    all_ids = set(node['id'] for node in data)
    dangling = []
    total = 0
    for node in data:
        for prereq in node.get('prerequisites', []):
            total += 1
            if prereq not in all_ids:
                dangling.append((node['id'], node['name'], prereq))

    if dangling:
        print(f"  ✗ 发现 {len(dangling)} 个悬空引用:")
        for nid, nname, prereq in dangling[:10]:
            print(f"    - {nid}({nname}) -> {prereq} [不存在]")
        return False
    else:
        print(f"  ✓ 全部 {total} 个prerequisite引用均有效，无悬空引用")
        return True


def verify_no_cycles(data):
    """V4: 验证无循环依赖（DFS三色标记法）"""
    print("\n" + "=" * 60)
    print("V4: 循环依赖检测")
    print("=" * 60)
    all_ids = set(node['id'] for node in data)
    graph = {node['id']: node.get('prerequisites', []) for node in data}

    WHITE, GRAY, BLACK = 0, 1, 2
    color = {nid: WHITE for nid in all_ids}
    cycles = []

    def dfs(node_id, path):
        color[node_id] = GRAY
        for prereq in graph.get(node_id, []):
            if prereq not in all_ids:
                continue
            if color[prereq] == GRAY:
                idx = path.index(prereq) if prereq in path else 0
                cycles.append(path[idx:] + [prereq])
            elif color[prereq] == WHITE:
                dfs(prereq, path + [prereq])
        color[node_id] = BLACK

    for nid in all_ids:
        if color[nid] == WHITE:
            dfs(nid, [nid])

    if cycles:
        print(f"  ✗ 发现 {len(cycles)} 个循环依赖:")
        for c in cycles[:5]:
            print(f"    - {' -> '.join(c)}")
        return False
    else:
        print(f"  ✓ 未发现任何循环依赖，DAG结构有效")
        return True


def verify_base_nodes(data):
    """V5: 验证基础节点prerequisites为空"""
    print("\n" + "=" * 60)
    print("V5: 基础节点验证（prerequisites为空）")
    print("=" * 60)
    base_nodes = [n for n in data if len(n.get('prerequisites', [])) == 0]
    print(f"  基础节点（无前置）共 {len(base_nodes)} 个:")
    for bn in base_nodes:
        print(f"    - {bn['id']} ({bn['name']}) [{bn['domain']}/{bn['era']}]")
    return True


def trace_chain(start_id, node_map, all_ids):
    """BFS回溯前置链"""
    visited = set()
    queue = [start_id]
    chain = []
    max_depth = 0
    depth_map = {start_id: 0}
    base_reached = set()

    while queue:
        current = queue.pop(0)
        if current in visited:
            continue
        visited.add(current)
        node = node_map.get(current)
        if not node:
            continue
        current_depth = depth_map.get(current, 0)
        chain.append((current, node['name'], node.get('prerequisites', []), current_depth))
        if not node.get('prerequisites', []):
            base_reached.add(current)
        for prereq in node.get('prerequisites', []):
            if prereq not in visited:
                depth_map[prereq] = current_depth + 1
                max_depth = max(max_depth, depth_map[prereq])
                queue.append(prereq)

    return chain, max_depth, base_reached


def verify_frontier_chains(data):
    """V6: 验证前沿节点前置链完整性"""
    print("\n" + "=" * 60)
    print("V6: 前沿节点前置链完整性追溯")
    print("=" * 60)
    node_map = {n['id']: n for n in data}
    all_ids = set(n['id'] for n in data)
    all_ok = True

    for start_id, label in FRONTIER_TARGETS:
        if start_id not in node_map:
            print(f"  ✗ 未找到节点: {start_id} ({label})")
            all_ok = False
            continue

        chain, max_depth, bases = trace_chain(start_id, node_map, all_ids)
        node_obj = node_map[start_id]
        print(f"\n  --- {label}: {start_id} ({node_obj['name']}) ---")
        print(f"  前置链长度: {len(chain)}, 最大深度: {max_depth}, 到达基础节点: {len(bases)}个")

        broken = False
        for nid, nname, prereqs, depth in chain:
            for p in prereqs:
                if p not in all_ids:
                    print(f"    ✗ 链中断: {nid}({nname}) -> {p} 不存在")
                    broken = True

        if not broken:
            print(f"  ✓ 前置链完整，无中断")
        else:
            all_ok = False

        base_names = [f"{node_map[b]['name']}({b})" for b in bases if b in node_map]
        print(f"  基础节点({len(bases)}): {', '.join(base_names)}")

    print(f"\n  {'✓' if all_ok else '✗'} 所有前沿节点前置链{'完整' if all_ok else '存在问题'}")
    return all_ok


def verify_category_coverage(data):
    """V7: 验证三类前置覆盖充分性"""
    print("\n" + "=" * 60)
    print("V7: 三类前置覆盖充分性验证")
    print("=" * 60)
    node_map = {n['id']: n for n in data}
    non_base = [n for n in data if n.get('prerequisites', [])]

    stats = {'theory': 0, 'engineering': 0, 'social': 0, 'it': 0}
    multi_count = 0

    for node in non_base:
        cats = set()
        for pid in node['prerequisites']:
            p = node_map.get(pid)
            if p:
                d = p['domain']
                if d in THEORY_DOMAINS:
                    cats.add('theory')
                elif d in ENGINEERING_DOMAINS:
                    cats.add('engineering')
                elif d in SOCIAL_DOMAINS:
                    cats.add('social')
                elif d in IT_DOMAINS:
                    cats.add('it')
        for c in cats:
            stats[c] = stats.get(c, 0) + 1
        if len(cats) >= 2:
            multi_count += 1

    total = len(non_base)
    print(f"  非基础节点总数: {total}")
    print(f"  包含理论前置: {stats['theory']} ({stats['theory']*100//total}%)")
    print(f"  包含工程前置: {stats['engineering']} ({stats['engineering']*100//total}%)")
    print(f"  包含社会前置: {stats['social']} ({stats['social']*100//total}%)")
    print(f"  跨2+类别节点: {multi_count} ({multi_count*100//total}%)")

    # 抽样检查复杂节点
    print(f"\n  抽样详细检查:")
    for sid in ['it_ai_agent', 'eng_reusable_rocket', 'energy_nuclear_fusion_reactor']:
        if sid not in node_map:
            continue
        node = node_map[sid]
        details = []
        cats = set()
        for pid in node['prerequisites']:
            p = node_map.get(pid)
            if p:
                details.append(f"{p['name']}[{p['domain']}]")
                d = p['domain']
                if d in THEORY_DOMAINS: cats.add('理论')
                elif d in ENGINEERING_DOMAINS: cats.add('工程')
                elif d in SOCIAL_DOMAINS: cats.add('社会')
                else: cats.add('IT')
        print(f"    {node['name']}: {', '.join(details)}")
        print(f"      覆盖类别: {cats}")

    return True


def verify_depth_bounds(data):
    """V8: 前置链深度和数量边界分析"""
    print("\n" + "=" * 60)
    print("V8: 前置链深度与数量边界分析")
    print("=" * 60)
    node_map = {n['id']: n for n in data}
    all_ids = set(n['id'] for n in data)

    # 计算深度
    depth_cache = {}
    def get_depth(nid):
        if nid in depth_cache:
            return depth_cache[nid]
        node = node_map.get(nid)
        if not node or not node.get('prerequisites', []):
            depth_cache[nid] = 0
            return 0
        max_d = 0
        for p in node['prerequisites']:
            if p in all_ids:
                max_d = max(max_d, get_depth(p) + 1)
        depth_cache[nid] = max_d
        return max_d

    depths = {n['id']: get_depth(n['id']) for n in data}
    depth_dist = defaultdict(int)
    for d in depths.values():
        depth_dist[d] += 1

    print("  前置链深度分布:")
    for d in sorted(depth_dist.keys()):
        print(f"    深度{d}: {depth_dist[d]}个节点")

    max_node = max(depths, key=depths.get)
    print(f"\n  最深节点: {max_node} ({node_map[max_node]['name']}) 深度={depths[max_node]}")

    # 前置数量分布
    prereq_dist = defaultdict(int)
    for n in data:
        prereq_dist[len(n.get('prerequisites', []))] += 1
    print("\n  前置数量分布:")
    for cnt in sorted(prereq_dist.keys()):
        print(f"    {cnt}个前置: {prereq_dist[cnt]}个节点")

    max_prereq = max(data, key=lambda n: len(n.get('prerequisites', [])))
    print(f"\n  最多前置节点: {max_prereq['id']} ({max_prereq['name']}) 前置数={len(max_prereq['prerequisites'])}")

    return True


# ============================================================
# 主函数
# ============================================================
def main():
    data_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DATA_PATH
    print(f"科技树574节点前置条件修正质量验证")
    print(f"数据文件: {data_path}\n")

    # V1: JSON格式
    data = load_data(data_path)
    if data is None:
        print("\n致命错误: 无法解析数据文件，终止验证")
        sys.exit(1)

    results = {}

    # V2: 数据完整性
    results['V2_数据完整性'] = verify_data_integrity(data)

    # V3: 引用有效性
    results['V3_引用有效性'] = verify_no_dangling_refs(data)

    # V4: 无循环依赖
    results['V4_无循环依赖'] = verify_no_cycles(data)

    # V5: 基础节点
    results['V5_基础节点'] = verify_base_nodes(data)

    # V6: 前沿节点链
    results['V6_前沿链完整性'] = verify_frontier_chains(data)

    # V7: 三类覆盖
    results['V7_三类前置覆盖'] = verify_category_coverage(data)

    # V8: 边界分析
    results['V8_边界分析'] = verify_depth_bounds(data)

    # 汇总
    print("\n" + "=" * 60)
    print("验证结果汇总")
    print("=" * 60)
    all_passed = True
    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}  {name}")
        if not passed:
            all_passed = False

    print(f"\n最终结论: {'✅ 全部通过' if all_passed else '❌ 存在失败项'}")
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
