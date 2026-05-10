#!/usr/bin/env python3
"""修正 energy_natural_gas 并同步所有数据文件。"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

BASE = Path("public/data")
PARENT = Path("public")


def load_full_data() -> list[dict]:
    """加载 full_data.json。"""
    with open(BASE / "full_data.json", "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: object) -> None:
    """保存JSON文件。"""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main() -> None:
    # 1. 加载数据
    data = load_full_data()
    all_ids = {n["id"] for n in data}
    index = {n["id"]: n for n in data}

    # 2. 修正 energy_natural_gas
    # 天然气工业(1821年)：早期天然气用于照明，需要铸铁管道和工业需求
    # 注意：不能依赖 energy_gas_turbine(1939年) 因为它更晚
    energy_ng = index["energy_natural_gas"]
    new_prereqs = ["mat_fire", "mat_cast_iron", "soc_industrial_society"]
    valid_prereqs = [p for p in new_prereqs if p in all_ids]
    energy_ng["prerequisites"] = valid_prereqs
    print(f"Fixed energy_natural_gas: {valid_prereqs}")

    # 3. 保存 full_data.json
    save_json(BASE / "full_data.json", data)
    print(f"Saved full_data.json ({len(data)} nodes)")

    # 4. 按领域拆分并同步到 public/data/nodes/*.json
    domains: dict[str, list[dict]] = {}
    for node in data:
        d = node["domain"]
        domains.setdefault(d, []).append(node)

    for domain, nodes in domains.items():
        path = BASE / "nodes" / f"{domain}.json"
        save_json(path, nodes)
        print(f"  Synced {path} ({len(nodes)} nodes)")

    # 5. 同步到 public/ 根目录的领域文件
    for domain, nodes in domains.items():
        path = PARENT / f"{domain}.json"
        save_json(path, nodes)
        print(f"  Synced {path} ({len(nodes)} nodes)")

    # 6. 验证
    # 重新加载验证
    with open(BASE / "full_data.json", "r", encoding="utf-8") as f:
        verify = json.load(f)

    # 检查引用有效性
    vid_set = {n["id"] for n in verify}
    invalid = []
    for n in verify:
        for p in n["prerequisites"]:
            if p not in vid_set:
                invalid.append(f"{n['id']} -> {p}")
    if invalid:
        print(f"\nERROR: {len(invalid)} invalid refs!")
        for i in invalid:
            print(f"  {i}")
    else:
        print("\n✓ All references valid")

    # 检查时间一致性（前置不能晚于节点本身）
    time_issues = []
    for n in verify:
        n_year = int(n["year"])
        for p in n["prerequisites"]:
            p_node = next((x for x in verify if x["id"] == p), None)
            if p_node:
                p_year = int(p_node["year"])
                if p_year > n_year:
                    time_issues.append(f"{n['id']}({n_year}) <- {p}({p_year})")
    if time_issues:
        print(f"\nWARNING: {len(time_issues)} time-order issues (prereq after node):")
        for t in time_issues[:20]:
            print(f"  {t}")
    else:
        print("✓ No time-order issues")

    # 检查重复
    dups = [n["id"] for n in verify if len(n["prerequisites"]) != len(set(n["prerequisites"]))]
    if dups:
        print(f"\nERROR: Duplicate prereqs in: {dups}")
    else:
        print("✓ No duplicate prerequisites")

    # 检查循环
    visited: set[str] = set()
    in_stack: set[str] = set()
    v_index = {n["id"]: n for n in verify}

    def has_cycle(nid: str) -> bool:
        if nid in in_stack:
            return True
        if nid in visited:
            return False
        in_stack.add(nid)
        for p in v_index[nid].get("prerequisites", []):
            if p in v_index and has_cycle(p):
                return True
        in_stack.remove(nid)
        visited.add(nid)
        return False

    has_any_cycle = False
    for n in verify:
        if n["id"] not in visited:
            if has_cycle(n["id"]):
                print(f"ERROR: Cycle involving {n['id']}")
                has_any_cycle = True
    if not has_any_cycle:
        print("✓ No cycles detected")

    print("\nDone!")


if __name__ == "__main__":
    main()
