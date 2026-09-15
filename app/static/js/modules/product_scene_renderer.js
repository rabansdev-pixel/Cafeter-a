import { WebGLRenderer, Scene, PerspectiveCamera, Group, Box3, Vector3,
    MeshStandardMaterial, CanvasTexture, SRGBColorSpace, Float32BufferAttribute,
    HemisphereLight, DirectionalLight, GLTFLoader, ACESFilmicToneMapping,
    PMREMGenerator, Mesh, PlaneGeometry, MeshBasicMaterial, DoubleSide } from '../../vendor/three/three-gltf.js';

let sharedRenderer;
let environment;
const modelBytes = new Map();
export function disposeRenderer() {
    environment?.dispose(); environment = undefined;
    sharedRenderer?.dispose(); sharedRenderer = undefined;
}
function release(root) {
    const textures = new Set(), materials = new Set(), geometries = new Set();
    root.traverse(object => {
        if (object.geometry) geometries.add(object.geometry);
        const list = Array.isArray(object.material) ? object.material : [object.material];
        list.filter(Boolean).forEach(material => materials.add(material));
    });
    materials.forEach(material => {
        Object.values(material).filter(value => value?.isTexture).forEach(texture => textures.add(texture));
        material.dispose();
    });
    textures.forEach(texture => { texture.source?.data?.close?.(); texture.dispose(); });
    geometries.forEach(geometry => geometry.dispose());
}
function studio(renderer) {
    const room = new Scene();
    room.background = null;
    for (const [x, y, z, w, h, intensity] of [[-4, 3, 2, 4, 6, 5], [4, 2, 0, 2, 5, 3], [0, 5, -3, 6, 2, 4]]) {
        const panel = new Mesh(new PlaneGeometry(w, h), new MeshBasicMaterial({ color: 0xffffff, side: DoubleSide }));
        panel.material.color.multiplyScalar(intensity);
        panel.position.set(x, y, z); panel.lookAt(0, 0, 0); room.add(panel);
    }
    const pmrem = new PMREMGenerator(renderer);
    const target = pmrem.fromScene(room, .04);
    pmrem.dispose(); release(room);
    return target;
}
function brand(root, bounds, host) {
    const size = bounds.getSize(new Vector3());
    const canvas = document.createElement('canvas'); canvas.width = 1024; canvas.height = 1536;
    const ctx = canvas.getContext('2d');
    const colors = { 'geisha-huila': '#ddd9c8', yirgacheffe: '#b8c2b0', 'borbon-rosado': '#c9b0a7', 'kenia-nyeri': '#aaaebc', cups: '#d9d9cb' };
    ctx.fillStyle = colors[host.dataset.asset] || '#d9d9cb'; ctx.fillRect(0, 0, 1024, 1536);
    ctx.fillStyle = '#242a29'; ctx.textAlign = 'center';
    ctx.font = '62px Georgia'; ctx.fillText('ZERO-DAY', 512, 590, 780);
    ctx.font = '20px sans-serif'; ctx.fillText('C O F F E E', 512, 650);
    ctx.fillRect(265, 750, 494, 2);
    ctx.font = '48px Georgia'; ctx.fillText((host.dataset.variety || 'CAFÉ DE ORIGEN').toUpperCase(), 512, 870, 780);
    ctx.font = '21px sans-serif'; ctx.fillText((host.dataset.origin || 'UN MOMENTO PARA TI').toUpperCase(), 512, 935, 780);
    ctx.font = '18px sans-serif'; ctx.fillText('ORIGEN ÚNICO · CARÁCTER PROPIO', 512, 1100, 780);
    const texture = new CanvasTexture(canvas); texture.colorSpace = SRGBColorSpace; texture.channel = 2;
    root.updateMatrixWorld(true);
    root.traverse(object => {
        if (!object.isMesh) return;
        const geometry = object.geometry;
        const position = geometry.attributes.position;
        const surfaceBounds = host.dataset.asset === 'cups' ? new Box3().setFromObject(object) : bounds;
        const surfaceSize = surfaceBounds.getSize(new Vector3());
        const uv = new Float32Array(position.count * 2);
        const p = new Vector3();
        for (let i = 0; i < position.count; i++) {
            p.fromBufferAttribute(position, i).applyMatrix4(object.matrixWorld);
            const cups = host.dataset.asset === 'cups';
            const front = cups ? p.x < (surfaceBounds.min.x + surfaceBounds.max.x) / 2 : p.z > (bounds.min.z + bounds.max.z) / 2;
            uv[i * 2] = front ? cups ? (p.z - surfaceBounds.min.z) / surfaceSize.z : (p.x - bounds.min.x) / size.x : .015;
            uv[i * 2 + 1] = front ? (p.y - surfaceBounds.min.y) / surfaceSize.y : .015;
        }
        geometry.setAttribute('uv2', new Float32BufferAttribute(uv, 2));
        const old = object.material;
        object.material = new MeshStandardMaterial({ map: texture, roughness: .72, metalness: 0,
            roughnessMap: old.roughnessMap, aoMap: old.aoMap, aoMapIntensity: .35 });
        old.dispose();
    });
}

