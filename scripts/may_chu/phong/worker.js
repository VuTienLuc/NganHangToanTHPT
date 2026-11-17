// Phòng thi đấu trực tiếp (kiểu Quizizz) — mỗi phòng là một Durable Object, kết nối WebSocket (ngủ đông khi rảnh).
// Chỉ trang Pages (functions/api) gọi vào qua binding PHONG; Pages đã kiểm đăng nhập và gắn danh tính vào header.
const DIEM_CO_BAN = 600, DIEM_TOC_DO = 400, THUONG_CHUOI = 100, CHUOI_TOI_DA = 5;

function so(x) {
  const t = String(x ?? '').trim().replace(/\$/g, '').replace(/\{,\}/g, ',').replace(/\s/g, '').replace(/^\+/, '').replace(',', '.');
  return /^-?\d+(\.\d+)?$/.test(t) ? Number(t) : null;
}
function bangDapSo(got, exp) {
  if (String(got ?? '').trim() === '') return false;
  const a = so(got), b = so(exp);
  if (a !== null && b !== null) return Math.abs(a - b) <= 1e-10 * Math.max(1, Math.abs(b));
  return String(got).trim().normalize('NFC') === String(exp).trim().normalize('NFC');
}
// tỉ lệ đúng của một câu: mcq/short 0|1, tf = số ý đúng / 4
function tiLe(k, v) {
  if (!k) return 0;
  if (k.type === 'mcq') return Number.isInteger(v) && v === k.answer ? 1 : 0;
  if (k.type === 'tf') { const a = Array.isArray(v) ? v : []; return k.answer.reduce((n, x, j) => n + (a[j] === x ? 1 : 0), 0) / 4; }
  return bangDapSo(v, k.answer) ? 1 : 0;
}

export class Phong {
  constructor(ctx, env) { this.ctx = ctx; this.env = env; this.s = null; }

  async nap() {
    if (!this.s) this.s = (await this.ctx.storage.get('s')) || null;
    return this.s;
  }
  async luu() { await this.ctx.storage.put('s', this.s); }

  async fetch(req) {
    const u = new URL(req.url), duong = u.pathname.replace(/^\/+/, '');
    if (duong === 'tao') {                       // Pages gửi: {ma, slug, ten, khoa, vao, nhip, doi, giay, gv}
      const d = await req.json();
      this.s = { ma: d.ma, slug: d.slug, ten: d.ten, khoa: d.khoa, vao: d.vao, nhip: d.nhip, so_doi: d.doi | 0, giay: d.giay || 20,
        gv: d.gv, tao_luc: Date.now(), giai_doan: 'cho', cur: -1, cau: [], nguoi: {}, het_luc: 0 };
      await this.luu();
      await this.ctx.storage.setAlarm(Date.now() + 6 * 3600e3);       // phòng tự xoá sau 6 giờ
      return Response.json({ ok: true });
    }
    const s = await this.nap();
    if (duong === 'thong-tin') {
      if (!s) return Response.json({ ok: false, loi: 'Không có phòng này (sai mã hoặc phòng đã đóng).' });
      return Response.json({ ok: true, ten: s.ten, vao: s.vao, nhip: s.nhip, giai_doan: s.giai_doan, so_doi: s.so_doi });
    }
    if (duong === 'ket-qua') {
      if (!s) return Response.json({ ok: false });
      return Response.json({ ok: true, ...this.bangKetQua(true) });
    }
    if (duong === 'ws') {
      if (!s) return new Response('Không có phòng', { status: 404 });
      if (req.headers.get('Upgrade') !== 'websocket') return new Response('Cần WebSocket', { status: 426 });
      const vai = req.headers.get('X-Vai') === 'gv' ? 'gv' : 'hs';
      const id = vai === 'gv' ? 'gv' : (req.headers.get('X-Tk') || (req.headers.get('X-Khach') ? 'k' + req.headers.get('X-Khach') : 'k' + crypto.randomUUID().slice(0, 8)));
      const [a, b] = Object.values(new WebSocketPair());
      this.ctx.acceptWebSocket(b, [vai, id]);
      b.serializeAttachment({ vai, id, tk: req.headers.get('X-Tk') || '', ho_ten: decodeURIComponent(req.headers.get('X-Ho-Ten') || ''),
        lop: req.headers.get('X-Lop') || '', stt: req.headers.get('X-Stt') || '' });
      return new Response(null, { status: 101, webSocket: a });
    }
    return new Response('?', { status: 404 });
  }

