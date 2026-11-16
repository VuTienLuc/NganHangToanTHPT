# -*- coding: utf-8 -*-
"""THI TRỰC TUYẾN: đưa bài kiểm tra (mẫu "Xuất HTML bài kiểm tra" của ứng dụng trình chiếu) lên Cloudflare Pages.

- Mỗi đề một đường link:  https://<dự án>.pages.dev/<đường-dẫn>/
- Bản đăng lên MÃ HOÁ ĐÁP ÁN (băm SHA-256 có muối) và BỎ LỜI GIẢI → mở mã nguồn không đọc được đáp án;
  máy vẫn tự chấm, vẫn gửi điểm về Google Sheet như bản gốc.
- Thi xong: "Mở lời giải" → đăng lại bản gốc (có đáp án + lời giải) ở đúng link đó. "Đóng đề" → trang báo đã đóng.
- Lưu trong thi-truc-tuyen/ (đồng bộ GitHub để máy nào cũng đăng được, không mất đề cũ):
    site/        đúng những gì đưa lên Cloudflare (bản đã mã hoá)
    du_lieu/     bản gốc có đáp án (<đường-dẫn>.goc.html) — chỉ thầy giữ
    danh_sach.json, cau_hinh.json
- Đăng bằng wrangler (Node.js):  npx wrangler pages deploy … (lần đầu mở trình duyệt để thầy đăng nhập Cloudflare).
"""
import os, re, json, time, shutil, secrets, subprocess, datetime, urllib.request, urllib.error
from nh_core import GOC, ten_khong_dau

THU = os.path.join(GOC, "thi-truc-tuyen")
SITE = os.path.join(THU, "site")
DL = os.path.join(THU, "du_lieu")
P_DS = os.path.join(THU, "danh_sach.json")
P_CH = os.path.join(THU, "cau_hinh.json")
WRANGLER = (os.environ.get("NH_WRANGLER") or "npx --yes wrangler@3").split()   # có wrangler cài sẵn: NH_WRANGLER=wrangler


# ---------------------------------------------------------------- cấu hình, danh sách
def cau_hinh():
    try:
        c = json.load(open(P_CH, encoding="utf-8"))
    except Exception:
        c = {}
    c.setdefault("du_an", "thi-toan-vtl")
    c.setdefault("ten_mien", "")
    c.setdefault("script_url", "")
    return c


