// Thư viện chung: phiên đăng nhập (cookie ký HMAC), băm mật khẩu, chấm điểm theo thang THPT 2025
const enc = new TextEncoder();
export const b64u = buf => btoa(String.fromCharCode(...new Uint8Array(buf))).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
const ub64 = s => Uint8Array.from(atob(s.replace(/-/g, '+').replace(/_/g, '/')), c => c.charCodeAt(0));
const khoaHmac = secret => crypto.subtle.importKey('raw', enc.encode(secret || 'chua-dat'), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign', 'verify']);

export async function kyPhien(env, o) {
  const p = b64u(enc.encode(JSON.stringify(o)));
  const s = await crypto.subtle.sign('HMAC', await khoaHmac(env.SESSION_SECRET), enc.encode(p));
  return p + '.' + b64u(s);
}
export async function docPhien(env, req) {
  const m = /(?:^|;\s*)phien=([^;]+)/.exec(req.headers.get('Cookie') || '');
  if (!m) return null;
  const [p, s] = m[1].split('.');
  if (!p || !s) return null;
  try {
    if (!await crypto.subtle.verify('HMAC', await khoaHmac(env.SESSION_SECRET), ub64(s), enc.encode(p))) return null;
    const o = JSON.parse(new TextDecoder().decode(ub64(p)));
    return o.het > Date.now() ? o : null;
  } catch (e) { return null; }
}
export const cookiePhien = (gt, tuoi) => `phien=${gt}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=${tuoi}`;
export const json = (o, st = 200, h = {}) => new Response(JSON.stringify(o), { status: st, headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store', ...h } });
export const trang = (tieu, noi, st = 200) => new Response(`<!DOCTYPE html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><title>${tieu}</title><style>body{margin:0;min-height:100vh;display:grid;place-items:center;font:17px/1.6 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:#eef3f9;color:#1f2937}.the{background:#fff;border-radius:18px;padding:30px 36px;max-width:520px;box-shadow:0 12px 40px rgba(30,58,138,.12);text-align:center}h1{font-size:21px;color:#1e3a8a;margin:0 0 8px}a{color:#1d4ed8}</style></head><body><div class="the"><h1>${tieu}</h1>${noi}</div></body></html>`, { status: st, headers: { 'content-type': 'text/html; charset=utf-8', 'cache-control': 'no-store' } });

export async function bamMk(mk, muoi) {
  const k = await crypto.subtle.importKey('raw', enc.encode(String(mk)), 'PBKDF2', false, ['deriveBits']);
  return b64u(await crypto.subtle.deriveBits({ name: 'PBKDF2', salt: enc.encode(muoi), iterations: 5000, hash: 'SHA-256' }, k, 256));
}
export const muoiMoi = () => b64u(crypto.getRandomValues(new Uint8Array(12)));
export const soBam = s => { let h = 2166136261; for (const c of String(s)) h = Math.imul(h ^ c.charCodeAt(0), 16777619); return h >>> 0; };
export const lopKhop = (dsLop, lop) => !dsLop || String(dsLop).split(',').map(x => x.trim().toUpperCase()).filter(Boolean)
  .some(x => x === String(lop || '').trim().toUpperCase());

// ---- chấm điểm (giống examGrade của bài kiểm tra) ----
function so(v) {
  let s = String(v ?? '').trim().replace(/\\[()[\]]|\$/g, '').replace(/\{,\}/g, '.').replace(/\\,/g, '').replace(/,/g, '.').replace(/−/g, '-').replace(/\s/g, '');
  if (!s || !/^[+-]?(?:\d+(?:\.\d*)?|\.\d+)$/.test(s)) return null;
  const n = Number(s); return Number.isFinite(n) ? n : null;
}
function bangDapSo(got, exp) {
  if (String(got ?? '').trim() === '') return false;
  const a = so(got), b = so(exp);
  if (a !== null && b !== null) return Math.abs(a - b) <= 1e-10 * Math.max(1, Math.abs(b));
  return String(got).trim().normalize('NFC') === String(exp).trim().normalize('NFC');
}
export function cham(khoa, answers) {
  answers = answers || {};
  const points = { mcq: 0, tf: 0, short: 0 }, right = { mcq: 0, tf: 0, short: 0 }; let blank = 0;
  const rows = khoa.map((q, i) => {
    const a = answers[i]; let cents = 0, correct = 0, answered = false;
    if (q.type === 'mcq') { answered = Number.isInteger(a) && a >= 0 && a <= 3; correct = answered && a === q.answer ? 1 : 0; cents = correct * 25; }
    else if (q.type === 'tf') { const arr = Array.isArray(a) ? a : []; answered = arr.some(x => typeof x === 'boolean'); correct = q.answer.reduce((n, v, j) => n + (typeof arr[j] === 'boolean' && arr[j] === v ? 1 : 0), 0); cents = [0, 10, 25, 50, 100][correct]; }
    else { answered = typeof a === 'string' && a.trim() !== ''; correct = answered && bangDapSo(a, q.answer) ? 1 : 0; cents = correct * 50; }
    if (!answered) blank++;
    points[q.type] += cents; right[q.type] += q.type === 'tf' ? (correct === 4 ? 1 : 0) : correct;
    return { index: i, type: q.type, correct, answered, points: cents / 100, max: q.type === 'mcq' ? .25 : q.type === 'tf' ? 1 : .5 };
  });
  return { score: (points.mcq + points.tf + points.short) / 100, parts: { mcq: points.mcq / 100, tf: points.tf / 100, short: points.short / 100 }, right, blank, rows };
}