  // ---------- tiện ích gửi ----------
  gui(ws, m) { try { ws.send(JSON.stringify(m)); } catch (_) {} }
  cacWs(vai) { return this.ctx.getWebSockets(vai); }
  guiGV(m) { for (const w of this.cacWs('gv')) this.gui(w, m); }
  guiHS(m) { for (const w of this.cacWs('hs')) this.gui(w, m); }
  wsCua(id) { return this.ctx.getWebSockets(id)[0]; }

  danhSach() {
    const s = this.s;
    return Object.values(s.nguoi).map(p => ({ id: p.id, ten: p.ten, lop: p.lop, stt: p.stt, doi: p.doi, diem: p.diem, chuoi: p.chuoi,
      dung: p.dung, da_lam: Object.keys(p.tl).length, onl: !!this.wsCua(p.id) }));
  }
  bangDoi() {
    const s = this.s; if (!s.so_doi) return [];
    const d = Array.from({ length: s.so_doi }, (_, i) => ({ doi: i, tong: 0, n: 0 }));
    for (const p of Object.values(s.nguoi)) if (p.doi != null && d[p.doi]) { d[p.doi].tong += p.diem; d[p.doi].n++; }
    return d.map(x => ({ doi: x.doi, n: x.n, diem: x.n ? Math.round(x.tong / x.n) : 0 })).sort((a, b) => b.diem - a.diem);
  }
  // quy ra thang 10 theo cách chấm đề THPT (TN 0,25 · Đ/S 0,1/0,25/0,5/1 · TLN 0,5) để so được với bài làm thường
  diem10(p) {
    let t = 0;
    for (const [i, x] of Object.entries(p.tl)) { const k = this.s.khoa[i]; if (!k || !x) continue;
      t += k.type === 'mcq' ? .25 * x.ti_le : k.type === 'tf' ? [0, .1, .25, .5, 1][Math.round(x.ti_le * 4)] : .5 * x.ti_le; }
    return Math.round(t * 100) / 100;
  }
  bangKetQua(day) {
    const s = this.s, ds = this.danhSach().sort((a, b) => b.diem - a.diem).map((p, i) => ({ ...p, hang: i + 1, diem10: this.diem10(s.nguoi[p.id]) }));
    return { ten: s.ten, slug: s.slug, ma: s.ma, so_cau: s.cau.length, so_doi: s.so_doi, nhip: s.nhip, vao: s.vao,
      nguoi: day ? ds.map(p => ({ ...p, tk: s.nguoi[p.id].tk, ho_ten: s.nguoi[p.id].ho_ten, tl: s.nguoi[p.id].tl })) : ds, doi: this.bangDoi() };
  }
  // trạng thái gửi màn hình thầy
  trangThaiGV() {
    const s = this.s, k = s.cur >= 0 ? s.khoa[s.cur] : null;
    const dem = s.cur >= 0 ? Object.values(s.nguoi).filter(p => p.tl[s.cur]).length : 0;
    const chon = k && k.type === 'mcq' ? [0, 1, 2, 3].map(j => Object.values(s.nguoi).filter(p => p.tl[s.cur] && p.tl[s.cur].v === j).length) : null;
    return { t: 'phong', ma: s.ma, ten: s.ten, vao: s.vao, nhip: s.nhip, so_doi: s.so_doi, giay: s.giay, giai_doan: s.giai_doan, cur: s.cur,
      so_cau: s.cau.length, het_luc: s.het_luc, bay_gio: Date.now(), nguoi: this.danhSach(), doi: this.bangDoi(), da_tl: dem, chon,
      dap_an: s.giai_doan === 'dap_an' && k ? k.answer : null, co_cau: s.cau.length > 0 };
  }
  // câu i gửi cho học sinh (không kèm đáp án)
  cauHS(i) { const c = this.s.cau[i]; return c ? { i, type: c.type, html: c.html, so_pa: c.so_pa } : null; }
  trangThaiHS(p) {
    const s = this.s;
    const m = { t: 'trang_thai', ten: s.ten, nhip: s.nhip, giai_doan: s.giai_doan, so_cau: s.cau.length, bay_gio: Date.now(), giay: s.giay,
      toi: p ? { id: p.id, ten: p.ten, doi: p.doi, diem: p.diem, chuoi: p.chuoi, hang: this.hangCua(p.id) } : null, so_doi: s.so_doi };
    if (s.nhip === 'gv') {
      m.cur = s.cur; m.het_luc = s.het_luc;
      if (s.cur >= 0 && (s.giai_doan === 'cau' || s.giai_doan === 'dap_an')) {
        m.cau = this.cauHS(s.cur); const x = p ? p.tl[s.cur] : null;
        m.da_tl = x ? (s.giai_doan === 'dap_an' ? x : { v: x.v }) : null;      // chưa công bố thì không lộ đúng/sai
        if (s.giai_doan === 'dap_an') m.dap_an = s.khoa[s.cur].answer;
      }
    } else if (p && s.giai_doan === 'cau') {
      const i = p.cur ?? 0;
      if (i < s.cau.length) { m.cur = i; m.cau = this.cauHS(i); m.het_luc = p.het_luc; }
      else m.xong = true;
    }
    if (s.giai_doan === 'ket_thuc') m.ket_qua = { top: this.danhSach().sort((a, b) => b.diem - a.diem).slice(0, 5), doi: this.bangDoi() };
    return m;
  }
  hangCua(id) { const ds = Object.values(this.s.nguoi).sort((a, b) => b.diem - a.diem); return ds.findIndex(p => p.id === id) + 1; }
  phatTat() {
    this.guiGV(this.trangThaiGV());
    for (const w of this.cacWs('hs')) { const a = w.deserializeAttachment(); this.gui(w, this.trangThaiHS(this.s.nguoi[a.id])); }
  }

