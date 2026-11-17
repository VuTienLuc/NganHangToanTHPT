// ===== MÀN HÌNH THẦY — phòng thi đấu trực tiếp (chèn vào trang đề; bật khi địa chỉ có ?phong) =====
const __PG = { ws: null, st: null, ma: '', lech: 0, nap: false, hen: null, tat: false };
const __MAU_PA = ['#e11d48', '#2563eb', '#d97706', '#059669'], __HINH_PA = ['▲', '◆', '●', '■'];
const __DOI = [['Đỏ', '#ef4444'], ['Xanh dương', '#3b82f6'], ['Xanh lá', '#22c55e'], ['Vàng', '#eab308'], ['Tím', '#a855f7'], ['Cam', '#f97316'], ['Hồng', '#ec4899'], ['Ngọc', '#14b8a6']];
const __pe = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
function __pgCss() {
  const c = document.createElement('style'); c.textContent = `
#pg{position:fixed;inset:0;z-index:99999;background:#0f172a;color:#f8fafc;font:18px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;display:flex;flex-direction:column;overflow:hidden}
#pg *{box-sizing:border-box}#pg button{font:inherit;border:0;border-radius:12px;padding:12px 20px;font-weight:700;cursor:pointer;background:#334155;color:#fff;min-height:48px}
#pg button:focus-visible{outline:3px solid #93c5fd;outline-offset:2px}#pg button.chinh{background:#7c3aed}#pg button.xanh{background:#16a34a}#pg button:disabled{opacity:.5;cursor:default}
#pg .dau{display:flex;align-items:center;gap:14px;padding:12px 22px;background:#111827;border-bottom:1px solid #1f2937;flex-wrap:wrap}#pg .dau h1{font-size:20px;margin:0;flex:1;min-width:200px}
#pg .than{flex:1;overflow:auto;padding:22px 28px;display:flex;flex-direction:column;gap:18px}
#pg .the{background:#1e293b;border-radius:18px;padding:22px}#pg label{display:flex;flex-direction:column;gap:6px;font-weight:700;font-size:15px}
#pg select,#pg input{font:inherit;font-size:17px;padding:10px 12px;border-radius:10px;border:1px solid #475569;background:#0f172a;color:#fff}
#pg .luoi{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px}
#pg .ma{font:900 clamp(44px,5.6vw,84px)/1.1 ui-monospace,Menlo,monospace;letter-spacing:.06em;color:#fde68a;white-space:nowrap}
#pg .cho{display:grid;grid-template-columns:minmax(260px,380px) 1fr;gap:22px;align-items:start}@media (max-width:900px){#pg .cho{grid-template-columns:1fr}}
#pg .qr{background:#fff;border-radius:16px;padding:10px;width:100%;aspect-ratio:1}
#pg .chip{display:inline-flex;align-items:center;gap:6px;background:#334155;border-radius:999px;padding:6px 14px;margin:4px;font-weight:600;font-size:16px}
#pg .chip.off{opacity:.45}#pg .chip button{min-height:0;padding:0 4px;background:none;color:#94a3b8;font-size:14px}
#pg .cau{background:#fff;color:#0f172a;border-radius:18px;padding:22px 26px;font-size:clamp(20px,2.2vw,32px)}
#pg .cau img,#pg .cau svg{max-width:100%;height:auto}#pg .pa{display:grid;grid-template-columns:1fr 1fr;gap:14px}
#pg .pa>div{border-radius:16px;padding:16px 20px;color:#fff;font-size:clamp(18px,1.9vw,28px);display:flex;gap:12px;align-items:flex-start;position:relative;min-height:84px}
#pg .pa .k{font-weight:900;font-size:1.2em;opacity:.9}#pg .pa .noi{background:#fff;color:#0f172a;border-radius:10px;padding:4px 10px;flex:1}
#pg .pa>div.sai{opacity:.28}#pg .pa>div.dung{outline:6px solid #fde68a;transform:scale(1.02)}
#pg .pa .dem{position:absolute;right:12px;bottom:8px;font-weight:900;font-size:22px;background:rgba(0,0,0,.35);border-radius:10px;padding:0 10px}
#pg .tf>div{display:flex;justify-content:space-between;gap:12px;background:#1e293b;border-radius:12px;padding:10px 16px;margin:6px 0;font-size:clamp(18px,1.8vw,26px)}
#pg .tf .noi{background:#fff;color:#0f172a;border-radius:8px;padding:2px 10px;flex:1}
#pg .dong-ho{font:900 46px/1 ui-monospace,Menlo,monospace;min-width:110px;text-align:center;background:#7c3aed;border-radius:16px;padding:10px 14px}
#pg .dong-ho.gap{background:#dc2626;animation:pgNhay .5s infinite alternate}@keyframes pgNhay{to{opacity:.65}}
#pg .xh{display:flex;flex-direction:column;gap:8px}#pg .xh>div{display:grid;grid-template-columns:52px 1fr auto;gap:12px;align-items:center;background:#1e293b;border-radius:12px;padding:10px 16px;font-size:20px}
#pg .xh .h{font-weight:900;font-size:24px;text-align:center}#pg .xh .d{font:800 22px ui-monospace,Menlo,monospace;color:#fde68a}
#pg .tien{height:8px;background:#334155;border-radius:9px;overflow:hidden;margin-top:4px}#pg .tien>i{display:block;height:100%;background:#22c55e}
#pg .bp{display:flex;gap:18px;align-items:flex-end;justify-content:center;min-height:300px}#pg .bp>div{text-align:center;width:200px}
#pg .bp .cot{border-radius:14px 14px 0 0;display:grid;place-items:center;font-size:48px;font-weight:900}
#pg .doi{display:flex;gap:12px;flex-wrap:wrap}#pg .doi>div{flex:1;min-width:140px;border-radius:14px;padding:12px 16px;font-weight:800;font-size:20px}
#pg .goi{color:#94a3b8;font-size:15px}#pg .toast{position:fixed;left:50%;bottom:24px;transform:translateX(-50%);background:#f8fafc;color:#0f172a;padding:10px 18px;border-radius:12px;font-weight:700;display:none;z-index:100000}
@media (prefers-reduced-motion:reduce){#pg *{animation:none!important;transition:none!important}}`;
  document.head.appendChild(c);
}
function __pgToast(m) { const t = document.getElementById('pg-toast'); if (!t) return; t.textContent = m; t.style.display = 'block'; clearTimeout(__pgToast.h); __pgToast.h = setTimeout(() => t.style.display = 'none', 2200); }
// dựng HTML câu hỏi từ dữ liệu đề (dùng latex() của trang đề — hình TikZ đã có SVG)
function __pgCau(q) {
  const anh = q.imageSvg ? '<img class="figure" src="' + __pe(svgUrl(q.imageSvg)) + '">' : q.image ? '<img class="figure" src="' + __pe(q.image) + '">' : '';
  const de = '<div class="de">' + latex(q.stem, q, 'stem', false) + anh + '</div>';
  const pa = (q.options || []).map((o, i) => latex(o, q, 'option' + i, false));
  return { de, pa };
}
function __pgDuLieu() { return JSON.parse(document.getElementById('exam-data').textContent); }
function __pgGoi(duong, d) {
  return fetch('/api/' + duong, { method: d ? 'POST' : 'GET', credentials: 'same-origin', headers: { 'content-type': 'application/json' }, body: d ? JSON.stringify(d) : undefined })
    .then(r => r.json()).catch(e => ({ ok: false, loi: String(e) }));
}
function __pgMath(el) { if (window.MathJax && MathJax.typesetPromise) MathJax.typesetPromise([el]).catch(() => {}); }
const __pgUrlChoi = ma => location.origin + '/choi/' + ma;
const __pgQr = u => 'https://api.qrserver.com/v1/create-qr-code/?size=700x700&margin=10&data=' + encodeURIComponent(u);

