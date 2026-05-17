---
name: spotify
description: "Spotify: play, search, queue, manage playlists and devices. Includes playback state perception, voice song announcements, background music automation, and Chinese TTS integration."
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  tools: [spotify_playback, spotify_devices, spotify_queue, spotify_search, spotify_playlists, spotify_albums, spotify_library]
  skills: [tts]
metadata:
  hermes:
    tags: [spotify, music, playback, playlists, media, voice-announcement, background-music, chinese-tts]
    related_skills: [tts, gif-search]
---

# Spotify

Control the user's Spotify account via the Hermes Spotify toolset (7 tools). Setup guide: https://hermes-agent.nousresearch.com/docs/user-guide/features/spotify

## When to use this skill

The user says something like "play X", "pause", "skip", "queue up X", "what's playing", "search for X", "add to my X playlist", "make a playlist", "save this to my library", etc.

## The 7 tools

- `spotify_playback` — play, pause, next, previous, seek, set_repeat, set_shuffle, set_volume, get_state, get_currently_playing, recently_played
- `spotify_devices` — list, transfer
- `spotify_queue` — get, add
- `spotify_search` — search the catalog
- `spotify_playlists` — list, get, create, add_items, remove_items, update_details
- `spotify_albums` — get, tracks
- `spotify_library` — list/save/remove with `kind: "tracks"|"albums"`

Playback-mutating actions require Spotify Premium; search/library/playlist ops work on Free.

## Canonical patterns (minimize tool calls)

### "Play <artist/track/album>"
One search, then play by URI. Do NOT loop through search results describing them unless the user asked for options.

```
spotify_search({"query": "miles davis kind of blue", "types": ["album"], "limit": 1})
→ got album URI spotify:album:1weenld61qoidwYuZ1GESA
spotify_playback({"action": "play", "context_uri": "spotify:album:1weenld61qoidwYuZ1GESA"})
```

For "play some <artist>" (no specific song), prefer `types: ["artist"]` and play the artist context URI — Spotify handles smart shuffle. If the user says "the song" or "that track", search `types: ["track"]` and pass `uris: [track_uri]` to play.

### "What's playing?" / "What am I listening to?"
Single call — don't chain get_state after get_currently_playing.

```
spotify_playback({"action": "get_currently_playing"})
```

If it returns 204/empty (`is_playing: false`), tell the user nothing is playing. Don't retry.

### "Pause" / "Skip" / "Volume 50"
Direct action, no preflight inspection needed.

```
spotify_playback({"action": "pause"})
spotify_playback({"action": "next"})
spotify_playback({"action": "set_volume", "volume_percent": 50})
```

### "Add to my <playlist name> playlist"
1. `spotify_playlists list` to find the playlist ID by name
2. Get the track URI (from currently playing, or search)
3. `spotify_playlists add_items` with the playlist_id and URIs

```
spotify_playlists({"action": "list"})
→ found "Late Night Jazz" = 37i9dQZF1DX4wta20PHgwo
spotify_playback({"action": "get_currently_playing"})
→ current track uri = spotify:track:0DiWol3AO6WpXZgp0goxAV
spotify_playlists({"action": "add_items",
                   "playlist_id": "37i9dQZF1DX4wta20PHgwo",
                   "uris": ["spotify:track:0DiWol3AO6WpXZgp0goxAV"]})
```

### "Create a playlist called X and add the last 3 songs I played"
```
spotify_playback({"action": "recently_played", "limit": 3})
spotify_playlists({"action": "create", "name": "Focus 2026"})
→ got playlist_id back in response
spotify_playlists({"action": "add_items", "playlist_id": <id>, "uris": [<3 uris>]})
```

### "Save / unsave / is this saved?"
Use `spotify_library` with the right `kind`.

```
spotify_library({"kind": "tracks", "action": "save", "uris": ["spotify:track:..."]})
spotify_library({"kind": "albums", "action": "list", "limit": 50})
```

### "Transfer playback to my <device>"
```
spotify_devices({"action": "list"})
→ pick the device_id by matching name/type
spotify_devices({"action": "transfer", "device_id": "<id>", "play": true})
```

## Critical failure modes

**`403 Forbidden — No active device found`** on any playback action means Spotify isn't running anywhere. Tell the user: "Open Spotify on your phone/desktop/web player first, start any track for a second, then retry." Don't retry the tool call blindly — it will fail the same way. You can call `spotify_devices list` to confirm; an empty list means no active device.

