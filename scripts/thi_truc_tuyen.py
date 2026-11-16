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
     "$('loginError').textContent=m;return}await __camXuc(k);if(k.thong_bao)notice(k.thong_bao);enter();}"
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
// ---- 💡 GỢI Ý AI (kiểu Pólya): học sinh chụp màn hình lời nhắn + đề gửi ChatGPT/Gemini; máy chủ đếm số lần mở
const __GOI_Y=__GOI_Y_AI__;
const __LOI_NHAN=`Bạn là một giáo viên Toán THPT xuất sắc. Hãy hướng dẫn em tự giải bài toán bên dưới theo 4 bước của George Pólya: (1) Hiểu đề → (2) Lập kế hoạch → (3) Thực hiện → (4) Kiểm tra lại.
Yêu cầu:
• Thật ngắn gọn: mỗi lần chỉ 1–2 câu hỏi gợi mở cho bước tiếp theo.
• KHÔNG đưa đáp số, KHÔNG giải hết, KHÔNG chọn đáp án A/B/C/D hay Đúng/Sai thay em.
• Đợi em trả lời rồi mới gợi ý tiếp; em làm sai thì chỉ ra chỗ sai và gợi ý cách sửa.
• Chỉ khi em đã tự làm ra kết quả, mới xác nhận đúng hay sai.
Đề bài:`;
function __gyCss(){if(document.getElementById('__gy-st'))return;const st=document.createElement('style');st.id='__gy-st';st.textContent=`
 .__gy-nen{position:fixed;inset:0;z-index:9998;background:rgba(15,23,42,.55);display:grid;place-items:start center;overflow:auto;padding:14px}
 .__gy{background:#fff;color:#0f172a;border-radius:16px;max-width:760px;width:100%;box-shadow:0 20px 60px rgba(0,0,0,.3);font:16px/1.55 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
 .__gy-chup{padding:16px 18px}.__gy-ln{background:#eff6ff;border:2px solid #93c5fd;border-radius:12px;padding:12px 14px;white-space:pre-wrap;font-size:15px}
 .__gy-ln b{color:#1e3a8a}.__gy-de{margin-top:12px;border:2px dashed #cbd5e1;border-radius:12px;padding:12px 14px}
 .__gy-de button,.__gy-de input{pointer-events:none}.__gy-than{font-size:17px;white-space:pre-line}.__gy-pa{display:grid;grid-template-columns:1fr 1fr;gap:6px 18px;margin-top:8px}.__gy-y div,.__gy-pa div{margin:3px 0}.__gy-loai{margin-top:6px;color:#64748b;font-size:14px;font-style:italic}.__gy img.fig,.__gy svg{max-width:100%;height:auto}@media(max-width:560px){.__gy-pa{grid-template-columns:1fr}}.__gy-nhan{font-weight:800;color:#b45309;font-size:13px;margin-bottom:4px}
 .__gy-hd{padding:10px 18px;background:#fef3c7;color:#78350f;font-size:14px;border-top:1px solid #fde68a}
 .__gy-nut{display:flex;gap:8px;flex-wrap:wrap;padding:12px 18px;border-top:1px solid #e2e8f0}
 .__gy-nut button,.__gy-nut a{font:inherit;font-size:14px;font-weight:700;padding:9px 14px;border-radius:10px;border:1px solid #cbd5e1;background:#fff;color:#0f172a;cursor:pointer;text-decoration:none}
 .__gy-nut .chinh{background:#1e40af;color:#fff;border-color:#1e40af}
 #__gy-btn{position:fixed;right:14px;bottom:76px;z-index:9000;font:700 15px system-ui;padding:11px 16px;border-radius:999px;border:0;background:#f59e0b;color:#111;box-shadow:0 6px 20px rgba(0,0,0,.25);cursor:pointer}`;document.head.appendChild(st)}
function __goiYMo(){
 const q=document.getElementById('question');if(!q)return;
 let d=null,i=0;try{d=JSON.parse(document.getElementById('exam-data').textContent)}catch(_){}
 const cur=document.querySelector('#questionNav .current');if(cur)i=+cur.dataset.jump||0;
 const qq=d&&d.questions[i];
 __gyCss();
 const o=document.createElement('div');o.className='__gy-nen';
 const so=cur?cur.textContent.trim():String(i+1);
 o.innerHTML='<div class="__gy"><div class="__gy-chup"><div class="__gy-ln"><b>👨‍🏫 Lời nhắn cho AI</b>\n'+__LOI_NHAN.replace(/[<>&]/g,c=>({'<':'&lt;','>':'&gt;','&':'&amp;'}[c])).replace('Bạn là','<b>Bạn là</b>')+'</div>'+
  '<div class="__gy-de"><div class="__gy-nhan">ĐỀ BÀI — Câu '+so+'</div><div class="__gy-q"></div></div></div>'+
  '<div class="__gy-hd">📸 <b>Chụp màn hình khung trên</b> (cả lời nhắn và đề) rồi gửi cho ChatGPT / Gemini — hoặc bấm <b>Chép chữ</b> để dán. AI chỉ gợi ý từng bước, em tự tính ra đáp số nhé!</div>'+
  '<div class="__gy-nut"><button class="chinh" data-v="chep">📋 Chép chữ (lời nhắn + đề)</button><a href="https://chatgpt.com/" target="_blank" rel="noopener">Mở ChatGPT</a><a href="https://gemini.google.com/" target="_blank" rel="noopener">Mở Gemini</a><button data-v="dong" style="margin-left:auto">Đóng — quay lại làm bài</button></div></div>';
 const vung=o.querySelector('.__gy-q');
 if(qq&&typeof latex==='function'){   // dựng lại đề từ dữ liệu: hiện đủ phương án (kể cả khi đề đang ở chế độ lật)
  let h='<div class="__gy-than">'+latex(qq.stem,qq,'stem',false)+'</div>';
  if(qq.type==='mcq')h+='<div class="__gy-pa">'+qq.options.map((x,j)=>'<div><b>'+'ABCD'[j]+'.</b> '+latex(x,qq,'option'+j,false)+'</div>').join('')+'</div>';
  if(qq.type==='tf')h+='<div class="__gy-y">'+qq.options.map((x,j)=>'<div><b>'+'abcd'[j]+')</b> '+latex(x,qq,'option'+j,false)+'</div>').join('')+'</div><div class="__gy-loai">Xét mỗi ý a), b), c), d) Đúng hay Sai.</div>';
  if(qq.type==='short')h+='<div class="__gy-loai">Câu trả lời ngắn: tìm một số.</div>';
  vung.innerHTML=h;
 }else{const k=q.cloneNode(true);k.removeAttribute('id');k.querySelectorAll('[id]').forEach(e=>e.removeAttribute('id'));vung.appendChild(k)}
 document.body.appendChild(o);
 if(window.MathJax&&MathJax.typesetPromise)MathJax.typesetPromise([vung]).catch(()=>{});
 o.querySelector('[data-v=dong]').onclick=()=>o.remove();o.onclick=e=>{if(e.target===o)o.remove()};
 o.querySelector('[data-v=chep]').onclick=async e=>{
  let t=__LOI_NHAN+'\n';
  if(qq){t+=qq.stem+'\n';if(qq.type==='mcq')qq.options.forEach((x,j)=>t+='ABCD'[j]+'. '+x+'\n');
   if(qq.type==='tf'){t+='(Xét Đúng hay Sai từng ý)\n';qq.options.forEach((x,j)=>t+='abcd'[j]+') '+x+'\n')}
   if(qq.type==='short')t+='(Câu trả lời ngắn: tìm một số)\n'}
  else t+=q.innerText;
  try{await navigator.clipboard.writeText(t);e.target.textContent='✓ Đã chép — dán vào ChatGPT/Gemini'}catch(_){e.target.textContent='Không chép được — hãy chụp màn hình'}};
 try{const kk='__gy:'+__DE+':'+i;if(!sessionStorage.getItem(kk)){sessionStorage.setItem(kk,'1');__goi('goi-y',{de:__DE,cau:i+1}).catch(()=>{})}}catch(_){}
}
if(__GOI_Y){__gyCss();const b=Object.assign(document.createElement('button'),{id:'__gy-btn',type:'button',textContent:'💡 Gợi ý AI'});
 b.title='Hướng dẫn kiểu Pólya — không cho đáp số';b.onclick=__goiYMo;b.style.display='none';
 document.addEventListener('DOMContentLoaded',()=>document.body.appendChild(b));if(document.body)document.body.appendChild(b);
 setInterval(()=>{const w=document.getElementById('work');b.style.display=w&&!w.hidden?'':'none'},800);}
