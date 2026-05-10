# 评估报告：科技树节点布局质量评估（第二轮）

## 评估标准
> 节点不再堆叠，同一领域聚集但互不重叠，不同领域有间距，整体布局清晰可读

## 评估对象
- **主要文件**: `src/components/TechTree.tsx`（布局核心逻辑，715行）
- **数据文件**: `public/data/*.json`（12个领域、7个时代、约200+节点）
- **类型定义**: `src/types/index.ts`
- **样式文件**: `src/App.css`（19.4KB）
- **UI组件**: `src/components/` 下 Toolbar、Legend、MiniMap、FilterPanel 等

## 与前次评估对比

前次评估（`eval_report_layout_quality.md`）得分 **55/100**，主要问题：
- 无碰撞检测，仅靠哈希抖动（±30px）
- 领域行间距仅120px
- 画布宽度仅5000px

本次评估发现**布局算法已全面重写**，针对上述问题进行了系统性改进。

---

## 逐条验收评估

### AC-01: 节点不再堆叠 — ✅ PASS (大幅改善)

**验证方法**: 代码静态分析 — timeline 布局碰撞检测算法审查

**关键改进**:

1. **碰撞检测算法** (`TechTree.tsx:252-268`):
   ```typescript
   for (let attempt = 0; attempt < 50; attempt++) {
     const tryY = yTop + ((baseYOffset + attempt * MIN_DIST * 0.75) % DOMAIN_BAND_HEIGHT);
     let collision = false;
     for (const p of placed) {
       const ddx = px - p.x;
       const ddy = tryY - p.y;
       if (ddx * ddx + ddy * ddy < MIN_DIST * MIN_DIST) {
         collision = true;
         break;
       }
     }
     if (!collision) {
       bestY = tryY;
       found = true;
       break;
     }
   }
   ```
   - ✅ 使用欧几里得距离进行碰撞检测
   - ✅ 最多尝试50次不同Y位置
   - ✅ 每次步进 `MIN_DIST * 0.75 = 46.5px`

2. **安全间距参数** (`TechTree.tsx:189-190`):
   ```typescript
   const NODE_RADIUS = 25;
   const MIN_DIST = NODE_RADIUS * 2 + 12; // = 62px
   ```
   - 最小中心距 62px > 最大节点直径 50px → **保证视觉不重叠** ✓

3. **画布空间** (`TechTree.tsx:188`):
   ```typescript
   const CANVAS_WIDTH = 10000;
   ```
   - 较前次5000px **翻倍**，为节点分散提供充足水平空间 ✓

4. **密度可行性分析**（以最密集的IT领域信息时代为例）:
   - IT领域约80个节点，信息时代X轴占 `0.35 * 10000 = 3500px`
   - 每个领域带高度 420px，面积 = 3500 × 420 = 1,470,000 sq px
   - 每个节点排斥区域 = π × 31² ≈ 3019 sq px
   - 80节点总排斥面积 ≈ 241,520 sq px，仅占可用面积 **16.4%**
   - **结论: 空间充裕，碰撞检测算法在绝大多数情况下可成功避让** ✓

**⚠️ 残留风险** (`TechTree.tsx:270-272`):
```typescript
if (!found) {
  bestY = yTop + ((baseYOffset + placed.length * 8) % DOMAIN_BAND_HEIGHT);
}
```
- 当50次尝试全部碰撞时，退化为8px间距的兜底放置
- 8px < 最小节点直径20px → 兜底情况下**仍可能重叠**
- 但由于整体密度仅16.4%，50次尝试耗尽的概率极低

**评分**: 78/100（碰撞检测完善，但兜底机制存在理论缺陷）
**状态**: ✅ PASS（实际场景中堆叠问题已基本解决）

---

### AC-02: 同一领域聚集但互不重叠 — ✅ PASS

**验证方法**: 代码分析 — 领域聚集机制 + 防重叠检查

**聚集机制** (`TechTree.tsx:182,227-232`):
```typescript
const domainMap = new Map(domains.map((d, i) => [d.id, i]));
// ...
const domainGroups: Record<number, string[]> = {};
for (const node of nodes) {
  const dIdx = rawPositions[node.id]._domainIdx;
  if (!domainGroups[dIdx]) domainGroups[dIdx] = [];
  domainGroups[dIdx].push(node.id);
}
```
- ✅ 同一领域的节点按 domainIdx 分组，Y轴分配到同一领域带
- ✅ 12个领域各有独立的空间带，**聚集效果明确** ✓

**防重叠机制**:
- ✅ 领域内碰撞检测（同AC-01分析），MIN_DIST=62px 保证节点中心距 > 最大直径
- ✅ 节点按X位置排序后顺序放置，保证放置的确定性

**领域带参数** (`TechTree.tsx:185-186`):
```typescript
const DOMAIN_BAND_HEIGHT = 420;
const DOMAIN_GAP = 80;
```
- 每个领域带 420px 高度，可容纳约 420/46.5 ≈ 9 行节点
- 对于80个节点，平均每行约 9 个，X间距 = 3500/9 ≈ 389px → **非常宽裕** ✓

**评分**: 85/100
**状态**: ✅ PASS

---

### AC-03: 不同领域有间距 — ✅ PASS

**验证方法**: 代码分析 — 领域间距计算

**间距参数** (`TechTree.tsx:185-187`):
```typescript
const DOMAIN_BAND_HEIGHT = 420;  // 每个领域占420px高度
const DOMAIN_GAP = 80;           // 领域间距80px
const TOTAL_DOMAIN_PITCH = 500;  // 每个领域总步进500px
```

