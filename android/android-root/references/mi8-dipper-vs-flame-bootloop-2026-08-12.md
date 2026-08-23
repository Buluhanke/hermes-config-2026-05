# MI8 dipper vs flame — boot.img 代号不匹配导致 bootloop（2026-08-12）

## 事件

用户说"MI 8 标准版"，我按 dipper 处理：
- 从 OTA 包提取 boot.img（96MB）→ 超出 boot 分区 64MB
- 从用户发的 dipper.img（57MB）→ 刷了 3 次，全部 bootloop 进 recovery

## 真相

MI 8 有三个型号，代号不同：

| 型号 | 代号 | 特征 |
|------|------|------|
| MI 8 标准版 | dipper | 无指纹 |
| MI 8 **屏幕指纹版** | **flame** | 屏幕指纹 |
| MI 8 UD | ursa | 屏幕指纹+结构光 |

设备代号查询：
```bash
fastboot getvar product
# dipper → 标准版
# flame → 屏幕指纹版
# ursa → UD版
```

当前设备（从 payload_properties.txt）：
- post-build: `Redmi/flame/flame:14/UKQ1.240523.001/V816.0.2.0.UGUINXM`
- **代号是 flame（屏幕指纹版）**，不是 dipper

## boot.img 代号兼容性

**结论：boot.img 代号必须与设备完全一致。**

| boot.img 代号 | 设备代号 | 结果 |
|--------------|----------|------|
| dipper | flame | ❌ bootloop（基带/GPU 固件不兼容）|
| flame | dipper | ❌ bootloop |
| dipper | dipper | ✅ |
| flame | flame | ✅ |

## 教训

1. **不要相信用户的型号描述** — "标准版"可能指屏幕指纹版或无指纹版，必须用 `fastboot getvar product` 确认
2. **bootloop 不一定是大小问题** — 57MB 塞进 64MB 分区没问题，问题是代号不对
3. **dipper 和 flame 的 boot.img 互不兼容** — 即使版本相同（都是 V816.0.2.0.UGUINXM），代号不同也不能混用

## 正确流程

```
Step 1: fastboot getvar product → 确认设备真实代号
Step 2: 根据代号找对应 ROM 包（flame → flame ROM，dipper → dipper ROM）
Step 3: 提取对应代号的 boot.img
Step 4: fastboot boot 测试（不写分区）
Step 5: 成功后再 fastboot flash
```

## flame ROM 下载

需要找 `V816.0.2.0.UGUINXM` 对应的 **flame**（非 dipper）Fastboot 包。

xiaomirom.com / mifirm.net 搜索 "flame" 而非 "dipper"。