export async function createProductScene(host, signal, Renderer = WebGLRenderer) {
    const url = new URL(host.dataset.model, window.location.href).href;
    let bytes = modelBytes.get(url);
    if (!bytes) {
        const response = await fetch(url, { signal });
        if (!response.ok) throw new Error('Product model unavailable');
        bytes = await response.arrayBuffer();
        if (modelBytes.size >= 4) modelBytes.delete(modelBytes.keys().next().value);
        modelBytes.set(url, bytes);
    }
    const gltf = await new GLTFLoader().parseAsync(bytes, new URL('.', url).href);
    const scene = new Scene();
    const root = gltf.scene;
    const group = new Group(); group.add(root); scene.add(group);
    let renderer;
    let canvas;
    const dispose = () => { release(scene); canvas?.remove(); if (Renderer !== WebGLRenderer) renderer?.dispose(); };
    try {
        if (signal.aborted) throw new Error('Product scene cancelled');
        root.updateMatrixWorld(true);
        let bounds = new Box3().setFromObject(root);
        if (host.dataset.brand === 'true') brand(root, bounds, host);
        const size = bounds.getSize(new Vector3());
        root.position.sub(bounds.getCenter(new Vector3()));
        group.scale.setScalar(2.8 / Math.max(size.x, size.y, size.z));
        // The six takeaway cups are composed across the original Z axis.
        if (host.dataset.asset === 'cups') group.rotation.y = Math.PI / 2;
        const baseY = host.dataset.asset === 'cups' ? Math.PI / 2 : Number(host.dataset.angle || -.28);
        group.rotation.y = baseY;
        const dimensions = new Box3().setFromObject(group).getSize(new Vector3());
        const aspect = host.dataset.asset === 'cups' ? 2.6 : host.dataset.brand === 'true' ? .8 : 1.2;
        const flat = host.dataset.asset === 'beans';
        const camera = new PerspectiveCamera(34, 1, .01, 100);
        camera.position.set(0, flat ? 3.6 : .8, flat ? 4.8 : 6);
        camera.lookAt(0, 0, 0);
        scene.add(new HemisphereLight('#f5f7f4', '#485648', 1));
        const key = new DirectionalLight('#ffffff', 3.2); key.position.set(-4, 3, 2.5); scene.add(key);
        const rim = new DirectionalLight('#e5eadd', 2.2); rim.position.set(3, 2, -3); scene.add(rim);
        if (Renderer === WebGLRenderer) {
            sharedRenderer ||= new Renderer({ alpha: true, antialias: true, powerPreference: 'low-power', preserveDrawingBuffer: true });
            renderer = sharedRenderer;
            environment ||= studio(renderer);
            scene.environment = environment.texture;
            scene.environmentIntensity = .4;
        } else renderer = new Renderer({ alpha: true, antialias: true });
        renderer.toneMapping = ACESFilmicToneMapping;
        renderer.toneMappingExposure = 1;
        renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, window.innerWidth < 768 ? 1.5 : 2));
        canvas = renderer.domElement || document.createElement('canvas');
        canvas.setAttribute('aria-hidden', 'true'); host.append(canvas);
        let width = 0, height = 0;
        return {
            render(progress = .5) {
                if (width !== host.clientWidth || height !== host.clientHeight) {
                    width = Math.max(1, host.clientWidth); height = Math.max(1, host.clientHeight);
                    renderer.setSize(width, height, false);
                    const viewWidth = Math.min(width, height * aspect);
                    const viewHeight = viewWidth / aspect;
                    renderer.setViewport((width - viewWidth) / 2, (height - viewHeight) / 2, viewWidth, viewHeight);
                    camera.aspect = aspect;
                    const distance = Math.max(dimensions.y, dimensions.x / aspect) / (2 * Math.tan(34 * Math.PI / 360)) * 1.18 + dimensions.z / 2;
                    camera.position.set(0, flat ? distance * .65 : distance * .16, distance);
                    camera.lookAt(0, 0, 0); camera.updateProjectionMatrix();
                }
                group.rotation.y = baseY + (progress - .5) * .12;
                group.rotation.z = host.dataset.brand === 'true' ? -.025 + (progress - .5) * .025 : 0;
                renderer.render(scene, camera);
            }, dispose
        };
    } catch (error) { dispose(); throw error; }
}