  chiaDoi() {
    const s = this.s; if (!s.so_doi) { for (const p of Object.values(s.nguoi)) p.doi = null; return; }
    const ds = Object.values(s.nguoi).sort(() => Math.random() - .5);
    ds.forEach((p, i) => { p.doi = i % s.so_doi; });
  }

  // ---------- nhận tin ----------
  async webSocketMessage(ws, raw) {
    const s = await this.nap(); if (!s) return;
    let m; try { m = JSON.parse(raw); } catch (_) { return; }
    const a = ws.deserializeAttachment();
    if (a.vai === 'gv') return this.lenhGV(ws, m);
    return this.lenhHS(ws, a, m);
  }

  async lenhGV(ws, m) {
    const s = this.s;
    if (m.t === 'chao') return this.gui(ws, this.trangThaiGV());
    if (m.t === 'nap') {                        // màn hình thầy gửi câu hỏi đã dựng sẵn (HTML, chưa có đáp án)
      if (!Array.isArray(m.cau) || m.cau.length !== s.khoa.length) return this.gui(ws, { t: 'loi', loi: 'Số câu không khớp đáp án trên máy chủ.' });
      s.cau = m.cau.map((c, i) => ({ type: s.khoa[i].type, html: String(c.html || '').slice(0, 400000), so_pa: c.so_pa | 0 }));
      await this.luu(); return this.phatTat();
    }
    if (m.t === 'cai_dat' && s.giai_doan === 'cho') {
      if (m.so_doi != null) s.so_doi = Math.max(0, Math.min(8, m.so_doi | 0));
      if (m.giay) s.giay = Math.max(5, Math.min(300, m.giay | 0));
      if (m.nhip === 'gv' || m.nhip === 'tu_do') s.nhip = m.nhip;
      this.chiaDoi(); await this.luu(); return this.phatTat();
    }
    if (m.t === 'chia_lai' && s.giai_doan === 'cho') { this.chiaDoi(); await this.luu(); return this.phatTat(); }
    if (m.t === 'moi_ra' && m.id && s.nguoi[m.id]) {
      delete s.nguoi[m.id]; const w = this.wsCua(m.id); if (w) { this.gui(w, { t: 'bi_moi_ra' }); try { w.close(4000, 'out'); } catch (_) {} }
      await this.luu(); return this.phatTat();
    }
    if (m.t === 'bat_dau' && s.giai_doan === 'cho') {
      if (!s.cau.length) return this.gui(ws, { t: 'loi', loi: 'Chưa nạp câu hỏi.' });
      if (s.so_doi && Object.values(s.nguoi).some(p => p.doi == null)) this.chiaDoi();
      if (s.nhip === 'tu_do') {
        s.giai_doan = 'cau';
        for (const p of Object.values(s.nguoi)) { p.cur = 0; p.het_luc = Date.now() + s.giay * 1000; }
        await this.luu(); return this.phatTat();
      }
      return this.moCau(0);
    }
    if (s.nhip === 'gv') {
      if (m.t === 'cau' && Number.isInteger(m.i) && m.i >= 0 && m.i < s.cau.length && s.giai_doan !== 'ket_thuc') return this.moCau(m.i);
      if (m.t === 'het_gio' && s.giai_doan === 'cau') return this.dapAn();
      if (m.t === 'them_gio' && s.giai_doan === 'cau') { s.het_luc += 10000; await this.datHen(); await this.luu(); return this.phatTat(); }
    }
    if (m.t === 'ket_thuc') { s.giai_doan = 'ket_thuc'; await this.luu(); return this.phatTat(); }
  }