**`403 Forbidden — Premium required`** means the user is on Free and tried to mutate playback. Don't retry; tell them this action needs Premium. Reads still work (search, playlists, library, get_state).

**`204 No Content` on `get_currently_playing`** is NOT an error — it means nothing is playing. The tool returns `is_playing: false`. Just report that to the user.

**`429 Too Many Requests`** = rate limit. Wait and retry once. If it keeps happening, you're looping — stop.

**`401 Unauthorized` after a retry** — refresh token revoked. Tell the user to run `hermes auth spotify` again.

## URI and ID formats

Spotify uses three interchangeable ID formats. The tools accept all three and normalize:

- URI: `spotify:track:0DiWol3AO6WpXZgp0goxAV` (preferred)
- URL: `https://open.spotify.com/track/0DiWol3AO6WpXZgp0goxAV`
- Bare ID: `0DiWol3AO6WpXZgp0goxAV`

When in doubt, use full URIs. Search results return URIs in the `uri` field — pass those directly.

Entity types: `track`, `album`, `artist`, `playlist`, `show`, `episode`. Use the right type for the action — `spotify_playback.play` with a `context_uri` expects album/playlist/artist; `uris` expects an array of track URIs.

## What NOT to do

- **Don't call `get_state` before every action.** Spotify accepts play/pause/skip without preflight. Only inspect state when the user asked "what's playing" or you need to reason about device/track.
- **Don't describe search results unless asked.** If the user said "play X", search, grab the top URI, play it. They'll hear it's wrong if it's wrong.
- **Don't retry on `403 Premium required` or `403 No active device`.** Those are permanent until user action.
- **Don't use `spotify_search` to find a playlist by name** — that searches the public Spotify catalog. User playlists come from `spotify_playlists list`.
- **Don't mix `kind: "tracks"` with album URIs** in `spotify_library` (or vice versa). The tool normalizes IDs but the API endpoint differs.

---

## (1) 播放状态感知 — Playback State Perception

### 主动心跳轮询（语音播歌 / 背景音乐场景必需）

每首歌曲播放时，主动查询一次当前播放状态，用于：
- 确认是否真正在播放（Spotify 可能卡在 loading 状态）
- 获取歌曲详情用于语音播报
- 触发下一曲检测（背景音乐自动化）

```javascript
// Hermes Agent 实现模式
spotify_playback({"action": "get_currently_playing"})
// → 返回 is_playing, progress_ms, item { name, artists, album, duration_ms }
// 204 No Content = 没有播放任何内容
```

### 状态机

```
IDLE          →  nothing playing, no device
PLAYING       →  is_playing: true
PAUSED        →  is_playing: false, progress_ms > 0
LOADING       →  Spotify 客户端正在缓冲（get_currently_playing 可能返回旧数据）
TRANSITIONING →  歌曲切换瞬间，progress_ms 重置，item 可能为 null
```

### 状态变化检测逻辑（背景音乐自动化核心）

```javascript
// 检测到歌曲切换（TRANSITIONING）
function detect_track_change(prev, curr) {
  if (!prev || !curr) return false
  if (prev.item?.id !== curr.item?.id) return true   // 歌曲ID变了 = 切歌了
  if (prev.is_playing !== curr.is_playing) return true  // 播放↔暂停切换
  return false
}

// 检测播放卡死（LOADING 超时）
function detect_stall(prev, curr, now_ms) {
  if (prev?.is_playing === true && curr?.is_playing === true) {
    if (curr.progress_ms <= prev.progress_ms) {
      // progress 没有前进，可能卡住了
      return now_ms - stall_detected_at > 15000  // 15秒没动 = 卡死
    }
  }
  return false
}
```

### 轮询间隔建议

| 场景 | 轮询间隔 |
|------|---------|
| 语音播歌（播报当前曲） | 播放开始后查询1次即可 |
| 背景音乐监控 | 每30秒查询一次 |
| 语音播报文本生成中 | 停止轮询，播完恢复 |

### 播放异常处理

- **get_currently_playing 返回 204**：Spotify 没有在播放任何内容，无需处理
- **item 为 null 但 is_playing=true**：Spotify 正在加载新曲目，等待 2 秒后重查
- **progress_ms 长时间不变**：可能是 Spotify 客户端卡死，尝试 `spotify_playback({"action": "pause"})` 再 `play`

---

## (2) 语音播歌场景 — Voice Song Announcements

