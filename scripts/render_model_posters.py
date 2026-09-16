"""Render faithful static fallbacks from prepared models using a local server.
Usage: PLAYWRIGHT_BROWSERS_PATH=/tmp/cafe-browsers .venv/bin/python scripts/render_model_posters.py
Requires Playwright Chromium and ImageMagick. Start run.py on port 5071 first.
"""
from pathlib import Path
import base64
import subprocess
from playwright.sync_api import sync_playwright

ASSETS = ['geisha-huila', 'yirgacheffe', 'borbon-rosado', 'kenia-nyeri', 'espresso', 'beans', 'ceramic', 'cappuccino', 'takeaway', 'cups']
ROOT = Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    browser = p.chromium.launch(args=['--enable-unsafe-swiftshader'])
    page = browser.new_page(viewport={'width': 800, 'height': 1000})
    page.route('**/js/main.js', lambda route: route.fulfill(status=200, content_type='text/javascript', body=''))
    page.goto('http://127.0.0.1:5071/')
    page.evaluate("document.body.innerHTML='<div id=stage></div>'; document.body.style='margin:0;background:transparent';")
    for asset in ASSETS:
        encoded = page.evaluate('''async asset => {
            const module = await import('/static/js/modules/product_scene_renderer.js');
            const host = document.querySelector('#stage');
            host.style = 'width:800px;height:' + (asset === 'cups' ? 308 : 667) + 'px';
            Object.assign(host.dataset, {model:'/static/models/'+asset+'.glb', asset, brand:'false'});
            const scene = await module.createProductScene(host, new AbortController().signal);
            scene.render(.5);
            const result = host.querySelector('canvas').toDataURL('image/png');
            scene.dispose(); return result;
        }''', asset)
        subprocess.run(['magick', '-', '-quality', '88', str(ROOT / 'app/static/img/products' / (asset + '.webp'))], input=base64.b64decode(encoded.split(',')[1]), check=True)
        print('Rendered', asset, flush=True)
    browser.close()