const __DV=__DONG_VIEN__;
function __camXuc(k){if(k&&k.tiep)return Promise.resolve();return new Promise(xong=>{
 const st=document.createElement('style');st.textContent=`.__cx{position:fixed;inset:0;z-index:9999;background:rgba(15,23,42,.55);display:grid;place-items:center;padding:16px;animation:__mo .25s}
 @keyframes __mo{from{opacity:0}to{opacity:1}}@keyframes __bay{from{transform:translateY(14px) scale(.96);opacity:0}to{transform:none;opacity:1}}
 .__cx .h{background:#fff;border-radius:22px;max-width:560px;width:100%;padding:24px 22px;box-shadow:0 24px 70px rgba(0,0,0,.3);animation:__bay .3s;font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
 .__cx h2{margin:0 0 4px;font-size:21px;color:#1e3a8a;text-align:center}.__cx .p{margin:0 0 16px;color:#64748b;text-align:center;font-size:14px}
 .__cx .l{display:grid;grid-template-columns:1fr 1fr;gap:10px}.__cx .l button{border:2px solid #e2e8f0;background:#f8fafc;border-radius:16px;padding:14px 8px;cursor:pointer;font-size:15px;font-weight:600;color:#334155;transition:.15s}
 .__cx .l button:hover{transform:translateY(-3px);box-shadow:0 8px 20px rgba(0,0,0,.08)}.__cx .l b{display:block;font-size:44px;line-height:1.15;margin-bottom:4px}
 .__cx .bong{display:flex;gap:12px;align-items:flex-start;margin:4px 0 18px;animation:__bay .35s}.__cx .av{font-size:42px;line-height:1}
 .__cx .noi{background:#eff6ff;border-radius:4px 18px 18px 18px;padding:14px 16px;font-size:17px;line-height:1.55;color:#1e293b}.__cx .noi strong{color:#1e3a8a}
 .__cx .vao{width:100%;border:0;border-radius:14px;padding:14px;font-size:18px;font-weight:800;color:#fff;cursor:pointer}.__cx .doi{display:block;margin:10px auto 0;background:none;border:0;color:#64748b;cursor:pointer;text-decoration:underline;font-size:13px}`;
 const o=document.createElement('div');o.className='__cx';document.body.append(st,o);
 const chon=()=>{o.innerHTML='<div class="h"><h2>Trước khi làm bài, em đang thấy thế nào?</h2><p class="p">Chọn một cảm xúc — thầy có lời nhắn riêng cho em</p><div class="l">'+
  Object.entries(__DV).map(([k,v])=>'<button data-k="'+k+'" style="border-color:'+v.mau+'33"><b>'+v.icon+'</b>'+v.ten+'</button>').join('')+'</div></div>';
  o.querySelectorAll('[data-k]').forEach(b=>b.onclick=()=>nhan(b.dataset.k))};
 const nhan=k=>{const v=__DV[k],n=v.cau.length;let cu=-1;try{cu=+localStorage.getItem('__dv_'+k)}catch(_){}
  let i=Math.floor(Math.random()*n);if(n>1&&i===cu)i=(i+1+Math.floor(Math.random()*(n-1)))%n;try{localStorage.setItem('__dv_'+k,i)}catch(_){}
  const c=v.cau[i].replace(/^Thầy Lực:\s*/,'');
  o.innerHTML='<div class="h"><div class="bong"><div class="av">👨‍🏫</div><div class="noi"><strong>Thầy Lực:</strong> '+c.replace(/[<>]/g,'')+'</div></div>'+
   '<button class="vao" style="background:'+v.mau+'">'+v.icon+' Vào làm bài 🚀</button><button class="doi">← chọn lại cảm xúc</button></div>';
  o.querySelector('.doi').onclick=chon;
  o.querySelector('.vao').onclick=()=>{__goi('cam-xuc',{de:__DE,cam_xuc:k}).catch(()=>{});o.remove();st.remove();xong()}};
 chon();})}