当 Hermes 需要"说出来"当前播放的歌曲时，使用 TTS 技能生成中文语音播报。

### 典型触发语

> "现在放的是什么歌？"、"帮我播报一下当前歌曲"、"这首歌叫什么"

### 播报文本组织原则

- 为耳朵写，不是为眼睛写：口语化、自然
- 短句为主，中文标点停顿
- 包含歌手、专辑（可选）、时长（可选）
- 播报时长控制在 15 秒以内

### 播报模板

```
正在播放：{歌曲名}
歌手：{歌手名}
专辑：{专辑名}  // 可选，专辑名与歌曲名重复时省略
时长：{分:秒}  // 可选，仅当用户主动问及时加入
```

示例：
```
正在播放：夜曲
歌手：周杰伦
专辑：十一月的萧邦
```

### 完整播报流程

```javascript
// Step 1: 获取当前播放状态（单次，不轮询）
spotify_playback({"action": "get_currently_playing"})
// → is_playing: true, item: { name: "夜曲", artists: [{name:"周杰伦"}], album: {name:"十一月的萧邦"}, duration_ms: 258000 }

// Step 2: 组织播报文本
const text = `正在播放：夜曲，歌手：周杰伦，专辑：十一月的萧邦`

// Step 3: 生成 TTS 音频（Edge TTS，优先用 XiaoxiaoNeural）
~/.hermes/hermes-agent/venv/bin/edge-tts \
  --text "正在播放：夜曲，歌手：周杰伦，专辑：十一月的萧邦" \
  --voice "zh-CN-XiaoxiaoNeural" \
  --write-media ~/.hermes/audio_cache/spotify_now_playing.ogg

// Step 4: 发送音频（根据渠道选择发送方式）
// → 通过 send_message(message="MEDIA:/path/to/file.ogg", target="telegram") 发送
```

### 播报时机

| 场景 | 是否播报 |
|------|---------|
| 用户主动问"现在放什么" | ✅ 播报 |
| 语音播歌指令（如"播报当前歌曲"） | ✅ 播报 |
| 背景音乐切换到新歌曲 | ✅ 播报（轻提示） |
| 定时整点报时 + 当前歌曲 | ✅ 播报 |
| 歌曲播放出错/卡住 | ❌ 不播报（避免重复错误提示） |
| 用户正在专注工作（Do Not Disturb） | ❌ 不播报（尊重用户状态） |

### 播报优先级（多任务冲突时）

```
用户语音打断          → 停止当前播报，立即响应
紧急通知              → 压低音乐音量，播报通知
定时任务（整点报时）   → 排队，等待当前播报结束
背景音乐自动切歌       → 轻提示音，不打断主流程
```

---

## (3) 背景音乐自动化 — Background Music Automation

### 核心设计

背景音乐模式下，Hermes 作为"隐形 DJ"，不主动打断用户，但持续监控播放状态并在必要时采取行动。

### 模式 1：持续播放（Free/Premium 通用）

```javascript
// 用户说"放点背景音乐"时的处理流程
// 1. 搜索适合的背景音乐播放列表
spotify_search({"query": "chill lofi study beats", "types": ["playlist"], "limit": 3})
// 2. 播放选中的播放列表
spotify_playback({"action": "play", "context_uri": "spotify:playlist:..."})
// 3. 启动定时轮询（每30秒）
// 4. 监听歌曲切换事件
```

### 模式 2：场景化播放列表

```javascript
// 用户说"工作的时候放什么音乐好"
// 搜索场景播放列表
spotify_search({"query": "focus work study music", "types": ["playlist"], "limit": 5})
// 推荐给用户，用户确认后播放
```

### 歌曲切换检测与自动处理

```javascript
// 背景音乐监控循环
function background_music_monitor() {
  const state = spotify_playback({"action": "get_currently_playing"})
  
  // 检测切歌
  if (state.item && state.item.id !== last_track_id) {
    last_track_id = state.item.id
    on_new_track(state.item)  // 可选：语音提示 / 记录
  }
  
  // 检测播放停止（用户手动停了）
  if (!state.is_playing && state.progress_ms > 0) {
    // 用户按了暂停，不自动恢复
    stop_monitoring()
    return
  }
  
  // 继续轮询
  setTimeout(background_music_monitor, 30000)
}
```

### 自动音量调节（Premium 限定）

