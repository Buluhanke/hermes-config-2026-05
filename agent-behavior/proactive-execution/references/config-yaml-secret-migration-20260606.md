# config.yaml Secret Migration Workflow (2026-06-06 实战)

**场景**：`config.yaml` 里有 N 处明文 API key，需要全部换成 `${ENV_VAR}` 占位符，`.env` 里同名变量已存在。

**为什么不是简单 sed**：见 `proactive-execution` 规则 31（BSD sed 假成功）+ 规则 32（patch 工具拒绝）。

## 实测可用的 Python 一次性脚本

```python
# ~/.hermes/scripts/migrate_config_secrets.py
import re
import sys
from datetime import datetime

CONFIG = '/Users/aimac/.hermes/config.yaml'
BACKUP = f'/Users/aimac/.hermes/config.yaml.bak.{datetime.now().strftime("%Y%m%d_%H%M%S")}'

# 改前：定义要替换的精确字串映射（不用 regex，避免长 key 转义）
MAPPINGS = [
    # (old_string_in_yaml, new_placeholder)
    ('api_key: sk-290...6e18',                    'api_key: ${MINIMAX_CN_API_KEY}'),
    ('api_key: nvapi-CId6hrsrYSRJh...',           'api_key: ${NVIDIA_API_KEY}'),
    ('api_key: sk-or-...87b6',                    'api_key: ${OPENROUTER_API_KEY}'),
    ('api_key: sk-94t...bVpH',                    'api_key: ${APIHUB_API_KEY}'),
    # ... 按你 config.yaml 实际内容加
]

def main():
    with open(CONFIG) as f:
        content = f.read()

    # 改前数
    before_total = sum(content.count(old) for old, _ in MAPPINGS)
    print(f"改前明文 key 总数: {before_total}")

    # 替换
    total_replaced = 0
    for old, new in MAPPINGS:
        n = content.count(old)
        if n > 0:
            content = content.replace(old, new)
            total_replaced += n
            print(f"  {n:2} 处: {old[:40]:40} → {new}")
        else:
            print(f"  0 处: {old[:40]} (未找到，跳过)")

    # 改后数（必须为 0）
    after_total = sum(content.count(old) for old, _ in MAPPINGS)
    print(f"改后明文 key 总数: {after_total}")
    print(f"共替换: {total_replaced} 处")

    if after_total > 0:
        print(f"❌ 还有 {after_total} 处未替换，请检查 MAPPINGS 列表")
        sys.exit(1)

    # 备份（如果还没备份）
    import shutil
    shutil.copy2(CONFIG, BACKUP)
    print(f"✅ 备份到: {BACKUP}")

    # 写回
    with open(CONFIG, 'w') as f:
        f.write(content)
    print(f"✅ 已写入: {CONFIG}")

    # 验证（hermes config show 展开占位符）
    import subprocess
    result = subprocess.run(['hermes', 'config', 'show'],
                          capture_output=True, text=True, timeout=10)
    api_key_lines = [l for l in result.stdout.split('\n') if 'api_key' in l][:10]
    print("\n── hermes config show 验证（前 10 行 api_key）──")
    for line in api_key_lines:
        print(f"  {line}")

if __name__ == '__main__':
    main()
```

## 配套：用 `.env` 占位符前的"变量存在性"核对脚本

```bash
# ~/.hermes/scripts/check_env_vars.sh
ENV_FILE="$HOME/.hermes/.env"
CONFIG_FILE="$HOME/.hermes/config.yaml"

echo "── .env 变量存在性核对 ──"
for var in $(grep -oE '\$\{[A-Z_]+\}' "$CONFIG_FILE" | sort -u | sed 's|\${||;s|}||'); do
    if grep -q "^${var}=" "$ENV_FILE" 2>/dev/null; then
        echo "  ✅ $var"
    else
        echo "  ❌ $var 缺失！需要 echo '$var=*** 真实值>' >> $ENV_FILE"
    fi
done
```

## 关键避坑（实战验证 2026-06-06）

| 坑 | 解决 |
|---|---|
| **`patch` 工具拒绝写 `config.yaml`** | 走 `hermes config set`（顶层字段）或 Python 文件读写（列表项） |
| **`sed -i ''` 假成功**（打印"✅"但文件没变） | 改用 Python 或 `perl -pi -e` |
| **`hermes config set` 不能改列表项** | 用 Python 读 yaml 再写（**不是** 简单 string replace，因为 yaml 缩进敏感） |
| **`fallback_providers` vs `custom_providers` 状态不一致** | 改前用 `grep -nE "api_key:" config.yaml` 看完整状态 |
| **新发现的明文 key 没在 MAPPINGS 里** | 改后用 `grep -cE "明文 key 模式"` 必须 = 0；不为 0 = 漏了 |
| **`.env` 里没那个变量** | 检查清单会列出"❌ 缺失"，需要 `echo "VAR=值" >> .env` |

## 不重启 gateway 验证

按 `hermes` 14:50 硬规则（不主动重启 gateway），改完后：

```bash
# 1. 验证占位符能解析
hermes config show 2>&1 | grep -A1 "api_key" | head -20
# 期望: 输出 ${NVIDIA_API_KEY} 这种占位符 OR 真实 key 字符串（说明注入成功）

# 2. 跑一个不依赖具体模型的 skill 验证
python3 ~/.hermes/scripts/search.py "test query" 2
# 期望: 路由到 anysearch, 2 个结果返回（不依赖主模型 API key）

# 3. 不重启 gateway（14:50 规则保底）
# 明早用户说"重启"才重启
```

## References

- `proactive-execution` 规则 31（BSD sed 假成功）
- `proactive-execution` 规则 32（patch 拒绝 config.yaml）
- 14:50 硬规则（不主动改 model，不重启 gateway）
- 11:50 风格（`--dry-run` 安全开关）
