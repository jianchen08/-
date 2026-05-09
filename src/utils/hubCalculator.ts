import type { TechNode } from '../types';

/**
 * 计算每个节点的枢纽值（hubScore）。
 * 枢纽值 = 被其他节点 prerequisites 引用的次数，归一化到 0-100。
 * 返回 Map<nodeId, hubScore>，不修改输入。
 */
export function calculateHubScores(nodes: TechNode[]): Map<string, number> {
  // 统计每个节点被引用的次数
  const refCount = new Map<string, number>();
  for (const node of nodes) {
    refCount.set(node.id, 0);
  }

  for (const node of nodes) {
    for (const prereq of node.prerequisites) {
      const count = refCount.get(prereq);
      if (count !== undefined) {
        refCount.set(prereq, count + 1);
      }
    }
  }

  // 找到最大引用次数用于归一化
  let maxCount = 0;
  for (const count of refCount.values()) {
    if (count > maxCount) {
      maxCount = count;
    }
  }

  // 归一化到 0-100 并写入结果 Map
  const scoreMap = new Map<string, number>();
  for (const node of nodes) {
    const count = refCount.get(node.id) ?? 0;
    scoreMap.set(node.id, maxCount > 0 ? Math.round((count / maxCount) * 100) : 0);
  }
  return scoreMap;
}

/** 获取按 hubScore 降序排列的节点 ID 列表 */
export function getRankedNodeIds(nodes: TechNode[], scoreMap: Map<string, number>): string[] {
  return [...nodes]
    .sort((a, b) => (scoreMap.get(b.id) ?? 0) - (scoreMap.get(a.id) ?? 0))
    .map((n) => n.id);
}
