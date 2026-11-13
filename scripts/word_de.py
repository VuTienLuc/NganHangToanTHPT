# -*- coding: utf-8 -*-
"""
XUẤT ĐỀ THI RA WORD (.docx) VỚI BỐ CỤC GIỐNG ĐỀ PDF CHUẨN — mỗi mã đề 2 file:
  Word_De_101.docx       : đầu đề Sở/Trường – Kỳ thi/Môn/Thời gian, ô Mã đề, PHẦN I/II/III, Câu 1., phương án A. B. C. D.
                           tự xếp 4 cột / 2 cột / 1 cột theo độ dài, ý a) b) c) d), "HẾT", chân trang "Trang x/y – Mã đề"
  Word_LoiGiai_101.docx  : như trên + lời giải dưới từng câu (đáp án đúng gạch chân) + bảng đáp án cuối
Công thức: Equation của Word (pandoc) hoặc ảnh SVG thẳng dòng (như k12word). Cỡ chữ 10–14 tuỳ chọn.

  python3 scripts/word_de.py "de-da-ra/<thư mục đề>" [equation|svg] [cỡ chữ]
"""
import os, sys, re, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import k12word as K
from k12word import Docx, Doan, chuyen, tach_cau, chay_xml, xe

TWIP = 20                                   # 1 pt = 20 twip
LE = (850, 851, 850, 1021)                  # lề trên, phải, dưới, trái (≈ đề PDF: 1,5 / 1,5 / 1,5 / 1,8 cm)
RONG = 11906 - LE[1] - LE[3]                # bề rộng vùng chữ (twip)
THUT = 284                                  # thụt lề phương án (0,5 cm)
PHAN = [
    ("TN", "PHẦN I. Câu trắc nghiệm nhiều phương án lựa chọn.",
     "Thí sinh trả lời từ câu 1 đến câu {n}. Mỗi câu hỏi thí sinh chỉ chọn một phương án."),
    ("DS", "PHẦN II. Câu trắc nghiệm đúng sai.",
     "Thí sinh trả lời từ câu 1 đến câu {n}. Trong mỗi ý a), b), c), d) ở mỗi câu, thí sinh chọn đúng hoặc sai."),
    ("TLN", "PHẦN III. Câu trắc nghiệm trả lời ngắn.", "Thí sinh trả lời từ câu 1 đến câu {n}."),
    ("TL", "PHẦN IV. Tự luận.", "Thí sinh trình bày lời giải từ câu 1 đến câu {n}."),
]

def truong_so(ma):                          # trường PAGE / NUMPAGES
    return ('<w:r><w:fldChar w:fldCharType="begin"/></w:r>'
            f'<w:r><w:instrText xml:space="preserve"> {ma} </w:instrText></w:r>'
            '<w:r><w:fldChar w:fldCharType="separate"/></w:r><w:r><w:t>1</w:t></w:r>'
            '<w:r><w:fldChar w:fldCharType="end"/></w:r>')

def chu(s, dd=(), co=None, vien=False):
    rp = "".join(x for x, c in (("<w:b/>", "b"), ("<w:i/>", "i"), ('<w:u w:val="single"/>', "u")) if c in dd)
    if co:
        rp += f'<w:sz w:val="{int(co * 2)}"/><w:szCs w:val="{int(co * 2)}"/>'
    if vien:
        rp += '<w:bdr w:val="single" w:sz="8" w:space="2" w:color="000000"/>'
    return f'<w:r>{"<w:rPr>" + rp + "</w:rPr>" if rp else ""}<w:t xml:space="preserve">{xe(s)}</w:t></w:r>'

