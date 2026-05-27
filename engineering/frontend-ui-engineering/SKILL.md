---
name: frontend-ui-engineering
description: 前端UI工程 — 组件化、响应式、可访问性、性能优化。
triggers:
  - "开发新的UI组件"
  - "需要实现响应式布局"
  - "需要优化前端性能"
  - "发现可访问性问题"
  - "需要统一设计系统"
---

# Frontend UI Engineering

## Overview

好的前端不仅是视觉上的美观，更是组件化、可访问、响应式、高性能的结合。用户用各种设备、各种环境访问你的应用，前端需要适配所有场景。

## When to Use

- 开发新的UI组件
- 实现响应式设计
- 优化前端性能
- 修复可访问性问题
- 建立或接入设计系统

## Process

### Phase 1: 组件设计

#### 1.1 组件拆分原则
- 单一职责：每个组件只做一件事
- 可组合：组件可以嵌套组合
- 独立性：组件无外部依赖

#### 1.2 组件API设计
```jsx
// 好的组件API
<Button variant="primary" size="medium" disabled={false}>
  点击我
</Button>

// 不好的组件API
<Button className="btn-primary" style={{fontSize: 14}}>
  点击我
</Button>
```

#### 1.3 状态管理
- 组件状态（useState）
- 提升的状态（props drilling vs Context）
- 服务端状态（React Query/SWR）

### Phase 2: 响应式设计

#### 2.1 移动优先
```css
/* 移动优先 */
.container { padding: 16px; }

/* 平板 */
@media (min-width: 768px) {
  .container { padding: 24px; }
}

/* 桌面 */
@media (min-width: 1024px) {
  .container { padding: 32px; }
}
```

#### 2.2 断点策略
| 断点 | 设备 |
|------|------|
| < 640px | 手机 |
| 640-1024px | 平板 |
| > 1024px | 桌面 |

#### 2.3 弹性布局
- Flexbox用于一维布局
- Grid用于二维布局
- 避免固定宽度，使用相对单位

### Phase 3: 可访问性

#### 3.1 语义化HTML
```html
<!-- 不好 -->
<div onClick={handleClick}>点击</div>

<!-- 好 -->
<button onClick={handleClick}>点击</button>
```

#### 3.2 ARIA属性
```jsx
<button
  aria-label="关闭"
  aria-expanded={isOpen}
  aria-controls="menu"
>
  ✕
</button>
```

#### 3.3 键盘导航
- 所有交互元素可Tab访问
- 焦点样式可见
- 支持Escape关闭模态框

### Phase 4: 性能优化

#### 4.1 渲染优化
- React.memo避免不必要渲染
- useMemo/useCallback缓存计算
- 虚拟列表（大量数据）

#### 4.2 加载优化
- Code Splitting（按需加载）
- 图片懒加载
- 预加载关键资源

#### 4.3 缓存策略
- Service Worker缓存
- 静态资源长期缓存
- API响应缓存

## Common Rationalizations

| 常见借口 | 真相 | 反制 |
|---------|------|------|
| "手机用户不多，专注桌面" | 移动流量往往超过50% | 移动优先设计 |
| "可访问性太麻烦，以后再说" | 可访问性是基本要求，不是锦上添花 | 开发时内建可访问性 |
| "性能优化上线后再做" | 上线后往往没有动力做 | 前端性能是用户体验核心 |

## Red Flags

- 使用div代替button
- 没有keyboard导航
- 图片没有alt
- 颜色对比度不足
- 没有响应式，移动端溢出
- 大量重渲染
- 首屏加载超过3秒

## Verification

验证清单：

- [ ] 语义化HTML
- [ ] ARIA属性正确
- [ ] 键盘导航可用
- [ ] 颜色对比度达标
- [ ] 响应式布局正常
- [ ] 首屏加载<3秒
- [ ] 组件可复用
- [ ] 测试覆盖交互逻辑
