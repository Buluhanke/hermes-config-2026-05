---
name: songwriting-and-ai-music
description: "Songwriting craft and Suno AI music prompts."
tags: [songwriting, music, suno, parody, lyrics, creative]
platforms: [linux, macos, windows]
triggers:
  - writing a song
  - song lyrics
  - music prompt
  - suno prompt
  - parody song
  - adapting a song
  - AI music generation
---

# Songwriting & AI Music Generation

Everything here is a GUIDELINE, not a rule. Art breaks rules on purpose.
Use what serves the song. Ignore what doesn't.

---

## 1. Song Structure (Pick One or Invent Your Own)

Common skeletons — mix, modify, or throw out as needed:

```
ABABCB  Verse/Chorus/Verse/Chorus/Bridge/Chorus    (most pop/rock)
AABA    Verse/Verse/Bridge/Verse (refrain-based)    (jazz standards, ballads)
ABAB    Verse/Chorus alternating                    (simple, direct)
AAA     Verse/Verse/Verse (strophic, no chorus)     (folk, storytelling)
```

The six building blocks:
- Intro      — set the mood, pull the listener in
- Verse      — the story, the details, the world-building
- Pre-Chorus — optional tension ramp before the payoff
- Chorus     — the emotional core, the part people remember
- Bridge     — a detour, a shift in perspective or key
- Outro      — the farewell, can echo or subvert the rest

You don't need all of these. Some great songs are just one section
that evolves. Structure serves the emotion, not the other way around.

---

## 2. Rhyme, Meter, and Sound

RHYME TYPES (from tight to loose):
- Perfect: lean/mean
- Family: crate/braid
- Assonance: had/glass (same vowels, different endings)
- Consonance: scene/when (different vowels, similar endings)
- Near/slant: enough to suggest connection without locking it down

Mix them. All perfect rhymes can sound like a nursery rhyme.
All slant rhymes can sound lazy. The blend is where it lives.

INTERNAL RHYME: Rhyming within a line, not just at the ends.
  "We pruned the lies from bleeding trees / Distilled the storm
   from entropy" — "lies/flies," "trees/entropy" create internal echoes.

METER: The rhythm of stressed vs unstressed syllables.
- Matching syllable counts between parallel lines helps singability
- The STRESSED syllables matter more than total count
- Say it out loud. If you stumble, the meter needs work.
- Intentionally breaking meter can create emphasis or surprise

---

## 3. Emotional Arc and Dynamics

Think of a song as a journey, not a flat road.

ENERGY MAPPING (rough idea, not prescription):
  Intro: 2-3  |  Verse: 5-6  |  Pre-Chorus: 7
  Chorus: 8-9  |  Bridge: varies  |  Final Chorus: 9-10

The most powerful dynamic trick: CONTRAST.
- Whisper before a scream hits harder than just screaming
- Sparse before dense. Slow before fast. Low before high.
- The drop only works because of the buildup
- Silence is an instrument

"Whisper to roar to whisper" — start intimate, build to full power,
strip back to vulnerability. Works for ballads, epics, anthems.

---

## 4. Writing Lyrics That Work

SHOW, DON'T TELL (usually):
- "I was sad" = flat
- "Your hoodie's still on the hook by the door" = alive
- But sometimes "I give my life" said plainly IS the power

THE HOOK:
- The line people remember, hum, repeat
- Usually the title or core phrase
- Works best when melody + lyric + emotion all align
- Place it where it lands hardest (often first/last line of chorus)

PROSODY — lyrics and music supporting each other:
- Stable feelings (resolution, peace) pair with settled melodies,
  perfect rhymes, resolved chords
- Unstable feelings (longing, doubt) pair with wandering melodies,
  near-rhymes, unresolved chords
- Verse melody typically sits lower, chorus goes higher
- But flip this if it serves the song