async function __phongGV() {
  __pgCss();
  const d = __pgDuLieu(), sl = (d.settings && d.settings.studentExam && d.settings.studentExam.examId) || location.pathname.split('/').filter(Boolean)[0];
  const g = document.createElement('div'); g.id = 'pg'; document.body.appendChild(g);
  g.innerHTML = '<div class="dau"><h1>' + (new URLSearchParams(location.search).has('phieu') ? '🎫 ' : '🎮 Phòng thi đấu · ') + __pe(d.title) + '</h1><span id="pg-ma-nho" class="goi"></span><button id="pg-tat" title="Toàn màn hình (F)">⛶</button></div><div class="than" id="pg-than"></div><div class="toast" id="pg-toast" role="status"></div>';
  document.getElementById('pg-tat').onclick = () => document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen?.().catch(() => {});
  document.addEventListener('keydown', e => { if (e.target.matches('input,select,textarea')) return; if (e.key === 'f' || e.key === 'F') document.getElementById('pg-tat').click(); if ((e.key === 'ArrowRight' || e.key === ' ') && __PG.st) { e.preventDefault(); __pgTiep(); } });
  const daCo = new URLSearchParams(location.search).get('phong');
  if (/^\d{6}$/.test(daCo || '')) return __pgNoi(daCo);
  if (new URLSearchParams(location.search).has('phieu')) {        // 🎫 phiếu cuối giờ: mở phòng ngay, học sinh tự làm, không xếp hạng
    document.getElementById('pg-than').innerHTML = '<div class="the">Đang mở phiếu cuối giờ…</div>';
    const k = await __pgGoi('phong/tao', { slug: sl, vao: 'tk', nhip: 'tu_do', doi: 0, giay: 120, kieu: 'phieu' });
    if (!k.ok) { document.getElementById('pg-than').innerHTML = '<div class="the">' + __pe(k.loi || 'Chưa mở được phòng') + '</div>'; return; }
    history.replaceState(null, '', location.pathname + '?phong=' + k.ma + '&phieu=1'); __PG.tuBatDau = true; return __pgNoi(k.ma);
  }
  // cài đặt trước khi mở phòng
  const than = document.getElementById('pg-than');
  than.innerHTML = `<div class="the"><h2 style="margin:0 0 6px">Mở phòng thi đấu</h2><p class="goi" style="margin:0 0 16px">${d.questions.length} câu · học sinh quét QR bằng điện thoại để vào phòng, chọn đáp án trên máy của mình.</p>
    <div class="luoi"><label>Học sinh vào phòng bằng<select id="pg-vao"><option value="tk">Tài khoản thầy đã cấp (điểm gắn đúng tên)</option><option value="biet_danh">Nhập biệt danh (không cần tài khoản)</option></select></label>
    <label>Nhịp chạy câu<select id="pg-nhip"><option value="gv">Thầy bấm sang câu — cả lớp cùng câu</option><option value="tu_do">Học sinh tự làm theo tốc độ riêng</option></select></label>
    <label>Chơi theo<select id="pg-doi"><option value="0">Cá nhân</option>${[2, 3, 4, 5, 6, 7, 8].map(n => `<option value="${n}">${n} đội (máy chia ngẫu nhiên)</option>`).join('')}</select></label>
    <label>Thời gian mỗi câu (giây)<input id="pg-giay" type="number" min="5" max="300" value="30"></label></div>
    <div style="margin-top:20px;display:flex;gap:12px;flex-wrap:wrap"><button class="chinh" id="pg-mo">🚪 Mở phòng</button><button id="pg-huy">Thoát</button></div>
    <p class="goi" style="margin:14px 0 0">Tính điểm: đúng được 600–1000 điểm tuỳ nhanh chậm, đúng liên tiếp thưởng thêm. Câu Đúng/Sai tính theo số ý đúng. Đội: điểm trung bình các thành viên.</p></div>`;
  try { const c = JSON.parse(localStorage.getItem('pg_cai') || '{}'); for (const k of ['vao', 'nhip', 'doi', 'giay']) if (c[k] != null) document.getElementById('pg-' + k).value = c[k]; } catch (_) {}
  document.getElementById('pg-huy').onclick = () => { location.href = location.pathname; };
  document.getElementById('pg-mo').onclick = async ev => {
    const c = { slug: sl, vao: document.getElementById('pg-vao').value, nhip: document.getElementById('pg-nhip').value, doi: +document.getElementById('pg-doi').value, giay: +document.getElementById('pg-giay').value || 30 };
    try { localStorage.setItem('pg_cai', JSON.stringify(c)); } catch (_) {}
    ev.target.disabled = true; ev.target.textContent = 'Đang mở…';
    const k = await __pgGoi('phong/tao', c);
    if (!k.ok) { ev.target.disabled = false; ev.target.textContent = '🚪 Mở phòng'; alert(k.loi || 'Chưa mở được phòng'); return; }
    history.replaceState(null, '', location.pathname + '?phong=' + k.ma); __pgNoi(k.ma);
  };
}
function __pgNoi(ma) {
  __PG.ma = ma; document.getElementById('pg-ma-nho').textContent = 'Mã phòng ' + ma + ' · ' + __pgUrlChoi(ma).replace(/^https?:\/\//, '');
  const ws = new WebSocket((location.protocol === 'https:' ? 'wss://' : 'ws://') + location.host + '/api/phong/' + ma + '/ws?vai=gv');
  __PG.ws = ws;
  ws.onopen = () => { __PG.lan = 0; ws.send(JSON.stringify({ t: 'chao' })); };
  ws.onmessage = e => { const m = JSON.parse(e.data); if (m.t === 'loi') return __pgToast(m.loi); if (m.t === 'phong') __pgNhan(m); };
  ws.onclose = ev => {
    if (ev.code === 1008 || ev.code === 4404) return;
    __pgToast('Mất kết nối — đang nối lại…'); setTimeout(() => __pgNoi(ma), Math.min(8000, 1000 * (1 + (__PG.lan = (__PG.lan || 0) + 1))));
  };
}
function __pgGui(m) { if (__PG.ws && __PG.ws.readyState === 1) __PG.ws.send(JSON.stringify(m)); }
function __pgNhan(m) {
  __PG.lech = m.bay_gio - Date.now(); __PG.st = m;
  if (!m.co_cau && !__PG.nap) {             // nạp câu hỏi (HTML dựng sẵn, không đáp án) cho máy chủ — chỉ một lần
    __PG.nap = true; const d = __pgDuLieu();
    __pgGui({ t: 'nap', cau: d.questions.map(q => { const c = __pgCau(q); return { html: c.de + (q.type === 'short' ? '' : '<ol class="pa-ds" type="' + (q.type === 'mcq' ? 'A' : 'a') + '">' + c.pa.map(x => '<li>' + x + '</li>').join('') + '</ol>'), so_pa: (q.options || []).length }; }) });
    return;
  }
  if (m.kieu === 'phieu' && m.giai_doan === 'cho' && m.co_cau && !__PG.daBD) { __PG.daBD = true; __pgGui({ t: 'bat_dau_phieu' }); }
  if (m.kieu === 'phieu' && m.giai_doan === 'ket_thuc' && !__PG.daLuu) { __PG.daLuu = true; __pgGoi('phong/' + m.ma + '/luu', {}).then(k => __pgToast(k.ok ? '✓ Đã lưu kết quả phiếu (' + k.so + ' em)' : (k.loi || 'Chưa lưu được'))); }
  __pgVe();
}
function __pgTiep() {
  const s = __PG.st; if (!s) return;
  if (s.giai_doan === 'cho') return __pgGui({ t: 'bat_dau' });
  if (s.nhip !== 'gv') return;
  if (s.giai_doan === 'cau') return __pgGui({ t: 'het_gio' });
  if (s.giai_doan === 'dap_an') return s.cur + 1 < s.so_cau ? __pgGui({ t: 'cau', i: s.cur + 1 }) : __pgGui({ t: 'ket_thuc' });
}
const __pgTenDoi = i => i == null ? '' : (__DOI[i] || ['Đội ' + (i + 1), '#64748b'])[0];
const __pgMauDoi = i => i == null ? '#334155' : (__DOI[i] || ['', '#64748b'])[1];
function __pgXH(ds, n) {
  return '<div class="xh">' + ds.slice(0, n).map((p, i) => `<div><span class="h">${['🥇', '🥈', '🥉'][i] || i + 1}</span><span>${__pe(p.ten)}${p.doi != null ? ` <span class="chip" style="background:${__pgMauDoi(p.doi)};font-size:13px;padding:2px 10px">${__pgTenDoi(p.doi)}</span>` : ''}${p.chuoi >= 3 ? ` <span title="Chuỗi đúng">🔥${p.chuoi}</span>` : ''}</span><span class="d">${p.diem}</span></div>`).join('') + '</div>';
}
function __pgBangDoi(s) {
  if (!s.so_doi || !s.doi.length) return '';
  return '<div class="doi">' + s.doi.map((x, i) => `<div style="background:${__pgMauDoi(x.doi)}">${i === 0 && x.diem ? '👑 ' : ''}Đội ${__pgTenDoi(x.doi)}<br><span style="font:900 30px ui-monospace,Menlo,monospace">${x.diem}</span> <span style="font-size:14px;font-weight:600">· ${x.n} người</span></div>`).join('') + '</div>';
}
function __pgVe() {
  const s = __PG.st, than = document.getElementById('pg-than'), d = __pgDuLieu(); clearInterval(__PG.hen);
  const xep = s.nguoi.slice().sort((a, b) => b.diem - a.diem), onl = s.nguoi.filter(p => p.onl).length;
  if (s.giai_doan === 'cho') {
    const url = __pgUrlChoi(s.ma);
    than.innerHTML = `<div class="cho"><div class="the" style="text-align:center"><img class="qr" alt="QR vào phòng" src="${__pgQr(url)}"><div class="goi" style="margin-top:10px">hoặc vào <b style="color:#fff">${__pe(url.replace(/^https?:\/\//, '').replace(/\/choi\/.*/, '/choi'))}</b> nhập mã</div><div class="ma">${s.ma}</div>
        <div class="goi">${s.vao === 'tk' ? '🔐 Đăng nhập tài khoản đã cấp' : '😀 Nhập biệt danh, không cần tài khoản'} · ${s.nhip === 'gv' ? 'thầy bấm sang câu' : 'tự làm theo tốc độ riêng'} · ${s.giay} giây/câu</div></div>
      <div class="the"><div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:10px"><h2 style="margin:0;flex:1">👥 ${s.nguoi.length} học sinh trong phòng</h2>
        <label style="flex-direction:row;align-items:center">Chơi theo <select id="pg-doi2">${[0, 2, 3, 4, 5, 6, 7, 8].map(n => `<option value="${n}" ${s.so_doi === n ? 'selected' : ''}>${n ? n + ' đội' : 'Cá nhân'}</option>`).join('')}</select></label>
        ${s.so_doi ? '<button id="pg-chia">🎲 Chia đội lại</button>' : ''}<button class="xanh" id="pg-bd" ${s.nguoi.length ? '' : 'disabled'}>▶ Bắt đầu</button></div>
        ${s.so_doi ? __pgBangDoi(s) + '<div style="height:8px"></div>' : ''}
        <div>${s.nguoi.length ? s.nguoi.map(p => `<span class="chip ${p.onl ? '' : 'off'}" style="${p.doi != null ? 'background:' + __pgMauDoi(p.doi) : ''}">${__pe(p.ten)}<button data-ra="${__pe(p.id)}" title="Mời ra khỏi phòng" aria-label="Mời ${__pe(p.ten)} ra">✕</button></span>`).join('') : '<p class="goi">Chờ học sinh quét mã… Tên các em sẽ hiện ở đây.</p>'}</div></div></div>`;
    document.getElementById('pg-bd').onclick = () => __pgGui({ t: 'bat_dau' });
    document.getElementById('pg-doi2').onchange = e => __pgGui({ t: 'cai_dat', so_doi: +e.target.value });
    const c = document.getElementById('pg-chia'); if (c) c.onclick = () => __pgGui({ t: 'chia_lai' });
    than.querySelectorAll('[data-ra]').forEach(b => b.onclick = () => { if (confirm('Mời em này ra khỏi phòng?')) __pgGui({ t: 'moi_ra', id: b.dataset.ra }); });
    return;
  }
  if (s.giai_doan === 'ket_thuc') return s.kieu === 'phieu' ? __pgVePhieu(s, true) : __pgVeKetThuc(s);
  if (s.kieu === 'phieu') return __pgVePhieu(s);
  if (s.nhip === 'tu_do') {
    than.innerHTML = `<div style="display:flex;align-items:center;gap:14px;flex-wrap:wrap"><h2 style="margin:0;flex:1">🏃 Học sinh đang tự làm · ${s.so_cau} câu · ${onl}/${s.nguoi.length} em đang kết nối</h2><button class="chinh" id="pg-kt">🏁 Kết thúc &amp; xem kết quả</button></div>
      ${__pgBangDoi(s)}<div class="xh">${xep.map((p, i) => `<div><span class="h">${['🥇', '🥈', '🥉'][i] || i + 1}</span><span>${__pe(p.ten)} ${p.doi != null ? `<span class="chip" style="background:${__pgMauDoi(p.doi)};font-size:13px;padding:2px 10px">${__pgTenDoi(p.doi)}</span>` : ''}
        <div class="tien"><i style="width:${Math.round(100 * p.da_lam / Math.max(1, s.so_cau))}%"></i></div><span class="goi">${p.da_lam}/${s.so_cau} câu · đúng ${p.dung}</span></span><span class="d">${p.diem}</span></div>`).join('')}</div>`;
    document.getElementById('pg-kt').onclick = () => { if (confirm('Kết thúc phòng? Các em chưa làm xong sẽ dừng ở câu hiện tại.')) __pgGui({ t: 'ket_thuc' }); };
    return;
  }
  const q = d.questions[s.cur], c = __pgCau(q), lo = s.giai_doan === 'dap_an', da = s.dap_an;
  let pa = '';
  if (q.type === 'mcq') pa = '<div class="pa">' + c.pa.map((x, j) => `<div class="${lo ? (da === j ? 'dung' : 'sai') : ''}" style="background:${__MAU_PA[j]}"><span class="k">${__HINH_PA[j]} ${'ABCD'[j]}</span><span class="noi">${x}</span>${lo && s.chon ? `<span class="dem">${s.chon[j]}</span>` : ''}</div>`).join('') + '</div>';
  else if (q.type === 'tf') pa = '<div class="tf">' + c.pa.map((x, j) => `<div><b>${'abcd'[j]})</b><span class="noi">${x}</span>${lo && da ? `<b style="color:${da[j] ? '#4ade80' : '#f87171'}">${da[j] ? 'ĐÚNG' : 'SAI'}</b>` : ''}</div>`).join('') + '</div>';
  else pa = lo ? `<div class="the" style="font-size:28px">Đáp số: <b style="color:#fde68a">${__pe(da)}</b></div>` : '<div class="the goi" style="font-size:22px">✍️ Học sinh nhập đáp số trên điện thoại</div>';
  than.innerHTML = `<div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap"><span style="font-size:22px;font-weight:800">Câu ${s.cur + 1}/${s.so_cau}</span>
      <span class="goi">${{ mcq: 'Trắc nghiệm', tf: 'Đúng / Sai', short: 'Trả lời ngắn' }[q.type]}</span><span style="flex:1"></span>
      <span style="font-size:20px">✋ <b>${s.da_tl}</b>/${onl || s.nguoi.length} đã trả lời</span>${lo ? '' : '<div class="dong-ho" id="pg-dh">–</div>'}</div>
    <div class="cau" id="pg-cau">${c.de}</div>${pa}
    <div style="display:flex;gap:12px;flex-wrap:wrap;align-items:flex-start">${lo ? `<div style="flex:1;min-width:300px"><h3 style="margin:0 0 8px">🏆 Bảng xếp hạng</h3>${__pgBangDoi(s)}<div style="height:8px"></div>${__pgXH(xep, 5)}</div>` : '<span style="flex:1"></span>'}
      <div style="display:flex;gap:10px;flex-wrap:wrap">${lo ? (s.cur + 1 < s.so_cau ? '<button class="chinh" id="pg-sau">Câu tiếp ▶</button>' : '<button class="chinh" id="pg-kt">🏁 Xem kết quả chung cuộc</button>') : '<button id="pg-them">+10 giây</button><button class="chinh" id="pg-hg">⏹ Hết giờ · hiện đáp án</button>'}</div></div>`;
  __pgMath(than);
  const b = id => document.getElementById(id);
  if (b('pg-sau')) b('pg-sau').onclick = () => __pgGui({ t: 'cau', i: s.cur + 1 });
  if (b('pg-kt')) b('pg-kt').onclick = () => __pgGui({ t: 'ket_thuc' });
  if (b('pg-hg')) b('pg-hg').onclick = () => __pgGui({ t: 'het_gio' });
  if (b('pg-them')) b('pg-them').onclick = () => __pgGui({ t: 'them_gio' });
  if (!lo) {
    const chay = () => { const con = Math.max(0, Math.ceil((s.het_luc - (Date.now() + __PG.lech)) / 1000)), el = b('pg-dh'); if (!el) return clearInterval(__PG.hen);
      el.textContent = con; el.classList.toggle('gap', con <= 5); };
    chay(); __PG.hen = setInterval(chay, 250);
  }
}
function __pgVeKetThuc(s) {
  const than = document.getElementById('pg-than'), xep = s.nguoi.slice().sort((a, b) => b.diem - a.diem), top = xep.slice(0, 3);
  const bac = [1, 0, 2].filter(i => top[i]).map(i => `<div><div style="font-size:22px;font-weight:800;margin-bottom:6px">${__pe(top[i].ten)}</div><div class="goi" style="color:#fde68a;font:800 22px ui-monospace,Menlo,monospace">${top[i].diem}</div>
      <div class="cot" style="height:${[220, 160, 120][i]}px;background:${['#eab308', '#94a3b8', '#b45309'][i]}">${['🥇', '🥈', '🥉'][i]}</div></div>`).join('');
  than.innerHTML = `<h2 style="margin:0;text-align:center;font-size:30px">🏁 Kết quả chung cuộc</h2>${s.so_doi && s.doi.length ? `<div class="the" style="text-align:center"><div style="font-size:26px;font-weight:900">👑 Đội ${__pgTenDoi(s.doi[0].doi)} vô địch!</div><div style="height:10px"></div>${__pgBangDoi(s)}</div>` : ''}
    <div class="bp">${bac}</div><div style="display:flex;gap:10px;flex-wrap:wrap;justify-content:center"><button class="xanh" id="pg-luu">💾 Lưu kết quả vào máy chủ</button><button id="pg-csv">⬇ Tải Excel (CSV)</button><button id="pg-moi">Mở phòng mới</button></div>
    <div class="the"><h3 style="margin:0 0 8px">Bảng xếp hạng đầy đủ (${xep.length} em)</h3>${__pgXH(xep, 500)}</div>`;
  document.getElementById('pg-moi').onclick = () => { location.href = location.pathname + '?phong'; };
  document.getElementById('pg-luu').onclick = async e => { e.target.disabled = true; const k = await __pgGoi('phong/' + s.ma + '/luu', {}); e.target.disabled = false;
    __pgToast(k.ok ? '✓ Đã lưu ' + k.so + ' kết quả' : (k.loi || 'Chưa lưu được')); };
  document.getElementById('pg-csv').onclick = async () => {
    const k = await __pgGoi('phong/' + s.ma + '/ket-qua'); if (!k.ok) return __pgToast('Phòng không còn');
    const F = v => String(v).replace('.', ','), dau = ['Hạng', 'Tên', 'Tài khoản', 'Lớp', 'STT', 'Đội', 'Điểm thi đấu', 'Số câu đúng', 'Số câu đã trả lời', 'Điểm thang 10'];
    const csv = '﻿' + [dau, ...k.nguoi.map(p => [p.hang, p.ho_ten || p.ten, p.tk || '', p.lop || '', p.stt || '', p.doi != null ? __pgTenDoi(p.doi) : '', p.diem, p.dung, p.da_lam, F(p.diem10)])]
      .map(r => r.map(v => '"' + String(v).replace(/"/g, '""') + '"').join(',')).join('\n');
    const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv' })); a.download = 'ThiDau_' + s.ma + '.csv'; a.click();
  };
}

// ===== 🎫 PHIẾU CUỐI GIỜ: thống kê từng câu + lỗi sai phổ biến + tự đánh giá =====
function __pgDapChu(type, v) { if (v == null) return '—'; return type === 'mcq' ? 'ABCD'[v] : type === 'tf' ? (Array.isArray(v) ? v.map((x, j) => 'abcd'[j] + (x ? 'Đ' : 'S')).join(' ') : '—') : String(v); }
function __pgVePhieu(s, xong) {
  const than = document.getElementById('pg-than'), d = __pgDuLieu(), tk = s.thong_ke || [], url = __pgUrlChoi(s.ma);
  const nop = s.nguoi.filter(p => p.da_lam >= s.so_cau).length, dg = s.danh_gia || [0, 0, 0], tdg = dg[0] + dg[1] + dg[2];
  const pt = x => x == null ? '—' : Math.round(100 * x) + '%', mau = x => x == null ? '#475569' : x >= .8 ? '#16a34a' : x >= .6 ? '#ca8a04' : '#dc2626';
  const yeu = tk.map((x, i) => ({ ...x, i })).filter(x => x.n && x.dung < .6).sort((a, b) => a.dung - b.dung);
  than.innerHTML = `<div style="display:grid;grid-template-columns:${xong ? '1fr' : 'minmax(220px,300px) 1fr'};gap:20px;align-items:start">
    ${xong ? '' : `<div class="the" style="text-align:center"><img class="qr" alt="QR" src="${__pgQr(url)}"><div class="ma" style="font-size:52px">${s.ma}</div><div class="goi">${__pe(url.replace(/^https?:\/\//, '').replace(/\/choi\/.*/, '/choi'))}</div>
      <div style="font-size:30px;font-weight:900;margin-top:10px">${nop}<span class="goi" style="font-size:18px">/${s.nguoi.length} em đã nộp</span></div>
      <button class="chinh" id="pg-kt" style="margin-top:12px;width:100%">🏁 Kết thúc &amp; lưu</button></div>`}
    <div style="display:flex;flex-direction:column;gap:14px">
      <h2 style="margin:0">🎫 Phiếu cuối giờ · ${__pe(s.ten)}${xong ? ' — kết quả' : ''}</h2>
      <div class="the" style="display:flex;gap:18px;flex-wrap:wrap;align-items:center;font-size:22px"><b>Các em tự đánh giá:</b>
        <span>😀 Hiểu rõ <b>${dg[0]}</b></span><span>😐 Còn chỗ chưa chắc <b>${dg[1]}</b></span><span>😟 Chưa hiểu <b>${dg[2]}</b></span>
        ${tdg ? `<div style="flex-basis:100%;display:flex;height:16px;border-radius:9px;overflow:hidden"><i style="width:${100 * dg[0] / tdg}%;background:#22c55e"></i><i style="width:${100 * dg[1] / tdg}%;background:#eab308"></i><i style="width:${100 * dg[2] / tdg}%;background:#ef4444"></i></div>` : ''}</div>
      ${xong && yeu.length ? `<div class="the" style="background:#422006;border:2px solid #f59e0b"><b style="font-size:22px">💡 Gợi ý mở đầu tiết sau</b>${yeu.map(x => `<div style="margin-top:8px;font-size:19px">• Sửa <b>câu ${x.i + 1}</b>${x.ten_dang ? ' (' + __pe(x.ten_dang) + ')' : ''}: chỉ ${pt(x.dung)} đúng${x.sai_nhieu ? `, ${x.sai_nhieu.so} em chọn <b>${__pe(__pgDapChu(x.type, x.sai_nhieu.v))}</b>` : ''} — đáp án ${__pe(__pgDapChu(x.type, x.dap_an))}.</div>`).join('')}</div>`
        : xong ? '<div class="the" style="background:#052e16;border:2px solid #22c55e;font-size:20px">🎉 Mọi câu đều trên 60% đúng — lớp nắm bài tốt!</div>' : ''}
      ${tk.map((x, i) => { const q = d.questions[i], c = __pgCau(q);
        return `<div class="the"><div style="display:flex;gap:12px;align-items:center;flex-wrap:wrap"><b style="font-size:22px">Câu ${i + 1}</b><span class="goi">${__pe(x.ten_dang || '')}</span><span style="flex:1"></span>
          <span style="font:900 34px ui-monospace,Menlo,monospace;color:${mau(x.dung)}">${pt(x.dung)}</span><span class="goi">${x.n} em</span></div>
          <div class="tien" style="height:12px;margin:8px 0"><i style="width:${Math.round(100 * (x.dung || 0))}%;background:${mau(x.dung)}"></i></div>
          <details><summary class="goi" style="cursor:pointer">Xem đề</summary><div class="cau" style="font-size:18px;margin-top:8px">${c.de}</div></details>
          ${x.chon ? `<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-top:8px">${x.chon.map((n, j) => `<div style="border-radius:10px;padding:8px 10px;background:${j === x.dap_an ? '#166534' : '#334155'};${j === x.dap_an ? 'outline:3px solid #4ade80' : ''}"><b>${'ABCD'[j]}</b>${j === x.dap_an ? ' ✓' : ''} <span style="float:right;font-weight:900">${n}</span></div>`).join('')}</div>` : ''}
          ${x.sai_nhieu && x.dung < 1 ? `<div style="margin-top:8px;color:#fca5a5">Sai nhiều nhất: <b>${__pe(__pgDapChu(x.type, x.sai_nhieu.v))}</b> (${x.sai_nhieu.so} em) · đáp án <b style="color:#86efac">${__pe(__pgDapChu(x.type, x.dap_an))}</b></div>` : ''}</div>`; }).join('')}
      ${xong ? '<div style="display:flex;gap:10px;flex-wrap:wrap"><button id="pg-csv">⬇ Tải Excel</button><button id="pg-moi">Đóng phiếu</button></div>' : ''}</div></div>`;
  __pgMath(than);
  const b = id => document.getElementById(id);
  if (b('pg-kt')) b('pg-kt').onclick = () => { if (confirm('Kết thúc phiếu và lưu kết quả? Em chưa nộp sẽ dừng ở câu đang làm.')) __pgGui({ t: 'ket_thuc' }); };
  if (b('pg-moi')) b('pg-moi').onclick = () => { location.href = location.pathname; };
  if (b('pg-csv')) b('pg-csv').onclick = async () => {
    const k = await __pgGoi('phong/' + s.ma + '/ket-qua'); if (!k.ok) return __pgToast('Phòng không còn');
    const DG = ['😀 Hiểu rõ', '😐 Chưa chắc', '😟 Chưa hiểu'], dau = ['Tên', 'Tài khoản', 'Lớp', 'STT', ...Array.from({ length: k.so_cau }, (_, i) => 'Câu ' + (i + 1)), 'Số câu đúng', 'Tự đánh giá'];
    const csv = '﻿' + [dau, ...k.nguoi.map(p => [p.ho_ten || p.ten, p.tk || '', p.lop || '', p.stt || '', ...Array.from({ length: k.so_cau }, (_, i) => { const x = p.tl[i]; return x ? (x.ti_le === 1 ? 'Đúng' : x.ti_le > 0 ? 'Một phần' : 'Sai') : ''; }), p.dung, p.danh_gia != null ? DG[p.danh_gia] : ''])]
      .map(r => r.map(v => '"' + String(v).replace(/"/g, '""') + '"').join(',')).join('\n');
    const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv' })); a.download = 'PhieuCuoiGio_' + s.ma + '.csv'; a.click();
  };
}
