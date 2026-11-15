// Local review server: expose only these previews and the app's Vazirmatn fonts.
import { createServer } from 'node:http';
import { readFileSync, statSync } from 'node:fs';
import { dirname, resolve, extname } from 'node:path';
import { fileURLToPath } from 'node:url';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'../../..');
const prefix='/docs/designs/smart-search-2026-11/';
const fontPrefix='/frontend/node_modules/@expo-google-fonts/vazirmatn/';
const mime={'.html':'text/html; charset=utf-8','.css':'text/css','.js':'text/javascript','.png':'image/png','.ttf':'font/ttf'};
const server=createServer((req,res)=>{
  try {
    const pathname=decodeURIComponent(new URL(req.url,'http://localhost').pathname);
    if(pathname==='/'){res.writeHead(302,{Location:prefix+'index.html'});res.end();return;}
    const file=resolve(root,'.'+pathname);
    if((!pathname.startsWith(prefix)&&!pathname.startsWith(fontPrefix))||!file.startsWith(root+'/')||!mime[extname(file)]||!statSync(file).isFile())throw Error('NOT_FOUND');
    res.writeHead(200,{'Content-Type':mime[extname(file)],'Cache-Control':'no-store'});res.end(readFileSync(file));
  } catch {res.writeHead(404);res.end('Not found');}
});
server.listen(8097,'127.0.0.1',()=>console.log('Design review: http://127.0.0.1:8097/ (Ctrl+C to stop)'));
for(const signal of ['SIGINT','SIGTERM'])process.once(signal,()=>server.close());
