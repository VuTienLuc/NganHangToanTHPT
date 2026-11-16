/* Tổng hợp quá trình học online theo lớp — dùng chung cho ứng dụng ra đề (máy thầy) và trang giáo viên trên web.
   TongHop.mo({goi:(viec, du_lieu) => Promise<json>, lop?:'10A1'})   viec: 'tong-hop' | 'loi-nhan' */
(function () {
  const KY = '— Thầy Vũ Tiến Lực';
  const CSS = `
#th-hop{position:fixed;inset:0;background:rgba(15,23,42,.5);display:none;align-items:center;justify-content:center;z-index:9000;font:14px/1.45 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;color:#0f172a}
#th-hop *{box-sizing:border-box}#th-hop table{display:table}#th-hop th,#th-hop td{display:table-cell}#th-hop button{width:auto;margin:0}#th-hop label{display:inline-flex;align-items:center;gap:6px;font-weight:600;margin:0}#th-hop input[type=checkbox]{width:18px;height:18px;padding:0}#th-hop button,#th-hop select{font:inherit;font-size:13.5px;border:1px solid #cbd5e1;background:#fff;color:#0f172a;border-radius:8px;padding:6px 11px;min-height:36px;cursor:pointer}
#th-hop button:hover{border-color:#1e40af}#th-hop button:focus-visible,#th-hop select:focus-visible{outline:3px solid #93c5fd;outline-offset:1px}
#th-hop button.chinh{background:#1e40af;border-color:#1e40af;color:#fff;font-weight:700}#th-hop button.hong{background:#db2777;border-color:#db2777;color:#fff;font-weight:700}
#th-hop button:disabled{opacity:.55;cursor:default}
#th-hop .th-noi{background:#fff;border-radius:14px;width:min(1200px,97vw);max-height:94vh;display:flex;flex-direction:column;box-shadow:0 20px 60px rgba(0,0,0,.3)}
#th-hop .th-dau{display:flex;align-items:center;gap:10px;padding:12px 16px;border-bottom:1px solid #e2e8f0;flex-wrap:wrap}#th-hop .th-dau h2{margin:0;font-size:17px;flex:1;min-width:220px}
#th-hop .th-than{overflow:auto;padding:12px 16px}#th-hop .th-chan{display:flex;gap:8px;padding:10px 16px;border-top:1px solid #e2e8f0;flex-wrap:wrap;justify-content:flex-end}
.th-the{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px;margin-bottom:10px}
.th-the>div{border:1px solid #e2e8f0;border-radius:10px;padding:8px 10px}.th-the b{display:block;font-size:22px;color:#1e40af;font-variant-numeric:tabular-nums}.th-the span{font-size:12px;color:#64748b}
.th-the .qt b{color:#db2777}
.th-hop2{border-radius:10px;padding:10px 12px;margin-bottom:10px}.th-hop2 h3{margin:0 0 6px;font-size:14px}
.th-nx{background:#f0fdf4;border:1px solid #bbf7d0}.th-nx h3{color:#15803d}
.th-qt{background:#fdf2f8;border:1px solid #fbcfe8}.th-qt h3{color:#be185d;display:flex;align-items:center;gap:8px;flex-wrap:wrap}
#th-hop textarea{font:inherit;width:100%;min-height:110px;border:1px solid #bbf7d0;border-radius:8px;padding:8px;font-size:13.5px;line-height:1.5;resize:vertical;background:#fff;color:#0f172a}
.th-em{display:grid;grid-template-columns:auto 190px minmax(0,1fr) auto;gap:8px;align-items:start;padding:8px 0;border-top:1px dashed #fbcfe8}
.th-em:first-of-type{border-top:0}.th-em input[type=checkbox]{width:18px;height:18px;margin-top:4px;accent-color:#db2777}
.th-em .ten{font-weight:700}.th-em .ly{display:flex;gap:4px;flex-wrap:wrap;margin-top:3px}
.th-ly{font-size:11.5px;border-radius:6px;padding:0 6px;background:#fff;border:1px solid #fbcfe8;color:#9d174d;font-weight:600}
.th-em textarea{min-height:64px!important;border-color:#fbcfe8!important}.th-em .da{font-size:11.5px;color:#64748b;margin-top:3px}
.th-bd svg{width:100%;height:150px}
.th-bang{border-collapse:collapse;font-size:12.5px;width:100%}.th-bang th,.th-bang td{border-bottom:1px solid #eef0f4;padding:5px 6px;text-align:center}
.th-bang th{position:sticky;top:0;background:#f8fafc;font-weight:700;color:#334155;z-index:1}.th-bang th.cot-dot{font-weight:600;font-size:11.5px}
.th-bang td.ten,.th-bang th.ten{text-align:left;white-space:nowrap}.th-bang td.nx{text-align:left;min-width:260px;font-size:12.5px;color:#14532d}
.th-bang td.nx[contenteditable]:focus{outline:2px solid #86efac;background:#f0fdf4}
.th-bang tr.qt td{background:#fdf2f8}.th-co{border:0!important;background:none!important;padding:2px 4px!important;min-height:0!important;font-size:15px!important;color:#cbd5e1!important}
.th-co[aria-pressed=true]{color:#db2777!important}
.o-d{display:inline-block;min-width:34px;border-radius:6px;padding:1px 4px;font-weight:700;font-variant-numeric:tabular-nums}
.o-d.g{background:#dcfce7;color:#15803d}.o-d.k{background:#dbeafe;color:#1e40af}.o-d.tb{background:#fef3c7;color:#b45309}.o-d.y{background:#fee2e2;color:#b91c1c}.o-d.c{color:#cbd5e1;font-weight:400}
.th-len{color:#15803d;font-weight:700}.th-xuong{color:#b45309;font-weight:700}
.th-toast{position:fixed;left:50%;bottom:24px;transform:translateX(-50%);background:#0f172a;color:#fff;padding:9px 16px;border-radius:10px;z-index:9100;font-size:14px;display:none}
.th-co.th-sao[aria-pressed=true]{color:#d97706!important}.th-ten{border:0!important;background:none!important;padding:0!important;min-height:0!important;color:#1e40af!important;font-weight:600;text-decoration:underline dotted;text-underline-offset:3px;text-align:left}
#th-hs{position:absolute;inset:0;display:none;align-items:center;justify-content:center;background:rgba(15,23,42,.35)}
#th-hs .th-hs-noi{background:#fff;border-radius:14px;width:min(1000px,95vw);max-height:92vh;display:flex;flex-direction:column;box-shadow:0 20px 60px rgba(0,0,0,.3)}
.th-td{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:10px}.th-td-the{border:1px solid #e2e8f0;border-radius:12px;padding:10px 12px;display:flex;flex-direction:column;gap:8px}
.th-td-dau{display:flex;gap:6px;align-items:center;flex-wrap:wrap}.th-td-dau .th-ten{font-size:15px}.th-td-the textarea{min-height:70px!important;border-color:#fbcfe8!important}
.th-giao{font-size:11px!important;min-height:0!important;padding:1px 6px!important;margin-top:3px!important;border-radius:999px!important;color:#64748b!important}
.th-giao.bat{background:#dcfce7!important;border-color:#86efac!important;color:#15803d!important}.th-bang th.them,.th-bang td.them{background:#f8fafc;color:#94a3b8}
@media (max-width:760px){.th-em{grid-template-columns:auto minmax(0,1fr)}.th-em textarea,.th-em .nut{grid-column:1/-1}}`;
  const e = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const F = v => v == null || isNaN(v) ? '—' : (Math.round(v * 10) / 10).toString().replace('.', ',');
  const mau = v => v == null ? 'c' : v >= 8 ? 'g' : v >= 6.5 ? 'k' : v >= 5 ? 'tb' : 'y';
  const bam = s => [...String(s)].reduce((a, c) => (a * 31 + c.charCodeAt(0)) >>> 0, 7);
  const goiTen = h => h.ho_ten ? h.ho_ten.trim().split(/\s+/).pop() : 'Em';
  const st = { goi: null, lop: null, k: null, T: null, danh: {}, bien: {} };
  let hop;

  function dung() {
    if (hop) return;
    const c = document.createElement('style'); c.textContent = CSS; document.head.appendChild(c);
    hop = document.createElement('div'); hop.id = 'th-hop'; hop.setAttribute('role', 'dialog'); hop.setAttribute('aria-modal', 'true'); hop.setAttribute('aria-labelledby', 'th-tieu');
    hop.innerHTML = `<div class="th-noi"><div class="th-dau"><h2 id="th-tieu">📊 Tổng hợp quá trình học online</h2>
      <label>Lớp <select id="th-lop" style="min-width:130px"></select></label><button id="th-tai" title="Lấy số liệu mới nhất">↻ Làm mới</button></div>
      <div class="th-than" id="th-than"></div>
      <div class="th-chan"><button id="th-chep">💬 Chép nhận xét lớp</button><button id="th-chep-em">Chép nhận xét từng em</button>
      <button id="th-xuat" class="chinh">⬇ Tải bảng tổng hợp (Excel)</button><button id="th-dong">Đóng</button></div></div><div class="th-toast" id="th-toast" role="status"></div>`;
    document.body.appendChild(hop);
    const $ = id => document.getElementById(id);
    $('th-dong').onclick = () => { hop.style.display = 'none' };
    hop.addEventListener('keydown', ev => { if (ev.key === 'Escape') hop.style.display = 'none' });
    $('th-lop').onchange = tai; $('th-tai').onclick = () => { st.lop = null; mo({ goi: st.goi, lop: $('th-lop').value }) };
    $('th-xuat').onclick = xuat;
    $('th-chep').onclick = () => chep($('th-nx-lop')?.value || '', 'Đã chép nhận xét lớp');
    $('th-chep-em').onclick = () => chep([...hop.querySelectorAll('td.nx')].map(td => td.innerText.trim()).join('\n'), 'Đã chép nhận xét từng em');
  }
  function toast(m) { const t = document.getElementById('th-toast'); t.textContent = m; t.style.display = 'block'; clearTimeout(toast.h); toast.h = setTimeout(() => t.style.display = 'none', 1800) }
  function chep(s, m) { navigator.clipboard.writeText(s).then(() => toast('✓ ' + m), () => toast('Chưa chép được — thầy bôi đen rồi Cmd+C')) }
  const luu = (k, v) => { try { localStorage.setItem('th_' + k, JSON.stringify(v)) } catch (_) {} };
  const doc = k => { try { return JSON.parse(localStorage.getItem('th_' + k) || 'null') } catch (_) { return null } };

  async function mo(o) {
    dung(); st.goi = o.goi; hop.style.display = 'flex';
    const $ = id => document.getElementById(id), than = $('th-than');
    than.innerHTML = 'Đang lấy danh sách lớp…';
    if (!st.lop) {
      const k = await st.goi('tong-hop', {}).catch(x => ({ ok: false, loi: String(x) }));
      if (!k.ok) { than.innerHTML = `<p style="color:#b45309">${e(k.loi || 'Chưa kết nối máy chủ')}</p>`; return }
      st.lop = k.cac_lop || [];
    }
    if (!st.lop.length) { $('th-lop').innerHTML = ''; than.innerHTML = '<p>Chưa có tài khoản học sinh. Nhập danh sách lớp ở mục 👥 Tài khoản học sinh trong ứng dụng ra đề.</p>'; return }
    $('th-lop').innerHTML = '<option value="__td">⭐ Học sinh đang theo dõi (mọi lớp)</option>' + st.lop.map(x => `<option value="${e(x.lop)}">${e(x.lop)} (${x.n} em)</option>`).join('');
    const muon = String(o.lop || doc('lop') || '').toUpperCase(), co = st.lop.find(x => x.lop.toUpperCase() === muon);
    $('th-lop').value = muon === '__TD' ? '__td' : co ? co.lop : st.lop[0].lop; $('th-lop').focus(); tai();
  }
  async function tai() {
    const lop = document.getElementById('th-lop').value, than = document.getElementById('th-than'); luu('lop', lop);
    const p0 = document.getElementById('th-hs'); if (p0) p0.style.display = 'none';
    if (lop === '__td') {
      than.innerHTML = 'Đang lấy học sinh theo dõi…'; st.T = null;
      const k = await st.goi('theo-doi', {}).catch(x => ({ ok: false, loi: String(x) }));
      if (!k.ok) { than.innerHTML = `<p style="color:#b45309">${e(k.loi || 'Lỗi')} — thầy bấm Đăng lại tất cả trong ứng dụng để máy chủ có chức năng theo dõi.</p>`; return }
      return veTD(k);
    }
    than.innerHTML = `Đang tổng hợp lớp ${e(lop)}…`;
    const k = await st.goi('tong-hop', { lop }).catch(x => ({ ok: false, loi: String(x) }));
    if (!k.ok) { than.innerHTML = `<p style="color:#b45309">${e(k.loi || 'Lỗi')}</p>`; return }
    st.k = k; st.danh = doc('danh_' + k.lop) || {}; st.bien = {}; ve();
  }

  // ---------- tính toán ----------
  const lopKhop = (ds, lop) => !String(ds || '').trim() || String(ds).split(',').map(x => x.trim().toUpperCase()).filter(Boolean).includes(String(lop || '').trim().toUpperCase());
  // bài “đã giao” mới tính hoàn thành / điểm TB; bài chưa giao em tự làm thì ghi nhận là tự luyện thêm
  const daGiao = (d, lop) => d.giao === 1 && lopKhop(d.lop, lop);   // chỉ bài thầy đã XÁC NHẬN giao mới tính
  function nhomBai(bai) {
    const theo = {};
    for (const b of bai) {
      const o = (theo[b.tk] ??= {})[b.nhom] ??= { lan: [], ds: [], goi_y: 0, cx: '', tab: 0 };
      o.lan.push(b.diem); o.ds.push(b); o.goi_y += b.goi_y || 0; o.tab += b.chuyen_tab || 0; if (b.cam_xuc) o.cx = b.cam_xuc;
    }
    return theo;
  }
  // một học sinh: điểm từng đợt (cao nhất), tiến bộ, lý do cần quan tâm
  function motEm(h, de, m, nhan, deThem) {
    m = m || {};
    const them = (deThem || []).filter(d => m[d.slug]).map(d => ({ de: d, cao: Math.max(...m[d.slug].lan), ds: m[d.slug].ds }));
    const tbThem = them.length ? them.reduce((a, x) => a + x.cao, 0) / them.length : null;
    const o = de.map(d => { const x = m[d.slug]; return x ? { cao: Math.max(...x.lan), dau: x.lan[0], so: x.lan.length, goi_y: x.goi_y, cx: x.cx, tab: x.tab, ds: x.ds } : null });
    const lam = o.filter(Boolean), diem = lam.map(x => x.cao), tb = diem.length ? diem.reduce((a, b) => a + b, 0) / diem.length : null;
    const xu = lam.length >= 2 ? (lam.slice(-2).reduce((a, x) => a + x.cao, 0) / 2 - lam.slice(0, 2).reduce((a, x) => a + x.cao, 0) / 2) : null;
    const sua = lam.filter(x => x.so > 1 && x.cao > x.dau).length, gy = lam.reduce((a, x) => a + x.goi_y, 0);
    const cuoi = lam.length ? lam[lam.length - 1] : null, truoc = lam.length > 1 ? lam[lam.length - 2] : null, caoNhat = diem.length ? Math.max(...diem) : null;
    const chuaLam = de.map((d, j) => o[j] ? null : d).filter(Boolean);
    const moiNhat = lam.length ? lam.flatMap(x => x.ds).map(b => b.nop_luc).sort().pop() : null;
    const cuoiDe = cuoi ? de[o.lastIndexOf(cuoi)] : null;
    const n = de.length, ly = [];
    if (n && !lam.length) ly.push(['chua_lam', 'Chưa làm bài nào']);
    else if (n && lam.length < n) { const gan = de.slice(-2).filter(d => chuaLam.includes(d)).length; ly.push(['thieu', `Thiếu ${n - lam.length} bài${gan ? ' (có bài gần đây)' : ''}`]) }
    if (tb != null && tb < 5) ly.push(['diem_thap', `TB ${F(tb)}`]);
    if (xu != null && xu <= -1) ly.push(['giam', `Giảm ${F(-xu)} điểm`]);
    if (cuoi && (cuoi.cx === 'lo_lang' || cuoi.cx === 'met_moi')) ly.push(['cam_xuc', cuoi.cx === 'lo_lang' ? '😰 Đang lo lắng' : '😴 Đang mệt']);
    return { ...h, de, n, o, them, tbThem, lam: lam.length, tb, xu, sua, gy, cuoi, truoc, cuoiDe, caoNhat, chuaLam, moiNhat, nhan: nhan || [], ly, tuDong: ly.length > 0 };
  }
  function tinh(k) {
    const de = k.de.filter(d => daGiao(d, k.lop)), deThem = k.de.filter(d => !daGiao(d, k.lop)), theo = nhomBai(k.bai), nhan = {}; for (const m of k.nhan || []) (nhan[m.tk] ??= []).push(m);
    const td = Object.fromEntries((k.theo_doi || []).map(x => [x.tk, x]));
    const hs = k.hs.map(h => Object.assign(motEm(h, de, theo[h.ten], nhan[h.ten], deThem), { td: td[h.ten] || null, lop: k.lop }));
    const dot = de.map((d, j) => { const v = hs.map(h => h.o[j]).filter(Boolean); return { ...d, so: v.length, tb: v.length ? v.reduce((a, x) => a + x.cao, 0) / v.length : null } });
    const them0 = deThem.map(d => ({ ...d, so: hs.filter(h => h.them.some(x => x.de.slug === d.slug)).length }));
    return { de, hs, dot, them: them0, chuaGiao: them0 };
  }
  const canQT = h => st.danh[h.ten] != null ? st.danh[h.ten] : h.tuDong;

  // ---------- lời văn ----------
  function nxEm(h, n) {
    const t = goiTen(h), c = [];
    if (!n) return 'Chưa có đợt bài nào được giao.';
    if (!h.lam && h.them && h.them.length) return `${t}: đã chủ động làm ${h.them.length} bài tự luyện — rất đáng khen! Em làm thêm các bài thầy giao nhé.`;
    if (!h.lam) return `${t}: chưa vào làm bài nào — thầy tin em sẽ bắt đầu ngay từ bài gần nhất, mỗi bài chỉ mất ít phút thôi!`;
    if (h.lam === n) c.push(`hoàn thành đủ ${n}/${n} bài, rất chăm chỉ và đều đặn`); else if (h.lam / n >= .7) c.push(`làm bài khá đều (${h.lam}/${n} bài)`); else c.push(`đã làm ${h.lam}/${n} bài, em cố gắng làm bù các bài còn lại nhé`);
    if (h.tb >= 8) c.push(`kết quả rất tốt (TB ${F(h.tb)})`); else if (h.tb >= 6.5) c.push(`nắm bài khá vững (TB ${F(h.tb)})`); else if (h.tb >= 5) c.push(`đã nắm được kiến thức cơ bản (TB ${F(h.tb)})`); else c.push('đang tích luỹ dần kiến thức nền — thầy tin em sẽ tiến bộ nếu ôn lại ví dụ mẫu');
    if (h.xu != null && h.xu >= 1) c.push(`tiến bộ rõ (+${F(h.xu)} điểm so với các bài đầu)`); else if (h.xu != null && h.xu > -.5 && h.tb >= 6.5) c.push('giữ phong độ ổn định');
    if (h.sua) c.push(`biết làm lại để sửa sai (${h.sua} bài lần sau cao hơn)`);
    if (h.gy) c.push('biết dùng Gợi ý AI để tự tìm cách giải');
    if (h.them && h.them.length) c.push(`chủ động làm thêm ${h.them.length} bài tự luyện`);
    return `${t}: ${c.join('; ')}. Cố lên em!`;
  }
  function nxLop(lop, T) {
    const n = T.de.length, s = T.hs.length; if (!n) return `Lớp ${lop} chưa có đợt bài online nào.`;
    const coLam = T.hs.filter(h => h.lam), du = T.hs.filter(h => h.lam === n), tl = s ? T.hs.reduce((a, h) => a + h.lam, 0) / (s * n) : 0;
    const diem = coLam.map(h => h.tb), tb = diem.length ? diem.reduce((a, b) => a + b, 0) / diem.length : null;
    const d1 = T.dot.find(d => d.tb != null), d2 = [...T.dot].reverse().find(d => d.tb != null);
    const tienBo = T.hs.filter(h => h.xu != null && h.xu >= 1).sort((a, b) => b.xu - a.xu), gioi = coLam.filter(h => h.tb >= 8).sort((a, b) => b.tb - a.tb);
    const ten = h => (h.ho_ten || h.ten).trim(), ds = a => a.slice(0, 5).map(ten).join(', ') + (a.length > 5 ? ` và ${a.length - 5} bạn khác` : '');
    const c = [`📊 Tổng kết học online lớp ${lop} (${n} đợt bài, ${s} học sinh)`];
    c.push(`• Cả lớp đã hoàn thành ${Math.round(tl * 100)}% lượt bài được giao${du.length ? `, ${du.length} bạn làm đủ tất cả các đợt — rất đáng khen!` : '.'}`);
    if (tb != null) c.push(`• Điểm trung bình lớp: ${F(tb)}${d1 && d2 && d1 !== d2 ? (d2.tb - d1.tb >= .3 ? ` — tăng từ ${F(d1.tb)} (đợt đầu) lên ${F(d2.tb)} (đợt gần nhất), lớp đang tiến bộ rõ` : d2.tb - d1.tb > -.3 ? ', giữ ổn định qua các đợt' : '; các đợt sau khó hơn, các em xem lại lời giải để vững vàng hơn nhé') : ''}.`);
    if (du.length) c.push(`• Chăm chỉ, đều đặn: ${ds(du)}.`);
    if (tienBo.length) c.push(`• Tiến bộ nổi bật: ${ds(tienBo)}.`);
    if (gioi.length) c.push(`• Kết quả xuất sắc (TB từ 8): ${ds(gioi)}.`);
    const chua = s - coLam.length, thieu = T.hs.filter(h => h.lam && h.lam < n).length;
    if (chua || thieu) c.push(`• ${chua ? `Còn ${chua} bạn chưa bắt đầu` : ''}${chua && thieu ? ', ' : ''}${thieu ? `${thieu} bạn còn thiếu bài` : ''} — các em vào làm bù nhé, link vẫn mở.`);
    c.push('Thầy rất vui với tinh thần tự học của lớp. Tiếp tục giữ nhịp mỗi tuần một chút, kết quả sẽ đến! 💪');
    return c.join('\n');
  }
  // tin nhắn riêng: tích cực + hài hước, theo lý do chính
  const MAU = {
    chua_lam: [
      '{t} ơi, bài online nhớ em lắm rồi đó 😄 Chỉ cần khoảng 15 phút thôi — em vào làm thử “{de}” nhé, thầy đang chờ điểm của em như chờ tập phim hay!',
      'Alô alô, {t} có đó không? 📞 Đề “{de}” gọi tên em mãi mà chưa thấy em nghe máy. Em làm thử một lần thôi, sai đâu thầy chỉ đó!',
      'Nghe đồn {t} giải toán khá lắm mà đang giấu nghề 🤫 Em vào làm “{de}” để thầy được chứng kiến nhé!',
      '{t} ơi, máy chấm điểm của thầy đang ngồi buồn vì chưa được chấm bài em 🤖💤 Em vào làm “{de}” để nó vui lên nha!'],
    thieu: [
      '{t} ơi, em đã chinh phục {lam}/{n} bài rồi, giỏi lắm! 👏 Còn {thieu} bài (như “{de}”) đang xếp hàng chờ em “giải cứu” 🦸 — link vẫn mở, làm bù nhé!',
      'Bảng thành tích của {t} đang {lam}/{n}, chỉ còn {thieu} ô trống nữa là full combo 🎮 Thầy tin em phá đảo được!',
      '{t} ơi, bài “{de}” bảo là nó thấy hơi bị bỏ rơi 🥺 Em ghé làm một chút nhé — mỗi bài thêm vào là một bước tiến đó!'],
    diem_thap: [
      '{t} à, điểm chưa cao không sao cả — nhà toán học Pólya cũng từng giải sai rồi mới giỏi 😉 Em xem lại lời giải, bấm 💡 Gợi ý khi bí, rồi làm lại lần nữa nhé. Thầy tin em!',
      '{t} ơi, học toán như leo cầu thang: mấy bậc đầu hơi mỏi chân thôi 🧗 Em ôn lại ví dụ mẫu rồi thử lại, điểm sẽ lên từng bậc!',
      '{t}, mỗi câu sai là một “boss nhỏ” em vừa tìm ra 🐉 Xem lại lời giải để hạ boss, lần sau điểm sẽ khác ngay! Cần gì cứ hỏi thầy nhé.'],
    giam: [
      '{t} ơi, đợt vừa rồi hơi “trượt vỏ chuối” một chút 🍌 Em từng đạt {cao} điểm cơ mà — chắc chắn lấy lại phong độ được. Thầy chờ màn comeback của em!',
      'Phong độ là nhất thời, đẳng cấp là mãi mãi 😎 {t} xem lại bài gần nhất rồi làm lại nhé, {cao} điểm vẫn trong tầm tay em!'],
    khen_tien_bo: [
      '{t} ơi, bài “{de}” em được {d} điểm — tăng {x} so với bài trước! 🎉 Thầy thấy rõ em đang tiến bộ, cứ giữ nhịp này nhé!',
      'Tin vui nè {t}: {d} điểm ở bài “{de}”, hơn bài trước {x} điểm 📈 Cái cầu thang toán học em leo đều lắm rồi đó!',
      '{t} ơi, +{x} điểm! 🚀 Bài “{de}” em làm tốt hơn hẳn. Thầy rất vui — tuần này mình cố thêm một bài nữa nha!'],
    khen_cham: [
      '{t} ơi, thầy thấy em đã làm bài “{de}” rồi 👍 Chăm như vậy là điểm sẽ lên thôi! Câu nào chưa hiểu em xem lời giải hoặc hỏi thầy nha.',
      'Thầy ghi nhận nè {t}: em làm bài đều đặn lắm ✅ Mỗi lần làm là một lần não được “tập gym” 💪 Cố lên em!',
      '{t} ơi, kiên trì như em là điều thầy quý nhất 🌱 Lần tới em thử bấm 💡 Gợi ý ở câu khó, chắc chắn sẽ gỡ được thêm điểm!'],
    cam_xuc: [
      '{t} ơi, thầy thấy em hơi lo khi làm bài 🤗 Cứ bình tĩnh nha: sai thì làm lại, bí thì bấm 💡 Gợi ý, còn thầy luôn ở đây giúp em.',
      '{t} ơi, nghỉ ngơi một chút rồi học tiếp cũng là chiến thuật hay đó ☕ Em làm từng câu một, thầy tin em làm được!']
  };
  function tinNhan(h, n, bien, kieu) {
    n = h.n ?? n;
    const ly = kieu || (h.ly[0] || [h.lam ? (h.lam < n ? 'thieu' : 'diem_thap') : 'chua_lam'])[0];
    const ds = MAU[ly] || MAU.thieu, i = (bam(h.ten) + (bien || 0)) % ds.length;
    const de = ((ly === 'khen_tien_bo' || ly === 'khen_cham' ? h.cuoiDe : null) || h.chuaLam[h.chuaLam.length - 1] || h.de[h.de.length - 1] || {}).ten || 'bài gần nhất';
    return ds[i].replace(/\{t\}/g, goiTen(h)).replace(/\{de\}/g, de).replace(/\{lam\}/g, h.lam).replace(/\{n\}/g, n)
      .replace(/\{thieu\}/g, n - h.lam).replace(/\{cao\}/g, F(h.caoNhat)).replace(/\{d\}/g, F(h.cuoi && h.cuoi.cao))
      .replace(/\{x\}/g, F(h.cuoi && h.truoc ? h.cuoi.cao - h.truoc.cao : 0)) + ' ' + KY;
  }

  function kieuTD(h) {
    const moiDe = h.de[h.de.length - 1];
    if (moiDe && h.chuaLam.includes(moiDe)) return h.lam ? 'thieu' : 'chua_lam';
    if (h.cuoi && h.truoc && h.cuoi.cao - h.truoc.cao >= .5) return 'khen_tien_bo';
    if (h.cuoi && h.cuoi.cao < 5) return 'diem_thap';
    return h.lam ? 'khen_cham' : 'chua_lam';
  }
  const ngayVN = s2 => s2 ? new Date(s2).toLocaleDateString('vi-VN') : '';
  const truocDay = s2 => { if (!s2) return 'chưa có bài nộp'; const d = Math.floor((Date.now() - new Date(s2)) / 864e5); return d <= 0 ? 'hôm nay' : d === 1 ? 'hôm qua' : d + ' ngày trước' };
  function soDo(h, W = 260, H = 54) {   // đường điểm cao nhất mỗi đợt (đợt chưa làm để trống)
    const n = h.o.length; if (!n) return '';
    const x = j => 6 + (n === 1 ? (W - 12) / 2 : j * (W - 12) / (n - 1)), y = v => H - 6 - v / 10 * (H - 12);
    const pt = h.o.map((v, j) => v ? [x(j), y(v.cao), v.cao, j] : null).filter(Boolean);
    return `<svg viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" role="img" aria-label="Điểm qua các đợt"><line x1="6" x2="${W - 6}" y1="${y(5)}" y2="${y(5)}" stroke="#fecaca" stroke-dasharray="3 3"/>
      <polyline fill="none" stroke="#1e40af" stroke-width="2" points="${pt.map(p => p[0] + ',' + p[1]).join(' ')}"/>
      ${h.o.map((v, j) => v ? `<circle cx="${x(j)}" cy="${y(v.cao)}" r="3.5" fill="${v.cao >= 5 ? '#1e40af' : '#dc2626'}"><title>Đợt ${j + 1}: ${F(v.cao)}</title></circle>` : `<circle cx="${x(j)}" cy="${H - 6}" r="2.5" fill="#cbd5e1"><title>Đợt ${j + 1}: chưa làm</title></circle>`).join('')}</svg>`;
  }
  async function datTD(h, bat, ghi_chu) {
    const k = await st.goi('theo-doi-dat', { tk: h.ten, bat, ...(ghi_chu != null ? { ghi_chu } : {}) }).catch(x => ({ ok: false, loi: String(x) }));
    if (!k.ok) { alert(k.loi || 'Chưa lưu được — thầy Đăng lại tất cả để máy chủ có chức năng theo dõi'); return false }
    return true;
  }
  async function guiMot(tk, noi_dung) {
    const k = await st.goi('loi-nhan', { ds: [{ tk, noi_dung }] }).catch(x => ({ ok: false, loi: String(x) }));
    if (!k.ok) { alert(k.loi || 'Chưa gửi được'); return false } toast('✓ Đã gửi vào trang học của em'); return true;
  }

  // ---------- hồ sơ một học sinh ----------
  function hoSo(h) {
    let p = document.getElementById('th-hs');
    if (!p) { p = document.createElement('div'); p.id = 'th-hs'; hop.appendChild(p) }
    const CX = { tu_tin: '🤩 Tự tin', binh_thuong: '🙂 Bình thường', lo_lang: '😰 Lo lắng', met_moi: '😴 Mệt mỏi' };
    const phan = ['p1', 'p2', 'p3'].map(k2 => { const v = h.o.filter(Boolean).map(x => x.ds.find(b => b.diem === x.cao)).map(b => b && b[k2]).filter(v2 => v2 != null); return v.length ? v.reduce((a, b) => a + b, 0) / v.length : null });
    const tg = h.o.filter(Boolean).flatMap(x => x.ds).reduce((a, b) => a + (b.thoi_gian || 0), 0);
    const kieu = kieuTD(h);
    p.innerHTML = `<div class="th-hs-noi" role="dialog" aria-modal="true" aria-labelledby="th-hs-ten"><div class="th-dau"><h2 id="th-hs-ten">👤 ${e(h.ho_ten || h.ten)} <span style="font-weight:400;color:#64748b;font-size:14px">· ${e(h.lop || '')} · ${e(h.ten)}</span></h2>
      <button id="th-hs-td" aria-pressed="${!!h.td}" class="${h.td ? 'hong' : ''}">${h.td ? '⭐ Đang theo dõi' : '☆ Theo dõi em này'}</button><button id="th-hs-dong">← Quay lại</button></div>
      <div class="th-than"><div class="th-the"><div><b>${h.lam}/${h.n}</b><span>bài đã làm</span></div><div><b>${F(h.tb)}</b><span>điểm TB (cao nhất mỗi đợt)</span></div>
        <div><b>${F(h.caoNhat)}</b><span>điểm cao nhất</span></div><div><b>${h.xu == null ? '—' : (h.xu > 0 ? '+' : '') + F(h.xu)}</b><span>tiến bộ (2 bài cuối − 2 bài đầu)</span></div>
        <div><b>${tg ? Math.round(tg / 60) : 0}′</b><span>tổng thời gian làm bài</span></div><div><b>${h.gy}</b><span>câu mở 💡 Gợi ý AI</span></div></div>
        <div style="display:flex;gap:16px;flex-wrap:wrap;align-items:center;margin-bottom:10px"><div>${soDo(h, 420, 90)}</div>
          <div style="font-size:13px">${phan.some(v => v != null) ? `<b>Điểm TB từng phần</b> (bài tốt nhất mỗi đợt):<br>Trắc nghiệm ${F(phan[0])} · Đúng/Sai ${F(phan[1])} · Trả lời ngắn ${F(phan[2])}` : ''}
          <div style="margin-top:6px;color:#64748b">Lần nộp gần nhất: ${truocDay(h.moiNhat)}</div>${h.ly.length ? `<div class="ly" style="margin-top:6px;display:flex;gap:4px;flex-wrap:wrap">${h.ly.map(x => `<span class="th-ly">${e(x[1])}</span>`).join('')}</div>` : ''}</div></div>
        ${h.td || 1 ? `<label style="display:flex;gap:8px;align-items:center;margin-bottom:10px;font-weight:600">Ghi chú theo dõi <input id="th-hs-gc" value="${e(h.td && h.td.ghi_chu || '')}" placeholder="vd: hổng kiến thức lớp 9, cần kèm thêm phần hàm số" style="flex:1;padding:7px 9px;border:1px solid #cbd5e1;border-radius:8px;font:inherit;font-size:13.5px;width:auto"></label>` : ''}
        <div style="overflow:auto;border:1px solid #e2e8f0;border-radius:10px;margin-bottom:10px"><table class="th-bang"><thead><tr><th class="ten">Đợt</th><th>Lần</th><th>Điểm</th><th>Phần TN · ĐS · TLN</th><th>Thời gian</th><th>Cảm xúc</th><th>💡</th><th>Rời tab</th><th>Nộp lúc</th></tr></thead><tbody>
          ${h.de.map((d, j) => { const v = h.o[j]; if (!v) return `<tr><td class="ten">${e(d.ten)}</td><td colspan="8" style="color:#b91c1c;text-align:left">Chưa làm</td></tr>`;
            return v.ds.map((b, q) => `<tr>${q ? '' : `<td class="ten" rowspan="${v.ds.length}">${e(d.ten)}</td>`}<td>${b.lan}</td><td><span class="o-d ${mau(b.diem)}">${F(b.diem)}</span></td>
              <td>${[b.p1, b.p2, b.p3].map(F).join(' · ')}</td><td>${b.thoi_gian ? Math.round(b.thoi_gian / 60) + '′' : ''}</td><td>${CX[b.cam_xuc] || ''}</td><td>${b.goi_y || ''}</td><td>${b.chuyen_tab || ''}</td><td>${ngayVN(b.nop_luc)}</td></tr>`).join('') }).join('')}
          ${(h.them || []).map(x => x.ds.map((b, q) => `<tr class="them" style="color:#64748b">${q ? '' : `<td class="ten" rowspan="${x.ds.length}">${e(x.de.ten)} <span class="th-ly" style="color:#64748b;border-color:#cbd5e1">tự luyện</span></td>`}<td>${b.lan}</td><td><span class="o-d ${mau(b.diem)}">${F(b.diem)}</span></td>
              <td>${[b.p1, b.p2, b.p3].map(F).join(' · ')}</td><td>${b.thoi_gian ? Math.round(b.thoi_gian / 60) + '′' : ''}</td><td>${CX[b.cam_xuc] || ''}</td><td>${b.goi_y || ''}</td><td>${b.chuyen_tab || ''}</td><td>${ngayVN(b.nop_luc)}</td></tr>`).join('')).join('')}
        </tbody></table></div>
        <div class="th-hop2 th-nx"><h3>📝 Nhận xét</h3><div style="color:#14532d">${e(nxEm(h, h.n))}</div></div>
        <div class="th-hop2 th-qt"><h3>💌 Nhắn riêng cho em <button data-doi title="Đổi câu khác">🎲</button></h3>
          <textarea id="th-hs-tn">${e(tinNhan(h, h.n, 0, kieu))}</textarea>
          <div style="display:flex;gap:8px;margin-top:8px;flex-wrap:wrap"><button class="hong" id="th-hs-gui">💌 Gửi vào trang học của em</button><button id="th-hs-chep">Chép (Zalo)</button></div>
          ${h.nhan.length ? `<div style="margin-top:10px;font-size:12.5px"><b>Đã nhắn:</b>${h.nhan.slice(0, 8).map(m => `<div style="border-top:1px dashed #fbcfe8;padding:5px 0">${ngayVN(m.tao_luc)} · ${m.xem_luc ? '✓ em đã đọc' : 'em chưa đọc'}<br>${e(m.noi_dung)}</div>`).join('')}</div>` : ''}</div>
      </div></div>`;
    p.style.display = 'flex';
    let b2 = 0; const $ = id => document.getElementById(id);
    $('th-hs-dong').onclick = () => { p.style.display = 'none' }; $('th-hs-dong').focus();
    p.querySelector('[data-doi]').onclick = () => { b2++; $('th-hs-tn').value = tinNhan(h, h.n, b2, kieu) };
    $('th-hs-chep').onclick = () => chep($('th-hs-tn').value, 'Đã chép tin nhắn');
    $('th-hs-gui').onclick = async ev => { ev.target.disabled = true; if (await guiMot(h.ten, $('th-hs-tn').value.trim())) { p.style.display = 'none'; tai() } ev.target.disabled = false };
    $('th-hs-td').onclick = async () => { const bat = !h.td; if (await datTD(h, bat, bat ? $('th-hs-gc').value : null)) { toast(bat ? '⭐ Đã thêm vào danh sách theo dõi' : 'Đã bỏ theo dõi'); p.style.display = 'none'; tai() } };
    $('th-hs-gc').onchange = async ev => { if (h.td && await datTD(h, true, ev.target.value)) { h.td.ghi_chu = ev.target.value; toast('Đã lưu ghi chú') } };
  }

  // ---------- học sinh đang theo dõi (mọi lớp) ----------
  function veTD(k) {
    const theo = nhomBai(k.bai), nhan = {}; for (const m of k.nhan || []) (nhan[m.tk] ??= []).push(m);
    const hs = k.hs.map(h => { const m = theo[h.ten] || {}; const de = k.de.filter(d => daGiao(d, h.lop)), deThem = k.de.filter(d => !daGiao(d, h.lop) && m[d.slug]);
      return Object.assign(motEm(h, de, m, nhan[h.ten], deThem), { td: { ghi_chu: h.ghi_chu, tu_luc: h.tu_luc }, lop: h.lop }) });
    st.TD = hs; const than = document.getElementById('th-than');
    if (!hs.length) { than.innerHTML = `<div class="th-hop2 th-nx"><h3>⭐ Chưa theo dõi em nào</h3><p style="margin:0">Chọn một lớp → bấm ☆ ở cột “Theo dõi” (hoặc bấm tên em → ☆ Theo dõi em này). Gợi ý: những em có TB dưới 5 hoặc hay bỏ bài. Danh sách lưu trên máy chủ, dùng chung app và trang web.</p></div>`; return }
    const canNhac = hs.filter(h => ['chua_lam', 'thieu'].includes(kieuTD(h))).length, tienBo = hs.filter(h => kieuTD(h) === 'khen_tien_bo').length;
    than.innerHTML = `<div class="th-the"><div><b>${hs.length}</b><span>em đang theo dõi</span></div><div><b>${tienBo}</b><span>🎉 vừa tiến bộ — khen ngay!</span></div><div class="qt"><b>${canNhac}</b><span>chưa làm bài mới</span></div>
      <div><b>${hs.filter(h => h.moiNhat && Date.now() - new Date(h.moiNhat) < 7 * 864e5).length}</b><span>có nộp bài trong 7 ngày</span></div></div>
      <div class="th-td">${hs.map((h, i) => { const kieu = kieuTD(h); return `<div class="th-td-the" data-i="${i}">
        <div class="th-td-dau"><button class="th-ten" data-hs="${i}">${e(h.ho_ten || h.ten)}</button><span class="th-ly">${e(h.lop)}</span>
          ${kieu === 'khen_tien_bo' ? '<span class="th-ly" style="color:#15803d;border-color:#bbf7d0">🎉 Tiến bộ</span>' : ''}${h.ly.map(x => `<span class="th-ly">${e(x[1])}</span>`).join('')}</div>
        <div style="display:flex;gap:12px;align-items:center;flex-wrap:wrap">${soDo(h)}<div style="font-size:12.5px;color:#475569">Đã làm ${h.lam}/${h.n} · TB ${F(h.tb)}<br>Bài gần nhất: ${h.cuoi ? F(h.cuoi.cao) + ' điểm' : '—'} · ${truocDay(h.moiNhat)}${h.td.ghi_chu ? `<br><i>📌 ${e(h.td.ghi_chu)}</i>` : ''}</div></div>
        <textarea aria-label="Tin nhắn cho ${e(h.ho_ten || h.ten)}">${e(tinNhan(h, h.n, 0, kieu))}</textarea>
        <div style="display:flex;gap:6px;flex-wrap:wrap"><button class="hong" data-gui="${i}">💌 Gửi</button><button data-doi2="${i}" title="Đổi câu khác">🎲</button><button data-hs="${i}">Hồ sơ</button><button data-bo="${i}" style="margin-left:auto;color:#64748b">Bỏ theo dõi</button></div>
        ${h.nhan[0] ? `<div style="font-size:11.5px;color:#64748b">Lần nhắn gần nhất ${ngayVN(h.nhan[0].tao_luc)} · ${h.nhan[0].xem_luc ? '✓ em đã đọc' : 'em chưa đọc'}</div>` : ''}</div>` }).join('')}</div>`;
    const bien = {};
    than.querySelectorAll('[data-hs]').forEach(b => b.onclick = () => hoSo(hs[+b.dataset.hs]));
    than.querySelectorAll('[data-doi2]').forEach(b => b.onclick = () => { const i = +b.dataset.doi2; bien[i] = (bien[i] || 0) + 1; b.closest('.th-td-the').querySelector('textarea').value = tinNhan(hs[i], hs[i].n, bien[i], kieuTD(hs[i])) });
    than.querySelectorAll('[data-gui]').forEach(b => b.onclick = async () => { const i = +b.dataset.gui; b.disabled = true; if (await guiMot(hs[i].ten, b.closest('.th-td-the').querySelector('textarea').value.trim())) tai(); b.disabled = false });
    than.querySelectorAll('[data-bo]').forEach(b => b.onclick = async () => { const h = hs[+b.dataset.bo]; if (confirm(`Bỏ theo dõi ${h.ho_ten || h.ten}?`) && await datTD(h, false)) tai() });
  }

  // ---------- giao diện ----------
  function ve() {
    const k = st.k, T = tinh(k), n = T.de.length; st.T = T;
    const s = T.hs.length, coLam = T.hs.filter(h => h.lam).length, tl = s && n ? Math.round(T.hs.reduce((a, h) => a + h.lam, 0) / (s * n) * 100) : 0;
    const diem = T.hs.filter(h => h.tb != null).map(h => h.tb), tb = diem.length ? diem.reduce((a, b) => a + b, 0) / diem.length : null;
    const tienBo = T.hs.filter(h => h.xu != null && h.xu >= 1).length, qt = T.hs.filter(canQT);
    const W = 1000, H = 150, p = 28, bw = n ? (W - 2 * p) / n : 0, y = v => H - 20 - (v / 10) * (H - 40);
    const svg = n ? `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Số em nộp và điểm trung bình theo đợt">
      ${[0, 5, 10].map(v => `<line x1="${p}" x2="${W - p}" y1="${y(v)}" y2="${y(v)}" stroke="#eef0f4"/><text x="4" y="${y(v) + 4}" font-size="10" fill="#94a3b8">${v}</text>`).join('')}
      ${T.dot.map((d, j) => `<rect x="${p + j * bw + bw * .2}" y="${H - 20 - (d.so / (s || 1)) * (H - 40)}" width="${bw * .6}" height="${(d.so / (s || 1)) * (H - 40)}" fill="#bfdbfe" rx="3"><title>${e(d.ten)}: ${d.so}/${s} em nộp</title></rect>
        <text x="${p + j * bw + bw / 2}" y="${H - 5}" font-size="10" fill="#64748b" text-anchor="middle">Đợt ${j + 1}</text>`).join('')}
      <polyline fill="none" stroke="#15803d" stroke-width="2.5" points="${T.dot.map((d, j) => d.tb == null ? '' : `${p + j * bw + bw / 2},${y(d.tb)}`).filter(Boolean).join(' ')}"/>
      ${T.dot.map((d, j) => d.tb == null ? '' : `<circle cx="${p + j * bw + bw / 2}" cy="${y(d.tb)}" r="4" fill="#15803d"><title>${e(d.ten)}: TB ${F(d.tb)}</title></circle>`).join('')}</svg>
      <div style="font-size:12px;color:#64748b"><span style="display:inline-block;width:10px;height:10px;background:#bfdbfe;border-radius:2px"></span> Số em nộp &nbsp; <span style="color:#15803d;font-weight:700">●—</span> Điểm TB (điểm cao nhất mỗi em)</div>` : '';
    const ngay = s2 => s2 ? new Date(s2).toLocaleDateString('vi-VN') : '';
    const than = document.getElementById('th-than');
    than.innerHTML = `<div class="th-the"><div><b>${n}</b><span>đợt bài đã giao</span></div><div><b>${coLam}/${s}</b><span>em đã tham gia</span></div>
      <div><b>${tl}%</b><span>lượt bài hoàn thành</span></div><div><b>${F(tb)}</b><span>điểm TB lớp</span></div><div><b>${tienBo}</b><span>em tiến bộ ≥ 1 điểm</span></div>
      <div class="qt"><b>${qt.length}</b><span>⚑ em cần quan tâm</span></div></div>
      ${n ? `<div class="th-bd">${svg}</div>` : ''}
      <div class="th-hop2 th-qt" id="th-qt"><h3>⚑ Học sinh cần quan tâm — tin nhắn riêng (tích cực, vui)</h3><div id="th-qt-ds"></div></div>
      <div class="th-hop2 th-nx"><h3>💬 Nhận xét chung cho lớp (sửa được, chép gửi nhóm lớp)</h3><textarea id="th-nx-lop">${e(nxLop(k.lop, T))}</textarea></div>
      ${!n && T.chuaGiao.length ? `<div class="th-hop2" style="background:#fffbeb;border:1px solid #fde68a"><h3 style="color:#b45309">Chưa có bài nào được xác nhận giao cho lớp ${e(k.lop)}</h3><div style="font-size:13px">Bảng dưới vẫn hiện điểm mọi bài (cột xám = chưa giao). Thầy bấm <b>✓ Xác nhận đã giao</b> dưới tên bài nào đã thật sự giao — bài đó mới tính hoàn thành, điểm TB, tiến bộ.</div></div>` : ''}
      ${n || T.chuaGiao.length ? `<div style="overflow:auto;max-height:55vh;border:1px solid #e2e8f0;border-radius:10px"><table class="th-bang"><thead><tr><th title="Đánh dấu cần quan tâm">⚑</th><th title="Theo dõi thường xuyên (lưu trên máy chủ)">⭐</th><th>STT</th><th class="ten">Họ tên</th>
        ${T.dot.map((d, j) => `<th class="cot-dot" title="${e(d.ten)}">Đợt ${j + 1}<br><span style="font-weight:400;color:#64748b">${e(d.ten.length > 16 ? d.ten.slice(0, 15) + '…' : d.ten)}</span><br><button class="th-giao bat" data-giao="${e(d.slug)}" data-v="0" title="Đang tính vào tổng hợp. Bấm nếu bài này chưa giao (chỉ tự luyện)">✓ Đã giao</button></th>`).join('')}
        ${T.them.map(d => `<th class="cot-dot them" title="${e(d.ten)} — chưa giao, không tính vào hoàn thành / điểm TB">○ Chưa giao<br><span style="font-weight:400">${e(d.ten.length > 16 ? d.ten.slice(0, 15) + '…' : d.ten)}</span><br><button class="th-giao" data-giao="${e(d.slug)}" data-v="1" title="Bấm để xác nhận bài này đã giao — tính vào tổng hợp">✓ Xác nhận đã giao</button></th>`).join('')}
        <th>Hoàn thành</th><th>TB</th><th title="TB 2 bài gần nhất − TB 2 bài đầu">Tiến bộ</th><th class="ten">Nhận xét tích cực (bấm để sửa)</th></tr></thead><tbody>
        ${T.hs.map((h, i) => `<tr class="${canQT(h) ? 'qt' : ''}"><td><button class="th-co" data-tk="${e(h.ten)}" aria-pressed="${canQT(h)}" title="${h.ly.map(x => x[1]).join(' · ') || 'Bấm để đánh dấu cần quan tâm'}" aria-label="Đánh dấu ${e(h.ho_ten || h.ten)}">⚑</button></td>
          <td><button class="th-co th-sao" data-sao="${i}" aria-pressed="${!!h.td}" title="${h.td ? 'Đang theo dõi — bấm để bỏ' : 'Theo dõi em này thường xuyên'}" aria-label="Theo dõi ${e(h.ho_ten || h.ten)}">${h.td ? '★' : '☆'}</button></td>
          <td>${h.stt || ''}</td><td class="ten"><button class="th-ten" data-hs="${i}" title="Xem hồ sơ từng bài">${e(h.ho_ten || h.ten)}</button></td>
          ${h.o.map(x => `<td><span class="o-d ${mau(x && x.cao)}" title="${x ? `Cao nhất ${F(x.cao)} · ${x.so} lần${x.goi_y ? ` · 💡 ${x.goi_y}` : ''}` : 'Chưa làm'}">${x ? F(x.cao) : '—'}</span></td>`).join('')}
          ${T.them.map(d => { const x = h.them.find(y => y.de.slug === d.slug); return `<td class="them">${x ? `<span class="o-d ${mau(x.cao)}">${F(x.cao)}</span>` : ''}</td>` }).join('')}
          <td>${n ? h.lam + '/' + n : '—'}</td><td>${n ? `<b>${F(h.tb)}</b>` : `<span style="color:#94a3b8" title="TB các bài chưa giao em đã làm">${F(h.tbThem)}</span>`}</td><td>${h.xu == null ? '' : h.xu >= .5 ? `<span class="th-len">▲ ${F(h.xu)}</span>` : h.xu <= -.5 ? `<span class="th-xuong">▼ ${F(-h.xu)}</span>` : '≈'}</td>
          <td class="nx" contenteditable data-i="${i}">${e(nxEm(h, n))}</td></tr>`).join('')}</tbody></table></div>
        <p style="font-size:12px;color:#64748b;margin:6px 0 0">Mỗi ô là điểm cao nhất của em trong đợt (rê chuột xem số lần làm, số câu mở Gợi ý AI). Xanh lá ≥ 8 · xanh dương ≥ 6,5 · vàng ≥ 5 · đỏ &lt; 5 · “—” chưa làm. Chỉ bài thầy đã <b>xác nhận ✓ Đã giao</b> mới tính hoàn thành, điểm TB, tiến bộ; bấm nút dưới tên đợt để chuyển về Chưa giao (cột xám “○ Chưa giao” vẫn hiện điểm em đã làm nhưng không tính, chỉ để khen). Bấm ⚑ để đánh dấu / bỏ đánh dấu em cần quan tâm · ☆ để theo dõi thường xuyên (xem ở mục ⭐ đầu danh sách lớp) · bấm tên em để xem hồ sơ từng bài.</p>`
        : `<p>Lớp này chưa có bài nào được <b>xác nhận đã giao</b>. Thầy bấm “✓ Xác nhận đã giao” ở danh sách trên (hoặc nút ○ Chưa giao trong Thư viện) — chỉ bài đã xác nhận mới tính hoàn thành, điểm TB, tiến bộ.</p>`}`;
    veQT();
    than.querySelectorAll('[data-giao]').forEach(b => b.onclick = async () => {
      const v = b.dataset.v === '1', d = k.de.find(x => x.slug === b.dataset.giao);
      if (!confirm(v ? `Xác nhận “${d.ten}” là bài ĐÃ GIAO?\nEm chưa làm sẽ bị tính thiếu bài.` : `Đánh dấu “${d.ten}” là CHƯA GIAO?\nBài này không tính vào hoàn thành / điểm TB; em nào làm thì ghi nhận là tự luyện thêm.`)) return;
      b.disabled = true; const r = await st.goi('de-giao', { slug: d.slug, giao: v ? 1 : 0 }).catch(x => ({ ok: false, loi: String(x) }));
      if (!r.ok) { b.disabled = false; alert(r.loi || 'Chưa lưu được — thầy Đăng lại tất cả để máy chủ có chức năng này'); return }
      toast(v ? '✓ Đã tính là bài đã giao' : 'Đã chuyển sang tự luyện (chưa giao)'); tai() });
    than.querySelectorAll('.th-bang [data-hs]').forEach(b => b.onclick = () => hoSo(T.hs[+b.dataset.hs]));
    than.querySelectorAll('[data-sao]').forEach(b => b.onclick = async () => { const h = T.hs[+b.dataset.sao], bat = !h.td;
      if (await datTD(h, bat)) { h.td = bat ? { ghi_chu: '' } : null; b.setAttribute('aria-pressed', bat); b.textContent = bat ? '★' : '☆'; toast(bat ? `⭐ Đã theo dõi ${h.ho_ten || h.ten}` : 'Đã bỏ theo dõi') } });
    than.querySelectorAll('.th-co:not(.th-sao)').forEach(b => b.onclick = () => {
      const h = T.hs.find(x => x.ten === b.dataset.tk), moi = !canQT(h);
      if (moi === h.tuDong) delete st.danh[h.ten]; else st.danh[h.ten] = moi;
      luu('danh_' + k.lop, st.danh); b.setAttribute('aria-pressed', moi); b.closest('tr').classList.toggle('qt', moi);
      hop.querySelector('.th-the .qt b').textContent = T.hs.filter(canQT).length; veQT();
    });
  }
  function veQT() {
    const T = st.T, n = T.de.length, ds = T.hs.filter(canQT), hop2 = document.getElementById('th-qt-ds');
    const ngay = s2 => s2 ? new Date(s2).toLocaleDateString('vi-VN') : '';
    if (!ds.length) { hop2.innerHTML = '<p style="margin:0;color:#64748b">Không có em nào cần nhắc riêng 🎉 Bấm ⚑ trong bảng để đánh dấu thêm nếu thầy muốn nhắn riêng.</p>'; return }
    hop2.innerHTML = `<p style="margin:0 0 6px;font-size:12.5px;color:#9d174d">Máy tự đánh dấu em chưa làm, thiếu bài, TB dưới 5, tụt từ 1 điểm, hoặc đang lo lắng/mệt. Tin nhắn gửi vào <b>trang học của em</b> (hiện khung “💌 Thầy nhắn em” khi em đăng nhập) — sửa được, 🎲 để đổi câu khác.</p>
      ${ds.map(h => { const cu = h.nhan[0]; return `<div class="th-em" data-tk="${e(h.ten)}"><input type="checkbox" checked aria-label="Chọn ${e(h.ho_ten || h.ten)}">
        <div><div class="ten">${e(h.ho_ten || h.ten)}</div><div class="ly">${(h.ly.length ? h.ly : [['tay', 'Thầy đánh dấu']]).map(x => `<span class="th-ly">${e(x[1])}</span>`).join('')}</div>
          ${cu ? `<div class="da">Đã nhắn ${ngay(cu.tao_luc)} · ${cu.xem_luc ? '✓ em đã đọc' : 'em chưa đọc'}</div>` : ''}</div>
        <textarea aria-label="Tin nhắn cho ${e(h.ho_ten || h.ten)}">${e(tinNhan(h, n, st.bien[h.ten] || 0))}</textarea>
        <div class="nut"><button data-doi title="Đổi câu khác">🎲</button></div></div>` }).join('')}
      <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:8px"><button class="hong" id="th-gui">💌 Gửi vào trang học của các em đã chọn</button>
        <button id="th-chep-qt">Chép tin nhắn (Zalo / Messenger)</button><label style="display:flex;align-items:center;gap:6px;font-size:13px"><input type="checkbox" id="th-tat-ca" checked> Chọn tất cả</label></div>`;
    hop2.querySelectorAll('[data-doi]').forEach(b => b.onclick = () => {
      const r = b.closest('.th-em'), h = T.hs.find(x => x.ten === r.dataset.tk); st.bien[h.ten] = (st.bien[h.ten] || 0) + 1;
      r.querySelector('textarea').value = tinNhan(h, n, st.bien[h.ten]) });
    document.getElementById('th-tat-ca').onchange = ev => hop2.querySelectorAll('.th-em input[type=checkbox]').forEach(c => c.checked = ev.target.checked);
    const chon = () => [...hop2.querySelectorAll('.th-em')].filter(r => r.querySelector('input').checked)
      .map(r => ({ tk: r.dataset.tk, ten: (T.hs.find(x => x.ten === r.dataset.tk) || {}).ho_ten || r.dataset.tk, noi_dung: r.querySelector('textarea').value.trim() }));
    document.getElementById('th-chep-qt').onclick = () => { const c = chon(); if (!c.length) return toast('Chưa chọn em nào'); chep(c.map(x => `${x.ten}:\n${x.noi_dung}`).join('\n\n'), `Đã chép ${c.length} tin nhắn`) };
    document.getElementById('th-gui').onclick = async ev => {
      const c = chon(); if (!c.length) return toast('Chưa chọn em nào');
      if (!confirm(`Gửi ${c.length} tin nhắn vào trang học của các em đã chọn?\nEm sẽ thấy khung “💌 Thầy nhắn em” khi đăng nhập.`)) return;
      ev.target.disabled = true; ev.target.textContent = 'Đang gửi…';
      const k = await st.goi('loi-nhan', { ds: c.map(x => ({ tk: x.tk, noi_dung: x.noi_dung })) }).catch(x => ({ ok: false, loi: String(x) }));
      ev.target.disabled = false; ev.target.textContent = '💌 Gửi vào trang học của các em đã chọn';
      if (!k.ok) { alert(k.loi || 'Chưa gửi được'); return }
      toast(`✓ Đã gửi ${k.so} tin nhắn`); tai();
    };
  }
  function xuat() {
    const T = st.T, k = st.k; if (!T) return;
    const nx = {}; hop.querySelectorAll('td.nx').forEach(td => { nx[+td.dataset.i] = td.innerText.trim() });
    const dau = ['STT', 'Họ tên', 'Tài khoản', ...T.dot.map((d, j) => `Đợt ${j + 1}: ${d.ten}`), ...T.them.map(d => `(Chưa giao) ${d.ten}`), 'Số bài đã làm', 'Tổng số đợt', 'Điểm TB', 'Tiến bộ', 'Số bài làm lại cao hơn', 'Số câu mở Gợi ý AI', 'Cần quan tâm', 'Theo dõi', 'Lý do', 'Nhận xét'];
    const dong = T.hs.map((h, i) => [h.stt || '', h.ho_ten || '', h.ten, ...h.o.map(x => x ? F(x.cao) : ''), ...T.them.map(d => { const x = h.them.find(y => y.de.slug === d.slug); return x ? F(x.cao) : '' }), h.lam, T.de.length, F(h.tb), h.xu == null ? '' : F(h.xu), h.sua, h.gy,
      canQT(h) ? 'x' : '', h.td ? 'x' : '', h.ly.map(x => x[1]).join('; '), nx[i] || nxEm(h, T.de.length)]);
    const csv = '﻿' + [dau, ...dong, [], ['Nhận xét lớp'], [document.getElementById('th-nx-lop').value]].map(r => r.map(v => `"${String(v).replace(/"/g, '""')}"`).join(',')).join('\n');
    const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv' })); a.download = `TongHop_${k.lop}_${new Date().toISOString().slice(0, 10)}.csv`; a.click();
  }
  window.TongHop = { mo };
})();
