import { build } from 'esbuild';
await build({ entryPoints:['frontend/firebase-login.ts'], outfile:'app/static/js/firebase-login.js', bundle:true, minify:true, format:'esm', target:['es2020'], define:{'process.env.NODE_ENV':'"production"'}, legalComments:'external' });
