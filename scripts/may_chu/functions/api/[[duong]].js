// API: học sinh (đăng nhập, đổi mật khẩu, bắt đầu, nộp bài, kết quả) và quản trị (x-admin: ADMIN_TOKEN)
import { docPhien, kyPhien, cookiePhien, json, bamMk, muoiMoi, cham, lopKhop } from '../_lib.js';

const BAY_GIO = () => new Date().toISOString();
const NGAY30 = 30 * 86400;

async function phatPhien(env, t) {
  const o = { tk: t.ten, ho_ten: t.ho_ten, lop: t.lop, stt: t.stt, vai: t.vai, doi_mk: t.doi_mk ? 1 : 0, het: Date.now() + NGAY30 * 1000 };
  return cookiePhien(await kyPhien(env, o), NGAY30);
}

async function luot(env, tk, de) {
  const nhom = de.nhom || de.slug;
  const dem = (await env.DB.prepare('SELECT COUNT(*) AS n FROM bai WHERE tk = ? AND nhom = ?').bind(tk, nhom).first()).n;
  const them = (await env.DB.prepare('SELECT so FROM luot_them WHERE tk = ? AND nhom = ?').bind(tk, nhom).first())?.so || 0;
  const gioi = de.so_luot ? de.so_luot + them : 0;
  return { nhom, dem, gioi, con_lai: gioi ? Math.max(0, gioi - dem) : null };
}

