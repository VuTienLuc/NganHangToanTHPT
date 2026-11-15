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
import os, re, json, time, shutil, secrets, hashlib, unicodedata, subprocess, datetime
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


def lam_slug(s):
    s = ten_khong_dau(s or "", 80).lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:60]
    return s or "de-thi"


# ---------------------------------------------------------------- mã hoá đáp án
def _so(v):   # = examNumber() của bài kiểm tra
    s = str(v if v is not None else "").strip()
    s = re.sub(r"\\[()\[\]]|\$", "", s).replace("{,}", ".").replace("\\,", "").replace(",", ".").replace("−", "-")
    s = re.sub(r"\s", "", s)
    if not s or not re.fullmatch(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)", s):
        return None
    return float(s)


def chuan_dap_so(v):
    n = _so(v)
    if n is None:
        return unicodedata.normalize("NFC", str(v if v is not None else "").strip())
    x = round(n * 1e9) / 1e9
    if x == 0:
        x = 0.0
    return ("%.9f" % x).rstrip("0").rstrip(".")


def bam(muoi, khoa, gia_tri):
    return hashlib.sha256(f"{muoi}:{khoa}:{gia_tri}".encode("utf-8")).hexdigest()[:20]


JS_THEM = r"""
function __sha(ascii){function rr(v,a){return (v>>>a)|(v<<(32-a))}var P=Math.pow,M=P(2,32),i,j,r='',w=[],L=ascii.length*8,h=__sha.h=__sha.h||[],k=__sha.k=__sha.k||[],pc=k.length,c={};for(var n=2;pc<64;n++){if(!c[n]){for(i=0;i<313;i+=n)c[i]=n;h[pc]=(P(n,.5)*M)|0;k[pc++]=(P(n,1/3)*M)|0}}ascii+='\x80';while(ascii.length%64-56)ascii+='\x00';for(i=0;i<ascii.length;i++){j=ascii.charCodeAt(i);if(j>>8)return'';w[i>>2]|=j<<((3-i)%4)*8}w[w.length]=((L/M)|0);w[w.length]=L;for(j=0;j<w.length;){var W=w.slice(j,j+=16),o=h;h=h.slice(0,8);for(i=0;i<64;i++){var a=W[i-15],b=W[i-2],A=h[0],E=h[4],t1=h[7]+(rr(E,6)^rr(E,11)^rr(E,25))+((E&h[5])^((~E)&h[6]))+k[i]+(W[i]=(i<16)?W[i]:(W[i-16]+(rr(a,7)^rr(a,18)^(a>>>3))+W[i-7]+(rr(b,17)^rr(b,19)^(b>>>10)))|0),t2=(rr(A,2)^rr(A,13)^rr(A,22))+((A&h[1])^(A&h[2])^(h[1]&h[2]));h=[(t1+t2)|0].concat(h);h[4]=(h[4]+t1)|0}for(i=0;i<8;i++)h[i]=(h[i]+o[i])|0}for(i=0;i<8;i++)for(j=3;j+1;j--){var x=(h[i]>>(j*8))&255;r+=((x<16)?0:'')+x.toString(16)}return r}
function __bam(d,khoa,v){return __sha(unescape(encodeURIComponent(d.settings.__s+':'+khoa+':'+v))).slice(0,20)}
function __chuan(v){const n=examNumber(v);if(n===null)return String(v??'').trim().normalize('NFC');let x=Math.round(n*1e9)/1e9;if(x===0)x=0;return x.toFixed(9).replace(/0+$/,'').replace(/\.$/,'')}
"""

