import { build } from 'esbuild';
import { execFileSync } from 'node:child_process';
import { mkdirSync } from 'node:fs';
mkdirSync('app/static/admin', { recursive: true });
await build({ entryPoints: ['frontend/admin.tsx'], outfile: 'app/static/admin/dashboard.js', bundle: true, minify: true, format: 'esm', target: ['es2020'], jsx: 'automatic', define: { 'process.env.NODE_ENV': '"production"' }, legalComments: 'external' });
execFileSync(process.execPath, ['node_modules/@tailwindcss/cli/dist/index.mjs', '-i', 'frontend/admin.css', '-o', 'app/static/admin/dashboard.css', '--minify'], { stdio: 'inherit' });
