#!/usr/bin/env python3
"""
QQ Bot credential and health checker.
Reads .env first (precedence), then falls back to config.yaml.

Usage:
    ~/.hermes/hermes-agent/venv/bin/python3 \
        /path/to/this/script/check_qqbot.py

Outputs:
    OK                     — credentials valid
    ALERT_CREATED         — invalid/missing credentials, alert file written
    GATEWAY_DOWN          — no gateway process found
    UNKNOWN_CODE:<code>   — unexpected API response
"""
import asyncio, httpx, json, os, sys, yaml
from pathlib import Path

sys.path.insert(0, '/Users/mac/.hermes/hermes-agent')
from gateway.platforms.qqbot.constants import TOKEN_URL

HERMES_HOME = Path(os.path.expanduser('~/.hermes'))
CRON_DIR    = HERMES_HOME / 'cron'
CRON_DIR.mkdir(exist_ok=True)


def get_credentials():
    """
    Resolve app_id + client_secret — .env takes precedence over config.yaml.
    Supports: QQ_APP_ID / QQ_CLIENT_SECRET (env), or platforms.qqbot.extra.app_id/client_secret (yaml).
    """
    app_id  = os.getenv('QQ_APP_ID',  '').strip()
    secret  = os.getenv('QQ_CLIENT_SECRET', '').strip()

    if not app_id or not secret:
        cfg_path = HERMES_HOME / 'config.yaml'
        if cfg_path.exists():
            cfg = yaml.safe_load(cfg_path.read_text())
            extra = cfg.get('platforms', {}).get('qqbot', {}).get('extra', {})
            if not app_id:
                app_id = str(extra.get('app_id', '')).strip()
            if not secret:
                secret = str(extra.get('client_secret', '')).strip()

    return app_id, secret


def gateway_running():
    """Check if gateway process is alive.
    On macOS the gateway is launchd-managed; also check ps aux as fallback.
    Note: pgrep -f is UNRELIABLE on macOS — process name is 'Python', not 'hermes'.
    """
    import subprocess

    # Method 1: launchctl (preferred on macOS)
    r = subprocess.run(['launchctl', 'list'], capture_output=True, text=True)
    for line in r.stdout.splitlines():
        if 'hermes' in line.lower():
            return True

    # Method 2: ps aux fallback
    r = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
    for line in r.stdout.splitlines():
        if 'hermes_cli' in line and 'gateway' in line and 'grep' not in line:
            return True

    return False


def write_health(status, gateway_pid=None):
    health = {
        'time':   asyncio.get_event_loop().time(),
        'status': status,
    }
    if gateway_pid:
        health['gateway_pid'] = gateway_pid
    (CRON_DIR / 'qqbot_health_check.json').write_text(
        json.dumps(health, indent=2)
    )


async def check():
    app_id, secret = get_credentials()

    if not app_id:
        (CRON_DIR / 'qqbot_credential_alert.json').write_text(json.dumps({
            'alert':   'QQBOT_CREDENTIALS_NOT_CONFIGURED',
            'code':    100007,
            'message': 'app_id is empty — set QQ_APP_ID in .env or platforms.qqbot.extra.app_id in config.yaml',
            'time':    str(asyncio.get_event_loop().time()),
            'fix':     'Set QQ_APP_ID + QQ_CLIENT_SECRET in ~/.hermes/.env, then hermes gateway restart',
        }, indent=2))
        write_health('CREDENTIALS_MISSING')
        return 'ALERT_CREATED'

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(TOKEN_URL, json={'appId': app_id, 'clientSecret': secret})
        data = resp.json()
        code = data.get('code')

        if code == 0 or 'access_token' in data:
            write_health('OK')
            return 'OK'
        elif code == 100016:
            (CRON_DIR / 'qqbot_credential_alert.json').write_text(json.dumps({
                'alert':   'QQBOT_CREDENTIALS_INVALID',
                'code':    code,
                'message': data.get('message'),
                'time':    str(asyncio.get_event_loop().time()),
                'fix':     'Update client_secret at https://q.qq.com then hermes gateway restart',
            }, indent=2))
            write_health('CREDENTIALS_INVALID')
            return 'ALERT_CREATED'
        else:
            return f'UNKNOWN_CODE:{code}'


if __name__ == '__main__':
    if not gateway_running():
        write_health('GATEWAY_DOWN')
        print('GATEWAY_DOWN')
    else:
        print(asyncio.run(check()))
