# -*- coding: utf-8 -*-
"""📚 ÔN THI HỌC KÌ — LÝ THUYẾT: trắc nghiệm 4 phương án CHỈ kiểm tra công thức, định nghĩa, tính chất (ghi nhớ để giải toán).

Luồng: chọn nhiều bài (mỗi bài một số câu) → prompt() cho AI (ChatGPT / Gemini / Claude hoặc gọi API) → dán kết quả
→ ứng dụng đọc, soát lỗi (de_ngoai.kiem_tat_ca) → Trộn đề (tron_de: nhiều mã đề, PDF đề + lời giải, Excel đáp án,
Word K12Online chỉ đánh số câu — không có "Phần I" vì đề chỉ có một phần) hoặc nhập vào ngân hàng.
Câu hỏi chỉ ở mức Nhận biết (N) và Thông hiểu (H); phương án nhiễu là các cách NHỚ SAI hay gặp (bẫy).
"""
import re
import kho_kien_thuc
from nh_core import tai_id_map

DOI_TUONG_KT = 2600          # độ dài tối đa phần kiến thức tham khảo mỗi bài trong prompt


def chia_muc(n, ti_le_n):
    """n câu → (số Nhận biết, số Thông hiểu) theo tỉ lệ % Nhận biết."""
    so_n = max(0, min(n, round(n * ti_le_n / 100)))
    return so_n, n - so_n


def _kien_thuc_gon(bai):
    t = kho_kien_thuc.doc(bai)
    if not t.strip():
        return ""
    t = re.split(r"^\s*%%\s*DANG\b", t, maxsplit=1, flags=re.M)[0]       # bỏ phương pháp từng dạng, giữ lý thuyết
    t = re.sub(r"(?<!\\)%[^\n]*", "", t)
    t = re.sub(r"\n{3,}", "\n\n", t).strip()
    return t[:DOI_TUONG_KT] + ("\n…" if len(t) > DOI_TUONG_KT else "")