  async moCau(i) {
    const s = this.s; s.cur = i; s.giai_doan = 'cau'; s.bat_dau = Date.now(); s.het_luc = s.bat_dau + s.giay * 1000;
    await this.datHen(); await this.luu(); this.phatTat();
  }
  async datHen() { await this.ctx.storage.setAlarm(this.s.het_luc + 300); }
  async dapAn() {
    const s = this.s; if (s.giai_doan !== 'cau') return;
    s.giai_doan = 'dap_an';
    for (const p of Object.values(s.nguoi)) if (!p.tl[s.cur]) p.chuoi = 0;    // không trả lời → mất chuỗi
    await this.ctx.storage.setAlarm(Date.now() + 6 * 3600e3);
    await this.luu(); this.phatTat();
  }
  async alarm() {
    const s = await this.nap(); if (!s) return;
    if (Date.now() - s.tao_luc > 6 * 3600e3 - 60e3) { await this.ctx.storage.deleteAll(); this.s = null; return; }
    if (s.nhip === 'gv' && s.giai_doan === 'cau' && Date.now() >= s.het_luc) return this.dapAn();
  }

  chamDiem(p, i, v, batDau, hetLuc) {
    const s = this.s, k = s.khoa[i], tl = tiLe(k, v), bay = Date.now();
    const tong = Math.max(1, hetLuc - batDau), con = Math.max(0, hetLuc - bay);
    let diem = 0;
    if (tl > 0) {
      p.chuoi = tl === 1 ? (p.chuoi || 0) + 1 : 0;
      diem = Math.round(tl * (DIEM_CO_BAN + DIEM_TOC_DO * con / tong)) + (tl === 1 ? THUONG_CHUOI * Math.min(CHUOI_TOI_DA, Math.max(0, p.chuoi - 1)) : 0);
      if (tl === 1) p.dung++;
    } else p.chuoi = 0;
    p.diem += diem;
    p.tl[i] = { v, ti_le: tl, diem, ms: Math.max(0, bay - batDau) };
    return p.tl[i];
  }

