# Automation Pipeline Guide

Create comics that explain automation processes, technical workflows, and digital transformation journeys.

## Content Type Profile

| Attribute | Value |
|-----------|-------|
| Triggers | 自动化流程、技术教程、CI/CD、DevOps、API集成、数据流 |
| Art Style | manga (default), ligne-claire |
| Tone | neutral (default), energetic |
| Layout | webtoon (default), dense |
| Aspect | 3:4 (portrait) |
| Page Count | 8-20 pages |

## Automation Comic Patterns

### Pattern 1: Pipeline Journey (流水线旅程)

Follow a task/item through an automated system:

```
Story Structure: [Task enters] → [Stage 1] → [Stage 2] → [Stage 3] → [Output]

Example: 代码提交 → CI检查 → 自动测试 → 部署上线
```

### Pattern 2: Before/After Comparison (前后对比)

Show manual vs automated process:

```
Structure: Manual process (3-4 pages) → Transformation moment → Automated process (3-4 pages) → Benefits summary
```

### Pattern 3: Character-Led Learning (角色学习)

Ohmsha-style educational comic following character learning automation:

```
Structure: Problem setup → Mentor introduces concept → Gadget/visual metaphor → Application → Mastery
```

### Pattern 4: System Architecture Story (系统架构故事)

Characters exploring and understanding a complex system:

```
Structure: System overview → Sub-component deep dive 1 → Sub-component deep dive 2 → Integration → Full system working
```

## Technical Concept Visualization

### Data Flow Visualization

| Concept | Visual Metaphor |
|---------|-----------------|
| API call | Two characters passing a sealed letter |
| Data pipeline | Assembly line with items moving between stations |
| Queue/buffer | Waiting room with characters orderly in line |
| Event-driven | Dominoes falling, triggering next action |
| Retry logic | Character trying again after failure, different attempt |
| Timeout | Hourglass running out, character looking at watch |

### System Component Personification

Give system components character traits:

| Component | Character Archetype | Visual Traits |
|-----------|--------------------|---------------|
| Database | Wise elder / library keeper | Glasses, books, calm demeanor |
| API Gateway | Gatekeeper / security guard | Uniform, checkpoint booth |
| Load Balancer | Traffic director / orchestra conductor | Baton, directing poses |
| Cache | Quick helper / squirrel with acorns | Small, fast, hiding spots |
| Message Queue | Post office worker | Sorting letters, organized bins |
| Container | Shipping container / traveling room | Box with character inside, portable |
| Microservice | Specialized worker | Tool belt, specific skill set |

### DevOps / CI-CD Visualization

| Stage | Character/Visual | Example Prompt Element |
|-------|-----------------|----------------------|
| Code Commit | Developer at desk, small lightbulb | "git push" shown on screen |
| Build | Factory assembly line | Parts coming together, machine sounds |
| Test | Strict examiner with checklist | Test tubes, checkmarks |
| Deploy | Rocket launch or train departing | Motion lines, excitement |
| Monitor | Control room operator | Multiple screens, alert lights |
| Rollback | Rewind button pressed | Reverse motion, concern |

## Automation Story Templates

### Template 1: API Integration Story

```
Scene: Buyer wants to connect online store to supplier inventory system
Pages 1-2: Problem setup - manual inventory updates causing stock issues
Page 3: Technical team introduces API concept (ohmsha gadget style)
Pages 4-6: Step-by-step API connection process (endpoint → auth → data flow)
Page 7: System working - real-time inventory sync visualized
Page 8: Time saved = more sales focus, happy business owner
```

### Template 2: Factory Automation Journey

```
Scene: Traditional factory upgrading to automated production
Pages 1-2: Factory owner worried about labor costs, quality inconsistency
Page 3: Industry 4.0 mentor introduces smart factory concept
Pages 4-7: Transformation phases (robot arms → sensors → data dashboard)
Page 8: Owner proud showing new efficient factory
Page 9: Quality improves, costs drop - competitive advantage
```

### Template 3: Data Pipeline Comic

```
Scene: Marketing team needs real-time sales dashboard
Pages 1-2: Team staring at outdated weekly reports, missing real-time visibility
Page 3: Data engineer introduces ETL pipeline concept
Pages 4-6: Pipeline visualization (Source → Transform → Load → Dashboard)
Page 7: Live dashboard working, alerts firing correctly
Page 8: Team celebrates data-driven decisions
```

## Technical Accuracy Checklist

| Topic | Accuracy Points |
|-------|----------------|
| API/Integration | Correct use of terms (endpoint, authentication, payload) |
| CI/CD | Realistic pipeline stages, proper terminology |
| Data Pipeline | Correct data flow direction, proper transformation representation |
| Cloud Infrastructure | Correct service icons, realistic architecture patterns |
| Database | Appropriate data model representation |
| DevOps | Realistic tool names, proper workflow stages |

## Automation Comic Prompt Patterns

### Pattern: Character Explaining Technical Concept

```
In style of [ohmsha/manga], with clean line art:

Page [N]: [Character A] is explaining [technical concept] to [Character B]

[Character A] should be pointing at or holding a visual metaphor gadget for [concept]
- [Technical term 1]: Show gadget representing this (e.g., "API" as a translator robot)
- [Technical term 2]: Show gadget representing this (e.g., "database" as organized filing cabinet)

[Character B] should show understanding progressing: confused → curious → "aha" moment

Background elements: Technical diagrams subtly appearing as the explanation progresses
```

### Pattern: System Architecture Overview

```
In style of [ligne-claire/manga], clean technical illustration:

Page [N]: Full system architecture diagram with character figures positioned at key nodes

Visual approach:
- Main system shown as interconnected buildings/platforms
- Data flows shown as animated paths (dashed lines with arrows)
- Each component has a small labeled icon
- Character in corner observing the whole system

Include technical accuracy:
- Correct port numbers when relevant
- Proper protocol icons (HTTPS, WebSocket)
- Realistic data format representations (JSON structure shown)
```

## Animation Hints for Automation Comics

For tools that support animated output:

| Technique | Use For | Visual Hint |
|-----------|---------|-------------|
| Sequential reveal | Pipeline stages, step-by-step | Dashed lines appearing one by one |
| Pulse animation | Active processing, data in motion | Soft glow spreading from component |
| Loop | Continuous processes, monitoring | Circular arrow indicators |
| Flash | Alerts, errors, achievements | Bright highlight on component |
| Pan/zoom | System exploration, detail focus | Camera movement indication |

## Technical Review Requirements

Automation comics need technical review because:

1. Developers/engineers are the target audience
2. Technical inaccuracies destroy credibility immediately
3. Accurate terminology matters for search/discoverability

**Before finalizing prompts for:**
- CI/CD pipelines: Verify with DevOps team member or documentation
- API documentation: Confirm correct endpoint/auth patterns
- Infrastructure: Check cloud provider service capabilities
- Data formats: Confirm realistic JSON/XML structure

## Quality Markers

- [ ] Technical concepts are accurately represented
- [ ] Visual metaphors are intuitive and memorable
- [ ] Pipeline/process flow is logically correct
- [ ] Character expressions show understanding progression
- [ ] Technical terms are used correctly
- [ ] Page titles follow narrative convention (not AI-style titles)
- [ ] End with practical takeaway or application
- [ ] Suitable for engineers reviewing alongside technical docs