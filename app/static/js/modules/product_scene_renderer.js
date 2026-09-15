import { WebGLRenderer, Scene, PerspectiveCamera, Group, Box3, Vector3,
    MeshStandardMaterial, CanvasTexture, SRGBColorSpace, Mesh, PlaneGeometry,
    AmbientLight, DirectionalLight, GLTFLoader } from '../../vendor/three/three-gltf.js';

function release(root) {
    root.traverse(object => {
        object.geometry?.dispose();
        const materials = Array.isArray(object.material) ? object.material : [object.material];
        materials.filter(Boolean).forEach(material => {
            Object.values(material).filter(value => value?.isTexture).forEach(texture => {
                texture.source?.data?.close?.();
                texture.dispose();
            });
            material.dispose();
        });
    });
}

export async function createProductScene(host, signal, Renderer = WebGLRenderer) {
    const canvas = document.createElement('canvas');
    canvas.setAttribute('aria-hidden', 'true');
    const renderer = new Renderer({ canvas, alpha: true, antialias: true, powerPreference: 'low-power' });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    const scene = new Scene();
    const camera = new PerspectiveCamera(32, 1, .01, 100);
    const group = new Group();
    scene.add(group);
    const dispose = () => { release(scene); renderer.dispose(); canvas.remove(); };
    try {
        const response = await fetch(host.dataset.model, { signal });
        if (!response.ok) throw new Error('Product model unavailable');
        const gltf = await new GLTFLoader().parseAsync(await response.arrayBuffer(), '');
        group.add(gltf.scene);
        if (signal.aborted) throw new Error('Product scene cancelled');
        // Remove the supplied third-party texture before the first frame.
        gltf.scene.traverse(object => {
            if (!object.isMesh) return;
            const old = object.material;
            old.map?.source?.data?.close?.();
            old.map?.dispose();
            old.dispose();
            object.material = new MeshStandardMaterial({ color: '#302820', roughness: .83, metalness: 0 });
        });
        const bounds = new Box3().setFromObject(gltf.scene);
        const size = bounds.getSize(new Vector3());
        const center = bounds.getCenter(new Vector3());
        gltf.scene.position.sub(center);
        const label = document.createElement('canvas');
        label.width = 768; label.height = 768;
        const ctx = label.getContext('2d');
        ctx.fillStyle = '#ded2bc'; ctx.fillRect(0, 0, 768, 768);
        ctx.fillStyle = '#292019'; ctx.textAlign = 'center';
        ctx.font = '500 68px Georgia'; ctx.fillText('ZERO-DAY', 384, 165);
        ctx.font = '20px sans-serif'; ctx.fillText('C O F F E E', 384, 220);
        ctx.fillStyle = '#846441'; ctx.fillRect(130, 300, 508, 2);
        ctx.font = '48px Georgia'; ctx.fillText(host.dataset.variety.toUpperCase(), 384, 420, 600);
        ctx.font = '23px sans-serif'; ctx.fillText(host.dataset.origin.toUpperCase(), 384, 485, 600);
        ctx.font = '18px sans-serif'; ctx.fillText('CAFÉ DE ESPECIALIDAD', 384, 640);
        const texture = new CanvasTexture(label); texture.colorSpace = SRGBColorSpace;
        const face = new Mesh(new PlaneGeometry(size.x * .78, size.y * .49), new MeshStandardMaterial({ map: texture, roughness: .9 }));
        face.position.set(0, -size.y * .03, size.z / 2 + .02);
        group.add(face);
        group.scale.setScalar(2.6 / size.y);
        scene.add(new AmbientLight('#fff2dd', 1.5));
        const key = new DirectionalLight('#fff5e4', 2.5); key.position.set(-3, 4, 5); scene.add(key);
        const rim = new DirectionalLight('#d6ba92', 2); rim.position.set(3, 1, -2); scene.add(rim);
        camera.position.set(0, .1, 6.3); camera.lookAt(0, 0, 0);
        host.append(canvas);
        let width = 0, height = 0;
        return {
            render(progress) {
                if (width !== host.clientWidth || height !== host.clientHeight) {
                    width = host.clientWidth; height = host.clientHeight;
                    renderer.setSize(width, height, false);
                    camera.aspect = width / Math.max(1, height); camera.updateProjectionMatrix();
                }
                group.rotation.set(.02, -.25 + progress * .23, -.065 + progress * .08);
                group.position.y = progress * .06;
                renderer.render(scene, camera);
            },
            dispose
        };
    } catch (error) { dispose(); throw error; }
}
