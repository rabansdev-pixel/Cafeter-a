"""Prepare user GLBs without changing originals (requires ImageMagick)."""
import json
import struct
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'app/static/img/products'
DEST = ROOT / 'app/static/models'
MODELS = {
    'geisha-huila': ('coffee_paper_bag_3d_scan', False),
    'yirgacheffe': ('costa_coffee_bag', False),
    'borbon-rosado': ('coffee_packaging', False),
    'kenia-nyeri': ('dunkin_donuts_coffee', False),
    'espresso': ('espresso_coffee_machine', False),
    'beans': ('coffee_beans-_autodesk_memento', False),
    'ceramic': ('capuchino_in_a_cup', False),
    'cappuccino': ('cup_of_cappuccino', False),
    'takeaway': ('coffee_paper-cup', False),
    'cups': ('cc0ffee_cups', False),
}


def prepare(key, source, branded):
    raw = (SOURCE / (source + '.glb')).read_bytes()
    length = struct.unpack_from('<I', raw, 12)[0]
    data = json.loads(raw[20:20 + length])
    binary = raw[length + 28:]
    for material in data.get('materials', []):
        extension = material.get('extensions', {})
        legacy = extension.pop('KHR_materials_pbrSpecularGlossiness', None)
        if legacy:
            material['pbrMetallicRoughness'] = {
                'baseColorFactor': legacy.get('diffuseFactor', [1, 1, 1, 1]),
                'metallicFactor': 0,
                'roughnessFactor': 1 - legacy.get('glossinessFactor', 0),
            }
            if legacy.get('diffuseTexture'):
                material['pbrMetallicRoughness']['baseColorTexture'] = legacy['diffuseTexture']
        if not extension:
            material.pop('extensions', None)
    for field in ['extensionsRequired', 'extensionsUsed']:
        data[field] = [x for x in data.get(field, []) if x != 'KHR_materials_pbrSpecularGlossiness']
        if not data[field]:
            data.pop(field)
    image_views = {image['bufferView'] for image in data.get('images', [])}
    views, output, mapping = [], bytearray(), {}
    for index, view in enumerate(data.get('bufferViews', [])):
        if index in image_views:
            continue
        mapping[index] = len(views)
        output.extend(b'\0' * (-len(output) % 4))
        start = view.get('byteOffset', 0)
        new = dict(view, byteOffset=len(output))
        output.extend(binary[start:start + view['byteLength']])
        views.append(new)
    for accessor in data.get('accessors', []):
        if 'bufferView' in accessor:
            accessor['bufferView'] = mapping[accessor['bufferView']]
    used_textures = set()
    for material in data.get('materials', []):
        def visit(value):
            if isinstance(value, dict):
                for name, item in value.items():
                    if name.endswith('Texture') and isinstance(item, dict):
                        used_textures.add(item['index'])
                    visit(item)
        visit(material)
    used_images = {data['textures'][i]['source'] for i in used_textures}
    for index, image in enumerate(data.get('images', [])):
        view = data['bufferViews'][image['bufferView']]
        start = view.get('byteOffset', 0)
        filename = key + '-texture-' + str(index) + '.webp'
        if index in used_images:
            subprocess.run(['magick', '-', '-resize', '1024x1024>', '-quality', '86', str(DEST / filename)],
                           input=binary[start:start + view['byteLength']], check=True)
        # Unreferenced texture definitions are removed below.
        data['images'][index] = {'uri': filename}
    tex_map = {old: new for new, old in enumerate(sorted(used_textures))}
    img_map = {old: new for new, old in enumerate(sorted(used_images))}
    data['textures'] = [dict(data['textures'][i], source=img_map[data['textures'][i]['source']]) for i in sorted(used_textures)]
    data['images'] = [data['images'][i] for i in sorted(used_images)]
    def remap(value):
        if isinstance(value, dict):
            for name, item in value.items():
                if name.endswith('Texture') and isinstance(item, dict):
                    item['index'] = tex_map[item['index']]
                remap(item)
    for material in data.get('materials', []):
        remap(material)
    for name in ['textures', 'images']:
        if not data[name]:
            data.pop(name)
    data['bufferViews'] = views
    output.extend(b'\0' * (-len(output) % 4))
    data['buffers'] = [{'byteLength': len(output)}]
    data['asset'].setdefault('extras', {})['adaptation'] = 'ZERO-DAY: external optimized textures; original geometry preserved; original brand identity and materials retained; legacy specular-glossiness converted to metallic-roughness.'
    payload = json.dumps(data, separators=(',', ':')).encode()
    payload += b' ' * (-len(payload) % 4)
    target = DEST / (key + '.glb')
    target.write_bytes(struct.pack('<III', 0x46546C67, 2, 28 + len(payload) + len(output)) +
                      struct.pack('<II', len(payload), 0x4E4F534A) + payload +
                      struct.pack('<II', len(output), 0x004E4942) + output)
    return dict(key=key, original=source + '.glb', bytes=len(raw), optimized=target.stat().st_size,
                credit=data['asset']['extras'])


if __name__ == '__main__':
    DEST.mkdir(exist_ok=True)
    manifest = [prepare(key, *value) for key, value in MODELS.items()]
    (DEST / 'credits.json').write_text(json.dumps(manifest, indent=2) + '\n')
    for item in manifest:
        print(item['key'], item['bytes'], '->', item['optimized'])
