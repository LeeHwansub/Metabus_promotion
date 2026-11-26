#!/usr/bin/env node
// metaBus 엔딩 v3 (Three.js + GSAP) → PNG 시퀀스
// 사용: node render.mjs 16x9|9x16 [출력폴더] [--only 0,24,60] [--page motion_graphics/animatic/index.html --frames 600]
//   - 기본 페이지는 엔딩(motion_graphics/ending_three/index.html, 120프레임)
//   - 05_PRODUCTION 폴더를 127.0.0.1 로컬 서버로 열고 (이미지를 canvas/WebGL에서 쓰기 위해)
//   - Chrome 헤드리스 하나를 DevTools 프로토콜로 조종해 window.renderAt(t) → 스크린샷을 프레임마다 반복
//   - 외부 패키지 없음 (Node 22 내장 http / fetch / WebSocket)
// 프레임은 f_0000.png 부터. MP4 변환은 ffmpeg-skill sequence.py 로.
import http from 'node:http';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const args = process.argv.slice(2);
const ASPECT = args[0] || '16x9';
if (!['16x9', '9x16', 'card'].includes(ASPECT)) { console.error('aspect must be 16x9 or 9x16'); process.exit(1); }
const onlyIdx = args.indexOf('--only');
const ONLY = onlyIdx >= 0 ? args[onlyIdx + 1].split(',').map(Number) : null;
const opt = (name, def) => { const i = args.indexOf(name); return i >= 0 ? args[i + 1] : def; };
const OUT = (args[1] && !args[1].startsWith('--')) ? path.resolve(args[1]) : path.join(os.tmpdir(), `metabus_ending3_${ASPECT}`);
// invite_card: 'card' = 폰 화면 비율 540x1000, 투명 배경 PNG
const [W, H] = ASPECT === '16x9' ? [1920, 1080] : ASPECT === 'card' ? [540, 1000] : [1080, 1920];
const FPS = 24, FRAMES = Number(opt('--frames', 120));
const PAGE = opt('--page', 'index.html');
const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = HERE;
const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const sleep = ms => new Promise(r => setTimeout(r, ms));

// ---- 로컬 정적 서버 (127.0.0.1 전용, ROOT 밖 경로 차단)
const TYPES = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.mjs': 'text/javascript',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp' };
const server = http.createServer((req, res) => {
  const p = path.normalize(path.join(ROOT, decodeURIComponent(new URL(req.url, 'http://x').pathname)));
  if (!p.startsWith(ROOT + path.sep)) { res.writeHead(403); return res.end(); }
  fs.readFile(p, (e, d) => {
    if (e) { res.writeHead(404); return res.end(); }
    res.writeHead(200, { 'content-type': TYPES[path.extname(p).toLowerCase()] || 'application/octet-stream' }); res.end(d);
  });
});
await new Promise(r => server.listen(0, '127.0.0.1', r));
const HTTP_PORT = server.address().port;

// ---- Chrome
const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'metabus-chrome-'));
const CDP_PORT = 9300 + Math.floor(Math.random() * 500);
const chrome = spawn(CHROME, ['--headless=new', `--remote-debugging-port=${CDP_PORT}`, `--user-data-dir=${profile}`,
  '--hide-scrollbars', '--force-device-scale-factor=1', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist',
  `--window-size=${W},${H}`, 'about:blank'], { stdio: 'ignore' });
// Chrome이 종료되며 프로필에 쓰는 중일 수 있어 삭제 실패는 무시 (OS 임시 폴더라 나중에 정리됨)
const cleanup = () => { try { chrome.kill(); } catch {} server.close(); try { fs.rmSync(profile, { recursive: true, force: true, maxRetries: 3 }); } catch {} };
process.on('exit', cleanup);

let wsUrl;
for (let i = 0; i < 100 && !wsUrl; i++) {
  try { wsUrl = (await (await fetch(`http://127.0.0.1:${CDP_PORT}/json/list`)).json()).find(x => x.type === 'page')?.webSocketDebuggerUrl; }
  catch { await sleep(150); }
}
if (!wsUrl) { console.error('Chrome DevTools 연결 실패'); process.exit(1); }
const ws = new WebSocket(wsUrl);
await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
let seq = 0; const pending = new Map();
ws.onmessage = ev => {
  const m = JSON.parse(ev.data);
  if (m.id && pending.has(m.id)) { const { res, rej } = pending.get(m.id); pending.delete(m.id); m.error ? rej(new Error(m.error.message)) : res(m.result); }
  else if (m.method === 'Runtime.exceptionThrown') console.error('[page]', m.params.exceptionDetails.exception?.description || m.params.exceptionDetails.text);
  else if (m.method === 'Runtime.consoleAPICalled' && m.params.type === 'error') console.error('[page]', m.params.args.map(a => a.value ?? a.description).join(' '));
};
const send = (method, params = {}) => new Promise((res, rej) => { const id = ++seq; pending.set(id, { res, rej }); ws.send(JSON.stringify({ id, method, params })); });
const evaluate = async (expression, awaitPromise = false) =>
  (await send('Runtime.evaluate', { expression, awaitPromise, returnByValue: true })).result.value;

await send('Runtime.enable'); await send('Page.enable');
await send('Emulation.setDeviceMetricsOverride', { width: W, height: H, deviceScaleFactor: 1, mobile: false });
if (ASPECT === 'card') await send('Emulation.setDefaultBackgroundColorOverride', { color: { r: 0, g: 0, b: 0, a: 0 } });   // 투명 배경
await send('Page.navigate', { url: `http://127.0.0.1:${HTTP_PORT}/${PAGE}?a=${ASPECT}&mode=render` });

const t0 = Date.now();
while (true) {
  const st = await evaluate('JSON.stringify({ready: window.READY === true, err: window.ERR || null, assets: window.ASSETS || null})').catch(() => null);
  const s = st ? JSON.parse(st) : {};
  if (s.err) { console.error('페이지 오류:', s.err); process.exit(1); }
  if (s.ready) { console.log('assets', JSON.stringify(s.assets)); break; }
  if (Date.now() - t0 > 60000) { console.error('준비 시간 초과 (CDN 로드 실패?)'); process.exit(1); }
  await sleep(200);
}
console.log('renderer', await evaluate(`(() => { const g = document.createElement('canvas').getContext('webgl2'); const d = g && g.getExtension('WEBGL_debug_renderer_info'); return d ? g.getParameter(d.UNMASKED_RENDERER_WEBGL) : 'unknown'; })()`));

fs.mkdirSync(OUT, { recursive: true });
const list = ONLY || [...Array(FRAMES).keys()];
for (const f of list) {
  await evaluate(`window.renderAt(${f / FPS})`, true);
  const { data } = await send('Page.captureScreenshot', { format: 'png', clip: { x: 0, y: 0, width: W, height: H, scale: 1 } });
  fs.writeFileSync(path.join(OUT, `f_${String(f).padStart(4, '0')}.png`), Buffer.from(data, 'base64'));
  if (f % 12 === 0 || ONLY) process.stdout.write(`frame ${f} (${((Date.now() - t0) / 1000).toFixed(0)}s)\n`);
}
console.log(`done: ${list.length} frames → ${OUT}`);
ws.close();
process.exit(0);