def luu_cau_hinh(c):
    os.makedirs(THU, exist_ok=True)
    cu = cau_hinh(); cu.update({k: v for k, v in c.items() if k in ("du_an", "ten_mien", "script_url")})
    cu["du_an"] = re.sub(r"[^a-z0-9-]+", "-", cu["du_an"].lower()).strip("-")[:58] or "thi-toan-vtl"
    json.dump(cu, open(P_CH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return cu


def danh_sach():
    try:
        return json.load(open(P_DS, encoding="utf-8"))
    except Exception:
        return []


def luu_ds(ds):
    os.makedirs(THU, exist_ok=True)
    json.dump(ds, open(P_DS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def goc_url(c=None):
    c = c or cau_hinh()
    return (c.get("ten_mien") or f"https://{c['du_an']}.pages.dev").rstrip("/")


def chuan_lop(s):
    """"10a1, 10A2 ;10a3" → "10A1,10A2,10A3" (trống = mọi lớp)."""
    return ",".join(dict.fromkeys(x.strip().upper() for x in re.split(r"[,;\s]+", s or "") if x.strip()))


def lam_slug(s):
    s = ten_khong_dau(s or "", 80).lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:60]
    return s or "de-thi"


# ---------------------------------------------------------------- vá bài kiểm tra cho chế độ đăng nhập
VA = [  # (tìm, thay) trong mã bài kiểm tra; thiếu một chỗ → không đăng (tránh lộ đáp án / hỏng chấm)
    ("correct=q.type==='mcq'?'ABCD'[q.answer]:", "correct=q.answer==null?'(thầy chưa công bố)':q.type==='mcq'?'ABCD'[q.answer]:"),
    ("latex(q.solution||'Chưa có lời giải.',q,'solution',false)",
     "latex(q.solution||(q.answer==null?'Thầy sẽ công bố lời giải sau khi kết thúc bài thi.':'Chưa có lời giải.'),q,'solution',false)"),
    ("$('loginForm').onsubmit=e=>{e.preventDefault();try{$('loginError').textContent='';enter();}catch(err){$('loginError').textContent=err.message;}};",
     "$('loginForm').onsubmit=async e=>{e.preventDefault();$('loginError').textContent='';try{const k=await __goi('bat-dau',{de:__DE});"
     "if(!k.ok){let m=k.loi||'Chưa được làm bài.';if(k.het){try{const r=await __goi('ket-qua?de='+encodeURIComponent(__DE));"
     "if(r.ds&&r.ds.length)m+=' Điểm các lần: '+r.ds.map(x=>'lần '+x.lan+': '+(x.cham?x.cham.score.toFixed(2).replace('.',','):'—')).join(' · ')+'.'}catch(_){}}"
     "$('loginError').textContent=m;return}if(k.thong_bao)notice(k.thong_bao);enter();}"
     "catch(err){$('loginError').textContent=err.message||'Lỗi mạng — thử lại.';}};"),
    ("function showResult(){",
     "function showResult(){const k=JSON.stringify(attempt.answers),at=attempt;if(at.daNopMayChu&&__CHAM[k])return __showResult0();"
     "__goi('nop',{de:__DE,answers:attempt.answers,chuyen_tab:attempt.tabSwitchCount||0,thoi_gian:Math.floor(examElapsed(attempt,attempt.submittedAt,limit)/1000)})"
     ".then(j=>{if(j.ok&&j.cham){__CHAM[k]=j.cham;at.daNopMayChu=true;save();}else notice(j.loi||'Máy chủ chưa nhận bài.');__showResult0();})"
     ".catch(()=>{notice('Chưa gửi được bài lên máy chủ — kiểm tra mạng rồi tải lại trang (bài vẫn được giữ trên máy).');__showResult0();});}\n function __showResult0(){"),
    ("function examGrade(", "function __examGrade0("),
]

JS_DANG_NHAP = r"""
const __DE=decodeURIComponent(location.pathname.split('/')[1]||''),__CHAM={};
async function __goi(duong,du_lieu){const r=await fetch('/api/'+duong,du_lieu?{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(du_lieu),credentials:'same-origin'}:{credentials:'same-origin'});if(r.status===401){location.href='/dang-nhap/?ve='+encodeURIComponent(location.pathname);throw Error('Cần đăng nhập lại.')}return r.json()}
function examGrade(d,answers){const c=__CHAM[JSON.stringify(answers)];if(c)return c;if(d.questions.every(q=>q.answer!=null))return __examGrade0(d,answers);
 return {score:0,parts:{mcq:0,tf:0,short:0},right:{mcq:0,tf:0,short:0},blank:0,rows:d.questions.map((q,i)=>({index:i,type:q.type,correct:0,answered:false,points:0,max:q.type==='mcq'?.25:q.type==='tf'?1:.5}))};}
async function __khoiDong(){
 try{const t=await __goi('toi');if(t.ok){const dat=(id,v)=>{const e=document.getElementById(id);if(e){e.value=v;e.readOnly=true;e.style.background='#f1f5f9'}};
  dat('studentClass',t.lop||'GV');dat('studentId',String(t.stt||t.tk));dat('studentName',t.ho_ten||t.tk);
  const m=document.querySelector('#login .muted');if(m)m.innerHTML='Đăng nhập: <b>'+(t.ho_ten||t.tk)+'</b> ('+t.tk+'). Bấm nút bên dưới để bắt đầu — số lượt làm do thầy quy định. <a href="/">Trang chính</a> · <a href="#" id="__thoat">Đăng xuất</a>';
  const th=document.getElementById('__thoat');if(th)th.onclick=async e=>{e.preventDefault();await __goi('dang-xuat',{});location.href='/dang-nhap/'}}}catch(e){}
 try{const k=await __goi('ket-qua?de='+encodeURIComponent(__DE));(k.ds||[]).forEach(x=>{if(x.cham)__CHAM[JSON.stringify(x.tra_loi)]=x.cham})}catch(e){}
}
"""
VA_ID = ("id=examFingerprint(d)", "id=(d.settings.studentExam&&d.settings.studentExam.examId)||examFingerprint(d)")
KHOI_DL = re.compile(r'(<script type="application/json" id="exam-data">)(.*?)(</script>)', re.S)


def _thay_ham(html, ten, moi):
    i = html.find("function " + ten + "(")
    if i < 0:
        raise RuntimeError(f"Bài kiểm tra không có hàm {ten} (phiên bản ứng dụng khác)")
    j = html.find("{", html.find(")", i)); muc = 0; k = j
    while k < len(html):
        if html[k] == "{":
            muc += 1
        elif html[k] == "}":
            muc -= 1
            if muc == 0:
                break
        k += 1
    return html[:i] + moi + html[k + 1:]


def ban_truc_tuyen(html, slug, an_dap_an=True):
    """HTML bài kiểm tra gốc → bản đăng mạng có đăng nhập: tự điền học sinh theo tài khoản, xin lượt ở máy chủ,
    nộp bài để MÁY CHỦ chấm. an_dap_an: bỏ hẳn đáp án + lời giải khỏi trang (trang không còn đáp án). Trả (html, số câu)."""
    m = KHOI_DL.search(html)
    if not m:
        raise RuntimeError("Không thấy dữ liệu đề (exam-data) trong bài kiểm tra")
    d = json.loads(m.group(2))
    d.setdefault("settings", {}).setdefault("studentExam", {})["examId"] = slug
    if VA_ID[0] in html:
        html = html.replace(VA_ID[0], VA_ID[1], 1)
    for a, b in VA:
        if a not in html:
            raise RuntimeError("Bài kiểm tra khác phiên bản (không tìm thấy: " + a[:40] + "…) — chưa đăng để tránh lỗi chấm/lộ đáp án.")
        html = html.replace(a, b, 1)
    if an_dap_an:
        for q in d["questions"]:
            q["answer"] = None
            q["solution"] = ""
            for k in [k for k in (q.get("figures") or {}) if k.startswith("solution:")]:
                del q["figures"][k]
    i = html.rfind("examRuntime();")
    html = html[:i] + JS_DANG_NHAP + "\n__khoiDong().then(()=>examRuntime());" + html[i + len("examRuntime();"):]
    for q in d["questions"]:
        for k in ("ma", "ma_dang", "ten_dang"):
            q.pop(k, None)
    nhung = json.dumps(d, ensure_ascii=False).replace("<", "\\u003c")
    m = KHOI_DL.search(html)
    html = html[:m.start(2)] + nhung + html[m.end(2):]
    html = html.replace("<head>", '<head><meta name="robots" content="noindex,nofollow">', 1)
    return html, len(d["questions"])


def khoa_dap_an(html_goc):
    """Đáp án để máy chủ chấm: [{type, answer}] theo đúng thứ tự câu."""
    d = json.loads(KHOI_DL.search(html_goc).group(2))
    return [{"type": q["type"], "answer": q["answer"]} for q in d["questions"]]


# ---------------------------------------------------------------- trang phụ
TRANG = """<!DOCTYPE html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>{tieu}</title><style>body{{margin:0;min-height:100vh;display:grid;place-items:center;
font:17px/1.6 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:#eef3f9;color:#1f2937}}.the{{background:#fff;border-radius:18px;
padding:34px 38px;max-width:520px;box-shadow:0 12px 40px rgba(30,58,138,.12);text-align:center}}h1{{font-size:22px;margin:0 0 8px;color:#1e3a8a}}
p{{margin:6px 0;color:#4b5563}}</style></head><body><div class="the"><h1>{tieu}</h1>{noi}</div></body></html>"""


KIEU = """<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow">
<style>body{margin:0;min-height:100vh;font:16px/1.55 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:#eef3f9;color:#1f2937}
.vo{max-width:560px;margin:0 auto;padding:7vh 16px}.the{background:#fff;border-radius:18px;padding:26px 28px;box-shadow:0 12px 40px rgba(30,58,138,.12)}
h1{font-size:22px;color:#1e3a8a;margin:0 0 4px}.phu{color:#6b7280;margin:0 0 16px;font-size:14px}label{display:block;font-weight:600;margin:10px 0 4px}
input{width:100%;box-sizing:border-box;padding:11px 12px;font-size:16px;border:1px solid #cbd5e1;border-radius:10px}
button{width:100%;margin-top:16px;padding:12px;font-size:16px;font-weight:700;border:0;border-radius:10px;background:#1e3a8a;color:#fff;cursor:pointer}
button:disabled{opacity:.6}.loi{color:#b91c1c;min-height:1.4em;margin:8px 0 0}a{color:#1d4ed8}
.de{display:flex;gap:10px;align-items:center;padding:12px 14px;border:1px solid #e5e7eb;border-radius:12px;margin:8px 0;text-decoration:none;color:#1f2937}
.de:hover{background:#f8fafc}.de b{flex:1}.nho{font-size:12.5px;color:#6b7280;white-space:nowrap}</style>"""

TRANG_DN = """<!DOCTYPE html><html lang="vi"><head>""" + KIEU + """<title>Đăng nhập — Toán thầy Lực</title></head><body><div class="vo"><div class="the">
<div id="dn"><h1>Đăng nhập</h1><p class="phu">Thầy Vũ Tiến Lực – Trường THPT Nguyễn Hữu Cảnh. Dùng tài khoản thầy cấp trên phiếu.</p>
<form id="f1"><label>Tên đăng nhập</label><input id="tk" autocomplete="username" autocapitalize="none" required>
<label>Mật khẩu</label><input id="mk" type="password" autocomplete="current-password" required><button>Đăng nhập</button><p class="loi" id="l1"></p></form></div>
<div id="dm" hidden><h1>Đổi mật khẩu</h1><p class="phu">Lần đầu đăng nhập: em đặt mật khẩu riêng (ít nhất 6 ký tự) và ghi nhớ. Quên thì báo thầy đặt lại.</p>
<form id="f2"><label>Mật khẩu hiện tại (trên phiếu)</label><input id="cu" type="password" autocomplete="current-password" required>
<label>Mật khẩu mới</label><input id="moi" type="password" autocomplete="new-password" minlength="6" required>
<label>Nhập lại mật khẩu mới</label><input id="moi2" type="password" autocomplete="new-password" minlength="6" required><button>Lưu mật khẩu</button><p class="loi" id="l2"></p></form></div>
</div></div><script>
const q=new URLSearchParams(location.search),ve=(q.get('ve')||'/').startsWith('/')?(q.get('ve')||'/'):'/',$=id=>document.getElementById(id);
const goi=(d,b)=>fetch('/api/'+d,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(b),credentials:'same-origin'}).then(r=>r.json());
function doiMk(){$('dn').hidden=true;$('dm').hidden=false;if($('mk').value)$('cu').value=$('mk').value;$('moi').focus()}
if(q.get('doi'))doiMk();
$('f1').onsubmit=async e=>{e.preventDefault();const b=e.submitter||e.target.querySelector('button');b.disabled=true;$('l1').textContent='';
 try{const r=await goi('dang-nhap',{tk:$('tk').value.trim(),mk:$('mk').value});if(!r.ok){$('l1').textContent=r.loi;return}
  if(r.doi_mk)return doiMk();location.href=ve}catch(x){$('l1').textContent='Lỗi mạng — thử lại.'}finally{b.disabled=false}};
$('f2').onsubmit=async e=>{e.preventDefault();$('l2').textContent='';if($('moi').value!==$('moi2').value){$('l2').textContent='Hai lần nhập mật khẩu mới chưa khớp.';return}
 const r=await goi('doi-mk',{cu:$('cu').value,moi:$('moi').value});if(!r.ok){$('l2').textContent=r.loi;return}location.href=ve};
</script></body></html>"""

TRANG_CHU = """<!DOCTYPE html><html lang="vi"><head>""" + KIEU + """<title>Toán — thầy Vũ Tiến Lực</title></head><body><div class="vo"><div class="the">
<h1>Trang học Toán</h1><p class="phu">Thầy Vũ Tiến Lực – Trường THPT Nguyễn Hữu Cảnh</p><div id="nd">Đang tải…</div></div></div><script>
const LOP=__LOP__,nd=document.getElementById('nd'),e=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
fetch('/api/toi',{credentials:'same-origin'}).then(r=>r.json()).then(t=>{
 if(!t.ok){nd.innerHTML='<p>Học sinh đăng nhập bằng tài khoản thầy cấp để làm bài kiểm tra.</p><a href="/dang-nhap/"><button>Đăng nhập</button></a>';return}
 if(t.doi_mk){location.href='/dang-nhap/?doi=1';return}
 let h='<p>Xin chào <b>'+e(t.ho_ten||t.tk)+'</b>'+(t.lop?' — lớp '+e(t.lop):'')+' · <a href="#" id="thoat">Đăng xuất</a></p>';
 if(t.vai==='gv'){h+='<h3>Bài giảng</h3>'+(LOP.length?LOP.map(l=>'<a class="de" href="/toan'+l+'/"><b>Toán '+l+'</b><span class="nho">mục lục</span></a>').join(''):'<p class="phu">Chưa có bài giảng.</p>')}
 else{h+='<h3>Bài kiểm tra của em</h3>'+((t.de||[]).length?t.de.map(x=>'<a class="de" href="/'+e(x.slug)+'/"><b>'+e(x.ten)+'</b><span class="nho">'+
  (x.da_lam?'Đã làm '+x.da_lam+' lần'+(x.cao_nhat!=null?' · cao nhất '+Number(x.cao_nhat).toFixed(2).replace('.',','):''):'Chưa làm')+(x.con_lai!=null?' · còn '+x.con_lai+' lượt':'')+(x.cong_bo?' · có lời giải':'')+'</span></a>').join(''):'<p class="phu">Hiện chưa có bài kiểm tra nào cho lớp em.</p>')}
 nd.innerHTML=h;document.getElementById('thoat').onclick=async ev=>{ev.preventDefault();await fetch('/api/dang-xuat',{method:'POST'});location.href='/dang-nhap/'};
}).catch(()=>{nd.innerHTML='<p>Không kết nối được máy chủ.</p>'});
</script></body></html>"""


def trang_chu():
    lop = sorted({int(x["lop"]) for x in danh_sach() if x.get("loai") == "bai_giang" and x.get("trang_thai") == "hien" and x.get("lop")})
    return TRANG_CHU.replace("__LOP__", json.dumps(lop))


def trang_dong(ten):
    return TRANG.format(tieu=ten.replace("<", "&lt;"), noi="<p><b>Bài thi đã đóng.</b></p><p>Liên hệ thầy nếu em cần làm lại.</p>")


def ghi_site():
    os.makedirs(SITE, exist_ok=True)
    open(os.path.join(SITE, "index.html"), "w", encoding="utf-8").write(trang_chu())
    _dat_trang("dang-nhap", TRANG_DN)
    open(os.path.join(SITE, "_headers"), "w", encoding="utf-8").write(
        "/*\n  X-Robots-Tag: noindex, nofollow\n  Cache-Control: no-cache\n")
    open(os.path.join(SITE, "404.html"), "w", encoding="utf-8").write(
        TRANG.format(tieu="Không có đề này", noi="<p>Kiểm tra lại đường link thầy gửi.</p>"))


def _dat_trang(slug, noi_dung):
    d = os.path.join(SITE, slug); os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(noi_dung)


# ---------------------------------------------------------------- tạo / đổi trạng thái
def them_de(slug, ten, html_goc, an_dap_an=True, phut=None, ghi_de=False, lop_giao="", so_luot=2):
    slug = lam_slug(slug or ten)
    ds = danh_sach()
    if not ghi_de:
        goc, n = slug, 2
        while any(x["slug"] == slug and x.get("loai") != "bai_giang" for x in ds):
            slug = f"{goc}-{n}"; n += 1
        # đổi examId theo slug mới (bản gốc)
    os.makedirs(DL, exist_ok=True)
    m = KHOI_DL.search(html_goc)
    if m:
        d = json.loads(m.group(2)); d.setdefault("settings", {}).setdefault("studentExam", {})["examId"] = slug
        html_goc = html_goc[:m.start(2)] + json.dumps(d, ensure_ascii=False).replace("<", "\\u003c") + html_goc[m.end(2):]
    open(os.path.join(DL, slug + ".goc.html"), "w", encoding="utf-8").write(html_goc)
    html, so = ban_truc_tuyen(html_goc, slug, an_dap_an)
    ghi_site(); _dat_trang(slug, html)
    ds = [x for x in ds if x["slug"] != slug or x.get("loai") == "bai_giang"]
    ds.insert(0, {"slug": slug, "ten": ten, "tao_luc": datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
                  "trang_thai": "dang_mo" if an_dap_an else "da_cong_bo", "so_cau": so, "phut": phut,
                  "lop_giao": chuan_lop(lop_giao), "so_luot": int(so_luot)})
    luu_ds(ds)
    return slug


TRANG_NHOM = """<!DOCTYPE html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>{tieu}</title></head><body style="font:17px system-ui;text-align:center;padding-top:30vh;color:#1e3a8a">
Đang mở đề…<script>(function(){{var ds={ds},k='nhom-de:{slug}',m=null;try{{m=localStorage.getItem(k)}}catch(e){{}}
if(ds.indexOf(m)<0){{m=ds[Math.floor(Math.random()*ds.length)];try{{localStorage.setItem(k,m)}}catch(e){{}}}}
location.replace('../'+m+'/');}})();</script></body></html>"""


def trang_nhom(slug, ten, cac_con):
    """Link chung: mỗi học sinh được chia ngẫu nhiên 1 mã đề (nhớ trên máy em đó, tải lại không đổi mã)."""
    return TRANG_NHOM.format(tieu=ten.replace("<", "&lt;"), ds=json.dumps(cac_con), slug=slug)


def them_nhom(slug, ten, cac_con, lop_giao="", so_luot=2):
    slug = lam_slug(slug or ten)
    ds = danh_sach(); goc, n = slug, 2
    while any(x["slug"] == slug and x.get("loai") != "bai_giang" for x in ds):
        slug = f"{goc}-{n}"; n += 1
    ghi_site(); _dat_trang(slug, trang_nhom(slug, ten, cac_con))
    for x in ds:
        if x["slug"] in cac_con:
            x["nhom"] = slug
    ds.insert(0, {"slug": slug, "ten": ten, "tao_luc": datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
                  "trang_thai": "dang_mo", "loai": "nhom", "con": cac_con, "so_cau": len(cac_con),
                  "lop_giao": chuan_lop(lop_giao), "so_luot": int(so_luot)})
    luu_ds(ds)
    return slug


def doi_trang_thai(slug, tt):
    x = next((y for y in danh_sach() if y["slug"] == slug and y.get("loai") != "bai_giang"), None)
    if x and x.get("loai") == "nhom":      # link chung: áp cho mọi mã đề con
        for con in x.get("con", []):
            if any(y["slug"] == con and y.get("loai") != "bai_giang" for y in danh_sach()):
                _doi_1(con, tt)
        if tt == "xoa":
            shutil.rmtree(os.path.join(SITE, slug), ignore_errors=True)
            luu_ds([y for y in danh_sach() if y["slug"] != slug or y.get("loai") == "bai_giang"]); return
        ds = danh_sach(); g = next(y for y in ds if y["slug"] == slug and y.get("loai") != "bai_giang")
        _dat_trang(slug, trang_dong(g["ten"]) if tt == "da_dong" else trang_nhom(slug, g["ten"], g["con"]))
        g["trang_thai"] = tt; luu_ds(ds); return
    _doi_1(slug, tt)


def _doi_1(slug, tt):
    """tt: dang_mo (ẩn đáp án) | da_cong_bo (có đáp án + lời giải) | da_dong | xoa"""
    ds = danh_sach(); x = next((y for y in ds if y["slug"] == slug and y.get("loai") != "bai_giang"), None)
    if not x:
        raise RuntimeError("Không có đề " + slug)
    p_goc = os.path.join(DL, slug + ".goc.html")
    ghi_site()
    if tt == "xoa":
        shutil.rmtree(os.path.join(SITE, slug), ignore_errors=True)
        cu = os.path.join(DL, "_da_xoa"); os.makedirs(cu, exist_ok=True)
        if os.path.exists(p_goc):
            shutil.move(p_goc, os.path.join(cu, slug + ".goc.html"))
        luu_ds([y for y in ds if y["slug"] != slug or y.get("loai") == "bai_giang"]); return
    if tt == "da_dong":
        _dat_trang(slug, trang_dong(x["ten"]))
    else:
        goc = open(p_goc, encoding="utf-8").read()
        _dat_trang(slug, ban_truc_tuyen(goc, slug, tt == "dang_mo")[0])
    x["trang_thai"] = tt; luu_ds(ds)


# ---------------------------------------------------------------- BÀI GIẢNG (HTML trình chiếu, PDF) + mục lục theo lớp
GIOI_HAN = 25 * 1024 * 1024          # Cloudflare Pages: tối đa 25 MiB mỗi file
AN = os.path.join(THU, "an")          # bài giảng đang ẩn (gỡ khỏi mạng, giữ file để hiện lại)

TRANG_PDF = """<!DOCTYPE html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>{tieu}</title><style>body{{margin:0;font:16px system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:#eef3f9;color:#1f2937}}
header{{display:flex;gap:10px;align-items:center;flex-wrap:wrap;padding:10px 16px;background:#1e3a8a;color:#fff}}header h1{{font-size:17px;margin:0;flex:1}}
header a{{color:#1e3a8a;background:#fff;border-radius:8px;padding:6px 12px;text-decoration:none;font-weight:600;font-size:14px}}
iframe{{border:0;width:100%;height:calc(100vh - 56px);display:block;background:#525659}}</style></head><body>
<header><h1>{tieu}</h1><a href="{lop_url}">☰ Mục lục</a><a href="bai-giang.pdf" target="_blank">Mở toàn màn hình</a><a href="bai-giang.pdf" download>Tải PDF</a></header>
<iframe src="bai-giang.pdf#view=FitH" title="{tieu}"></iframe></body></html>"""

TRANG_LOP = """<!DOCTYPE html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>Bài giảng Toán {lop}</title><style>body{{margin:0;font:16px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:#eef3f9;color:#1f2937}}
.vo{{max-width:820px;margin:0 auto;padding:26px 16px}}h1{{color:#1e3a8a;margin:0 0 2px;font-size:26px}}.phu{{color:#6b7280;margin:0 0 18px}}
a.bai{{display:flex;gap:12px;align-items:center;background:#fff;border-radius:12px;padding:13px 16px;margin:8px 0;text-decoration:none;color:#1f2937;box-shadow:0 2px 10px rgba(30,58,138,.07)}}
a.bai:hover{{box-shadow:0 4px 18px rgba(30,58,138,.16)}}.nhan{{font-size:12px;font-weight:700;border-radius:7px;padding:3px 8px;white-space:nowrap}}
.html{{background:#dbeafe;color:#1e40af}}.pdf{{background:#fee2e2;color:#991b1b}}.ten{{flex:1;font-weight:600}}.ngay{{color:#9ca3af;font-size:12.5px;white-space:nowrap}}
</style></head><body><div class="vo"><h1>Bài giảng Toán {lop}</h1><p class="phu">Thầy Vũ Tiến Lực – Trường THPT Nguyễn Hữu Cảnh</p>{ds}</div></body></html>"""


def _lop_slug(lop):
    return f"toan{int(lop)}"


def ghi_muc_luc():
    """Viết lại trang mục lục mọi lớp có bài giảng: /toan10/, /toan11/…"""
    ds = danh_sach()
    cac_lop = sorted({int(x["lop"]) for x in ds if x.get("loai") == "bai_giang" and x.get("lop")})
    for lop in cac_lop:
        bg = [x for x in ds if x.get("loai") == "bai_giang" and int(x.get("lop") or 0) == lop and x.get("trang_thai") == "hien"]
        dong = "".join(
            f'<a class="bai" href="../bai-giang/{x["slug"]}/"><span class="nhan {x["kieu"]}">{"Trình chiếu" if x["kieu"] == "html" else "PDF"}</span>'
            f'<span class="ten">{x["ten"].replace("<", "&lt;")}</span><span class="ngay">{x["tao_luc"][:10]}</span></a>' for x in bg) \
            or '<p class="phu">Chưa có bài giảng.</p>'
        _dat_trang(_lop_slug(lop), TRANG_LOP.format(lop=lop, ds=dong))
    open(os.path.join(SITE, "index.html"), "w", encoding="utf-8").write(trang_chu())


def them_bai_giang(slug, ten, lop, kieu, du_lieu, ghi_de=False, nguon=""):
    """kieu: html | pdf; du_lieu: bytes. Trả slug."""
    if kieu not in ("html", "pdf"):
        raise RuntimeError("Chỉ nhận bài giảng HTML hoặc PDF.")
    if len(du_lieu) > GIOI_HAN:
        raise RuntimeError(f"File {len(du_lieu) / 1048576:.1f} MB — Cloudflare Pages chỉ nhận tối đa 25 MB mỗi file.")
    slug = lam_slug(slug or ten)
    ds = danh_sach()
    if not ghi_de:
        goc, n = slug, 2
        while any(x["slug"] == slug and x.get("loai") == "bai_giang" for x in ds):
            slug = f"{goc}-{n}"; n += 1
    ghi_site()
    d = os.path.join(SITE, "bai-giang", slug)
    shutil.rmtree(d, ignore_errors=True); shutil.rmtree(os.path.join(AN, slug), ignore_errors=True)
    os.makedirs(d, exist_ok=True)
    if kieu == "html":
        t = du_lieu.decode("utf-8", "ignore")
        if "noindex" not in t:
            t = re.sub(r"<head([^>]*)>", r'<head\1><meta name="robots" content="noindex,nofollow">', t, count=1)
        open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(t)
    else:
        open(os.path.join(d, "bai-giang.pdf"), "wb").write(du_lieu)
        open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(
            TRANG_PDF.format(tieu=ten.replace("<", "&lt;"), lop_url=f"../../{_lop_slug(lop)}/"))
    cu = next((x for x in ds if x["slug"] == slug and x.get("loai") == "bai_giang"), None)
    ds = [x for x in ds if not (x["slug"] == slug and x.get("loai") == "bai_giang")]
    ds.insert(0, {"slug": slug, "ten": ten, "loai": "bai_giang", "lop": int(lop), "kieu": kieu, "trang_thai": "hien",
                  "tao_luc": (cu or {}).get("tao_luc") or datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
                  "cap_nhat": datetime.datetime.now().strftime("%d/%m/%Y %H:%M"), "nguon": nguon,
                  "kb": round(len(du_lieu) / 1024)})
    luu_ds(ds); ghi_muc_luc()
    return slug


def doi_bai_giang(slug, tt):
    """tt: hien | an | xoa"""
    ds = danh_sach(); x = next((y for y in ds if y["slug"] == slug and y.get("loai") == "bai_giang"), None)
    if not x:
        raise RuntimeError("Không có bài giảng " + slug)
    tren = os.path.join(SITE, "bai-giang", slug); cat = os.path.join(AN, slug)
    if tt in ("an", "xoa") and os.path.isdir(tren):
        shutil.rmtree(cat, ignore_errors=True); os.makedirs(AN, exist_ok=True); shutil.move(tren, cat)
    if tt == "hien" and os.path.isdir(cat):
        shutil.rmtree(tren, ignore_errors=True); os.makedirs(os.path.dirname(tren), exist_ok=True); shutil.move(cat, tren)
    if tt == "an":
        _dat_trang(os.path.join("bai-giang", slug), TRANG.format(tieu=x["ten"].replace("<", "&lt;"), noi="<p>Bài giảng đang tạm ẩn.</p>"))
    if tt == "xoa":
        xo = os.path.join(THU, "da_xoa"); os.makedirs(xo, exist_ok=True)
        if os.path.isdir(cat):
            shutil.rmtree(os.path.join(xo, slug), ignore_errors=True); shutil.move(cat, os.path.join(xo, slug))
        ds = [y for y in ds if y is not x]
    else:
        x["trang_thai"] = tt
    luu_ds(ds); ghi_site(); ghi_muc_luc()


def nguon_ung_dung(gioi_han=400):
    """File đã xuất từ ứng dụng (de-da-ra/): PDF + bài trình chiếu JSON (đổi sang HTML trình chiếu)."""
    goc = os.path.join(GOC, "de-da-ra"); ra = []
    for r, _, fs in os.walk(goc):
        if "/tex" in r.replace("\\", "/") or os.path.basename(r).startswith("_"):
            continue
        for f in fs:
            e = f.lower().rsplit(".", 1)[-1]
            if e == "pdf" or (e == "json" and os.path.basename(r) == "TrinhChieu"):
                p = os.path.join(r, f); st = os.stat(p)
                ra.append({"duong_dan": os.path.relpath(p, GOC), "ten": f, "thu_muc": os.path.relpath(r, goc),
                           "kieu": "pdf" if e == "pdf" else "json", "kb": round(st.st_size / 1024), "luc": st.st_mtime})
    ra.sort(key=lambda x: -x["luc"])
    for x in ra:
        x["luc"] = datetime.datetime.fromtimestamp(x["luc"]).strftime("%d/%m/%Y %H:%M")
    return ra[:gioi_han]


def doc_nguon(duong_dan):
    p = os.path.realpath(os.path.join(GOC, duong_dan))
    if not p.startswith(os.path.realpath(os.path.join(GOC, "de-da-ra")) + os.sep):
        raise RuntimeError("Chỉ lấy file trong de-da-ra/")
    return open(p, "rb").read()


# ---------------------------------------------------------------- đăng lên Cloudflare Pages
def _env():
    e = dict(os.environ)
    them = ["/opt/homebrew/bin", "/usr/local/bin", os.path.expanduser("~/.volta/bin"), os.path.expanduser("~/.nvm/current/bin")]
    nvm = os.path.expanduser("~/.nvm/versions/node")
    if os.path.isdir(nvm):
        them += [os.path.join(nvm, v, "bin") for v in sorted(os.listdir(nvm))[-1:]]
    e["PATH"] = os.pathsep.join([p for p in them if os.path.isdir(p)] + [e.get("PATH", "")])
    e["WRANGLER_SEND_METRICS"] = "false"; e["CI"] = e.get("CI", "")
    return e


def _chay(lenh, in_ra, timeout=600):
    p = subprocess.Popen(WRANGLER + lenh, cwd=THU, env=_env(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, errors="ignore")
    ra, t0 = [], time.time()
    for dong in p.stdout:
        dong = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", dong.rstrip())
        if dong.strip():
            ra.append(dong)
            if not re.match(r"^[\s⠁-⣿]*$", dong):
                in_ra("   " + dong[:160])
        if time.time() - t0 > timeout:
            p.kill(); break
    p.wait()
    return p.returncode, "\n".join(ra)


def co_node():
    return bool(shutil.which(WRANGLER[0], path=_env()["PATH"]))


MAY_CHU = os.path.join(os.path.dirname(os.path.abspath(__file__)), "may_chu")   # mã máy chủ (Functions + schema)
P_BM = os.path.join(THU, "bi_mat.json")       # mã quản trị + khoá phiên (KHÔNG đồng bộ GitHub)
TEN_DB = "thi-toan-db"
PHIEN_BAN_SCHEMA = 1


def _luu_ch(c):
    json.dump(c, open(P_CH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def bi_mat(tao=False):
    try:
        b = json.load(open(P_BM, encoding="utf-8"))
    except Exception:
        b = {}
    if tao or not b.get("admin"):
        b = {"admin": secrets.token_urlsafe(32), "phien": secrets.token_urlsafe(32), "chua_dat": True}
        os.makedirs(THU, exist_ok=True); json.dump(b, open(P_BM, "w"), indent=1)
    return b


def _chep_may_chu():
    """Chép functions/ + schema.sql + wrangler.toml vào thi-truc-tuyen/ (thư mục chạy wrangler)."""
    c = cau_hinh()
    shutil.rmtree(os.path.join(THU, "functions"), ignore_errors=True)
    shutil.copytree(os.path.join(MAY_CHU, "functions"), os.path.join(THU, "functions"))
    shutil.copy(os.path.join(MAY_CHU, "schema.sql"), os.path.join(THU, "schema.sql"))
    toml = (f'name = "{c["du_an"]}"\npages_build_output_dir = "./site"\ncompatibility_date = "2024-09-23"\n\n'
            f'[[d1_databases]]\nbinding = "DB"\ndatabase_name = "{TEN_DB}"\ndatabase_id = "{c.get("d1_id") or "chua-co"}"\n')
    open(os.path.join(THU, "wrangler.toml"), "w", encoding="utf-8").write(toml)


def _dat_bi_mat(c, in_ra):
    b = bi_mat()
    for ten, gt in (("ADMIN_TOKEN", b["admin"]), ("SESSION_SECRET", b["phien"])):
        p = subprocess.run(WRANGLER + ["pages", "secret", "put", ten, "--project-name", c["du_an"]], cwd=THU, env=_env(),
                           input=gt + "\n", capture_output=True, text=True, errors="ignore", timeout=180)
        if p.returncode != 0:
            raise RuntimeError(f"Chưa đặt được khoá {ten}: {(p.stdout + p.stderr)[-300:]}")
    b.pop("chua_dat", None); json.dump(b, open(P_BM, "w"), indent=1)
    in_ra("   đã đặt mã quản trị và khoá phiên đăng nhập trên Cloudflare")


def chuan_bi_may_chu(c, in_ra):
    """Lần đầu: tạo cơ sở dữ liệu D1, bảng, khoá bí mật. Các lần sau bỏ qua phần đã có."""
    if not c.get("d1_id"):
        in_ra(f"Tạo cơ sở dữ liệu tài khoản/điểm \"{TEN_DB}\" (chỉ lần đầu)…")
        rc, ra = _chay(["d1", "create", TEN_DB], in_ra, 180)
        m = re.search(r'database_id\s*=\s*"([0-9a-f-]{36})"', ra) or re.search(r'"database_id"\s*:\s*"([0-9a-f-]{36})"', ra)
        if not m:
            rc, ra = _chay(["d1", "list", "--json"], lambda *_: None, 120)
            try:
                for x in json.loads(ra[ra.find("["):ra.rfind("]") + 1]):
                    if x.get("name") == TEN_DB:
                        m = re.match(r"(.*)", x.get("uuid") or x.get("database_id") or "")
            except Exception:
                pass
        if not m or not m.group(1):
            raise RuntimeError("Chưa tạo được cơ sở dữ liệu D1 (xem nhật ký).")
        c["d1_id"] = m.group(1); _luu_ch(c)
    _chep_may_chu()
    if c.get("schema") != PHIEN_BAN_SCHEMA:
        in_ra("Tạo bảng tài khoản, đề, bài làm…")
        rc, ra = _chay(["d1", "execute", TEN_DB, "--remote", "--file", "schema.sql", "--yes"], in_ra, 240)
        if rc != 0:
            raise RuntimeError("Chưa tạo được bảng dữ liệu (xem nhật ký).")
        c["schema"] = PHIEN_BAN_SCHEMA; _luu_ch(c)
    if bi_mat().get("chua_dat"):
        _dat_bi_mat(c, in_ra)


def goi(duong, du_lieu=None, lan=0):
    """Gọi API quản trị trên trang (x-admin)."""
    if not cau_hinh().get("d1_id"):
        return {"ok": False, "chua_dung": True,
                "loi": "Trang trên Cloudflare chưa được dựng. Bấm \"Dựng trang lần đầu\" (hoặc \"Đăng lại tất cả\") — máy sẽ mở trình duyệt để thầy đăng nhập Cloudflare."}
    url = goc_url() + "/api/admin/" + duong
    req = urllib.request.Request(url, data=json.dumps(du_lieu or {}).encode(), method="POST",
                                 headers={"content-type": "application/json", "x-admin": bi_mat()["admin"],
                                          "user-agent": "NganHangCaNhan"})
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            k = json.loads(e.read().decode())
        except Exception:
            k = {"ok": False, "loi": f"HTTP {e.code}"}
        if e.code == 403 and lan == 0:
            k["loi"] = ("Mã quản trị trên máy này khác mã trên Cloudflare (đã đăng từ máy khác?). "
                        "Bấm \"Đăng lại tất cả\" để đặt lại mã rồi thử lại.")
            bi_mat(tao=True)
        return k
    except Exception as e:
        return {"ok": False, "loi": f"Chưa kết nối được trang {goc_url()} ({getattr(e, 'reason', e)}). Kiểm tra mạng; nếu vừa đăng lần đầu thì đợi 1–2 phút rồi thử lại."}


def dong_bo_de(in_ra=print):
    """Đẩy danh sách đề (lớp được giao, số lượt, nhóm mã, ĐÁP ÁN) lên cơ sở dữ liệu để máy chủ chấm."""
    ds = [x for x in danh_sach() if x.get("loai") != "bai_giang"]
    loi = 0
    for x in ds:
        g = {"slug": x["slug"], "ten": x["ten"], "lop": x.get("lop_giao", ""), "so_luot": int(x.get("so_luot", 2)),
             "nhom": x.get("nhom", ""), "trang_thai": x.get("trang_thai", "dang_mo")}
        if x.get("loai") == "nhom":
            g["con"] = x.get("con", [])
        else:
            p = os.path.join(DL, x["slug"] + ".goc.html")
            if os.path.exists(p):
                g["khoa"] = khoa_dap_an(open(p, encoding="utf-8").read())
        k = goi("de/luu", g)
        if not k.get("ok"):
            loi += 1; in_ra(f"   ✗ đề {x['slug']}: {k.get('loi')}")
    in_ra(f"   đồng bộ {len(ds) - loi}/{len(ds)} đề lên máy chủ chấm")
    return loi == 0


# ---------------------------------------------------------------- tài khoản học sinh / giáo viên
P_MK = os.path.join(THU, "mat_khau_dau.json")   # mật khẩu lần đầu để in phiếu (KHÔNG đồng bộ GitHub)


def _mk_dau():
    try:
        return json.load(open(P_MK, encoding="utf-8"))
    except Exception:
        return {}


def _luu_mk_dau(m):
    os.makedirs(THU, exist_ok=True); json.dump(m, open(P_MK, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def mk_moi():
    return "".join(str(secrets.randbelow(10)) for _ in range(6))


def ten_tk(lop, stt):
    return f"{re.sub(r'[^a-z0-9]', '', ten_khong_dau(lop, 20).lower())}-{int(stt):02d}"


def doc_danh_sach_hs(van_ban, lop_mac_dinh=""):
    """Dán từ Excel: "Lớp  STT  Họ tên" hoặc "STT  Họ tên" (lớp lấy ô Lớp). Bỏ dòng tiêu đề/trống."""
    ra, loi = [], []
    for i, dong in enumerate((van_ban or "").splitlines(), 1):
        o = [x.strip() for x in re.split(r"\t|;|\s{2,}", dong.strip()) if x.strip()]
        if not o:
            continue
        if len(o) >= 3 and re.fullmatch(r"\d{1,2}[A-Za-zĐđ]\w*", o[0]) and o[1].isdigit():
            lop, stt, ten = o[0], o[1], " ".join(o[2:])
        elif len(o) >= 2 and o[0].isdigit():
            lop, stt, ten = lop_mac_dinh, o[0], " ".join(o[1:])
        else:
            if i > 1 or not re.search(r"(?i)stt|họ|ten|lớp", dong):
                loi.append(f"dòng {i}: {dong[:40]}")
            continue
        if not lop:
            loi.append(f"dòng {i}: thiếu lớp"); continue
        ra.append({"ten": ten_tk(lop, stt), "ho_ten": re.sub(r"\s+", " ", ten), "lop": lop.strip().upper(), "stt": int(stt), "vai": "hs"})
    return ra, loi


def nhap_hs(van_ban, lop_mac_dinh=""):
    ds, loi = doc_danh_sach_hs(van_ban, lop_mac_dinh)
    if not ds:
        return {"ok": False, "loi": "Không đọc được dòng nào (cần: STT ⇥ Họ tên, hoặc Lớp ⇥ STT ⇥ Họ tên).", "dong_loi": loi}
    co = {x["ten"] for x in (goi("tk/ds").get("ds") or [])}
    mk = _mk_dau()
    for x in ds:
        if x["ten"] not in co:            # tài khoản mới → mật khẩu lần đầu; có rồi → chỉ cập nhật tên/lớp
            x["mk"] = mk[x["ten"]] = mk_moi()
    k = goi("tk/nhap", {"ds": ds})
    if not k.get("ok"):
        return k
    _luu_mk_dau(mk)
    return {"ok": True, "moi": sum(1 for x in ds if x.get("mk")), "cap_nhat": sum(1 for x in ds if not x.get("mk")), "dong_loi": loi}


def dat_lai_mk(ten):
    mk = mk_moi()
    t = next((x for x in (goi("tk/ds").get("ds") or []) if x["ten"] == ten), None)
    if not t:
        return {"ok": False, "loi": "Không có tài khoản " + ten}
    k = goi("tk/nhap", {"ds": [{**t, "mk": mk}]})
    if k.get("ok"):
        m = _mk_dau(); m[ten] = mk; _luu_mk_dau(m)
        return {"ok": True, "mk": mk}
    return k


def them_gv(ten, ho_ten, mk):
    ten = re.sub(r"[^a-z0-9._-]", "", (ten or "").lower())
    if not ten or len(mk or "") < 6:
        return {"ok": False, "loi": "Tên đăng nhập (chữ thường, số) và mật khẩu ít nhất 6 ký tự."}
    k = goi("tk/nhap", {"ds": [{"ten": ten, "ho_ten": ho_ten or ten, "lop": "", "stt": 0, "vai": "gv", "mk": mk}]})
    return k


PHIEU = """<!DOCTYPE html><html lang="vi"><head><meta charset="utf-8"><title>Phiếu tài khoản</title><style>
@page{{size:A4;margin:10mm}}body{{font:13px/1.45 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:0}}
.luoi{{display:grid;grid-template-columns:1fr 1fr;gap:0}}.p{{border:1px dashed #94a3b8;padding:10px 12px;break-inside:avoid;height:46mm;box-sizing:border-box}}
.p h3{{margin:0 0 4px;font-size:13.5px;color:#1e3a8a}}.p .u{{font-size:11.5px;color:#475569;word-break:break-all}}
.p b.k{{font:700 15px ui-monospace,Menlo,monospace;letter-spacing:.5px}}.p .g{{font-size:11px;color:#64748b;margin-top:4px}}
.nut{{position:fixed;top:8px;right:8px}}@media print{{.nut{{display:none}}}}</style></head><body>
<button class="nut" onclick="print()">In phiếu</button><div class="luoi">{the}</div></body></html>"""


def phieu_tai_khoan(lop=""):
    ds = goi("tk/ds").get("ds") or []
    mk = _mk_dau(); url = goc_url()
    the = []
    for x in ds:
        if x["vai"] != "hs" or (lop and x["lop"].upper() != lop.upper()):
            continue
        m = mk.get(x["ten"]) if x.get("doi_mk") else None
        dong_mk = (f'<div>Mật khẩu lần đầu: <b class="k">{m}</b></div>' if m
                   else '<div>Mật khẩu: <i>em đã tự đổi — quên thì báo thầy đặt lại</i></div>')
        the.append(f'<div class="p"><h3>Trang học Toán — thầy Vũ Tiến Lực</h3><div class="u">{url}</div>'
                   f'<div>Lớp <b>{x["lop"]}</b> · STT <b>{x["stt"]}</b> · {x["ho_ten"]}</div>'
                   f'<div>Tên đăng nhập: <b class="k">{x["ten"]}</b></div>' + dong_mk +
                   '<div class="g">Lần đầu đăng nhập máy sẽ yêu cầu đổi mật khẩu. Không cho bạn khác mượn tài khoản.</div></div>')
    return PHIEU.format(the="".join(the) or "<p>Chưa có tài khoản học sinh.</p>")


def dang(in_ra=print):
    if not co_node():
        raise RuntimeError("Máy chưa có Node.js (lệnh npx). Cài bản LTS ở https://nodejs.org rồi bấm Đăng lại.")
    c = cau_hinh(); ghi_site(); ghi_muc_luc()
    in_ra("Kiểm tra đăng nhập Cloudflare…")
    rc, ra = _chay(["whoami"], lambda *_: None, 120)
    if rc != 0 or "not authenticated" in ra.lower() or "You are not" in ra:
        in_ra("Chưa đăng nhập → trình duyệt sẽ mở trang Cloudflare: thầy đăng nhập rồi bấm Allow (cho phép).")
        rc, ra = _chay(["login"], in_ra, 300)
        if rc != 0:
            raise RuntimeError("Đăng nhập Cloudflare chưa xong. Bấm Đăng lại để thử lần nữa.")
    if not c.get("da_tao_du_an"):
        in_ra(f"Tạo dự án Cloudflare Pages \"{c['du_an']}\" (chỉ lần đầu)…")
        rc, ra = _chay(["pages", "project", "create", c["du_an"], "--production-branch", "main"], in_ra, 180)
        m = re.search(r"https://[a-z0-9-]+\.pages\.dev", ra)
        if rc == 0 or "already exists" in ra.lower():
            c["da_tao_du_an"] = True
            if m and not c.get("ten_mien"):
                c["ten_mien"] = m.group(0)
            _luu_ch(c)
        else:
            raise RuntimeError("Chưa tạo được dự án Cloudflare Pages (xem nhật ký). Có thể đổi tên dự án khác rồi thử lại.")
    chuan_bi_may_chu(c, in_ra)
    in_ra("Đang đưa trang lên Cloudflare Pages…")
    rc, ra = _chay(["pages", "deploy", SITE, "--project-name", c["du_an"], "--branch", "main", "--commit-dirty=true"], in_ra, 600)
    if rc != 0:
        raise RuntimeError("Đăng chưa thành công (xem nhật ký phía trên).")
    m = re.search(r"https://[a-z0-9]+\.([a-z0-9-]+)\.pages\.dev", ra)
    if m and not c.get("ten_mien"):
        c["ten_mien"] = f"https://{m.group(1)}.pages.dev"; _luu_ch(c)
    for lan in range(6):                      # trang mới cần vài giây để chạy
        time.sleep(3 if lan else 5)
        if goi("ping").get("ok"):
            break
    else:
        in_ra("   ⚠ máy chủ chưa trả lời — đợi 1 phút rồi bấm \"Đăng lại tất cả\" để đồng bộ đề.")
        return goc_url(c)
    dong_bo_de(in_ra)
    in_ra(f"✓ Đã đăng. Trang gốc: {goc_url(c)}")
    return goc_url(c)