async function __khoiDong(){
 try{const t=await __goi('toi');if(t.ok){const gv=t.vai==='gv',dat=(id,v)=>{const e=document.getElementById(id);if(e){e.value=v;e.readOnly=true;e.style.background='#f1f5f9'}};
  dat('studentClass',gv?'GV':(t.lop||''));dat('studentId',gv?'0':String(t.stt||''));dat('studentName',gv?'Giáo viên (làm thử)':(t.ho_ten||''));
  const m=document.querySelector('#login .muted');if(m)m.innerHTML=(gv?'Chế độ làm thử của giáo viên.':'Thông tin lấy theo tài khoản đã đăng nhập.')+' Bấm nút bên dưới để bắt đầu. <a href="/">Trang chính</a> · <a href="#" id="__thoat">Đăng xuất</a>';
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


def ban_truc_tuyen(html, slug, an_dap_an=True, goi_y=False):
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
    dv = json.dumps(json.load(open(os.path.join(MAY_CHU, "dong_vien.json"), encoding="utf-8")), ensure_ascii=False).replace("<", "\\u003c")
    html = html[:i] + JS_DANG_NHAP.replace("__DONG_VIEN__", dv).replace("__GOI_Y_AI__", "true" if goi_y else "false") \
        + "\n__khoiDong().then(()=>examRuntime());" + html[i + len("examRuntime();"):]
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
.de:hover{background:#f8fafc}.de b{flex:1}.nho{font-size:12.5px;color:#6b7280;white-space:nowrap}
.ln{background:linear-gradient(135deg,#fdf2f8,#eff6ff);border:1px solid #fbcfe8;border-radius:14px;padding:12px 14px;margin:0 0 12px}.ln-dau{font-weight:800;color:#be185d;display:flex;justify-content:space-between;gap:8px}
.ln-noi{margin:6px 0 2px;line-height:1.55}.ln-ok{width:auto;margin-top:8px;padding:8px 14px;font-size:14px;background:#db2777}</style>"""

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

GV_CSS = r"""<style>
:root{--bg:#f4f6fb;--surface:#fff;--surface-2:#f8fafc;--text:#0f172a;--muted:#64748b;--border:#e2e8f0;--primary:#1e40af;--primary-soft:#dbeafe;
 --pdf:#b91c1c;--pdf-soft:#fee2e2;--ok:#15803d;--ok-soft:#dcfce7;--warn:#b45309;--warn-soft:#fef3c7;--radius:14px;--r-sm:9px;
 --s1:4px;--s2:8px;--s3:12px;--s4:16px;--s5:24px;--shadow:0 1px 2px rgb(15 23 42/.05),0 4px 16px rgb(15 23 42/.06);--ring:0 0 0 3px rgb(37 99 235/.35)}
@media (prefers-color-scheme:dark){:root{--bg:#0b1120;--surface:#111827;--surface-2:#0f172a;--text:#e5e7eb;--muted:#94a3b8;--border:#1f2937;--primary:#93c5fd;--primary-soft:#1e3a8a55;
 --pdf:#fca5a5;--pdf-soft:#7f1d1d55;--ok:#86efac;--ok-soft:#14532d55;--warn:#fcd34d;--warn-soft:#78350f55;--shadow:0 1px 2px rgb(0 0 0/.4)}}
body.gv{background:var(--bg);color:var(--text)}body.gv .vo{max-width:1240px;padding:var(--s4)}body.gv .the{background:none;box-shadow:none;padding:0}
body.gv h1,body.gv .phu.dau{display:none}
.g-top{display:flex;align-items:center;gap:var(--s3);flex-wrap:wrap;margin-bottom:var(--s4)}
.g-top h2{margin:0;font-size:22px;color:var(--primary);flex:1;min-width:200px}.g-top small{display:block;color:var(--muted);font-weight:400;font-size:13px}
.g-btn{display:inline-flex;align-items:center;gap:6px;width:auto;margin:0;padding:9px 14px;min-height:40px;font-size:14px;font-weight:600;border-radius:var(--r-sm);
 border:1px solid var(--border);background:var(--surface);color:var(--text);cursor:pointer;text-decoration:none;transition:background .15s,border-color .15s}
.g-btn:hover{border-color:var(--primary)}.g-btn:focus-visible,.g-card:focus-visible,.chip:focus-visible,.g-tim input:focus{outline:none;box-shadow:var(--ring)}
.g-stat{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:var(--s3);margin-bottom:var(--s4)}
.g-stat div{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:var(--s3) var(--s4);box-shadow:var(--shadow)}
.g-stat b{display:block;font-size:26px;line-height:1.1}.g-stat span{color:var(--muted);font-size:13px}
.g-luoi{display:grid;grid-template-columns:minmax(0,1fr);gap:var(--s4)}@media (min-width:1080px){.g-luoi{grid-template-columns:minmax(0,1fr) 360px}}
.g-khoi{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:var(--s4);box-shadow:var(--shadow);min-width:0}
.g-khoi>h3{margin:0 0 var(--s3);font-size:16px;display:flex;align-items:center;gap:var(--s2)}.g-khoi>h3 .dem{color:var(--muted);font-weight:500;font-size:13px}
.g-tim{position:sticky;top:0;z-index:5;background:var(--surface);padding:var(--s2) 0 var(--s3);display:flex;flex-direction:column;gap:var(--s2)}
.g-tim .o{position:relative}.g-tim input{width:100%;box-sizing:border-box;padding:12px 44px 12px 42px;font-size:16px;border:1px solid var(--border);border-radius:12px;background:var(--surface-2);color:var(--text)}
.g-tim .kinh{position:absolute;left:14px;top:50%;transform:translateY(-50%);color:var(--muted)}
.g-tim input:focus+kbd,.g-tim input:not(:placeholder-shown)+kbd{display:none}.g-tim kbd{position:absolute;right:12px;top:50%;transform:translateY(-50%);font:12px ui-monospace,monospace;border:1px solid var(--border);border-radius:6px;padding:1px 6px;color:var(--muted)}
.g-loc{display:flex;gap:var(--s2);flex-wrap:wrap;align-items:center}
.chip{width:auto;margin:0;padding:6px 12px;min-height:34px;border-radius:999px;border:1px solid var(--border);background:var(--surface);color:var(--text);font-size:13.5px;font-weight:600;cursor:pointer}
.chip[aria-pressed=true]{background:var(--primary);border-color:var(--primary);color:#fff}
@media (prefers-color-scheme:dark){.chip[aria-pressed=true]{color:#0b1120}}
.g-loc select{padding:6px 10px;border-radius:999px;border:1px solid var(--border);background:var(--surface);color:var(--text);font-size:13.5px;margin-left:auto;min-height:34px}
.g-nhom{margin-top:var(--s4)}.g-nhom>summary{cursor:pointer;list-style:none;display:flex;align-items:center;gap:var(--s2);font-weight:700;font-size:15px;padding:6px 0;border-bottom:1px solid var(--border)}
.g-nhom>summary::-webkit-details-marker{display:none}.g-nhom>summary::before{content:"▸";color:var(--muted);transition:transform .15s}.g-nhom[open]>summary::before{transform:rotate(90deg)}
.g-nhom>summary .so{color:var(--muted);font-weight:500;font-size:12.5px;margin-left:auto}
.g-lop{font-size:12px;font-weight:800;color:var(--primary);background:var(--primary-soft);border-radius:6px;padding:2px 7px}
.g-cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:var(--s3);margin-top:var(--s3)}
.g-card{position:relative;display:flex;flex-direction:column;gap:6px;padding:var(--s3) var(--s3) var(--s3) var(--s4);min-height:92px;border:1px solid var(--border);border-radius:12px;
 background:var(--surface-2);text-decoration:none;color:var(--text);transition:transform .15s ease-out,box-shadow .15s,border-color .15s}
.g-card:hover{transform:translateY(-2px);box-shadow:var(--shadow);border-color:var(--primary)}
.g-card::before{content:"";position:absolute;left:0;top:10px;bottom:10px;width:4px;border-radius:4px;background:var(--primary)}.g-card.pdf::before{background:var(--pdf)}.g-card.phieu::before{background:#0d9488}
.g-card .t{font-weight:650;line-height:1.35;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;padding-right:30px}
.g-card .m{display:flex;gap:6px;align-items:center;flex-wrap:wrap;font-size:12px;color:var(--muted);margin-top:auto}
.nhan{font-size:11px;font-weight:800;border-radius:6px;padding:2px 7px;background:var(--primary-soft);color:var(--primary)}.nhan.pdf{background:var(--pdf-soft);color:var(--pdf)}
.nhan.cd{background:var(--warn-soft);color:var(--warn)}.nhan.ph{background:#ccfbf1;color:#0f766e}.nhan.hs{background:var(--ok-soft);color:var(--ok)}
.ghim{position:absolute;top:6px;right:6px;width:36px;height:36px;margin:0;padding:0;border:0;border-radius:8px;background:none;color:var(--muted);font-size:18px;cursor:pointer}
.ghim:hover{background:var(--border)}.ghim[aria-pressed=true]{color:#eab308}
mark{background:#fde68a;color:inherit;border-radius:3px;padding:0 1px}
.g-ngang{display:grid;grid-auto-flow:column;grid-auto-columns:minmax(220px,260px);gap:var(--s3);overflow-x:auto;padding-bottom:6px;margin-bottom:var(--s2)}
.g-tieu{font-size:13px;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.04em;margin:var(--s3) 0 var(--s2)}
.g-rong{text-align:center;color:var(--muted);padding:var(--s5) var(--s3)}.g-rong b{display:block;color:var(--text);font-size:16px;margin-bottom:4px}
.g-tab{display:flex;gap:var(--s1);background:var(--surface-2);border-radius:10px;padding:3px;margin-bottom:var(--s3)}
.g-tab button{flex:1;width:auto;margin:0;padding:7px 6px;border:0;border-radius:8px;background:none;color:var(--muted);font-size:13px;font-weight:700;cursor:pointer}
.g-tab button[aria-selected=true]{background:var(--surface);color:var(--text);box-shadow:var(--shadow)}
.g-de{display:flex;flex-direction:column;gap:6px;padding:var(--s3);border:1px solid var(--border);border-radius:12px;margin-bottom:var(--s2)}
.g-de .t{font-weight:650;line-height:1.35}.g-de .m{font-size:12.5px;color:var(--muted);display:flex;gap:8px;flex-wrap:wrap}
.g-de .n{display:flex;gap:6px}.g-de .n .g-btn{min-height:34px;padding:5px 10px;font-size:13px}
.toast{position:fixed;left:50%;bottom:24px;transform:translateX(-50%);background:#0f172a;color:#fff;padding:10px 16px;border-radius:10px;font-size:14px;opacity:0;transition:opacity .2s;pointer-events:none;z-index:50}
.toast.hien{opacity:1}
@media (max-width:640px){body.gv .vo{padding:var(--s3)}.g-loc select{margin-left:0}.g-cards{grid-template-columns:1fr}}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
</style>
"""
GV_JS = r"""function veGV(t){
 document.body.classList.add('gv');
 const L=k=>{try{return JSON.parse(localStorage.getItem('gv_'+k)||'null')}catch(_){return null}}, S=(k,v)=>{try{localStorage.setItem('gv_'+k,JSON.stringify(v))}catch(_){}};
 const bo=s=>[...String(s||'')].map(c=>c.normalize('NFD').replace(/[̀-ͯ]/g,'').replace(/đ/g,'d').replace(/Đ/g,'D').toLowerCase().charAt(0)||c).join('');
 const q0=new URLSearchParams(location.search);
 const st={q:'',lop:q0.get('lop')||L('lop')||'',kieu:'',xep:L('xep')||'muc_luc',tab:'dang_mo'};
 let BG=[], DE=t.de||[], ghim=L('ghim')||[], gan=L('gan')||[];
 nd.innerHTML=`<div class="g-top"><h2>Bàn làm việc giáo viên<small>Bài giảng trình chiếu · đề kiểm tra trực tuyến</small></h2>
  <button class="g-btn" id="g-th" style="background:#1e40af;color:#fff;border-color:#1e40af">📊 Tổng hợp quá trình</button><a class="g-btn" href="#" id="thoat">Đăng xuất</a></div>
  <div class="g-stat" id="g-stat"></div>
  <div class="g-luoi"><section class="g-khoi" aria-labelledby="h-bg"><h3 id="h-bg">📚 Bài giảng <span class="dem" id="bg-dem"></span></h3>
   <div class="g-tim"><div class="o"><span class="kinh" aria-hidden="true">🔍</span><input id="tim" type="search" placeholder="Tìm bài giảng: tên bài, chương, dạng…" aria-label="Tìm bài giảng" autocomplete="off"><kbd>/</kbd></div>
   <div class="g-loc" id="loc"></div></div><div id="bg"></div></section>
   <aside class="g-khoi" aria-labelledby="h-de"><h3 id="h-de">📝 Đề kiểm tra <span class="dem" id="de-dem"></span></h3><div class="g-tab" role="tablist" id="tab"></div><div id="de"></div></aside></div>
  <div class="toast" id="toast" role="status"></div>`;
 const $=id=>document.getElementById(id), toast=m=>{$('toast').textContent=m;$('toast').classList.add('hien');clearTimeout(toast.t);toast.t=setTimeout(()=>$('toast').classList.remove('hien'),1600)};
 const so=n=>Number(n).toFixed(2).replace('.',','), ngay=s=>s?s.slice(8,10)+'/'+s.slice(5,7)+'/'+s.slice(0,4):'';
 function veStat(){const ht=BG.filter(x=>x.kieu==='html').length,mo=DE.filter(x=>x.trang_thai==='dang_mo').length,nop=DE.reduce((a,x)=>a+(x.so_hs||0),0);
  $('g-stat').innerHTML=[[BG.length,'bài giảng · '+ht+' trình chiếu, '+(BG.length-ht)+' PDF'],[mo,'đề đang mở'],[DE.length,'đề đã đăng'],[nop,'học sinh đã nộp bài']]
   .map(([b,s])=>`<div><b>${b}</b><span>${s}</span></div>`).join('')}
 function veLoc(){const lops=[...new Set(BG.map(x=>x.lop).concat(DE.map(x=>parseInt(x.lop)).filter(Boolean)))].filter(Boolean).sort((a,b)=>a-b);
  if(st.lop&&!lops.includes(+st.lop))st.lop='';
  const chip=(k,v,nhan)=>`<button class="chip" data-k="${k}" data-v="${v}" aria-pressed="${String(st[k])===String(v)}">${nhan}</button>`;
  $('loc').innerHTML=chip('lop','','Mọi lớp')+lops.map(l=>chip('lop',l,'Toán '+l)).join('')+'<span style="width:8px"></span>'+chip('kieu','','Tất cả')+chip('kieu','html','▶ Trình chiếu')+chip('kieu','phieu','📝 Phiếu học tập')+chip('kieu','pdf','PDF')+
   `<select id="xep" aria-label="Sắp xếp"><option value="muc_luc">Theo mục lục</option><option value="moi">Mới nhất</option><option value="az">A → Z</option></select>`;
  $('xep').value=st.xep; $('xep').onchange=e=>{st.xep=e.target.value;S('xep',st.xep);veBG()};
  $('loc').querySelectorAll('.chip').forEach(b=>b.onclick=()=>{st[b.dataset.k]=b.dataset.v;if(b.dataset.k==='lop')S('lop',st.lop);veLoc();veBG();veDe()})}
 const hl=(s,tk)=>{s=String(s||'');if(!tk.length)return e(s);const n=bo(s),dau=new Array(s.length).fill(0);
  for(const k of tk){let i=n.indexOf(k);while(i>=0){for(let j=i;j<i+k.length;j++)dau[j]=1;i=n.indexOf(k,i+k.length)}}
  let o='',m=0;for(let i=0;i<s.length;i++){if(dau[i]&&!m){o+='<mark>';m=1}if(!dau[i]&&m){o+='</mark>';m=0}o+=e(s[i])}return o+(m?'</mark>':'')};
 function the(x,tk){const g=ghim.includes(x.slug);
  return `<a class="g-card ${x.loai_bg==='phieu'?'phieu':x.kieu}" href="/bai-giang/${encodeURIComponent(x.slug)}/" target="_blank" rel="noopener" data-s="${e(x.slug)}">
   <span class="t" title="${e(x.ten)}">${hl(String(x.ten).replace(/^Toán\s*\d+\s*[–-]\s*/,''),tk||[])}</span><span class="m"><span class="nhan ${x.loai_bg==='phieu'?'ph':x.kieu}">${x.loai_bg==='phieu'?'📝 Phiếu':x.kieu==='pdf'?'PDF':'▶ Trình chiếu'}</span>${x.hs?'<span class="nhan hs" title="Học sinh khối '+x.lop+' đăng nhập xem được">👥 HS xem</span>':''}${x.chua_de?'<span class="nhan cd">Chữa đề</span>':''}<span class="g-lop">${x.lop}</span>${x.bai_so?'<span>Bài '+x.bai_so+'</span>':''}<span>${ngay(x.ngay)}</span></span>
   <button class="ghim" data-g="${e(x.slug)}" aria-pressed="${g}" aria-label="${g?'Bỏ ghim':'Ghim'} ${e(x.ten)}" title="${g?'Bỏ ghim':'Ghim lên đầu'}">${g?'★':'☆'}</button></a>`}
 function locBG(){return BG.filter(x=>(!st.lop||x.lop==st.lop)&&(!st.kieu||(st.kieu==='phieu'?x.loai_bg==='phieu':x.kieu===st.kieu&&x.loai_bg!=='phieu')))}
 function veBG(){
  const tk=bo(st.q).split(/\s+/).filter(Boolean), ds=locBG(); let h='';
  if(tk.length){const kq=ds.map(x=>{const ten=bo(x.ten),hay=bo([x.ten,x.chuong,x.bai].join(' '));if(!tk.every(k=>hay.includes(k)))return null;
     let d=0;for(const k of tk){if(ten.startsWith(k))d+=6;else if(new RegExp('(^|[^a-z0-9])'+k.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')).test(ten))d+=4;else if(ten.includes(k))d+=2;else d+=1}
     if(ghim.includes(x.slug))d+=2;return[d,x]}).filter(Boolean).sort((a,b)=>b[0]-a[0]||String(b[1].ngay).localeCompare(a[1].ngay));
   $('bg-dem').textContent=kq.length+' kết quả';
   h=kq.length?`<div class="g-tieu">Kết quả cho “${e(st.q)}” — Enter mở bài đầu tiên</div><div class="g-cards">${kq.map(([,x])=>the(x,tk)).join('')}</div>`
    :`<div class="g-rong"><b>Không tìm thấy bài giảng</b>Thử bỏ dấu, gõ ít chữ hơn (vd “tich vo huong”), hoặc chọn “Mọi lớp”.</div>`}
  else{$('bg-dem').textContent=ds.length+' bài';
   const tim=ma=>ma.map(s=>ds.find(x=>x.slug===s)).filter(Boolean);
   const g=tim(ghim), r=tim(gan).filter(x=>!ghim.includes(x.slug)).slice(0,6);
   if(g.length)h+=`<div class="g-tieu">⭐ Đã ghim</div><div class="g-ngang">${g.map(x=>the(x)).join('')}</div>`;
   if(r.length)h+=`<div class="g-tieu">🕘 Mở gần đây</div><div class="g-ngang">${r.map(x=>the(x)).join('')}</div>`;
   if(!ds.length)h+=`<div class="g-rong"><b>Chưa có bài giảng${st.lop?' Toán '+st.lop:''}</b>Đăng từ ứng dụng ra đề: ⚡ Tạo nhanh theo bài, hoặc 📚 Đăng bài giảng.</div>`;
   else if(st.xep!=='muc_luc'){const x2=ds.slice().sort(st.xep==='moi'?(a,b)=>String(b.ngay).localeCompare(a.ngay):(a,b)=>a.ten.localeCompare(b.ten,'vi'));
    h+=`<div class="g-tieu">${st.xep==='moi'?'Mới nhất':'A → Z'}</div><div class="g-cards">${x2.map(x=>the(x)).join('')}</div>`}
   else{const nhom=new Map();
    for(const x of ds.slice().sort((a,b)=>a.lop-b.lop||(a.chua_de-b.chua_de)||(a.chuong_so-b.chuong_so)||(a.bai_so||999)-(b.bai_so||999)||String(b.ngay).localeCompare(a.ngay))){
     const k=x.lop+'|'+(x.chua_de?'Chữa đề kiểm tra':x.chuong||'Bài giảng khác');(nhom.get(k)||nhom.set(k,[]).get(k)).push(x)}
    const mo=L('mo')||{};let i=0;
    for(const [k,v] of nhom){const [lop,ten]=k.split('|');const open=mo[k]!=null?mo[k]:i<4;i++;
     h+=`<details class="g-nhom" data-k="${e(k)}" ${open?'open':''}><summary><span class="g-lop">${lop}</span>${e(ten)}<span class="so">${v.length} bài</span></summary><div class="g-cards">${v.map(x=>the(x)).join('')}</div></details>`}}}
  $('bg').innerHTML=h;
  $('bg').querySelectorAll('.g-nhom').forEach(d=>d.ontoggle=()=>{const m=L('mo')||{};m[d.dataset.k]=d.open;S('mo',m)});
  $('bg').querySelectorAll('.ghim').forEach(b=>b.onclick=ev=>{ev.preventDefault();ev.stopPropagation();const s=b.dataset.g;
   ghim=ghim.includes(s)?ghim.filter(x=>x!==s):[s,...ghim].slice(0,12);S('ghim',ghim);toast(ghim.includes(s)?'Đã ghim':'Đã bỏ ghim');veBG()});
  $('bg').querySelectorAll('.g-card').forEach(a=>a.addEventListener('click',()=>{gan=[a.dataset.s,...gan.filter(x=>x!==a.dataset.s)].slice(0,12);S('gan',gan);setTimeout(veBG,300)}))}
 const TT={dang_mo:['Đang mở','#15803d'],da_cong_bo:['Đã công bố','#b45309'],da_dong:['Đã đóng','#64748b']};
 function veDe(){const ds=DE.filter(x=>!st.lop||String(x.lop||'').toUpperCase().split(/[,\s]+/).some(l=>!l||l.startsWith(st.lop))||!x.lop);
  const dem=k=>ds.filter(x=>x.trang_thai===k).length;
  if(!dem(st.tab)&&!st.tabTay){const k=Object.keys(TT).find(dem);if(k)st.tab=k}
  $('de-dem').textContent=ds.length+' đề';
  $('tab').innerHTML=Object.entries(TT).map(([k,[n]])=>`<button role="tab" aria-selected="${st.tab===k}" data-t="${k}">${n} (${dem(k)})</button>`).join('');
  $('tab').querySelectorAll('button').forEach(b=>b.onclick=()=>{st.tab=b.dataset.t;st.tabTay=1;veDe()});
  const v=ds.filter(x=>x.trang_thai===st.tab);
  $('de').innerHTML=v.length?v.map(x=>`<div class="g-de"><span class="t">${e(x.ten)}</span><span class="m"><span>${x.lop?'Lớp '+e(x.lop):'Mọi lớp'}</span><span>${x.so_luot?x.so_luot+' lượt/em':'không giới hạn lượt'}</span>
    <span>${x.so_hs?x.so_hs+' HS nộp · TB '+so(x.tb||0):'chưa có bài nộp'}</span></span>
    <span class="n"><a class="g-btn" href="/${encodeURIComponent(x.slug)}/" target="_blank" rel="noopener">▶ Làm thử</a><button class="g-btn" data-l="${e(location.origin+'/'+x.slug+'/')}">Chép link</button></span></div>`).join('')
   :`<div class="g-rong"><b>Không có đề ${TT[st.tab][0].toLowerCase()}</b>Đăng đề từ ứng dụng ra đề (🌐 Link thi trực tuyến).</div>`;
  $('de').querySelectorAll('[data-l]').forEach(b=>b.onclick=()=>{navigator.clipboard.writeText(b.dataset.l).then(()=>toast('Đã chép link'))})}
 $('tim').oninput=e=>{st.q=e.target.value.trim();veBG()};
 $('tim').onkeydown=e=>{if(e.key==='Enter'){const a=$('bg').querySelector('.g-cards .g-card');if(a)a.click()}if(e.key==='Escape'){e.target.value='';st.q='';veBG()}};
 document.addEventListener('keydown',e=>{if(e.key==='/'&&document.activeElement!==$('tim')&&!/INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName)){e.preventDefault();$('tim').focus()}});
 $('g-th').onclick=()=>{const chay=()=>TongHop.mo({goi:(v,d)=>fetch('/api/gv/'+v,{method:'POST',credentials:'same-origin',headers:{'content-type':'application/json'},body:JSON.stringify(d||{})}).then(r=>r.json())});
  if(window.TongHop)return chay();const sc=document.createElement('script');sc.src='/_gv/tong_hop.js?v='+Date.now();sc.onload=chay;sc.onerror=()=>toast('Chưa tải được — thầy Đăng lại tất cả trong ứng dụng');document.head.appendChild(sc)};
 document.getElementById('thoat').onclick=async ev=>{ev.preventDefault();await fetch('/api/dang-xuat',{method:'POST'});location.href='/dang-nhap/'};
 veStat();veLoc();veBG();veDe();
 $('bg').innerHTML='<div class="g-rong">Đang tải bài giảng…</div>';
 fetch('/bai-giang/muc-luc.json',{credentials:'same-origin',cache:'no-store'}).then(r=>r.ok?r.json():[]).catch(()=>[]).then(d=>{BG=Array.isArray(d)?d:[];veStat();veLoc();veBG()});
}
"""

TRANG_CHU = """<!DOCTYPE html><html lang="vi"><head>""" + KIEU + GV_CSS + """<title>Toán — thầy Vũ Tiến Lực</title></head><body><div class="vo"><div class="the">
<h1>Trang học Toán</h1><p class="phu dau">Thầy Vũ Tiến Lực – Trường THPT Nguyễn Hữu Cảnh</p><div id="nd">Đang tải…</div></div></div><script>""" + GV_JS + """
const LOP=__LOP__,nd=document.getElementById('nd'),e=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
fetch('/api/toi',{credentials:'same-origin'}).then(r=>r.json()).then(t=>{
 if(!t.ok){nd.innerHTML='<p>Học sinh đăng nhập bằng tài khoản thầy cấp để làm bài kiểm tra.</p><a href="/dang-nhap/"><button>Đăng nhập</button></a>';return}
 if(t.doi_mk){location.href='/dang-nhap/?doi=1';return}
 if(t.vai==='gv'){veGV(t);return}
 let h='<p>'+(t.vai==='gv'?'Tài khoản giáo viên':'Xin chào <b>'+e(t.ho_ten||'')+'</b>'+(t.lop?' — lớp '+e(t.lop):''))+' · <a href="#" id="thoat">Đăng xuất</a></p>';
 if(t.vai==='gv'){const TT={dang_mo:'đang mở',da_cong_bo:'đã công bố lời giải',da_dong:'đã đóng'};
  h+='<h3>Đề thi — làm thử (không giới hạn lượt, không lưu điểm)</h3>'+((t.de||[]).length?t.de.map(x=>'<a class="de" href="/'+e(x.slug)+'/"><b>'+e(x.ten)+'</b><span class="nho">'+(x.lop||'mọi lớp')+' · '+(TT[x.trang_thai]||'')+'</span></a>').join(''):'<p class="phu">Chưa đăng đề nào.</p>');
  h+='<h3>Bài giảng</h3>'+(LOP.length?LOP.map(l=>'<a class="de" href="/toan'+l+'/"><b>Toán '+l+'</b><span class="nho">mục lục</span></a>').join(''):'<p class="phu">Chưa có bài giảng.</p>')}
 else{h+='<h3>Bài kiểm tra của em</h3>'+((t.de||[]).length?t.de.map(x=>'<a class="de" href="/'+e(x.slug)+'/"><b>'+e(x.ten)+'</b><span class="nho">'+
  (x.da_lam?'Đã làm '+x.da_lam+' lần'+(x.cao_nhat!=null?' · cao nhất '+Number(x.cao_nhat).toFixed(2).replace('.',','):''):'Chưa làm')+(x.con_lai!=null?' · còn '+x.con_lai+' lượt':'')+(x.cong_bo?' · có lời giải':'')+'</span></a>').join(''):'<p class="phu">Hiện chưa có bài kiểm tra nào cho lớp em.</p>');
  h+='<div id="hs-phieu"></div>';
  if((t.loi_nhan||[]).length)h='<div id="loi-nhan">'+t.loi_nhan.map(m=>'<div class="ln" data-id="'+m.id+'"><div class="ln-dau">💌 Thầy nhắn em <span class="nho">'+new Date(m.tao_luc).toLocaleDateString('vi-VN')+'</span></div><div class="ln-noi">'+e(m.noi_dung).replace(/\\n/g,'<br>')+'</div><button class="ln-ok">Em đã đọc 👍</button></div>').join('')+'</div>'+h;
  fetch('/bai-giang/hs.json',{credentials:'same-origin',cache:'no-store'}).then(r=>r.ok?r.json():[]).catch(()=>[]).then(ds=>{
   const k=parseInt(t.lop||'');ds=(ds||[]).filter(x=>!k||x.lop===k);if(!ds.length)return;
   document.getElementById('hs-phieu').innerHTML='<h3>Phiếu học tập &amp; bài học</h3>'+ds.map(x=>'<a class="de" href="/bai-giang/'+encodeURIComponent(x.slug)+'/"><b>'+e(x.ten)+'</b><span class="nho">'+(x.loai_bg==='phieu'?'Phiếu học tập':x.kieu==='pdf'?'PDF':'Bài giảng')+'</span></a>').join('')})}
 nd.innerHTML=h;nd.querySelectorAll('.ln-ok').forEach(b=>b.onclick=async()=>{const x=b.closest('.ln');b.disabled=true;b.textContent='Cảm ơn em! 💪';
  await fetch('/api/loi-nhan/da-xem',{method:'POST',credentials:'same-origin',headers:{'content-type':'application/json'},body:JSON.stringify({id:+x.dataset.id})}).catch(()=>{});setTimeout(()=>x.remove(),900)});
 document.getElementById('thoat').onclick=async ev=>{ev.preventDefault();await fetch('/api/dang-xuat',{method:'POST'});location.href='/dang-nhap/'};
}).catch(()=>{nd.innerHTML='<p>Không kết nối được máy chủ.</p>'});
</script></body></html>"""


def trang_chu():
    lop = sorted({int(x["lop"]) for x in danh_sach() if x.get("loai") == "bai_giang" and x.get("trang_thai") == "hien" and x.get("lop")})
    return TRANG_CHU.replace("__LOP__", json.dumps(lop))


def trang_dong(ten):
    return TRANG.format(tieu=ten.replace("<", "&lt;"), noi="<p><b>Bài thi đã đóng.</b></p><p>Liên hệ thầy nếu em cần làm lại.</p>")


def ghi_nang_cap_phieu():
    """site/_phieu/tc.css + tc.js: phần trình chiếu slide + nền sáng/tối lấy từ mẫu phiếu mới nhất.
    Máy chủ (middleware) tự chèn vào các phiếu HTML đăng từ bản cũ chưa có nút ▶ Trình chiếu."""
    import phieu_web
    t = phieu_web.TRANG
    css = t[t.index(":root[data-nen=toi]"):t.index("*{box-sizing:border-box}")]
    sang = re.search(r":root\{(--bg:[^}]*)\}", t).group(1)
    css = ":root[data-nen=sang]{" + sang + "}\n" + css
    js = t[t.index("// ================= TRÌNH CHIẾU TỪNG SLIDE"):t.rindex("</script>")]
    dau = ("(()=>{const v=document.querySelector('.thanh .vo');if(v&&!document.getElementById('nut-tc'))v.insertAdjacentHTML('beforeend',"
           "'<button class=\"nut\" id=\"nut-nen\" title=\"Nền trang: Tự động / Sáng / Tối\">🌓 Tự động</button>"
           "<button class=\"nut\" id=\"nut-tc\" title=\"Trình chiếu từng slide (phím P)\" style=\"background:#1e40af;color:#fff;border-color:#1e40af\">▶ Trình chiếu</button>')})();\n")
    d = os.path.join(SITE, "_phieu"); os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "tc.css"), "w", encoding="utf-8").write(css)
    open(os.path.join(d, "tc.js"), "w", encoding="utf-8").write(dau + js)


def ghi_site():
    os.makedirs(SITE, exist_ok=True)
    open(os.path.join(SITE, "index.html"), "w", encoding="utf-8").write(trang_chu())
    _dat_trang("dang-nhap", TRANG_DN)
    try:
        ghi_nang_cap_phieu()
    except Exception:
        pass
    os.makedirs(os.path.join(SITE, "_gv"), exist_ok=True)
    shutil.copy(os.path.join(os.path.dirname(os.path.abspath(__file__)), "tong_hop.js"), os.path.join(SITE, "_gv", "tong_hop.js"))
    open(os.path.join(SITE, "_headers"), "w", encoding="utf-8").write(
        "/*\n  X-Robots-Tag: noindex, nofollow\n  Cache-Control: no-cache\n")
    open(os.path.join(SITE, "404.html"), "w", encoding="utf-8").write(
        TRANG.format(tieu="Không có đề này", noi="<p>Kiểm tra lại đường link thầy gửi.</p>"))


def _dat_trang(slug, noi_dung):
    d = os.path.join(SITE, slug); os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(noi_dung)


# ---------------------------------------------------------------- tạo / đổi trạng thái
def them_de(slug, ten, html_goc, an_dap_an=True, phut=None, ghi_de=False, lop_giao="", so_luot=2, goi_y_ai=False):
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
    html, so = ban_truc_tuyen(html_goc, slug, an_dap_an, goi_y_ai)
    ghi_site(); _dat_trang(slug, html)
    ds = [x for x in ds if x["slug"] != slug or x.get("loai") == "bai_giang"]
    ds.insert(0, {"slug": slug, "ten": ten, "tao_luc": datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
                  "trang_thai": "dang_mo" if an_dap_an else "da_cong_bo", "so_cau": so, "phut": phut,
                  "lop_giao": chuan_lop(lop_giao), "so_luot": int(so_luot), "goi_y_ai": bool(goi_y_ai)})
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
                  "lop_giao": chuan_lop(lop_giao), "so_luot": int(so_luot),
                  "goi_y_ai": any(x.get("goi_y_ai") for x in ds if x["slug"] in cac_con)})
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
        _dat_trang(slug, ban_truc_tuyen(goc, slug, tt == "dang_mo", x.get("goi_y_ai"))[0])
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
<meta name="robots" content="noindex,nofollow"><title>Bài giảng Toán {lop}</title><meta http-equiv="refresh" content="0;url=/?lop={lop}"><script>location.replace('/?lop={lop}')</script><style>body{{margin:0;font:16px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:#eef3f9;color:#1f2937}}
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
    os.makedirs(os.path.join(SITE, "bai-giang"), exist_ok=True)
    the = [_the_bg(x) for x in ds if x.get("loai") == "bai_giang" and x.get("trang_thai") == "hien"]
    json.dump(the, open(os.path.join(SITE, "bai-giang", "muc-luc.json"), "w", encoding="utf-8"), ensure_ascii=False)
    # học sinh: chỉ những bài thầy cho phép (phiếu học tập…), theo khối lớp
    json.dump([{k: x[k] for k in ("slug", "ten", "lop", "loai_bg", "kieu", "ngay", "chuong", "bai_so")} for x in the if x.get("hs")],
              open(os.path.join(SITE, "bai-giang", "hs.json"), "w", encoding="utf-8"), ensure_ascii=False)
    open(os.path.join(SITE, "index.html"), "w", encoding="utf-8").write(trang_chu())


def _ngay_iso(s):
    m = re.match(r"(\d{2})/(\d{2})/(\d{4})(?:\s+(\d{2}:\d{2}))?", s or "")
    return f"{m.group(3)}-{m.group(2)}-{m.group(1)}T{m.group(4) or '00:00'}" if m else (s or "")


def _so_la_ma(v):
    if v.isdigit():
        return int(v)
    g = {"I": 1, "V": 5, "X": 10}; t = 0
    for i, c in enumerate(v):
        t += -g[c] if i + 1 < len(v) and g[v[i + 1]] > g[c] else g[c]
    return t


def _the_bg(x):
    """Mục bài giảng cho trang tổng quan giáo viên: lớp, chương, bài (số) để xếp theo mục lục."""
    ten = x.get("ten") or ""
    chua_de = bool(re.search(r"chữa đề", ten, re.I) or str(x.get("nguon") or "").startswith("đề "))
    m = re.search(r"\bBài\s+(\d+)", x.get("bai") or ten)
    mc = re.search(r"\bChương\s+([IVX\d]+)", x.get("chuong") or "")
    so_ch = 0
    if mc:
        so_ch = _so_la_ma(mc.group(1))
    return {"slug": x["slug"], "ten": ten, "lop": int(x.get("lop") or 0), "kieu": x.get("kieu") or "html",
            "chuong": x.get("chuong") or "", "chuong_so": x.get("chuong_so") or so_ch, "bai": x.get("bai") or "",
            "bai_so": int(m.group(1)) if m else None, "chua_de": chua_de,
            "ngay": _ngay_iso(x.get("cap_nhat") or x.get("tao_luc")), "kb": x.get("kb"),
            "hs": bool(x.get("hs")), "loai_bg": x.get("loai_bg") or ""}


def dat_hs(slug, hs):
    """Cho / thôi cho học sinh (đúng khối lớp, đã đăng nhập) mở bài giảng / phiếu này."""
    ds = danh_sach()
    x = next((y for y in ds if y["slug"] == slug and y.get("loai") == "bai_giang"), None)
    if not x:
        raise RuntimeError("Không có bài giảng " + slug)
    x["hs"] = bool(hs); luu_ds(ds); ghi_muc_luc()


def them_bai_giang(slug, ten, lop, kieu, du_lieu, ghi_de=False, nguon="", chuong="", bai="", chuong_so=0, hs=None, loai_bg=""):
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
                  "kb": round(len(du_lieu) / 1024),
                  **({"hs": bool(hs)} if hs is not None else ({"hs": True} if (cu or {}).get("hs") else {})),
                  **({"loai_bg": loai_bg} if loai_bg else ({"loai_bg": cu["loai_bg"]} if (cu or {}).get("loai_bg") else {})),
                  **({"chuong": chuong} if chuong else {}), **({"bai": bai} if bai else {}), **({"chuong_so": int(chuong_so)} if chuong_so else {})})
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
PHIEN_BAN_SCHEMA = 6


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
        if not c.get("schema"):
            in_ra("Tạo bảng tài khoản, đề, bài làm…")
            rc, ra = _chay(["d1", "execute", TEN_DB, "--remote", "--file", "schema.sql", "--yes"], in_ra, 240)
            if rc != 0:
                raise RuntimeError("Chưa tạo được bảng dữ liệu (xem nhật ký).")
        else:
            for v in range(int(c["schema"]) + 1, PHIEN_BAN_SCHEMA + 1):
                f = f"nang_cap_{v}.sql"
                shutil.copy(os.path.join(MAY_CHU, f), os.path.join(THU, f))
                in_ra(f"Nâng cấp cơ sở dữ liệu lên bản {v}…")
                rc, ra = _chay(["d1", "execute", TEN_DB, "--remote", "--file", f, "--yes"], in_ra, 240)
                if rc != 0 and "duplicate column" not in ra.lower():
                    raise RuntimeError("Chưa nâng cấp được cơ sở dữ liệu (xem nhật ký).")
        c["schema"] = PHIEN_BAN_SCHEMA; _luu_ch(c)
    if bi_mat().get("chua_dat"):
        _dat_bi_mat(c, in_ra)


def _ssl():
    """Python tải từ python.org trên macOS thường thiếu bộ chứng chỉ → dùng certifi hoặc /etc/ssl/cert.pem của macOS."""
    import ssl
    ctx = ssl.create_default_context()
    if ctx.cert_store_stats().get("x509_ca"):        # Python có sẵn bộ chứng chỉ → dùng luôn
        return ctx
    for f in ((__import__("certifi").where() if _co_certifi() else None), "/etc/ssl/cert.pem", "/private/etc/ssl/cert.pem"):
        if f and os.path.exists(f):
            try:
                return ssl.create_default_context(cafile=f)
            except Exception:
                pass
    return ssl.create_default_context()


def _co_certifi():
    try:
        import certifi  # noqa
        return True
    except Exception:
        return False


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
        with urllib.request.urlopen(req, timeout=40, context=_ssl() if url.startswith("https") else None) as r:
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


def lam_lai_trang_de(in_ra=print):
    """Dựng lại mọi trang đề từ bản gốc theo mã vá mới nhất (sửa lỗi/giao diện áp cho cả đề đã đăng)."""
    n = 0
    for x in danh_sach():
        if x.get("loai") in ("bai_giang", "nhom") or x.get("trang_thai") == "da_dong":
            continue
        p = os.path.join(DL, x["slug"] + ".goc.html")
        if os.path.exists(p):
            try:
                _dat_trang(x["slug"], ban_truc_tuyen(open(p, encoding="utf-8").read(), x["slug"], x.get("trang_thai") != "da_cong_bo",
                                                     x.get("goi_y_ai"))[0]); n += 1
            except Exception as e:
                in_ra(f"   ⚠ chưa dựng lại được đề {x['slug']}: {e}")
    if n:
        in_ra(f"   cập nhật giao diện {n} trang đề")


_PL = {}


def phan_loai(x, ds=None):
    """Khối / chương / bài của một đề hoặc bài giảng (để xếp thư viện theo mục lục)."""
    from nh_core import tai_id_map, lop_tu_so, ky_thi
    ten = x.get("ten") or ""
    m_lop = re.search(r"(?:toán|lớp|lop)\s*(1[0-2]|[6-9])\b", ten, re.I) or re.search(r"\b(1[0-2]|[6-9])[A-Z]\d", x.get("lop_giao") or "")
    if x.get("loai") == "bai_giang":
        t = _the_bg(x)
        lop_bg = t["lop"] or (int(m_lop.group(1)) if m_lop else 0)
        if not t["chuong_so"] and t["chuong"]:
            t["chuong_so"] = _so_chuong(lop_bg, t["chuong"])
        return _ten_chuong({"lop": lop_bg, "chuong": t["chuong"], "chuong_so": t["chuong_so"] or 0,
                "bai": t["bai"], "bai_so": t["bai_so"] or 0})
    if x.get("loai") == "nhom":
        con = next((y for y in (ds or danh_sach()) if y["slug"] in (x.get("con") or [])), None)
        r = dict(phan_loai(con, ds)) if con else {"lop": 0, "chuong": "", "chuong_so": 0, "bai": "", "bai_so": 0}
        return r
    p = os.path.join(DL, x["slug"] + ".goc.html")
    khoa = (x["slug"], os.path.getmtime(p) if os.path.exists(p) else 0)
    if khoa in _PL:
        return _PL[khoa]
    keys = []
    if os.path.exists(p):
        try:
            d = json.loads(KHOI_DL.search(open(p, encoding="utf-8").read()).group(2))
            keys = [q.get("ma_dang") for q in d.get("questions", []) if q.get("ma_dang")]
        except Exception:
            keys = []
    r = {"lop": int(m_lop.group(1)) if m_lop else 0, "chuong": "", "chuong_so": 0, "bai": "", "bai_so": 0}
    if keys:
        import collections as C
        idm = tai_id_map()
        lop = C.Counter(lop_tu_so(k[0]) for k in keys).most_common(1)[0][0]
        cua = [k for k in keys if lop_tu_so(k[0]) == lop]
        ch = C.Counter(k[:3] for k in cua); bai = C.Counter(k.split("-")[0] for k in cua)
        r["lop"] = lop
        if len(ch) == 1:
            v = idm.get(cua[0], {})
            r["chuong"] = (v.get("chap_name") or "").strip(); r["chuong_so"] = int(cua[0][2])
            if len(bai) == 1:
                mb = re.match(r"\d[A-Z]\d+\?(\d+)", cua[0]); r["bai_so"] = int(mb.group(1)) if mb else 0
                r["bai"] = f"Bài {r['bai_so']}. " + (v.get("lesson_name") or "").strip()
        else:
            r["chuong_so"] = 99; r["chuong"] = "Đề kiểm tra – Ôn thi" + ("" if ky_thi(ten) == "Đề kiểm tra khác" else " · " + ky_thi(ten))
    if not r["chuong"] and ky_thi(ten) != "Đề kiểm tra khác":
        r["chuong_so"] = 99; r["chuong"] = "Đề kiểm tra – Ôn thi · " + ky_thi(ten)
    r = _ten_chuong(r)
    _PL[khoa] = r
    return r


_CH = {}


def _so_chuong(lop, ten):
    """Số chương theo tên chương (lấy từ danh mục mã dạng), để phiếu/bài giảng gộp đúng nhóm với đề cùng chương."""
    from nh_core import tai_id_map, lop_tu_so, ten_khong_dau
    if not _CH:
        for k, v in tai_id_map().items():
            m = re.match(r"(\d)[A-Z](\d)", k)
            if m and v.get("chap_name"):
                _CH.setdefault((lop_tu_so(m.group(1)), ten_khong_dau(v["chap_name"]).lower().strip()), int(m.group(2)))
    ten = ten_khong_dau(re.sub(r"^\s*Chương\s+[IVX\d]+\s*[.:–-]?\s*", "", ten)).lower().strip()
    return _CH.get((int(lop or 0), ten), 0)


def _ten_chuong(r):
    """Cùng một kiểu tên chương cho đề và bài giảng: 'Chương N. Tên' (để gộp đúng một nhóm)."""
    so, ten = r.get("chuong_so") or 0, re.sub(r"^\s*Chương\s+[IVX\d]+\s*[.:–-]?\s*", "", r.get("chuong") or "")
    if 0 < so < 99 and ten:
        r["chuong"] = f"Chương {so}. {ten}"
    return r


def dat_thu_muc(slug, thu_muc):
    """Nhớ thư mục phiếu gốc (de-da-ra/…) để sau này dựng lại HTML bằng mẫu mới."""
    ds = danh_sach()
    for x in ds:
        if x["slug"] == slug and x.get("loai") == "bai_giang":
            x["thu_muc"] = thu_muc
    luu_ds(ds)


def tim_thu_muc_phieu(x):
    """Thư mục phiếu gốc: đã nhớ, hoặc tìm PhieuHocTap_Web.html trong de-da-ra trùng nội dung trang đang đăng."""
    goc = os.path.dirname(THU)
    if x.get("thu_muc") and os.path.isfile(os.path.join(goc, x["thu_muc"], "tex", "phieu_web.json")):
        return os.path.join(goc, x["thu_muc"])
    p = os.path.join(SITE, "bai-giang", x["slug"], "index.html")
    if not os.path.exists(p):
        p = os.path.join(AN, x["slug"], "index.html")
    try:
        dang = re.sub(r'<meta name="robots"[^>]*>', "", open(p, encoding="utf-8").read())
    except OSError:
        return None
    for g, _, tep in os.walk(os.path.join(goc, "de-da-ra")):
        if "PhieuHocTap_Web.html" in tep and os.path.isfile(os.path.join(g, "tex", "phieu_web.json")):
            try:
                if re.sub(r'<meta name="robots"[^>]*>', "", open(os.path.join(g, "PhieuHocTap_Web.html"), encoding="utf-8").read()) == dang:
                    return g
            except OSError:
                pass
    return None


def dat_goi_y(slug, bat):
    """Bật / tắt Gợi ý AI cho đề (link chung: áp cho mọi mã con), dựng lại trang."""
    ds = danh_sach()
    x = next((y for y in ds if y["slug"] == slug and y.get("loai") != "bai_giang"), None)
    if not x:
        raise RuntimeError("Không có đề " + slug)
    cac = [y for y in ds if y["slug"] in (x.get("con") or [])] if x.get("loai") == "nhom" else [x]
    x["goi_y_ai"] = bool(bat)
    for y in cac:
        y["goi_y_ai"] = bool(bat)
        p = os.path.join(DL, y["slug"] + ".goc.html")
        if y.get("trang_thai") != "da_dong" and os.path.exists(p):
            _dat_trang(y["slug"], ban_truc_tuyen(open(p, encoding="utf-8").read(), y["slug"], y.get("trang_thai") != "da_cong_bo", bat)[0])
    luu_ds(ds)


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
    lam_lai_trang_de(in_ra)
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