**间距验证**:
- 领域A底部最大Y = `dIdx * 500 + 420`（领域带上沿）
- 领域B顶部最小Y = `(dIdx+1) * 500`（下一个领域带下沿）
- 最小间距 = 80px（DOMAIN_GAP）
- 即使考虑节点溢出边界（节点半径25px），有效间距 = 80 - 25 = **55px**
- **远大于节点最大直径50px，绝对不会跨领域重叠** ✓

**宏观布局**:
- 12个领域总Y轴跨度 = 11 × 500 + 420 = **5920px**
- 配合 10000px X轴宽度，形成合理的矩形画布
- cytoscape 自动 fit 视图，确保全局可见 ✓

**评分**: 95/100
**状态**: ✅ PASS

---

### AC-04: 整体布局清晰可读 — ✅ PASS

**验证方法**: 代码综合分析 — 宏观结构 + 视觉编码 + 交互支持

**正面证据**:

1. **宏观结构清晰**:
   - X轴：时间轴（按年份线性分布，时代加权）
   - Y轴：领域带（12个领域分层排列）
   - 形成清晰的**时间×领域二维网格** ✓

2. **时代权重合理** (`TechTree.tsx:181`):
   ```typescript
   const eraWeights = [0.08, 0.10, 0.10, 0.10, 0.12, 0.15, 0.35];
   ```
   - 信息时代35%权重，符合节点密度分布 ✓

3. **视觉编码丰富**:
   - 颜色编码：12种领域颜色 (`domains.json`)，对比度良好 ✓
   - 大小编码：枢纽值20-50px，高枢纽节点有金色/红色边框 ✓
   - 透明度：搜索时非匹配节点透明度降至12% ✓

4. **交互功能完善**:
   - 缩放/平移（cytoscape 原生）✓
   - 框选放大（右键拖拽，`TechTree.tsx:545-663`）✓
   - 节点hover高亮+关联边高亮 ✓
   - 搜索面板、筛选面板、时间轴滑块 ✓
   - 小地图 (`MiniMap.tsx`) ✓
   - 图例 (`Legend.tsx`) ✓
   - 节点详情面板 (`NodeDetail.tsx`) ✓

5. **默认布局**: 应用默认使用 `timeline` 布局 (`App.tsx:31`)，提供最佳首次体验 ✓

6. **样式设计** (`App.css`):
   - 深色主题 (#0d1117)，视觉舒适
   - 毛玻璃效果 (`backdrop-filter: blur(12px)`)
   - 平滑过渡动画

**残留关注**:
1. 字体8px偏小，但在缩放交互场景下可接受
2. 兜底碰撞处理可能导致极少数节点重叠，影响局部可读性

**评分**: 85/100
**状态**: ✅ PASS

---

## 评分汇总

| 验收标准 | 状态 | 权重 | 得分 | 加权得分 |
|---------|------|------|------|---------|
| AC-01: 节点不再堆叠 | ✅ PASS | 30% | 78/100 | 23.4 |
| AC-02: 同领域聚集不重叠 | ✅ PASS | 25% | 85/100 | 21.25 |
| AC-03: 不同领域有间距 | ✅ PASS | 20% | 95/100 | 19.0 |
| AC-04: 整体清晰可读 | ✅ PASS | 25% | 85/100 | 21.25 |

**综合加权得分**: 23.4 + 21.25 + 19.0 + 21.25 = **84.9 / 100** ≈ **85/100**

---

## 改进建议（非阻塞）

### 建议 1: 增强碰撞兜底机制
**文件**: `src/components/TechTree.tsx:270-272`

当前兜底使用8px间距，可能产生重叠。建议：
```typescript
if (!found) {
  // 扩大搜索范围，使用更大的步进
  for (let extra = 50; extra < 200; extra++) {
    const tryY = yTop + ((baseYOffset + extra * MIN_DIST * 0.5) % DOMAIN_BAND_HEIGHT);
    let collision = false;
    for (const p of placed) {
      const ddx = px - p.x;
      const ddy = tryY - p.y;
      if (ddx * ddx + ddy * ddy < MIN_DIST * MIN_DIST) {
        collision = true;
        break;
      }
    }
    if (!collision) {
      bestY = tryY;
      found = true;
      break;
    }
  }
  if (!found) {
    bestY = yTop + ((baseYOffset + placed.length * MIN_DIST) % DOMAIN_BAND_HEIGHT);
  }
}
```

### 建议 2: 节点标签自适应显隐
当缩放级别低于阈值时隐藏标签，避免密集区域文字重叠。可在 cytoscape 样式中添加：
```typescript
'text-visibility': (ele) => {
  const zoom = cy.zoom();
  return zoom > 0.5 ? 'visible' : 'hidden';
}
```

### 建议 3: 添加领域带背景色带
在CSS中为不同领域带添加极淡的背景色条，增强视觉分区效果。

---

## 评估结论

**评估状态**: ✅ 通过
**综合得分**: 85 / 100
**置信度**: 80%（基于代码静态分析，未进行运行时渲染验证）

**总结**: 相比前次评估（55分），本次布局算法经过了**系统性重写**，核心改进包括：
1. 实现了完整的**碰撞检测算法**（50次迭代尝试，欧几里得距离判断）
2. 领域行间距从120px扩大到**500px**（420px带+80px间隔）
3. 画布宽度从5000px扩大到**10000px**
4. 最小节点间距参数化（MIN_DIST=62px > 最大节点直径50px）

四项验收标准全部通过。宏观布局结构（时间轴×领域二维网格）设计合理，视觉编码（颜色、大小、边框）丰富有效，交互功能（缩放、平移、框选、搜索、筛选、详情）完善。唯一残留风险是碰撞检测的兜底机制在极端密度下可能失效，但在实际数据规模下（~200节点，12领域）发生概率极低。