AVOID (unless you're doing it on purpose):
- Cliches on autopilot ("heart of gold" without earning it)
- Forcing word order to hit a rhyme ("Yoda-speak")
- Same energy in every section (flat dynamics)
- Treating your first draft as sacred — revision is creation

---

## 5. Parody and Adaptation

When rewriting an existing song with new lyrics:

THE SKELETON: Map the original's structure first.
- Count syllables per line
- Mark the rhyme scheme (ABAB, AABB, etc.)
- Identify which syllables are STRESSED
- Note where held/sustained notes fall

FITTING NEW WORDS:
- Match stressed syllables to the same beats as the original
- Total syllable count can flex by 1-2 unstressed syllables
- On long held notes, try to match the VOWEL SOUND of the original
  (if original holds "LOOOVE" with an "oo" vowel, "FOOOD" fits
   better than "LIFE")
- Monosyllabic swaps in key spots keep rhythm intact
  (Crime -> Code, Snake -> Noose)
- Sing your new words over the original — if you stumble, revise

CONCEPT:
- Pick a concept strong enough to sustain the whole song
- Start from the title/hook and build outward
- Generate lots of raw material (puns, phrases, images) FIRST,
  then fit the best ones into the structure
- If you need a specific line somewhere, reverse-engineer the
  rhyme scheme backward to set it up

KEEP SOME ORIGINALS: Leaving a few original lines or structures
intact adds recognizability and lets the audience feel the connection.

---

## 6. Suno AI Prompt Engineering

### Style/Genre Description Field

FORMULA (adapt as needed):
  Genre + Mood + Era + Instruments + Vocal Style + Production + Dynamics

```
BAD:  "sad rock song"
GOOD: "Cinematic orchestral spy thriller, 1960s Cold War era, smoky
       sultry female vocalist, big band jazz, brass section with
       trumpets and french horns, sweeping strings, minor key,
       vintage analog warmth"
```

DESCRIBE THE JOURNEY, not just the genre:
```
"Begins as a haunting whisper over sparse piano. Gradually layers
 in muted brass. Builds through the chorus with full orchestra.
 Second verse erupts with raw belting intensity. Outro strips back
 to a lone piano and a fragile whisper fading to silence."
```

TIPS:
- V4.5+ supports up to 1,000 chars in Style field — use them
- NO artist names or trademarks. Describe the sound instead.
  "1960s Cold War spy thriller brass" not "James Bond style"
  "90s grunge" not "Nirvana-style"
- Specify BPM and key when you have a preference
- Use Exclude Styles field for what you DON'T want
- Unexpected genre combos can be gold: "bossa nova trap",
  "Appalachian gothic", "chiptune jazz"
- Build a vocal PERSONA, not just a gender:
  "A weathered torch singer with a smoky alto, slight rasp,
   who starts vulnerable and builds to devastating power"

### Metatags (place in [brackets] inside lyrics field)

STRUCTURE:
  [Intro] [Verse] [Verse 1] [Pre-Chorus] [Chorus]
  [Post-Chorus] [Hook] [Bridge] [Interlude]
  [Instrumental] [Instrumental Break] [Guitar Solo]
  [Breakdown] [Build-up] [Outro] [Silence] [End]

VOCAL PERFORMANCE:
  [Whispered] [Spoken Word] [Belted] [Falsetto] [Powerful]
  [Soulful] [Raspy] [Breathy] [Smooth] [Gritty]
  [Staccato] [Legato] [Vibrato] [Melismatic]
  [Harmonies] [Choir] [Harmonized Chorus]

DYNAMICS:
  [High Energy] [Low Energy] [Building Energy] [Explosive]
  [Emotional Climax] [Gradual swell] [Orchestral swell]
  [Quiet arrangement] [Falling tension] [Slow Down]

GENDER:
  [Female Vocals] [Male Vocals]

ATMOSPHERE:
  [Melancholic] [Euphoric] [Nostalgic] [Aggressive]
  [Dreamy] [Intimate] [Dark Atmosphere]

SFX:
  [Vinyl Crackle] [Rain] [Applause] [Static] [Thunder]

Put tags in BOTH style field AND lyrics for reinforcement.
Keep to 5-8 tags per section max — too many confuses the AI.
Don't contradict yourself ([Calm] + [Aggressive] in same section).

### Custom Mode
- Always use Custom Mode for serious work (separate Style + Lyrics)
- Lyrics field limit: ~3,000 chars (~40-60 lines)
- Always add structural tags — without them Suno defaults to
  flat verse/chorus/verse with no emotional arc

---

## 7. Phonetic Tricks for AI Singers

AI vocalists don't read — they pronounce. Help them:

PHONETIC RESPELLING:
- Spell words as they SOUND: "through" -> "thru"
- Proper nouns are highest failure rate — test early
- "Nous" -> "Noose" (forces correct pronunciation)
- Hyphenate to guide syllables: "Re-search", "bio-engineering"

DELIVERY CONTROL:
- ALL CAPS = louder, more intense
- Vowel extension: "lo-o-o-ove" = sustained/melisma
- Ellipses: "I... need... you" = dramatic pauses
- Hyphenated stretch: "ne-e-ed" = emotional stretch

ALWAYS:
- Spell out numbers: "24/7" -> "twenty four seven"
- Space acronyms: "AI" -> "A I" or "A-I"
- Test proper nouns/unusual words in a short 30-second clip first
- Once generated, pronunciation is baked in — fix in lyrics BEFORE

---

## 8. Workflow

1. Write the concept/hook first — what's the emotional core?
2. If adapting, map the original structure (syllables, rhyme, stress)
3. Generate raw material — brainstorm freely before structuring
4. Draft lyrics into the structure
5. Read/sing aloud — catch stumbles, fix meter
6. Build the Suno style description — paint the dynamic journey
7. Add metatags to lyrics for performance direction
8. Generate 3-5 variations minimum — treat them like recording takes
9. Pick the best, use Extend/Continue to build on promising sections
10. If something great happens by accident, keep it

EXPECT: ~3-5 generations per 1 good result. Revision is normal.
Style can drift in extensions — restate genre/mood when extending.

---

## 9. Lessons Learned

- Describing the dynamic ARC in the style field matters way more
  than just listing genres. "Whisper to roar to whisper" gives
  Suno a performance map.
- Keeping some original lines intact in a parody adds recognizability
  and emotional weight — the audience feels the ghost of the original.
- The bridge slot in a song is where you can transform imagery.
  Swap the original's specific references for your theme's metaphors
  while keeping the emotional function (reflection, shift, revelation).
- Monosyllabic word swaps in hooks/tags are the cleanest way to
  maintain rhythm while changing meaning.
- A strong vocal persona description in the style field makes a
  bigger difference than any single metatag.
- Don't be precious about rules. If a line breaks meter but hits
  harder, keep it. The feeling is what matters. Craft serves art,
  not the other way around.

---

## 10. Chinese Lyrics Optimization 中文歌词优化技巧

Suno 对中文的支持在持续进步，但中文有其独特的音韵挑战。以下是让中文歌词在 Suno 中表现更好的经验：

### 声调与旋律的配合

普通话有四声 + 轻声，阴平/阳平/上声/去声：
- 一声（高平）：适合高亢旋律
- 二声（上升）：适合上行旋律
- 三声（降升）：注意在旋律高点时可能变调
- 四声（下降）：适合下行或重拍

窍门：把歌词读出来，顺着说话的自然语调走，Suno 更可能发出自然的音高。

### 押韵策略

中文押韵比英文更严格，因为中文单词通常单音节：
- 偶数句押韵最稳（2/4/6/8句...）
- 邻韵：ang/eng/ing 可以互通（帮/疼/情）
- 句内押韵比句尾押韵更自然，听感更像说话而非念经

避免：全文同一个韵脚，听感像绕口令。

### 字词密度控制

中文信息密度高，一句话往往比英文长：
- 每句 7-9 个字是黄金区间（跟英文 8-12 音节对应）
- 超过 12 字 / 句，Suno 容易吞字或节奏乱
- 如果信息量大，拆成短句，加 [Spoken Word] 标签

### 避免的陷阱

- 多音字：提前标音，例"行"读 xíng 不读 háng
- 同音混淆：Suno 可能把"业绩"读成"野鸡"，考虑换词
- 太文艺的词：Suno 对白话中文的理解好于文言/典故
- 品牌名/成语：拆开读或用谐音，Suno 对陌生词组容易乱发音

### 常用优化写法

```
# 原文（容易翻车）
业绩突破，遥遥领先

# 优化（更口语，更清晰）
业绩噌噌往上涨
排名稳稳坐头牌
```

```
# 原文（多音字风险）
和谐共处，行稳致远

# 优化（消除歧义）
大家齐心向前走
稳稳当当到远方
```

---

## 11. Commercial Scene Applications 商业场景应用

AI 音乐生成在商业场景中的实际价值：快速、低成本、可定制。以下是主流场景的适配思路：

### 广告音乐 / BGM

需求特点：15-60秒，情感明确，品牌调性匹配，不抢戏。

| 场景 | 情绪关键词 | 推荐风格描述 |
|------|-----------|-------------|
| 电商促销 | 兴奋、积极、紧迫 | Upbeat pop, 120+BPM, hand-clap rhythms, positive choir |
| 品牌故事 | 温暖、信任、叙事感 | Cinematic acoustic, soft piano, warm strings, gentle build |
| 科技产品 | 现代、未来感、干净 | Electronic ambient, minimalist synth, clean production |
| 食品饮料 | 愉悦、轻松、生活感 | Bossa nova, acoustic guitar, warm female vocal |
| 汽车/奢侈品 | 大气、高级、沉稳 | Orchestral epic, grand piano, cinematic sweep |

提示：
- 广告音乐不要有完整歌词，人声哼鸣 > 清晰歌词
- 用 [Instrumental] 标签避免人声干扰画面
- 如果必须有歌词，控制在 2 句话以内，主打记忆点

### 品牌主题曲 / Jingle

需求特点：5-15秒，极简，记忆点强，可循环。

写法：
- 核心品牌名/口号 → 3-5个音节 → 重复
- 结构：品牌名 + 核心词 + 情绪词 + 重复品牌名
- 押韵必须完美，因为短到没有上下文救场

```
示例（健身品牌）：
燃烧吧 燃烧吧 Every day
[品牌名] Every day
```

### 影视/短视频配乐

需求特点：情绪跟随画面，内容驱动，可无缝循环。

- 开头悬念：[Low Energy] + [Melancholic] + [Building Energy]
- 高潮推进：[High Energy] + [Explosive] + drums building
- 结尾落版：[Gradual swell] + [Fading] + [Outro]
- 循环段：用 [Instrumental Break] 标注适合循环的位置

### 播客/有声内容开场/结尾

需求特点：5-10秒，不干扰人声，标志性但不强硬。

推荐风格：
- Talk show opener: Energetic indie rock, guitar + drums, positive
- 知识类: Warm ambient, soft piano, subtle synth pad
- 新闻/严肃: Cinematic minimal, low register, subtle tension

---

## 12. 1688 Product Introduction Music 1688产品介绍配乐

1688（阿里巴巴批发平台）的产品视频有自己的风格语言——快、直接、信息密集、工厂风。以下是针对这类内容的配乐适配：

### 1688视频的节奏特点

- 时长：15-60秒为主（有些更短）
- 节奏：快切换，多产品特写，信息轰炸
- 配音：中文讲解，语速快，工厂老板/老板娘出镜多
- 调性：实在、接地气、便宜大碗、走量感

### 配乐适配策略

**风格选择：**
```
Positive wholesale, upbeat Chinese factory style, energetic
drum beat, bright synth melody, hand-clap percussion,
confident male vocal, 110 BPM, modern commercial pop
```

**节奏匹配：**
- 视频节奏快 → 选 100-120 BPM 的曲目
- 切换快 → 选择整首歌变化不多、Hook 明显的段落
- 不需要完整歌曲，用 [Instrumental] + 选 Hook 段落

**情绪关键词（中英混写效果更好）：**
- 工厂风：factory energy, wholesale prices, bulk orders
- 活力感：energetic, upbeat, positive, confident
- 现代感：modern pop, contemporary beat, fresh sound
- 信任感：steady rhythm, reliable groove, professional

### 产品类型适配音乐风格

| 产品类型 | 推荐风格描述 |
|---------|-------------|
| 服装/配饰 | Fresh fashion pop, female vocal, modern beat, 118 BPM |
| 电子配件 | Tech positive, electronic synth, clean production, 120 BPM |
| 家居/家装 | Warm home feeling, acoustic guitar, cozy strings, 95 BPM |
| 玩具/母婴 | Playful cartoon bounce, bright melody, happy energy, 125 BPM |
| 机械/工业 | Epic industrial, powerful drums, confident brass, 105 BPM |
| 食品/农产品 | Earthy wholesome, acoustic warm, natural feeling, 90 BPM |

### 1688场景专用 Prompt 模板

```
Upbeat Chinese wholesale commercial, energetic pop beat,
modern production, positive energy, confident vocal,
factory price feeling, bulk order excitement,
professional yet approachable, 115 BPM, clean mix
```

### 实操建议

1. **先选风格描述，再填中文歌词**（如果需要人声）
2. **避开：太高级/太文艺** — 1688 受众要的是实在感
3. **避开：太土/太老** — 05年彩铃风会显得廉价
4. **选 Hook 段落** — Suno 生成后，用 Extend 延续最好的 30 秒
5. **音量注意** — 配乐要低于人声，通常 -12dB 到 -18dB

---

## 13. Automated Generation Workflow 自动化生成流程

把 Suno 音乐生成嵌入标准化工作流，减少人工干预，提升批量产出质量。

### 基础自动化架构

```
输入（产品信息/情绪关键词）
    ↓
AI 歌词生成（Claude/GPT）
    ↓
Suno Prompt 组装
    ↓
Suno API / 手动生成
    ↓
音频筛选与评级
    ↓
输出（成品音频 + 适用场景标签）
```

### Step 1：信息输入标准化

建立模板，一次输入，多场景输出：

```markdown
## 产品/项目信息
- 产品名称：
- 核心卖点（3个）：
- 目标受众：
- 视频时长：
- 情绪调性（可选：活力/温暖/高级/科技/接地气）：

## 输出要求
- 是否需要歌词： 是 / 否
- 语种： 中文 / 英文 / 中英混
- 风格偏好：
```

### Step 2：AI 辅助歌词生成

用 Claude/GPT 根据输入生成多版本歌词：

```
 Prompt 示例：
"为一款 [产品类型] 写 3 版不同风格的歌词，
用于 1688 产品视频背景音乐，时长 30 秒。
风格分别是：活力促销风、品质感高级风、工厂批发风。
每版 4 句话，押韵，口语化，不要太文艺。"
```

### Step 3：Suno Prompt 自动组装

把歌词 + 风格描述拼接成完整 Suno Prompt：

```
Style 字段模板：
[Emotion] commercial, [Genre], [BPM] BPM,
[Instruments], [Vocal description],
[Dynamic journey summary]

Lyrics 字段：
[Structural tags] + [Generated lyrics]
```

### Step 4：批量生成与筛选

策略：一次生成 3-5 首，筛选维度：
- 节奏是否匹配视频节奏
- 情绪是否准确
- 有没有明显的 AI 瑕疵（怪音/破音/节奏崩）
- 混音是否干净（没有人声泄露到不该有的地方）

评级标准建议：
```
A：直接可用，无需修改
B：可用，需要小幅调整（延长/裁剪/换段）
C：部分可用，提取其中一段
D：废弃
```

### Step 5：输出交付标准化

每首成品附上元数据：
```yaml
filename: product_1688_clothing_v1.mp3
duration: 32s
bpm: 118
mood: energetic, wholesale, positive
scene: 1688 product video / 电商促销
suno_style_used: "Upbeat Chinese wholesale commercial..."
lyrics_used: "老板疯了一样推荐..."
rating: A
notes: "Hook 段落从 0:08 开始最好"
```

### 工具链推荐

| 环节 | 工具 |
|------|------|
| 歌词生成 | Claude / GPT（API 调用） |
| Suno 生成 | Suno.com（手动或 unofficial API） |
| 音频剪辑 | FFmpeg（命令行批量裁剪） |
| 格式转换 | FFmpeg（MP3/WAV/AAC） |
| 元数据管理 | CSV / Notion / Airtable |
| 批量存储 | 阿里云 OSS / 腾讯云 COS / 本地 NAS |

### 典型批量生产场景

**1688 产品视频 BGM 批量生产（每天 10-20 首）：**

1. 早晨整理产品列表（CSV 导入）
2. AI 批量生成歌词 + 风格描述（Claude API batch）
3. Suno 批量生成（3-5 首/产品）
4. 人工快速听筛（每首 30 秒，标记 A/B/C/D）
5. FFmpeg 批量裁剪 + 统一格式
6. 按产品 ID 归档，附元数据 CSV
7. 当日交付给视频剪辑团队

预期产能：熟练操作后，1首/5-10分钟（从输入到可交付）。

---

## 附录：快速参考卡

### Suno 风格描述检查清单

```
[ ] Genre（音乐类型）
[ ] Era/Feel（年代感或风格感）
[ ] BPM（如果在意节奏）
[ ] Key（如果在意调性）
[ ] Instruments（主要乐器）
[ ] Vocal type（人声描述）
[ ] Energy arc（动态旅程：从弱到强/从头到尾高能等）
[ ] Exclude（明确不要什么）
```

### 歌词标签速查

| 标签 | 用途 |
|------|------|
| [Verse] [Chorus] [Bridge] | 结构标记 |
| [Whispered] [Belted] [Powerful] | 人声表现 |
| [Building Energy] [Explosive] | 动态走向 |
| [Instrumental] | 纯器乐 |
| [Male Vocals] [Female Vocals] | 性别指定 |
| [Melancholic] [Euphoric] | 情绪氛围 |

### 常见问题排查

| 问题 | 解决方案 |
|------|---------|
| 人声发音奇怪 | phonetic respelling，在歌词中标注发音 |
| 风格漂移 | 风格描述中重述核心关键词 |
| 节奏不对 | 指定 BPM，加入 percussion/drummachine |
| 生成失败/报错 | 降低风格描述复杂度，分步生成 |
| 中文听起来像乱码 | 用英文风格描述 + 中文歌词，或用 [Spoken Word] |
| 重复段落太多 | 加入 [Bridge] / [Breakdown] 标签制造变化 |
