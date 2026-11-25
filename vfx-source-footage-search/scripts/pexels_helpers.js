// Browser helpers for reviewing Pexels search results and clips.
// Paste into the page (browser JS tool) after every navigation; then call:
//   await __grid()              -> overlay of search-result thumbnails with IDs
//   await __ovs('8457036')      -> overlay of 6 frames from the original clip + [id, duration, size]
//   await __sheetDownload(id)   -> same 6 frames saved as ~/Downloads/__cs_<id>.jpg (when screenshots don't refresh)
//   __clear()                   -> remove overlays

window.__clear = () => document.querySelectorAll('#__ov').forEach(o => o.remove());

window.__grid = async function (max = 28) {
  for (let i = 0; i < 16; i++) { scrollBy(0, 400); await new Promise(r => setTimeout(r, 500)); }
  await new Promise(r => setTimeout(r, 1500));
  const seen = new Set(), items = [];
  for (const a of document.querySelectorAll('a[href*="/video/"]')) {
    if (a.href.includes('/download/')) continue;
    const id = a.href.match(/(\d+)\/?$/)?.[1];
    if (!id || seen.has(id)) continue;
    const img = a.querySelector('img') || a.parentElement.querySelector('img');
    if (!img?.src || img.src.startsWith('data:')) continue;
    seen.add(id); items.push([id, img.src, a.href]);
  }
  __clear();
  const ov = document.createElement('div');
  ov.id = '__ov';
  ov.style = 'position:fixed;inset:0;z-index:999999;background:#fff;display:grid;grid-template-columns:repeat(4,1fr);gap:3px;overflow:auto;padding:3px;align-content:start';
  for (const [id, src] of items.slice(0, max)) {
    const d = document.createElement('div');
    d.style = 'position:relative';
    d.innerHTML = `<img src="${src}" style="width:100%;aspect-ratio:16/9;object-fit:cover"><span style="position:absolute;left:2px;top:2px;background:#ff0;font:bold 13px sans-serif">${id}</span>`;
    ov.appendChild(d);
  }
  document.body.appendChild(ov);
  window.__items = items;
  return items.map(([id, , href]) => id + ' ' + href.replace('https://www.pexels.com/video/', ''));
};

async function __grabFrames(id, width = 400) {
  const vv = document.createElement('video');
  vv.crossOrigin = 'anonymous'; vv.muted = true; vv.preload = 'auto';
  vv.src = 'https://www.pexels.com/download/video/' + id + '/';
  const ok = await new Promise(r => { vv.onloadedmetadata = () => r(true); vv.onerror = () => r(false); setTimeout(() => r(false), 25000); });
  if (!ok) return null;
  const d = vv.duration, fs = [0.03, 0.2, 0.4, 0.6, 0.8, 0.97], frames = [];
  for (const f of fs) {
    vv.currentTime = d * f;
    await new Promise(r => { vv.onseeked = r; setTimeout(r, 15000); });
    const c = document.createElement('canvas');
    c.width = width; c.height = Math.round(width * vv.videoHeight / vv.videoWidth);
    c.getContext('2d').drawImage(vv, 0, 0, c.width, c.height);
    frames.push({ c, t: Math.round(f * d) });
  }
  return { d, w: vv.videoWidth, h: vv.videoHeight, frames };
}

window.__ovs = async function (id) {
  const r = await __grabFrames(id);
  if (!r) return id + ': load fail';
  __clear();
  const ov = document.createElement('div');
  ov.id = '__ov';
  ov.style = 'position:fixed;inset:0;z-index:999999;background:#fff;display:grid;grid-template-columns:repeat(2,1fr);gap:4px;padding:4px;align-content:start';
  ov.innerHTML = r.frames.map(f => `<div style="position:relative"><img src="${f.c.toDataURL('image/jpeg', .7)}" style="width:100%"><span style="position:absolute;left:2px;top:2px;background:#ff0;font:bold 13px sans-serif">${id} ${f.t}s</span></div>`).join('');
  document.body.appendChild(ov);
  return [id, r.d.toFixed(1) + 's', r.w + 'x' + r.h];
};

window.__sheetDownload = async function (id) {
  const r = await __grabFrames(id, 480);
  if (!r) return id + ': load fail';
  const W = 480, H = r.frames[0].c.height, c = document.createElement('canvas');
  c.width = W * 3; c.height = H * 2;
  const g = c.getContext('2d');
  r.frames.forEach((f, i) => {
    const x = (i % 3) * W, y = Math.floor(i / 3) * H;
    g.drawImage(f.c, x, y);
    g.fillStyle = '#ff0'; g.fillRect(x, y, 120, 22);
    g.fillStyle = '#000'; g.font = 'bold 16px sans-serif'; g.fillText(id + ' ' + f.t + 's', x + 4, y + 17);
  });
  const b = await new Promise(res => c.toBlob(res, 'image/jpeg', .75));
  const a = document.createElement('a');
  a.href = URL.createObjectURL(b); a.download = '__cs_' + id + '.jpg';
  document.body.appendChild(a); a.click(); a.remove();
  return [id, r.d.toFixed(1) + 's', r.w + 'x' + r.h];
};
