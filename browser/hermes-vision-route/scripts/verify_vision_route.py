import os
import sys

sys.path.insert(0, '/Users/aimac/.hermes/hermes-agent')
os.environ.setdefault('HERMES_DISABLE_LAZY_INSTALLS', '1')
from hermes_cli.config import load_config
from agent.image_routing import decide_image_input_mode

cfg = load_config()
model = cfg.get('model', {}).get('default', '')
provider = cfg.get('model', {}).get('provider', '')
route = decide_image_input_mode(provider, model, cfg)
vis = cfg.get('auxiliary', {}).get('vision', {})
print('main:', provider, '/', model)
print('route:', route)
print('aux.vision:', {k: vis.get(k) for k in ('provider', 'model', 'base_url')})
assert route == 'native', 'route 不是 native：清空 auxiliary.vision.model/base_url 或检查 image_input_mode'