def doan(runs, can="left", truoc=0, sau=40, thut=0, tab=(), giu_sau=False):
    tabs = ("<w:tabs>" + "".join(f'<w:tab w:val="{k}" w:pos="{p}"{f" w:leader={chr(34)}{ld}{chr(34)}" if ld else ""}/>'
                                 for k, p, ld in tab) + "</w:tabs>") if tab else ""
    jc = {"center": '<w:jc w:val="center"/>', "right": '<w:jc w:val="right"/>', "both": '<w:jc w:val="both"/>'}.get(can, "")
    ind = f'<w:ind w:left="{thut}"/>' if thut else ""
    kn = "<w:keepNext/>" if giu_sau else ""
    return f'<w:p><w:pPr>{kn}{tabs}<w:spacing w:before="{truoc}" w:after="{sau}"/>{ind}{jc}</w:pPr>{runs}</w:p>'

# ----------------------------------------------------------------------------- ước lượng bề rộng phương án
def rong_uoc(ds_doan, anh, co):
    """Bề rộng (pt) của một phương án; vô cùng nếu nhiều đoạn hoặc có hình."""
    if len(ds_doan) != 1:
        return 1e9
    w = 0.0
    for r in ds_doan[0].chay:
        if r[0] == "t":
            w += len(r[1]) * co * 0.5
        elif r[0] == "br":
            return 1e9
        else:
            m = anh.get(r[1]) or {}
            loai, ma = MANH.get(r[1], ("im", ""))
            if loai == "fig":
                return 1e9
            if "w" in m:
                w += m["w"] * co / 12
            else:
                t = re.sub(r"\\(left|right|displaystyle|textstyle|dfrac|tfrac|frac|mathrm|text|limits)", "", ma)
                t = re.sub(r"\\[A-Za-z]+", "x", t)
                t = re.sub(r"[{}\s^_]", "", t)
                w += len(t) * co * 0.55
    return w

MANH = {}

def ghi_phuong_an(doc, pa, anh, co, nhan, dung=None):
    """Phương án A. B. C. D. (hoặc a) b) c) d)) — tự xếp 4 / 2 / 1 phương án mỗi dòng như \\choice của LaTeX."""
    rong_cot = (RONG - THUT) / TWIP           # pt
    w = max(rong_uoc(x, anh, co) for x in pa) + co * 1.6
    so_cot = 4 if w <= rong_cot / 4 - 6 else 2 if w <= rong_cot / 2 - 6 else 1
    def nhan_xml(j):
        return chu(nhan[j], ("b", "u") if dung is not None and j in dung else ("b",)) + chu(" ")
    if so_cot == 1:
        for j, x in enumerate(pa):
            ds = list(x or [Doan()])
            doc.p.append(doan(nhan_xml(j) + chay_xml(doc, ds[0], anh), thut=THUT, sau=20))
            for d in ds[1:]:
                doc.p.append(doan(chay_xml(doc, d, anh), d.can, thut=THUT, sau=20))
        return
    buoc = int((RONG - THUT) / so_cot)
    tab = [("left", THUT + buoc * k, None) for k in range(1, so_cot)]
    for h in range(0, 4, so_cot):
        runs = ""
        for j in range(h, min(4, h + so_cot)):
            if j > h:
                runs += "<w:r><w:tab/></w:r>"
            runs += nhan_xml(j) + (chay_xml(doc, pa[j][0], anh) if pa[j] else "")
        doc.p.append(doan(runs, thut=THUT, tab=tab, sau=20))

def ghi_doan(doc, ds, anh, dau="", sau=40):
    ds = list(ds or [])
    if dau:
        if ds and ds[0].can != "center":
            doc.p.append(doan(dau + chay_xml(doc, ds[0], anh), "both", sau=sau)); ds = ds[1:]
        else:
            doc.p.append(doan(dau, sau=sau))
    for d in ds:
        doc.p.append(doan(chay_xml(doc, d, anh), "center" if d.can == "center" else "both", sau=sau))

