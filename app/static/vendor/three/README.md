Three.js 0.186.0 (MIT), served locally to respect the existing CSP.
Source: https://registry.npmjs.org/three/-/three-0.186.0.tgz
Includes the WebGL module and GLTFLoader; no controls or postprocessing.
Official loader documentation: https://threejs.org/docs/pages/GLTFLoader.html

Reproduction (esbuild 0.28.2, temporary tooling; no app build required):
Create entry.js beside the extracted package:
  export * from './package/build/three.module.js';
  export { GLTFLoader } from './package/examples/jsm/loaders/GLTFLoader.js';
Run esbuild entry.js --bundle --minify --format=esm
  --alias:three=/absolute/path/package/build/three.module.js
  --outfile=three-gltf.js
Preserve LICENSE. Application code lives in js/modules/product_scene*.js.