GRADE_MOI = r"""function examGrade(d,answers){const points={mcq:0,tf:0,short:0},right={mcq:0,tf:0,short:0};let blank=0;const rows=d.questions.map((q,i)=>{const a=answers[i];let cents=0,correct=0,answered=false;if(q.type==='mcq'){answered=Number.isInteger(a)&&a>=0&&a<=3;correct=answered&&(q.h?__bam(d,i,a)===q.h:a===q.answer)?1:0;cents=correct*25;}else if(q.type==='tf'){const arr=Array.isArray(a)?a:[];answered=arr.some(x=>typeof x==='boolean');correct=[0,1,2,3].reduce((n,j)=>n+(typeof arr[j]==='boolean'&&(q.h?__bam(d,i+'.'+j,arr[j])===q.h[j]:arr[j]===q.answer[j])?1:0),0);cents=[0,10,25,50,100][correct];}else{answered=typeof a==='string'&&a.trim()!=='';correct=answered&&(q.h?__bam(d,i,__chuan(a))===q.h:examShortEqual(a,q.answer))?1:0;cents=correct*50;}if(!answered)blank++;points[q.type]+=cents;right[q.type]+=q.type==='tf'?(correct===4?1:0):correct;return {index:i,type:q.type,correct,answered,points:cents/100,max:q.type==='mcq'?.25:q.type==='tf'?1:.5};});return {score:(points.mcq+points.tf+points.short)/100,parts:{mcq:points.mcq/100,tf:points.tf/100,short:points.short/100},right,blank,rows};}"""

VA = [  # (tìm, thay) trong mã bài kiểm tra; thiếu một chỗ → không đăng (tránh lộ đáp án)
    ("correct=q.type==='mcq'?'ABCD'[q.answer]:", "correct=q.h?'(thầy chưa công bố)':q.type==='mcq'?'ABCD'[q.answer]:"),
    ("latex(q.solution||'Chưa có lời giải.',q,'solution',false)",
     "latex(q.solution||(q.h?'Thầy sẽ công bố lời giải sau khi kết thúc bài thi.':'Chưa có lời giải.'),q,'solution',false)"),
]
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
    """HTML bài kiểm tra gốc → bản đăng mạng (mã hoá đáp án, bỏ lời giải). Trả (html, số câu)."""
    m = KHOI_DL.search(html)
    if not m:
        raise RuntimeError("Không thấy dữ liệu đề (exam-data) trong bài kiểm tra")
    d = json.loads(m.group(2))
    d.setdefault("settings", {}).setdefault("studentExam", {})["examId"] = slug
    if VA_ID[0] in html:
        html = html.replace(VA_ID[0], VA_ID[1], 1)
    if an_dap_an:
        for a, b in VA:
            if a not in html:
                raise RuntimeError("Không tìm thấy chỗ cần sửa để ẩn đáp án (ứng dụng trình chiếu đã đổi phiên bản) — chưa đăng để tránh lộ đáp án.")
            html = html.replace(a, b)
        muoi = secrets.token_hex(8)
        d["settings"]["__s"] = muoi
        for i, q in enumerate(d["questions"]):
            if q["type"] == "mcq":
                q["h"] = bam(muoi, i, q["answer"])
            elif q["type"] == "tf":
                q["h"] = [bam(muoi, f"{i}.{j}", "true" if v else "false") for j, v in enumerate(q["answer"])]
            else:
                q["h"] = bam(muoi, i, chuan_dap_so(q["answer"]))
            q["answer"] = None
            q["solution"] = ""
            for k in [k for k in (q.get("figures") or {}) if k.startswith("solution:")]:
                del q["figures"][k]
        html = _thay_ham(html, "examGrade", GRADE_MOI)
        i = html.rfind("examRuntime();")
        html = html[:i] + JS_THEM + "\n" + html[i:]
    for q in d["questions"]:
        for k in ("ma", "ma_dang", "ten_dang"):
            q.pop(k, None)
    nhung = json.dumps(d, ensure_ascii=False).replace("<", "\\u003c")
    m = KHOI_DL.search(html)
    html = html[:m.start(2)] + nhung + html[m.end(2):]
    html = html.replace("<head>", '<head><meta name="robots" content="noindex,nofollow">', 1)
    return html, len(d["questions"])


# ---------------------------------------------------------------- trang phụ
TRANG = """<!DOCTYPE html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>{tieu}</title><style>body{{margin:0;min-height:100vh;display:grid;place-items:center;
font:17px/1.6 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:#eef3f9;color:#1f2937}}.the{{background:#fff;border-radius:18px;
padding:34px 38px;max-width:520px;box-shadow:0 12px 40px rgba(30,58,138,.12);text-align:center}}h1{{font-size:22px;margin:0 0 8px;color:#1e3a8a}}
p{{margin:6px 0;color:#4b5563}}</style></head><body><div class="the"><h1>{tieu}</h1>{noi}</div></body></html>"""


