// Gác cổng: bài giảng + mục lục lớp chỉ giáo viên; đề thi phải đăng nhập, đúng lớp, chia mã đề theo tài khoản
import { docPhien, trang, soBam, lopKhop } from './_lib.js';

export async function onRequest({ request: req, env, next }) {
  const u = new URL(req.url), p = u.pathname, seg = decodeURIComponent(p.split('/')[1] || '');
  if (!seg || seg === 'index.html' || seg === 'api' || seg === 'dang-nhap' || seg === '404.html' || seg.startsWith('_') || seg === 'favicon.ico')
    return next();
  const ph = await docPhien(env, req);
  const veDangNhap = () => Response.redirect(`${u.origin}/dang-nhap/?ve=${encodeURIComponent(p)}`, 302);
  if (seg === 'bai-giang' || /^toan\d+$/.test(seg)) {
    if (!ph) return veDangNhap();
    if (ph.vai !== 'gv') {
      const s2 = decodeURIComponent(p.split('/')[2] || '');
      if (seg === 'bai-giang' && s2 === 'hs.json') return next();
      if (seg === 'bai-giang' && s2 && env.ASSETS) {          // phiếu / bài thầy cho học sinh xem: đúng khối lớp
        let ds = [];
        try { const r = await env.ASSETS.fetch(new URL('/bai-giang/hs.json', u.origin)); if (r.ok) ds = await r.json(); } catch (_) {}
        const x = ds.find(y => y.slug === s2), k = parseInt(ph.lop || '', 10);
        if (x && (!k || x.lop === k)) {
          if (ph.doi_mk) return Response.redirect(`${u.origin}/dang-nhap/?doi=1&ve=${encodeURIComponent(p)}`, 302);
          return next();
        }
      }
      return trang('Chưa mở cho em', '<p>Bài này thầy chưa mở cho lớp em. Các phiếu học tập dành cho em có ở trang chính.</p><p><a href="/">Về trang chính</a></p>', 403);
    }
    return next();
  }
  if (!env.DB) return next();
  const de = await env.DB.prepare('SELECT slug, lop, nhom, con, trang_thai FROM de WHERE slug = ?').bind(seg).first();
  if (!de) return next();
  if (!ph) return veDangNhap();
  if (ph.vai === 'gv') return next();
  if (ph.doi_mk) return Response.redirect(`${u.origin}/dang-nhap/?doi=1&ve=${encodeURIComponent(p)}`, 302);
  if (de.trang_thai === 'da_dong') return next();
  if (!lopKhop(de.lop, ph.lop)) return trang('Đề không giao cho lớp em', `<p>Lớp ${ph.lop} không được giao đề này.</p><p><a href="/">Về trang chính</a></p>`, 403);
  const chon = ds => ds[soBam(ph.tk + '|' + (de.nhom || de.slug)) % ds.length];
  if (de.con) {                                    // link chung → mã đề cố định theo tài khoản
    const ds = JSON.parse(de.con); if (ds.length) return Response.redirect(`${u.origin}/${chon(ds)}/`, 302);
  }
  if (de.nhom) {                                   // mở thẳng mã khác mã được chia → đưa về đúng mã
    const g = await env.DB.prepare('SELECT con FROM de WHERE slug = ?').bind(de.nhom).first();
    if (g && g.con) { const ds = JSON.parse(g.con), m = soBam(ph.tk + '|' + de.nhom) % ds.length;
      if (ds[m] !== seg) return Response.redirect(`${u.origin}/${ds[m]}/`, 302); }
  }
  return next();
}