# ----------------------------------------------------------------------------- đầu đề
def dau_de(doc, tt, ma_de, loi_giai):
    o = lambda x: xe(x or "")
    def o_bang(noi):
        return f'<w:tc><w:tcPr><w:tcW w:w="{RONG // 2}" w:type="dxa"/></w:tcPr>{noi}</w:tc>'
    trai = (doan(chu(tt.get("so_gd") or ""), "center", sau=0) + doan(chu(tt.get("truong") or "", ("b",)), "center", sau=0)
            + doan(chu("──────────"), "center", sau=0)
            + doan(chu("(Đề thi có ", ("i",)) + truong_so("NUMPAGES")
                   + chu(" trang)", ("i",)), "center", sau=0))
    phai = (doan(chu(tt.get("ten_ky_thi") or "", ("b",)), "center", sau=0)
            + doan(chu(tt.get("nam_hoc") or "", ("b",)), "center", sau=0)
            + doan(chu("Môn: " + (tt.get("mon") or ""), ("b",)), "center", sau=0)
            + doan(chu(f"Thời gian làm bài: {tt.get('thoi_gian') or ''}, không kể thời gian phát đề", ("i",), co=doc.co_chu - 1),
                   "center", sau=0))
    doc.p.append('<w:tbl><w:tblPr><w:tblW w:w="5000" w:type="pct"/><w:tblLayout w:type="fixed"/></w:tblPr>'
                 f'<w:tblGrid><w:gridCol w:w="{RONG // 2}"/><w:gridCol w:w="{RONG // 2}"/></w:tblGrid>'
                 f'<w:tr>{o_bang(trai)}{o_bang(phai)}</w:tr></w:tbl>')
    if loi_giai:
        doc.p.append(doan(chu(f"ĐÁP ÁN VÀ LỜI GIẢI CHI TIẾT — MÃ ĐỀ {ma_de}", ("b",)), "center", truoc=120, sau=80))
        return
    doc.p.append(doan(chu("Họ, tên thí sinh: ") + "<w:r><w:tab/></w:r>" + "<w:r><w:tab/></w:r>"
                      + chu(f" Mã đề {ma_de} ", ("b",), vien=True),
                      truoc=160, sau=40, tab=[("left", 6800, "dot"), ("right", RONG, None)]))
    doc.p.append(doan(chu("Số báo danh: ") + "<w:r><w:tab/></w:r>", sau=80, tab=[("left", 5200, "dot")]))

def chan_trang(ma_de, loi_giai):
    nhan = f" – {'Lời giải ' if loi_giai else ''}Mã đề {ma_de}"
    return doan(chu("Trang ") + truong_so("PAGE") + chu("/") + truong_so("NUMPAGES") + chu(nhan), "center", sau=0)

