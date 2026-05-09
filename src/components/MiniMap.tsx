import { useEffect, useRef, useCallback } from 'react';
import type cytoscape from 'cytoscape';
import type { Domain } from '../types';

interface MiniMapProps {
  domains: Domain[];
  cy: cytoscape.Core | null;
}

const MINI_W = 200;
const MINI_H = 150;

export default function MiniMap({ domains, cy }: MiniMapProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const rafRef = useRef(0);
  const colorMapRef = useRef(new Map<string, string>());

  // 保持领域颜色映射最新
  useEffect(() => {
    colorMapRef.current = new Map(domains.map(d => [d.id, d.color]));
  }, [domains]);

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas || !cy) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    canvas.width = MINI_W * dpr;
    canvas.height = MINI_H * dpr;
    canvas.style.width = MINI_W + 'px';
    canvas.style.height = MINI_H + 'px';
    ctx.scale(dpr, dpr);

    // 背景
    ctx.fillStyle = 'rgba(10, 10, 30, 0.9)';
    ctx.fillRect(0, 0, MINI_W, MINI_H);

    const nodes = cy.nodes();
    if (nodes.length === 0) return;

    // 所有节点的包围盒
    const bbox = nodes.boundingBox({});
    const pad = 30;
    const bx = bbox.x1 - pad;
    const by = bbox.y1 - pad;
    const bw = Math.max(bbox.w + pad * 2, 1);
    const bh = Math.max(bbox.h + pad * 2, 1);

    // 画节点点
    const colors = colorMapRef.current;
    ctx.globalAlpha = 0.7;
    for (const node of nodes) {
      const p = node.position();
      const x = ((p.x - bx) / bw) * MINI_W;
      const y = ((p.y - by) / bh) * MINI_H;
      const domain = node.data('domain') as string;
      ctx.fillStyle = colors.get(domain) || '#888888';
      ctx.beginPath();
      ctx.arc(x, y, 1.5, 0, Math.PI * 2);
      ctx.fill();
    }

    // 画视口矩形
    const vp = cy.extent();
    const vx1 = ((vp.x1 - bx) / bw) * MINI_W;
    const vy1 = ((vp.y1 - by) / bh) * MINI_H;
    const vx2 = ((vp.x2 - bx) / bw) * MINI_W;
    const vy2 = ((vp.y2 - by) / bh) * MINI_H;

    ctx.globalAlpha = 0.12;
    ctx.fillStyle = '#4fc3f7';
    ctx.fillRect(vx1, vy1, vx2 - vx1, vy2 - vy1);

    ctx.globalAlpha = 0.9;
    ctx.strokeStyle = '#4fc3f7';
    ctx.lineWidth = 1.5;
    ctx.strokeRect(vx1, vy1, vx2 - vx1, vy2 - vy1);

    ctx.globalAlpha = 1;
  }, [cy]);

  // 节流重绘
  const scheduleDraw = useCallback(() => {
    cancelAnimationFrame(rafRef.current);
    rafRef.current = requestAnimationFrame(draw);
  }, [draw]);

  // 监听 cytoscape 视口和布局变化
  useEffect(() => {
    if (!cy) return;
    const handler = () => scheduleDraw();
    cy.on('pan zoom layoutstop', handler);
    draw();
    return () => {
      cy.off('pan zoom layoutstop', handler);
      cancelAnimationFrame(rafRef.current);
    };
  }, [cy, scheduleDraw, draw]);

  // 点击小地图导航到对应位置
  const handleClick = useCallback(
    (e: React.MouseEvent<HTMLCanvasElement>) => {
      if (!cy) return;
      const canvas = canvasRef.current;
      if (!canvas) return;

      const rect = canvas.getBoundingClientRect();
      const rx = (e.clientX - rect.left) / rect.width;
      const ry = (e.clientY - rect.top) / rect.height;

      const nodes = cy.nodes();
      if (nodes.length === 0) return;

      const bbox = nodes.boundingBox({});
      const pad = 30;
      const bx = bbox.x1 - pad;
      const by = bbox.y1 - pad;
      const bw = Math.max(bbox.w + pad * 2, 1);
      const bh = Math.max(bbox.h + pad * 2, 1);

      const tx = bx + rx * bw;
      const ty = by + ry * bh;
      const z = cy.zoom();

      cy.animate({
        pan: { x: cy.width() / 2 - tx * z, y: cy.height() / 2 - ty * z },
        duration: 300,
      });
    },
    [cy]
  );

  return (
    <div className="minimap">
      <div className="minimap-title">🗺️ 导航</div>
      <canvas
        ref={canvasRef}
        className="minimap-canvas"
        onClick={handleClick}
      />
    </div>
  );
}