async function hocSinh(duong, d, env, req, url) {
  const ph = await docPhien(env, req);
  if (duong === 'dang-nhap') {
    const ten = String(d.tk || '').trim().toLowerCase(), mk = String(d.mk || '');
    const t = await env.DB.prepare('SELECT * FROM tk WHERE ten = ?').bind(ten).first();
    if (!t || t.khoa) return json({ ok: false, loi: 'Sai tên đăng nhập hoặc mật khẩu.' });
    if (t.khoa_den > Date.now()) return json({ ok: false, loi: `Nhập sai nhiều lần — thử lại sau ${Math.ceil((t.khoa_den - Date.now()) / 60000)} phút.` });
    if (await bamMk(mk, t.muoi) !== t.bam) {
      const sai = (t.sai || 0) + 1;
      await env.DB.prepare('UPDATE tk SET sai = ?, khoa_den = ? WHERE ten = ?').bind(sai >= 5 ? 0 : sai, sai >= 5 ? Date.now() + 600000 : 0, ten).run();
      return json({ ok: false, loi: sai >= 5 ? 'Sai 5 lần — tài khoản tạm khoá 10 phút.' : 'Sai tên đăng nhập hoặc mật khẩu.' });
    }
    await env.DB.prepare('UPDATE tk SET sai = 0, khoa_den = 0, lan_cuoi = ? WHERE ten = ?').bind(BAY_GIO(), ten).run();
    return json({ ok: true, doi_mk: !!t.doi_mk, vai: t.vai }, 200, { 'set-cookie': await phatPhien(env, t) });
  }
  if (duong === 'dang-xuat') return json({ ok: true }, 200, { 'set-cookie': cookiePhien('', 0) });
  if (!ph) return json({ ok: false, loi: 'Chưa đăng nhập.', can_dang_nhap: true }, 401);
  if (duong === 'doi-mk') {
    const t = await env.DB.prepare('SELECT * FROM tk WHERE ten = ?').bind(ph.tk).first();
    if (!t || await bamMk(String(d.cu || ''), t.muoi) !== t.bam) return json({ ok: false, loi: 'Mật khẩu hiện tại chưa đúng.' });
    const moi = String(d.moi || '');
    if (moi.length < 6) return json({ ok: false, loi: 'Mật khẩu mới cần ít nhất 6 ký tự.' });
    if (moi === String(d.cu)) return json({ ok: false, loi: 'Mật khẩu mới phải khác mật khẩu cũ.' });
    const m = muoiMoi();
    await env.DB.prepare('UPDATE tk SET muoi = ?, bam = ?, doi_mk = 0 WHERE ten = ?').bind(m, await bamMk(moi, m), ph.tk).run();
    return json({ ok: true }, 200, { 'set-cookie': await phatPhien(env, { ...t, doi_mk: 0 }) });
  }
  if (duong === 'toi') {
    const ra = { ok: true, tk: ph.tk, ho_ten: ph.ho_ten, lop: ph.lop, stt: ph.stt, vai: ph.vai, doi_mk: !!ph.doi_mk };
    if (ph.vai === 'gv') {
      const { results } = await env.DB.prepare("SELECT d.slug, d.ten, d.lop, d.so_luot, d.trang_thai, d.tao_luc, (SELECT COUNT(DISTINCT b.tk) FROM bai b WHERE b.nhom = d.slug AND b.nop_luc IS NOT NULL) AS so_hs, (SELECT AVG(b.diem) FROM bai b WHERE b.nhom = d.slug AND b.nop_luc IS NOT NULL) AS tb FROM de d WHERE d.nhom IS NULL OR d.nhom = '' ORDER BY d.tao_luc DESC").all();
      ra.de = results;
    }
    if (ph.vai !== 'gv') {
      const { results } = await env.DB.prepare("SELECT slug, ten, lop, so_luot, nhom, trang_thai FROM de WHERE (nhom IS NULL OR nhom = '') AND trang_thai != 'da_dong' ORDER BY tao_luc DESC").all();
      ra.de = [];
      for (const x of results.filter(x => lopKhop(x.lop, ph.lop))) {
        const l = await luot(env, ph.tk, x);
        const tot = await env.DB.prepare('SELECT MAX(diem) AS d FROM bai WHERE tk = ? AND nhom = ? AND nop_luc IS NOT NULL').bind(ph.tk, l.nhom).first();
        ra.de.push({ slug: x.slug, ten: x.ten, da_lam: l.dem, con_lai: l.con_lai, cao_nhat: tot?.d ?? null, cong_bo: x.trang_thai === 'da_cong_bo' });
      }
    }
    return json(ra);
  }
  const slug = String(d.de || url.searchParams.get('de') || '');
  const de = await env.DB.prepare('SELECT * FROM de WHERE slug = ?').bind(slug).first();
  if (!de) return json({ ok: false, loi: 'Không có đề này.' }, 404);
  if (ph.vai !== 'gv' && !lopKhop(de.lop, ph.lop)) return json({ ok: false, loi: 'Đề không giao cho lớp em.' }, 403);
  if (duong === 'ket-qua') {
    const { results } = await env.DB.prepare('SELECT lan, tra_loi, cham FROM bai WHERE tk = ? AND de = ? AND nop_luc IS NOT NULL ORDER BY lan').bind(ph.tk, slug).all();
    return json({ ok: true, ds: results.map(x => ({ lan: x.lan, tra_loi: JSON.parse(x.tra_loi || '{}'), cham: JSON.parse(x.cham || 'null') })) });
  }
  if (duong === 'bat-dau') {
    if (ph.doi_mk) return json({ ok: false, loi: 'Em cần đổi mật khẩu trước (mở lại trang đăng nhập).' });
    if (de.trang_thai === 'da_dong') return json({ ok: false, loi: 'Bài thi đã đóng.' });
    if (ph.vai === 'gv') return json({ ok: true, thong_bao: 'Tài khoản giáo viên: làm thử, không giới hạn lượt, không lưu điểm.' });
    const l = await luot(env, ph.tk, de);
    const dang = await env.DB.prepare('SELECT id, lan FROM bai WHERE tk = ? AND nhom = ? AND nop_luc IS NULL').bind(ph.tk, l.nhom).first();
    if (dang) return json({ ok: true, tiep: true, lan: dang.lan, con_lai: l.con_lai, thong_bao: `Tiếp tục lần làm ${dang.lan}.` });
    if (l.gioi && l.dem >= l.gioi) return json({ ok: false, het: true, loi: `Em đã dùng hết ${l.gioi} lượt làm đề này. Cần làm thêm thì báo thầy.` });
    await env.DB.prepare('INSERT INTO bai (tk, de, nhom, lan, bat_dau) VALUES (?, ?, ?, ?, ?)').bind(ph.tk, slug, l.nhom, l.dem + 1, BAY_GIO()).run();
    return json({ ok: true, lan: l.dem + 1, con_lai: l.gioi ? l.gioi - l.dem - 1 : null,
      thong_bao: l.gioi ? `Lần làm ${l.dem + 1}/${l.gioi}.` : `Lần làm ${l.dem + 1}.` });
  }
  if (duong === 'goi-y') {            // học sinh mở "Gợi ý AI" — đếm để thầy biết
    if (ph.vai === 'gv') return json({ ok: true });
    await env.DB.prepare('UPDATE bai SET goi_y = COALESCE(goi_y, 0) + 1 WHERE id = (SELECT id FROM bai WHERE tk = ? AND de = ? AND nop_luc IS NULL ORDER BY id DESC LIMIT 1)').bind(ph.tk, slug).run();
    return json({ ok: true });
  }
  if (duong === 'cam-xuc') {
    if (ph.vai === 'gv') return json({ ok: true });
    const cx = String(d.cam_xuc || '').slice(0, 20);
    await env.DB.prepare('UPDATE bai SET cam_xuc = ? WHERE id = (SELECT id FROM bai WHERE tk = ? AND de = ? AND nop_luc IS NULL ORDER BY id DESC LIMIT 1)').bind(cx, ph.tk, slug).run();
    return json({ ok: true });
  }
  if (duong === 'nop') {
    const khoa = JSON.parse(de.khoa || '[]');
    if (!khoa.length) return json({ ok: false, loi: 'Đề chưa có đáp án trên máy chủ — báo thầy.' });
    const tl = d.answers || {}, kq = cham(khoa, tl), s = JSON.stringify(tl);
    if (ph.vai === 'gv') return json({ ok: true, cham: kq });
    const l = await luot(env, ph.tk, de);
    const dang = await env.DB.prepare('SELECT id FROM bai WHERE tk = ? AND nhom = ? AND nop_luc IS NULL ORDER BY id DESC').bind(ph.tk, l.nhom).first();
    if (dang) {
      await env.DB.prepare('UPDATE bai SET de = ?, nop_luc = ?, tra_loi = ?, diem = ?, cham = ?, chuyen_tab = ?, thoi_gian = ? WHERE id = ?')
        .bind(slug, BAY_GIO(), s, kq.score, JSON.stringify(kq), d.chuyen_tab | 0, d.thoi_gian | 0, dang.id).run();
      return json({ ok: true, cham: kq });
    }
    const cu = await env.DB.prepare('SELECT cham FROM bai WHERE tk = ? AND de = ? AND tra_loi = ?').bind(ph.tk, slug, s).first();
    if (cu) return json({ ok: true, cham: JSON.parse(cu.cham) });
    if (l.gioi && l.dem >= l.gioi) return json({ ok: false, loi: 'Bài này vượt số lượt cho phép nên không được tính.' });
    await env.DB.prepare('INSERT INTO bai (tk, de, nhom, lan, bat_dau, nop_luc, tra_loi, diem, cham, chuyen_tab, thoi_gian) VALUES (?,?,?,?,?,?,?,?,?,?,?)')
      .bind(ph.tk, slug, l.nhom, l.dem + 1, BAY_GIO(), BAY_GIO(), s, kq.score, JSON.stringify(kq), d.chuyen_tab | 0, d.thoi_gian | 0).run();
    return json({ ok: true, cham: kq });
  }
  return json({ ok: false, loi: 'Không có chức năng này.' }, 404);
}

