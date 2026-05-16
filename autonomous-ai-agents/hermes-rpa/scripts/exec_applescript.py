#!/usr/bin/env python3
"""
AppleScript 执行助手 — 解决 terminal tool 将 AppleScript 的 `&` 
误判为 shell 后台指令的问题。

用法: python3 exec_applescript.py <script_path> [args...]
  或: python3 exec_applescript.py -c "<inline applescript>"

自动将内联脚本写入临时文件执行，规避 `&` 解析问题。
"""
import sys, os, tempfile, subprocess, json

def exec_applescript(script_path_or_code, is_inline=False):
    """执行 AppleScript 文件或内联代码"""
    if is_inline:
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.applescript', delete=False
        ) as f:
            f.write(script_path_or_code)
            script_path = f.name
    else:
        script_path = script_path_or_code
    
    try:
        result = subprocess.run(
            ['osascript', script_path],
            capture_output=True, text=True, timeout=30
        )
        return {
            'stdout': result.stdout.strip(),
            'stderr': result.stderr.strip(),
            'exit_code': result.returncode,
            'success': result.returncode == 0
        }
    except subprocess.TimeoutExpired:
        return {
            'stdout': '',
            'stderr': 'AppleScript 执行超时 (30s)',
            'exit_code': -1,
            'success': False
        }
    finally:
        if is_inline:
            os.unlink(script_path)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('用法: python3 exec_applescript.py <file>')
        print('      python3 exec_applescript.py -c "<inline code>"')
        sys.exit(1)
    
    if sys.argv[1] == '-c':
        code = sys.argv[2]
        result = exec_applescript(code, is_inline=True)
    else:
        result = exec_applescript(sys.argv[1])
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result['success'] else 1)