def prompt(cfg):
    import de_ngoai
    cfg = cfg or {}
    ds = [(x.get("bai"), max(0, min(60, int(x.get("so") or 0)))) for x in (cfg.get("bai") or [])]
    ds = [(b, n) for b, n in ds if b and n]
    if not ds:
        raise ValueError("Chọn ít nhất một bài và nhập số câu.")
    cac = kho_kien_thuc.cac_bai(tai_id_map())
    ti_le = max(0, min(100, int(cfg.get("ti_le_n") if cfg.get("ti_le_n") not in (None, "") else 60)))
    hang, kt, tong = [], [], 0
    for b, n in ds:
        x = cac.get(b)
        if not x:
            raise ValueError(f"Không tìm thấy bài {b}.")
        so_n, so_h = chia_muc(n, ti_le)
        tong += n
        hang.append(f"| Toán {x['lop']} — Bài {x['so_bai']}. {x['ten_bai']} ({x['ten_chuong']}) | `{b}` | {so_n} | {so_h} | **{n}** |")
        g = _kien_thuc_gon(b) if cfg.get("kem_kt", True) else ""
        if g:
            kt.append(f"### `{b}` — {x['ten_bai']}\n{g}")
    chung, dm, so_dm = de_ngoai._phan_chung([b for b, _ in ds])
    ghi = (cfg.get("ghi_chu") or "").strip()
    ten = (cfg.get("ten") or "").strip()
    p = f"""# NHIỆM VỤ
Bạn là giáo viên Toán THPT giỏi (chương trình GDPT 2018, sách Kết nối tri thức). Soạn **{tong} câu trắc nghiệm 4 phương án**
để học sinh **ÔN THI HỌC KÌ PHẦN LÝ THUYẾT**{(' — ' + ten) if ten else ''}: câu hỏi **CHỈ kiểm tra công thức, định nghĩa, tính chất,
định lí, quy tắc, điều kiện, kí hiệu** của các bài dưới đây — giúp học sinh **ghi nhớ đúng công thức để giải toán**.

## Số câu từng bài (đúng bảng, đúng mức)
| Bài | Mã bài | Nhận biết (N) | Thông hiểu (H) | Cộng |
|---|---|---|---|---|
{chr(10).join(hang)}

## Yêu cầu nội dung
1. **Chỉ hỏi lý thuyết**: công thức, định nghĩa, tính chất, định lí, hệ quả, điều kiện xác định / điều kiện có nghĩa, kí hiệu, cách nhận dạng.
   KHÔNG ra bài tính toán nhiều bước. Câu Thông hiểu tối đa **một bước áp dụng trực tiếp** công thức với số liệu nhẩm được
   (vd thay số vào công thức, nhận ra công thức cần dùng, chọn khẳng định đúng về tính chất cho một ví dụ cụ thể).
2. **Chỉ hai mức**: Nhận biết (N) — nhớ, nhận ra công thức / định nghĩa / tính chất; Thông hiểu (H) — hiểu ý nghĩa, điều kiện,
   phân biệt các công thức gần giống, áp dụng trực tiếp một bước. Ghi mức đúng trong mã `%[…]`.
3. **Phủ đều** các mục kiến thức của từng bài (mỗi công thức / định nghĩa / tính chất quan trọng có câu hỏi), không lặp ý giữa các câu.
4. **Đa dạng cách hỏi**: “Công thức nào sau đây đúng?”, “Khẳng định nào sau đây **sai**?”, “Điều kiện để … là”, điền vào chỗ trống
   (“… bằng”), nhận dạng (“Hàm số / phương trình / mệnh đề nào sau đây là …?”), chọn kết luận đúng cho một trường hợp cụ thể.
   Câu hỏi phủ định in đậm chữ **sai** / **không** bằng `\\textbf{{…}}`.

## Phương án nhiễu — DỄ CHỌN SAI, có BẪY
- Mỗi phương án nhiễu là **một cách nhớ sai thật sự hay gặp** của học sinh, ví dụ: sai dấu (+/−), đảo tử – mẫu, nhầm sin/cos, tan/cot,
  nhầm công thức cộng với công thức nhân, thiếu / thừa hệ số 2 hoặc 1/2, quên bình phương / căn, nhầm $>$ với $\\ge$,
  nhầm khoảng mở – đóng, quên điều kiện ($a\\ne 0$, mẫu khác 0, biểu thức dưới căn không âm…), nhầm định nghĩa của hai khái niệm gần nhau,
  nhầm chiều của bất đẳng thức / chiều biến thiên, nhầm đơn vị (độ – radian).
- 4 phương án **cùng hình thức, độ dài tương đương**, cùng kiểu kí hiệu; phương án đúng không “nổi bật” (không dài hơn, không chi tiết hơn).
- KHÔNG dùng “Cả A và B đều đúng”, “Tất cả đều sai”, “Không có phương án nào”.
- Đáp án đúng **rải đều A, B, C, D** (mỗi chữ khoảng 1/4 số câu, không lặp một chữ quá 3 câu liền).

## Lời giải (để học sinh tự ôn)
`\\loigiai{{…}}` gồm: dòng đầu nêu **công thức / định nghĩa / tính chất đúng**; sau đó dòng **“Bẫy:”** chỉ ngắn gọn vì sao từng phương án nhiễu sai
(vd “A sai vì đảo tử – mẫu; B sai vì quên điều kiện $a\\ne 0$; …”). Mỗi ý một dòng, cuối dòng `\\\\`.
{('## Yêu cầu thêm của giáo viên' + chr(10) + ghi + chr(10)) if ghi else ''}
## Định dạng riêng của lần này
- **Mọi câu** là `\\begin{{ex}}%[mã dạng có chữ mức] … \\choice{{…}}{{…}}{{…}}{{…}} \\loigiai{{…}} \\end{{ex}}` với **đúng một** `\\True`.
- KHÔNG dùng `\\choiceTF` (Đúng/Sai), KHÔNG `\\shortans` (trả lời ngắn), KHÔNG tự luận.
- Mã dạng lấy trong DANH MỤC DẠNG ở cuối của **đúng bài** câu hỏi thuộc về (chọn dạng gần nhất với nội dung lý thuyết), thay `?` bằng N hoặc H.
- Không cần hình vẽ (nếu thật cần, vẽ TikZ nhỏ ngay trong câu).

""" + chung + (("# KIẾN THỨC CỦA CÁC BÀI (tham khảo — bám sát, có thể bổ sung công thức còn thiếu theo SGK)\n" + "\n\n".join(kt) + "\n\n") if kt else "") + f"""# KẾT QUẢ TRẢ VỀ
Một khối mã duy nhất ```latex … ``` chứa đúng {tong} câu, xếp **theo thứ tự bài như bảng**, trong mỗi bài N trước H.
Dòng đầu khối: `% nguồn: Ôn tập lý thuyết học kì{(' — ' + ten) if ten else ''}`. Không lời dẫn ngoài khối mã.
Trước khi trả lời, tự kiểm: đủ số câu từng bài × mức; mỗi câu đúng một `\\True` và phương án đúng thật sự đúng; các phương án nhiễu thật sự sai.

# DANH MỤC DẠNG ({so_dm} dạng) — chỉ dùng các mã dưới đây
{dm}"""
    p = p.replace("Đủ số câu như đề", "Đủ số câu từng bài × mức như bảng")
    return re.sub(r"\n{3,}", "\n\n", p)