# ----------------------------------------------------------------------------- ghép
def xuat(thu_muc_de, in_ra=print, cong_thuc="equation", co_chu=12):
    tex = os.path.join(thu_muc_de, "tex")
    du_lieu = json.load(open(os.path.join(tex, "_k12_cau.json"), encoding="utf-8"))
    try:
        tt = json.load(open(os.path.join(tex, "_thong_tin_de.json"), encoding="utf-8"))
    except OSError:
        tt = {}
    tt = {k: (v or "").replace("--", "–") if isinstance(v, str) else v for k, v in tt.items()}
    co = max(9, min(14, int(co_chu or 12)))
    manh, cau_tach = {}, {}
    for ma_de, ds in du_lieu.items():
        for i, c in enumerate(ds):
            p = tach_cau(c)
            q = {"de": chuyen(p["de"], manh), "pa": [chuyen(x, manh) for x in (p["pa"] or [])],
                 "lg": chuyen(p["lg"], manh) if not p["y_giai"] else None, "y_giai": None, "tln": p["tln"]}
            if p["y_giai"]:
                dau, ys, cuoi = p["y_giai"]
                q["y_giai"] = (chuyen(dau, manh), [chuyen(y, manh) for y in ys], chuyen(cuoi, manh))
            cau_tach[(ma_de, i)] = q
    MANH.clear(); MANH.update(manh)
    in_ra(f"Xuất Word đề thi (bố cục như PDF, chữ {co}pt) cho {len(du_lieu)} mã đề…")
    K.OMML.clear()
    K.OMML.update(K.omml_cong_thuc(manh, in_ra, cong_thuc))
    con_lai = {k: v for k, v in manh.items() if k not in K.OMML}
    anh = K.bien_dich_manh(con_lai, tex, in_ra) if con_lai else {}
    for ma_de, ds in du_lieu.items():
        for loi_giai in (False, True):
            doc = Docx(co_chu=co, le=LE, chan_trang=chan_trang(ma_de, loi_giai))
            dau_de(doc, tt, ma_de, loi_giai)
            dap_an = {}
            for loai, tieu, dan in PHAN:
                cac = [(i, c) for i, c in enumerate(ds) if c["loai"] == loai]
                if not cac:
                    continue
                doc.p.append(doan(chu(tieu + " ", ("b",)) + chu(dan.format(n=len(cac))), "both", truoc=100, sau=60))
                for so, (i, c) in enumerate(cac, 1):
                    q, da = cau_tach[(ma_de, i)], c.get("dap_an") or ""
                    ghi_doan(doc, q["de"], anh, chu(f"Câu {so}.", ("b",)) + chu(" "))
                    if loai == "TN" and q["pa"]:
                        dung = {"ABCD".index(da)} if loi_giai and da in ("A", "B", "C", "D") else None
                        ghi_phuong_an(doc, q["pa"], anh, co, ["A.", "B.", "C.", "D."], dung)
                        dap_an.setdefault(loai, []).append(f"{so}. {da}")
                    elif loai == "DS" and q["pa"]:
                        dung = {j for j, x in enumerate(da) if x == "Đ"} if loi_giai else None
                        ghi_phuong_an(doc, q["pa"], anh, co, ["a)", "b)", "c)", "d)"], dung)
                        dap_an.setdefault(loai, []).append(f"{so}. " + " ".join(f"{'abcd'[j]}){x}" for j, x in enumerate(da)))
                    elif loai == "TLN":
                        dap_an.setdefault(loai, []).append(f"{so}. {K.dap_so_tln(q, da)}")
                    if loi_giai:
                        nhan = chu("Lời giải. ", ("b", "i"))
                        if q["y_giai"]:
                            dau, ys, cuoi = q["y_giai"]
                            ghi_doan(doc, dau, anh, nhan if dau else "")
                            if not dau:
                                doc.p.append(doan(nhan, sau=20))
                            for j, y in enumerate(ys):
                                ghi_doan(doc, y or [Doan()], anh, chu(f"{'abcd'[j]}) ", ("b",)))
                            ghi_doan(doc, cuoi, anh)
                        elif q["lg"]:
                            ghi_doan(doc, q["lg"], anh, nhan)
                        if loai == "TLN":
                            doc.p.append(doan(chu("Đáp số: ", ("b",)) + chu(K.dap_so_tln(q, da)), sau=60))
            doc.p.append(doan(chu("------ HẾT ------", ("b",)), "center", truoc=200, sau=100))
            if loi_giai and dap_an:
                doc.p.append(doan(chu(f"BẢNG ĐÁP ÁN — MÃ ĐỀ {ma_de}", ("b",)), "center", truoc=200, sau=80, giu_sau=True))
                for loai, tieu, _ in PHAN:
                    if dap_an.get(loai):
                        doc.p.append(doan(chu(tieu.split(".")[0] + ".", ("b",)), sau=40, giu_sau=True))
                        doc.bang(dap_an[loai], 4 if loai == "DS" else 6)
            ra = os.path.join(thu_muc_de, f"Word_{'LoiGiai' if loi_giai else 'De'}_{ma_de}.docx")
            doc.luu(ra)
            in_ra(f"  ✓ {os.path.basename(ra)}")

if __name__ == "__main__":
    xuat(sys.argv[1], cong_thuc=(sys.argv[2] if len(sys.argv) > 2 else "equation"),
         co_chu=int(sys.argv[3]) if len(sys.argv) > 3 else 12)
