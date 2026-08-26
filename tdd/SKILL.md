---
name: tdd
description: "测试驱动开发 红-绿-重构循环。Use when 用户要 test-first 写功能/修 bug、提 red-green-refactor、要集成测试、或代码跑不起来需要反馈环"
triggers:
  - 测试驱动 / TDD / red-green-refactor / 先写测试
  - 写功能要带测试 / 修 bug 先补测试
  - 集成测试 / 单元测试 / 验收测试
  - 代码跑不起来、需要稳定反馈环
  - "质量差/测试怎么写"
pitfalls:
  - name: 水平切片（先写完所有测试再写实现）
    description: |
      一次性写一堆测试，再一次性写实现。批量测试验证的是「想象中的行为」，
      对真实改动不敏感，等于没测。
    fix: |
      走**垂直切片**：一个测试 → 一份最小实现 → 重复。每个测试是响应当前周期学到的「示踪弹」。
  - name: 测实现细节而非公共接口
    description: |
      mock 内部协作者、测私有方法、走旁路（直接查数据库而非走接口）。
      特征：重构后行为没变但测试挂了。
    fix: |
      只测**预对齐的 seam**（公共边界）。写测试前先写下被测 seam 并与用户确认。
      没有确认的 seam 不写测试。
  - name: 同义反复断言
    description: |
      断言用和代码相同方式重算期望值（expect(add(a,b)).toBe(a+b)），
      或手算快照、常量等于自身——构造性通过，永远不可能与代码冲突。
    fix: |
      期望值必须来自**独立真相源**：已知正确字面量、手工演算示例、spec。
  - name: 重构混进红-绿循环
    description: 在 red→green 实现周期里顺手重构，破坏最小实现纪律。
    fix: |
      重构属于 review 阶段（见 code-review 技能），不进红绿实现周期。
      每个周期只做：写失败测试 → 最小实现通过 → 下一周期。
  - name: 提前猜接口形状
    description: 模块该多深、seam 在哪、接口该暴露什么还没定就写测试。
    fix: |
      接口形状本身成疑时，调 codebase-design 技能拿词汇（module/interface/depth/seam/adapter），
      那是共享出处，是参考不是会话。
---

# Test-Driven Development — 测试驱动开发

源自 Matt Pocock `skills/engineering/tdd`，改写为 Hermes 技能。TDD 是 **red → green** 循环；本技能让这个循环产出「值得保留的测试」。

## 何时触发
用户要 test-first 写功能/修 bug、提 red-green-refactor、要集成测试，或代码缺乏反馈环。

## 探索前置
先读仓库 `CONTEXT.md`（若有），让测试名和接口词汇匹配项目领域语言；尊重所在区域的 ADR。

## 什么是好测试
测试通过**公共接口**验证行为，不验证实现细节。代码可整体重写，测试不应破。「用户能用有效购物车结账」读起来像规格说明，能扛重构。

延伸：`tests.md`（示例）、`mocking.md`（mock 指南）在原始仓库，落地时可自写参考文件。

## Seam：测试落在哪
**seam** = 你观察行为而不伸入内部的公共边界。测试只活在 seam 上，绝不贴内部。

**只测预对齐的 seam。** 写任何测试前，先写下被测 seam 并**与用户确认**。不可能测一切，提前对齐让测试精力落在关键路径和复杂逻辑上，而非每个边界情况。

问自己：「公共接口是什么，该测哪些 seam？」

当接口形状本身成疑（模块该多深、seam 在哪、该暴露什么）→ 调 `codebase-design` 技能拿词汇。它是共享出处、是参考，不是要跑的会话。

## 反模式（见 pitfalls）
实现耦合 / 同义反复 / 水平切片 —— 三条最常犯，每条在 pitfalls 有 fix。

## 循环规则
- **红先于绿**：先写失败测试，再只写够过的代码。不预判未来测试、不加投机特性。
- **一次一片**：每周期一个 seam、一个测试、一份最小实现。
- **重构不在循环内**：属于 review 阶段（见 `code-review`），不进红绿实现周期。

## Hermes 落地建议
- 周期用 `execute_code` / terminal 跑测试，确认 red 再写实现。
- 多个独立 seam 可并行 delegate，但每个 delegate 内部仍走垂直切片。
- 周期结束不要把多片测试合并成一批再实现——严格一对一。
