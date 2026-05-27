# Session恢复后capability验证流程

## 触发条件
用户问"XX功能没丢吧" → 直接验证，不废话

## 验证命令

### 终端权限
```bash
echo "terminal ok" && date
```
exit_code=0 → 正常

### 语音功能
直接用 text_to_speech 发一条语音，不发文字确认

### 浏览器/CDP
`lsof -i :9333` 检查Chrome CDP端口

## 原则
- 验证 → 回结果，两句话以内
- 不列清单，不解释过程
- 异常才说要修，正常就结束
