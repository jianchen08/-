import type { TechNode, Domain, Era, TechTreeData } from '../types';

async function fetchJson<T>(url: string, timeout = 10000): Promise<T> {
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

  return { nodes, domains, eras };
}