```javascript
// 场景：用户开始视频通话 / 语音助手被唤醒
function lower_volume_for_voice() {
  // 逐步降低音量，避免突兀
  for (let v = current_volume; v >= 20; v -= 5) {
    spotify_playback({"action": "set_volume", "volume_percent": v})
    sleep(200)
  }
}

// 场景：通话结束，恢复音量
function restore_volume() {
  spotify_playback({"action": "set_volume", "volume_percent": target_volume})
}
```

### 背景音乐与语音播报的互斥

- 背景音乐播报新歌曲时，使用"轻提示音"而非完整语音播报
- 用户正在说话时，背景音乐自动压低音量（-15dB），说完恢复
- 紧急通知打断时，音乐淡出，播报完成后淡入恢复

---

## (4) 中文播报适配 — Chinese TTS Adaptation

### Edge TTS 中文音色推荐

| 音色 ID | 风格 | 适用场景 |
|---------|------|---------|
| `zh-CN-XiaoxiaoNeural` | 女声，温柔自然（默认） | 通用播报、歌曲介绍 |
| `zh-CN-YunxiNeural` | 男声，轻松活泼 | 快速播报、切换提示 |
| `zh-CN-XiaoyiNeural` | 女声，年轻清新 | 轻提示、背景音乐切换 |
| `zh-CN-YunyangNeural` | 男声，新闻腔正式 | 正式通知、整点报时 |

### 中文播报特殊处理

#### 艺术家名称规范化

Spotify 返回的艺术家名可能是英文或中文，需要适配：
- 英文名：保持原名，不音译
- 中文名：直接使用
- 混排：优先显示中文名

```javascript
// 艺术家名称处理
function format_artists(artists) {
  if (!artists || artists.length === 0) return "未知歌手"
  if (artists.length === 1) return artists[0].name
  if (artists.length === 2) return `${artists[0].name}和${artists[1].name}`
  return `${artists[0].name}等${artists.length}位歌手`
}
```

#### 歌曲时长格式化

```javascript
function format_duration(ms) {
  const totalSeconds = Math.floor(ms / 1000)
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60
  return `${minutes}分${seconds.toString().padStart(2, '0')}秒`
}
```

#### 专辑名称去冗余

有些专辑名和歌曲名重复，需要省略避免啰嗦：
```javascript
// 例如"夜曲"专辑中的歌曲"夜曲"，播报时只说"专辑：十一月的萧邦"而不是重复"夜曲"
function should_include_album(songName, albumName) {
  return !albumName.includes(songName) && songName.length < albumName.length
}
```

### 播报文本示例库

| 场景 | 播报文本 |
|------|---------|
| 播报当前曲 | `正在播放：夜曲，歌手：周杰伦，专辑：十一月的萧邦` |
| 轻提示切歌 | `已切换到：夜曲，周杰伦` |
| 背景音乐模式开启 | `背景音乐已开启，当前播放：chill lofi 学习音乐` |
| 整点报时 | `现在是下午三点整，正在播放：夜曲，周杰伦` |
| 音乐已暂停 | `音乐已暂停，随时说继续播放` |
| 无播放内容 | `目前没有在播放任何音乐，说播放加歌曲名即可开始` |

### 播报速度与情感

- **默认速度**：1.0（Edge TTS 的 `rate` 参数）
- **背景音乐切换提示**：0.9（稍慢，柔和不突兀）
- **紧急通知**：1.1（稍快，紧急感）
- **情感参数**（Edge TTS 不支持，通过音色选择实现）

### 音频格式选择

```javascript
// QQ/微信/Telegram 等 IM 平台：优先 .ogg（Opus 编码，体积小）
// 文件名格式：spotify_now_playing_{timestamp}.ogg

// 音频缓存清理
// 每次生成新播报前，删除旧文件（保留最新1个）
const cache_dir = "~/.hermes/audio_cache/"
const old_files = fs.readdirSync(cache_dir).filter(f => f.startsWith("spotify_"))
old_files.sort()
old_files.slice(0, -1).forEach(f => fs.unlinkSync(cache_dir + f))  // 删除旧文件
```

---

## 集成总览

```
用户请求播放音乐
    ↓
spotify_playback(action=play)        ← Spotify 播放
    ↓
TTS 语音播报（Edge TTS）             ← 中文适配的语音合成
    ↓
send_message(MEDIA: audio.ogg)       ← 发送到用户
    ↓
背景音乐监控（每30秒轮询）           ← 播放状态感知
    ↓
检测到切歌 → 轻提示音 / 记录          ← 自动化处理
```
