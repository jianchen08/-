#!/usr/bin/env python3
"""
科技树数据集合并脚本
功能：将 public/data/nodes/ 目录下所有领域的 JSON 文件合并为完整的 full_data.json

用法：python scripts/merge_data.py [--nodes-dir public/data/nodes] [--output public/data/full_data.json]
"""

import json
import os
import sys
import glob
from collections import defaultdict


def main():
    import argparse
    parser = argparse.ArgumentParser(description="合并科技树领域数据为完整数据集")
    parser.add_argument("--nodes-dir", default="public/data/nodes", help="节点数据目录")
    parser.add_argument("--output", default="public/data/full_data.json", help="输出文件路径")
    args = parser.parse_args()

    nodes_dir = args.nodes_dir
    output_path = args.output

    print("=" * 50)
    print("  科技树数据集合并工具")
    print("=" * 50)

    if not os.path.isdir(nodes_dir):
        print(f"❌ 节点目录不存在: {nodes_dir}")
        sys.exit(1)

    all_nodes = []
    domain_stats = {}

    for filepath in sorted(glob.glob(os.path.join(nodes_dir, "*.json"))):
        domain = os.path.basename(filepath).replace(".json", "")
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                nodes = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"  ❌ 加载失败 {filepath}: {e}")
            continue

        domain_stats[domain] = len(nodes)
        all_nodes.extend(nodes)
        print(f"  ✓ {domain}: {len(nodes)} 个节点")

    # 按年份排序（处理负数年和字符串年）
    def sort_key(node):
        year = node.get("year", "0")
        try:
            return int(year)
        except (ValueError, TypeError):
            return 0

    all_nodes.sort(key=sort_key)

    # 写入输出文件
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_nodes, f, ensure_ascii=False, indent=2)

    print(f"\n{'─' * 50}")
    print(f"  合并完成！")
    print(f"  总节点数: {len(all_nodes)}")
    print(f"  领域数量: {len(domain_stats)}")
    print(f"  输出文件: {output_path}")
    print(f"  文件大小: {os.path.getsize(output_path) / 1024:.1f} KB")
    print(f"{'─' * 50}")


if __name__ == "__main__":
    main()