async function quanTri(duong, d, env) {
  const DB = env.DB;
  if (duong === 'tk/nhap') {
    const lenh = [];
    for (const x of d.ds || []) {
      const ten = String(x.ten).trim().toLowerCase(); if (!ten) continue;
      const cu = await DB.prepare('SELECT ten FROM tk WHERE ten = ?').bind(ten).first();
      if (x.mk) {
        const m = muoiMoi(), b = await bamMk(x.mk, m);
        lenh.push(cu ? DB.prepare('UPDATE tk SET ho_ten=?, lop=?, stt=?, vai=?, muoi=?, bam=?, doi_mk=?, sai=0, khoa_den=0 WHERE ten=?').bind(x.ho_ten || '', x.lop || '', x.stt | 0, x.vai || 'hs', m, b, x.vai === 'gv' ? 0 : 1, ten)
          : DB.prepare('INSERT INTO tk (ten, ho_ten, lop, stt, vai, muoi, bam, doi_mk, tao_luc) VALUES (?,?,?,?,?,?,?,?,?)').bind(ten, x.ho_ten || '', x.lop || '', x.stt | 0, x.vai || 'hs', m, b, x.vai === 'gv' ? 0 : 1, BAY_GIO()));
      } else if (cu) lenh.push(DB.prepare('UPDATE tk SET ho_ten=?, lop=?, stt=?, vai=? WHERE ten=?').bind(x.ho_ten || '', x.lop || '', x.stt | 0, x.vai || 'hs', ten));
    }
    if (lenh.length) await DB.batch(lenh);
    return json({ ok: true, so: lenh.length });
  }
  if (duong === 'tk/ds') {
    const { results } = await DB.prepare('SELECT ten, ho_ten, lop, stt, vai, doi_mk, khoa, lan_cuoi FROM tk ORDER BY vai DESC, lop, stt, ten').all();
    return json({ ok: true, ds: results });
  }
  if (duong === 'tk/khoa') { await DB.prepare('UPDATE tk SET khoa = ? WHERE ten = ?').bind(d.khoa ? 1 : 0, d.ten).run(); return json({ ok: true }); }
  if (duong === 'tk/xoa') { await DB.prepare('DELETE FROM tk WHERE ten = ?').bind(d.ten).run(); return json({ ok: true }); }
  if (duong === 'de/luu') {
    await DB.prepare(`INSERT INTO de (slug, ten, lop, so_luot, nhom, con, khoa, trang_thai, tao_luc) VALUES (?,?,?,?,?,?,?,?,?)
      ON CONFLICT(slug) DO UPDATE SET ten=excluded.ten, lop=excluded.lop, so_luot=excluded.so_luot, nhom=excluded.nhom, con=excluded.con,
      khoa=CASE WHEN excluded.khoa IS NULL OR excluded.khoa='' THEN de.khoa ELSE excluded.khoa END, trang_thai=excluded.trang_thai`)
      .bind(d.slug, d.ten || '', d.lop || '', d.so_luot ?? 2, d.nhom || '', d.con ? JSON.stringify(d.con) : '', d.khoa ? JSON.stringify(d.khoa) : '', d.trang_thai || 'dang_mo', d.tao_luc || BAY_GIO()).run();
    return json({ ok: true });
  }
  if (duong === 'de/xoa') { await DB.prepare('DELETE FROM de WHERE slug = ?').bind(d.slug).run(); return json({ ok: true }); }
  if (duong === 'diem') {
    const nhom = String(d.nhom || d.de || '');
    const { results } = await DB.prepare(`SELECT b.id, b.tk, b.de, b.lan, b.bat_dau, b.nop_luc, b.diem, b.chuyen_tab, b.thoi_gian, b.cam_xuc, b.goi_y, t.ho_ten, t.lop, t.stt
      FROM bai b LEFT JOIN tk t ON t.ten = b.tk WHERE b.nhom = ? ORDER BY t.lop, t.stt, b.lan`).bind(nhom).all();
    const them = (await DB.prepare('SELECT tk, so FROM luot_them WHERE nhom = ?').bind(nhom).all()).results;
    return json({ ok: true, ds: results, them });
  }
  if (duong === 'luot/them') {
    await DB.prepare(`INSERT INTO luot_them (tk, nhom, so) VALUES (?,?,?) ON CONFLICT(tk, nhom) DO UPDATE SET so = so + excluded.so`).bind(d.tk, d.nhom, d.so || 1).run();
    return json({ ok: true });
  }
  if (duong === 'bai/xoa') { await DB.prepare('DELETE FROM bai WHERE id = ?').bind(d.id).run(); return json({ ok: true }); }
  if (duong === 'ping') return json({ ok: true, db: !!DB });
  return json({ ok: false, loi: 'Không có chức năng quản trị này.' }, 404);
}

export async function onRequest({ request: req, env, params }) {
  const url = new URL(req.url);
  const duong = [].concat(params.duong || []).join('/');
  let d = {};
  if (req.method === 'POST') { try { d = await req.json(); } catch (e) { d = {}; } }
  if (!env.DB) return json({ ok: false, loi: 'Máy chủ chưa gắn cơ sở dữ liệu (D1).' }, 500);
  try {
    if (duong.startsWith('admin/')) {
      if (!env.ADMIN_TOKEN || req.headers.get('x-admin') !== env.ADMIN_TOKEN) return json({ ok: false, loi: 'Sai mã quản trị.' }, 403);
      return await quanTri(duong.slice(6), d, env);
    }
    if (['nop', 'bat-dau', 'cam-xuc', 'goi-y', 'doi-mk', 'dang-nhap', 'dang-xuat'].includes(duong) && req.method !== 'POST') return json({ ok: false, loi: 'Dùng POST.' }, 405);
    return await hocSinh(duong, d, env, req, url);
  } catch (e) { return json({ ok: false, loi: String(e && e.message || e) }, 500); }
}