def trang_chu():
    return TRANG.format(tieu="Trang thi Toán", noi="<p>Thầy Vũ Tiến Lực – Trường THPT Nguyễn Hữu Cảnh</p><p>Mở đúng đường link đề thi thầy gửi để làm bài.</p>")


def trang_dong(ten):
    return TRANG.format(tieu=ten.replace("<", "&lt;"), noi="<p><b>Bài thi đã đóng.</b></p><p>Liên hệ thầy nếu em cần làm lại.</p>")


def ghi_site():
    os.makedirs(SITE, exist_ok=True)
    open(os.path.join(SITE, "index.html"), "w", encoding="utf-8").write(trang_chu())
    open(os.path.join(SITE, "_headers"), "w", encoding="utf-8").write(
        "/*\n  X-Robots-Tag: noindex, nofollow\n  Cache-Control: no-cache\n")
    open(os.path.join(SITE, "404.html"), "w", encoding="utf-8").write(
        TRANG.format(tieu="Không có đề này", noi="<p>Kiểm tra lại đường link thầy gửi.</p>"))


def _dat_trang(slug, noi_dung):
    d = os.path.join(SITE, slug); os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(noi_dung)


# ---------------------------------------------------------------- tạo / đổi trạng thái
def them_de(slug, ten, html_goc, an_dap_an=True, phut=None, ghi_de=False):
    slug = lam_slug(slug or ten)
    ds = danh_sach()
    if not ghi_de:
        goc, n = slug, 2
        while any(x["slug"] == slug for x in ds):
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
    ds = [x for x in ds if x["slug"] != slug]
    ds.insert(0, {"slug": slug, "ten": ten, "tao_luc": datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
                  "trang_thai": "dang_mo" if an_dap_an else "da_cong_bo", "so_cau": so, "phut": phut})
    luu_ds(ds)
    return slug


def doi_trang_thai(slug, tt):
    """tt: dang_mo (ẩn đáp án) | da_cong_bo (có đáp án + lời giải) | da_dong | xoa"""
    ds = danh_sach(); x = next((y for y in ds if y["slug"] == slug), None)
    if not x:
        raise RuntimeError("Không có đề " + slug)
    p_goc = os.path.join(DL, slug + ".goc.html")
    ghi_site()
    if tt == "xoa":
        shutil.rmtree(os.path.join(SITE, slug), ignore_errors=True)
        cu = os.path.join(DL, "_da_xoa"); os.makedirs(cu, exist_ok=True)
        if os.path.exists(p_goc):
            shutil.move(p_goc, os.path.join(cu, slug + ".goc.html"))
        luu_ds([y for y in ds if y["slug"] != slug]); return
    if tt == "da_dong":
        _dat_trang(slug, trang_dong(x["ten"]))
    else:
        goc = open(p_goc, encoding="utf-8").read()
        _dat_trang(slug, ban_truc_tuyen(goc, slug, tt == "dang_mo")[0])
    x["trang_thai"] = tt; luu_ds(ds)


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


def dang(in_ra=print):
    if not co_node():
        raise RuntimeError("Máy chưa có Node.js (lệnh npx). Cài bản LTS ở https://nodejs.org rồi bấm Đăng lại.")
    c = cau_hinh(); ghi_site()
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
        if rc == 0 or "already exists" in ra.lower() or "A project with this name already exists" in ra:
            c["da_tao_du_an"] = True
            if m and not c.get("ten_mien"):
                c["ten_mien"] = m.group(0)
            json.dump(c, open(P_CH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        else:
            raise RuntimeError("Chưa tạo được dự án Cloudflare Pages (xem nhật ký). Có thể đổi tên dự án khác rồi thử lại.")
    in_ra("Đang đưa đề lên Cloudflare Pages…")
    rc, ra = _chay(["pages", "deploy", SITE, "--project-name", c["du_an"], "--branch", "main", "--commit-dirty=true"], in_ra, 600)
    if rc != 0:
        raise RuntimeError("Đăng chưa thành công (xem nhật ký phía trên).")
    m = re.search(r"https://[a-z0-9]+\.([a-z0-9-]+)\.pages\.dev", ra)
    if m and not c.get("ten_mien"):
        c["ten_mien"] = f"https://{m.group(1)}.pages.dev"
        json.dump(c, open(P_CH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    in_ra(f"✓ Đã đăng. Trang gốc: {goc_url(c)}")
    return goc_url(c)
