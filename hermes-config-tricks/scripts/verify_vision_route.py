#!/usr/bin/env python3
"""Print the effective image-input route for the active main model.

Run: HERMES_DISABLE_LAZY_INSTALLS=1 ~/.hermes/hermes-agent/.venv/bin/python \
     ~/.hermes/skills/hermes-config-tricks/scripts/verify_vision_route.py
Exit 0 = native pixels reach the main model; exit 1 = text-description route.
"""
import os
import sys

ROOT = os.path.expanduser('~/.hermes/hermes-agent')
sys.path.insert(0, ROOT)

from hermes_cli.config import load_config
from agent.image_routing import decide_image_input_mode

cfg = load_config()
model_cfg = cfg.get('model') or {}
model = model_cfg.get('default') or model_cfg.get('model') or ''
provider = model_cfg.get('provider') or ''
vision = (cfg.get('auxiliary') or {}).get('vision') or {}
route = decide_image_input_mode(provider, model, cfg)

print('main:', provider, '/', model)
print('aux.vision:', 'provider=', repr(vision.get('provider')), 'model=', repr(vision.get('model')))
print('route:', route)
if route != 'native':
    print('FIX: hermes config set auxiliary.vision.model ""  (keep provider auto)')
sys.exit(0 if route == 'native' else 1)