  async lenhHS(ws, a, m) {
    const s = this.s;
    if (m.t === 'vao') {
      let p = s.nguoi[a.id];
      if (!p) {
        if (s.vao === 'tk' && !a.tk) return this.gui(ws, { t: 'loi', loi: 'Phòng này cần đăng nhập tài khoản.' });
        if (s.giai_doan === 'ket_thuc') return this.gui(ws, { t: 'loi', loi: 'Phòng đã kết thúc.' });
        let ten = a.tk ? (a.ho_ten || a.tk) : String(m.biet_danh || '').trim().replace(/\s+/g, ' ').slice(0, 24);
        if (!ten) return this.gui(ws, { t: 'can_ten' });
        if (!a.tk) { const trung = new Set(Object.values(s.nguoi).map(x => x.ten.toLowerCase())); let t0 = ten, n = 2; while (trung.has(ten.toLowerCase())) ten = t0 + ' ' + n++; }
        if (Object.keys(s.nguoi).length >= 200) return this.gui(ws, { t: 'loi', loi: 'Phòng đã đủ 200 người.' });
        p = s.nguoi[a.id] = { id: a.id, tk: a.tk, ho_ten: a.ho_ten, ten, lop: a.lop, stt: a.stt, doi: null, diem: 0, chuoi: 0, dung: 0, tl: {} };
        if (s.so_doi) { const dem = Array(s.so_doi).fill(0); for (const x of Object.values(s.nguoi)) if (x.doi != null) dem[x.doi]++; p.doi = dem.indexOf(Math.min(...dem)); }
        if (s.nhip === 'tu_do' && s.giai_doan === 'cau') { p.cur = 0; p.het_luc = Date.now() + s.giay * 1000; }
        await this.luu();
      }
      this.gui(ws, this.trangThaiHS(p)); this.guiGV(this.trangThaiGV()); return;
    }
    const p = s.nguoi[a.id]; if (!p) return this.gui(ws, { t: 'can_vao' });
    if (m.t === 'tl') {
      if (s.nhip === 'gv') {
        if (s.giai_doan !== 'cau' || m.i !== s.cur || p.tl[s.cur]) return;
        if (Date.now() > s.het_luc + 1500) return;
        const kq = this.chamDiem(p, s.cur, m.v, s.bat_dau, s.het_luc);
        await this.luu();
        this.gui(ws, { t: 'da_nhan', i: s.cur });               // đáp án chỉ hiện khi thầy công bố
        this.guiGV(this.trangThaiGV());
        if (Object.values(s.nguoi).every(x => x.tl[s.cur] || !this.wsCua(x.id))) await this.dapAn();
        void kq; return;
      }
      // tự làm theo tốc độ riêng: chấm ngay, sang câu tiếp
      if (s.giai_doan !== 'cau' || m.i !== p.cur || p.tl[p.cur]) return;
      const batDau = p.het_luc - s.giay * 1000, kq = this.chamDiem(p, p.cur, m.v, batDau, Math.max(p.het_luc, Date.now()));
      const dapAn = s.khoa[p.cur].answer;
      p.cur++; p.het_luc = Date.now() + s.giay * 1000 + 2500;     // +2,5 giây xem đáp án trước câu sau
      await this.luu();
      this.gui(ws, { t: 'ket_qua_cau', i: m.i, ti_le: kq.ti_le, diem: kq.diem, dap_an: dapAn, tong: p.diem, chuoi: p.chuoi, hang: this.hangCua(p.id) });
      this.guiGV(this.trangThaiGV());
      return;
    }
    if (m.t === 'tiep' && s.nhip === 'tu_do') return this.gui(ws, this.trangThaiHS(p));
    if (m.t === 'het_gio_rieng' && s.nhip === 'tu_do' && s.giai_doan === 'cau' && m.i === p.cur && Date.now() >= p.het_luc - 500 && !p.tl[p.cur]) {
      p.tl[p.cur] = { v: null, ti_le: 0, diem: 0, ms: s.giay * 1000 }; p.chuoi = 0;
      const dapAn = s.khoa[p.cur].answer; p.cur++; p.het_luc = Date.now() + s.giay * 1000 + 2500; await this.luu();
      this.gui(ws, { t: 'ket_qua_cau', i: m.i, ti_le: 0, diem: 0, dap_an: dapAn, tong: p.diem, chuoi: 0, hang: this.hangCua(p.id), het_gio: true });
      this.guiGV(this.trangThaiGV());
    }
  }
  async webSocketClose(ws) {
    const s = await this.nap(); if (!s) return;
    const a = ws.deserializeAttachment(); if (a && a.vai === 'hs') this.guiGV(this.trangThaiGV());
  }
}

export default { fetch() { return new Response('Phòng thi đấu: chỉ dùng qua trang chính.', { status: 404 }); } };
