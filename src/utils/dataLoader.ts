import type { TechNode, Domain, Era, TechTreeData } from '../types';
import { calculateHubScores } from './hubCalculator';

async function fetchJson<T>(url: string, timeout = 15000): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeout);
  try {
    const response = await fetch(url, { signal: controller.signal });
    if (!response.ok) {
      throw new Error(`Failed to fetch ${url}: ${response.statusText}`);
    }
    return (await response.json()) as T;
  } finally {
    clearTimeout(timer);
  }
}

export async function loadTechTreeData(): Promise<TechTreeData> {
  const [nodes, domains, eras] = await Promise.all([
    fetchJson<TechNode[]>('/data/full_data.json'),
    fetchJson<Domain[]>('/data/domains.json'),
    fetchJson<Era[]>('/data/eras.json'),
  ]);

  // 计算 hubScore 并注入
  const scoreMap = calculateHubScores(nodes);
  for (const node of nodes) {
    node.hubScore = scoreMap.get(node.id) ?? 0;
  }

  // 确保 year 字段是数字（数据中有些是字符串）
  for (const node of nodes) {
    if (typeof node.year === 'string') {
      node.year = parseInt(node.year, 10);
    }
  }

  return { nodes, domains, eras };
}
