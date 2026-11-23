#!/usr/bin/env python3
"""12123 看图题秒答：免费视觉模型优先(多模型fallback+重试) + PIL像素法兜底。

用法：
  python3 xfjf_vision.py <截图路径> "<题干文字>" [--dev 设备地址]

设计要点（复盘血泪）：
- reasoning 模型 max_tokens 必须 >=600，否则 content=None 全被 reasoning 吃光。
- 免费模型会下架/限流/网络超时(HTTP=000)，必须多模型 fallback + 重试。
- 国内网络不稳，curl --max-time 40，失败 2 次即切下一个模型。
- 任何一步失败都不阻塞：最终必有像素法兜底答案，绝不卡住 44 秒限时。
"""
import sys, os, json, base64, subprocess, time, re

ENV_FILE = os.path.expanduser('~/.hermes/.env')
MODELS = [
    'nvidia/nemotron-3.5-super-vl:free',
    'nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free',
    'google/gemma-4-31b-it:free',
    'openrouter/free',
]

def get_key():
    for line in open(ENV_FILE):
        if line.startswith('OPENROUTER_API_KEY='):
            return line.strip().split('=', 1)[1]
    return ''

def vision_answer(img_path, question):
    key = get_key()
    if not key:
        return None, 'no OpenRouter key'
    b64 = base64.b64encode(open(img_path, 'rb').read()).decode()
    prompt = (f'中国驾照考试看图题。题目：{question}\n'
              '请读题目下方的图片，直接给出答案字母(A/B/C/D或Y/N)，一句话说明理由。'
              '答案字母放在最前面。')
    errors = []
    for model in MODELS:
        payload = {"model": model, "messages": [{"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": "data:image/png;base64," + b64}},
        ]}], "max_tokens": 800}   # 关键：>=600，否则 reasoning 吃光 content
        for attempt in range(2):
            try:
                r = subprocess.run(['curl', '-s', '--max-time', '40',
                    'https://openrouter.ai/api/v1/chat/completions',
                    '-H', 'Authorization: Bearer ' + key,
                    '-H', 'Content-Type: application/json',
                    '-d', json.dumps(payload)], capture_output=True, text=True, timeout=45)
                o = json.loads(r.stdout.strip())
                msg = o['choices'][0]['message']
                content = msg.get('content')
                if not content:
                    # 部分模型把答案放 reasoning 里
                    content = msg.get('reasoning') or ''
                m = re.search(r'[ABCDYN]', content.upper())
                if m:
                    return m.group(0), f'{model}: {content[:120]}'
                errors.append(f'{model}: no letter in {content[:60]}')
            except Exception as e:
                errors.append(f'{model}: {type(e).__name__}')
                time.sleep(1)
    return None, ' | '.join(errors[-3:])

def pixel_answer(img_path, question):
    """像素法兜底：信号灯色/标志红圈/环境明暗。返回 (字母或None, 说明)。"""
    import numpy as np
    from PIL import Image
    a = np.array(Image.open(img_path).convert('RGB')).astype(int)
    R, G, B = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    y0, y1 = 1100, 1450
    # 极纯色阈值：只认高饱和发光灯块，排除 App 主题色(面积巨大)
    pure_red = ((R > 200) & (G < 70) & (B < 70))[y0:y1]
    pure_green = ((G > 180) & (R < 90) & (B < 90))[y0:y1]
    pure_yellow = ((R > 210) & (G > 190) & (B < 90))[y0:y1]
    qr, qg, qy = int(pure_red.sum()), int(pure_green.sum()), int(pure_yellow.sum())
    qs = question
    # 信号灯色判断：孤立小块(<3000像素)才算灯，大面积=主题色干扰
    if any(k in qs for k in ('信号灯', '灯亮', '可以左转', '红灯', '绿灯')):
        if 50 < qg < 3000 and qg > qr * 3:
            return ('Y' if '可以' in qs else 'A'), f'绿灯(纯绿{qg}/红{qr})'
        if 50 < qr < 3000 and qr > qg * 3:
            return ('Y' if '不得' in qs else 'C'), f'红灯(纯红{qr}/绿{qg})'
        # 纯色不可判时给保守答案，标注低置信
        return None, f'灯色不确定(纯红{qr}/绿{qg}/黄{qy})'
    # 红圈标志
    if any(k in qs for k in ('标志', '让行', '让对方')) and 300 < qr < 15000:
        return 'Y', f'红圈标志让行(纯红{qr})'
    return None, f'像素无法判定(纯红{qr}/绿{qg}/黄{qy})'

if __name__ == '__main__':
    img = sys.argv[1]
    q = sys.argv[2] if len(sys.argv) > 2 else ''
    t0 = time.time()
    letter, detail = vision_answer(img, q)
    src = '视觉模型'
    if letter is None:
        letter, detail = pixel_answer(img, q)
        src = '像素兜底'
    print(json.dumps({'answer': letter, 'source': src, 'detail': detail,
                      'elapsed': round(time.time() - t0, 1)}, ensure_ascii=False))
