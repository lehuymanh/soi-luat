"""OCR tùy chọn — chỉ Importer được import module này. Không import pytesseract/PIL ở mức module."""

from __future__ import annotations

import importlib.util
import logging
import os
import shutil
import sys
from pathlib import Path

from soiluat.extract import IMAGE_SUFFIXES, ExtractedPage

log = logging.getLogger(__name__)

DPI = 300
MAX_SKEW = 5.0


class OcrUnavailable(RuntimeError):
    """OCR không dùng được (thiếu Tesseract, gói vie hoặc thư viện Python)."""


def _localappdata() -> Path | None:
    v = os.environ.get("LOCALAPPDATA")
    return Path(v) if v else None


def find_tesseract() -> str | None:
    cands: list[Path] = []
    env = os.environ.get("SOILUAT_TESSERACT")
    if env:
        p = Path(env)
        cands.append(p / "tesseract.exe" if p.is_dir() else p)
    if getattr(sys, "frozen", False):  # bản đóng gói dùng Tesseract đi kèm trước bản cài trên máy
        cands.append(Path(sys.executable).parent / "tesseract" / "tesseract.exe")
    which = shutil.which("tesseract")
    if which:
        cands.append(Path(which))
    cands.append(Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"))
    lad = _localappdata()
    if lad:
        cands.append(lad / "Programs" / "Tesseract-OCR" / "tesseract.exe")
    for c in cands:
        if c.is_file():
            return str(c)
    return None


def find_tessdata(tesseract_cmd: str | None) -> tuple[str | None, list[str]]:
    """Thư mục tessdata đầu tiên có vie.traineddata, kèm danh sách ngôn ngữ trong đó."""
    cands: list[Path] = []
    for var in ("SOILUAT_TESSDATA", "TESSDATA_PREFIX"):
        v = os.environ.get(var)
        if v:
            cands += [Path(v), Path(v) / "tessdata"]
    bundled = getattr(sys, "frozen", False) and tesseract_cmd is not None
    if bundled:  # bản đóng gói: tessdata đi kèm Tesseract trước
        cands.append(Path(tesseract_cmd).parent / "tessdata")
    lad = _localappdata()
    if lad:
        cands += [lad / "SoiLuat" / "tessdata", lad / "SoiLuatDemo" / "tessdata"]
    if tesseract_cmd and not bundled:
        cands.append(Path(tesseract_cmd).parent / "tessdata")
    for c in cands:
        if (c / "vie.traineddata").is_file():
            return str(c), sorted(p.stem for p in c.glob("*.traineddata"))
    return None, []


def ocr_status() -> dict:
    cmd = find_tesseract()
    tessdata, langs = find_tessdata(cmd)
    missing_py = [
        m for m in ("pytesseract", "PIL", "pypdfium2") if importlib.util.find_spec(m) is None
    ]
    msgs = []
    if missing_py:
        msgs.append(
            "Chưa cài thư viện OCR cho Python (" + ", ".join(missing_py) + "): "
            "chạy `pip install soiluat[ocr]`."
        )
    if not cmd:
        msgs.append(
            "Không tìm thấy tesseract.exe: cài Tesseract-OCR vào C:\\Program Files\\Tesseract-OCR "
            "hoặc đặt biến môi trường SOILUAT_TESSERACT trỏ tới tesseract.exe."
        )
    if not tessdata:
        msgs.append(
            "Thiếu gói tiếng Việt vie.traineddata: chép vào %LOCALAPPDATA%\\SoiLuat\\tessdata "
            "hoặc đặt biến môi trường SOILUAT_TESSDATA."
        )
    ok = not msgs
    message = f"OCR sẵn sàng: {cmd} · tessdata {tessdata}" if ok else " ".join(msgs)
    return {"ok": ok, "tesseract_cmd": cmd, "tessdata": tessdata, "langs": langs, "message": message}


# --- Tiền xử lý ảnh (chỉ PIL) ---


def _projection_score(small, angle: float) -> float:
    """Phương sai hình chiếu ngang: dòng chữ thẳng hàng thì hàng đen/trắng tách bạch nhất."""
    from PIL import Image

    rot = small.rotate(angle, resample=Image.Resampling.BILINEAR, fillcolor=0)
    rows = rot.resize((1, rot.height), Image.Resampling.BOX).tobytes()  # 1 byte/hàng (mode L)
    mean = sum(rows) / len(rows)
    return sum((r - mean) ** 2 for r in rows) / len(rows)


def estimate_skew(gray) -> float:
    """Góc xoay (độ, ngược chiều kim đồng hồ) làm thẳng dòng chữ, |góc| ≤ 5."""
    from PIL import Image

    scale = 1000 / max(gray.size)
    small = gray.resize(
        (max(1, int(gray.width * scale)), max(1, int(gray.height * scale))),
        Image.Resampling.BILINEAR,
    )
    small = small.point(lambda v: 255 if v < 160 else 0)  # chữ = trắng, nền = 0
    score = {a / 2: _projection_score(small, a / 2) for a in range(-10, 11)}
    best = max(score, key=score.get)
    if score[best] <= score[0.0] * 1.02:
        return 0.0  # trang trắng/không rõ dòng: đừng xoay bừa
    return max(
        (best - 0.25, best, best + 0.25), key=lambda a: _projection_score(small, a)
    )


# Lượt đầu conf thấp hơn mức này mới thử OSD. Không lấy 60: trang xoay 180° vẫn ra conf ~63
# (đo bằng test_real_ocr_rotated_page_uses_osd); scan thật bình thường 88–91.
OSD_CONF = 75.0
OSD_MIN_CHARS_PER_MP = 30  # hoặc chữ quá thưa so với diện tích trang (ký tự chữ / megapixel)


def preprocess(img):
    """Xám, tăng tương phản nhẹ, khử nghiêng nhỏ."""
    from PIL import Image, ImageOps

    # cutoff=0: trang thưa chữ (<1% điểm đen) với cutoff>0 sẽ biến nhiễu nền thành vết đen
    gray = ImageOps.autocontrast(img.convert("L"), cutoff=0)
    angle = estimate_skew(gray)
    if abs(angle) >= 0.3:
        gray = gray.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True, fillcolor=255)
    return gray


def osd_rotation(gray, tess_cfg: str) -> int:
    """Góc OSD cần xoay (0/90/180/270); 0 nếu OSD không chắc hoặc trang quá ít chữ."""
    import pytesseract

    try:
        osd = pytesseract.image_to_osd(gray, config=tess_cfg, output_type=pytesseract.Output.DICT)
    except pytesseract.TesseractError:
        return 0  # OSD cần đủ chữ; trang ít chữ thì bỏ qua
    # OSD trên scan nhiễu đôi khi đoán 180° với độ tin ~1–2: chỉ xoay khi chắc
    if float(osd.get("orientation_conf") or 0) < 5:
        return 0
    return int(osd.get("rotate") or 0)


def ocr_data(gray, tess_cfg: str) -> tuple[str, float | None]:
    """Chữ + độ tin cậy trung bình (0–100) từ image_to_data."""
    import pytesseract

    data = pytesseract.image_to_data(
        gray, lang="vie", config=tess_cfg, output_type=pytesseract.Output.DICT
    )
    lines: dict[tuple[int, int, int], list[str]] = {}
    confs: list[float] = []
    for i, word in enumerate(data["text"]):
        word = (word or "").strip()
        if not word:
            continue
        key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
        lines.setdefault(key, []).append(word)
        conf = float(data["conf"][i])
        if conf >= 0:
            confs.append(conf)
    text = "\n".join(" ".join(ws) for ws in lines.values())
    return text, (round(sum(confs) / len(confs), 1) if confs else None)


def needs_osd(text: str, conf: float | None, size: tuple[int, int]) -> bool:
    letters = sum(1 for c in text if c.isalpha())
    mp = max(size[0] * size[1] / 1e6, 0.01)
    return (conf or 0) < OSD_CONF or letters / mp < OSD_MIN_CHARS_PER_MP


def ocr_image(img, tess_cfg: str, use_osd: bool) -> tuple[str, float | None]:
    """OCR một trang. OSD (≈1 s/trang) chỉ chạy khi lượt đầu kém; giữ bản conf cao hơn."""
    gray = preprocess(img)
    text, conf = ocr_data(gray, tess_cfg)
    if use_osd and needs_osd(text, conf, gray.size):
        rot = osd_rotation(gray, tess_cfg)
        if rot:
            text2, conf2 = ocr_data(gray.rotate(-rot, expand=True, fillcolor=255), tess_cfg)
            if (conf2 or 0) > (conf or 0):
                return text2, conf2
    return text, conf


def _page_images(path: Path, page_nos: list[int]):
    """(page_no, ảnh PIL) cho PDF (render 300 dpi) hoặc từng frame của file ảnh."""
    if path.suffix.lower() in IMAGE_SUFFIXES:
        from PIL import Image

        with Image.open(path) as img:
            for n in page_nos:
                img.seek(n - 1)
                yield n, img.copy()
        return
    import pypdfium2 as pdfium

    from soiluat.pageimg import PDFIUM

    with PDFIUM:
        pdf = pdfium.PdfDocument(str(path))
    try:
        for n in page_nos:
            with PDFIUM:  # khoá chỉ quanh từng trang, không giữ qua yield: Tesseract chậm không chặn /page
                img = _render_page(pdf, n)
            yield n, img
    finally:
        with PDFIUM:
            pdf.close()


def _render_page(pdf, n: int):
    page = pdf[n - 1]
    return page.render(scale=render_dpi(page) / 72).to_pil()


def render_dpi(page) -> float:
    """300 dpi, trừ trang scan độ phân giải thấp hơn: render đúng dpi gốc của ảnh lớn nhất.

    Đo trên d05/d06 (scan 200/150 dpi): phóng lên 300 dpi làm nhoè nét, độ chính xác tụt 3–5 điểm.
    """
    import pypdfium2.raw as pdfium_c

    best = None
    for obj in page.get_objects(filter=[pdfium_c.FPDF_PAGEOBJ_IMAGE], max_depth=2):
        m = obj.get_metadata()
        if best is None or m.width * m.height > best.width * best.height:
            best = m
    if best is None or not best.horizontal_dpi:
        return DPI
    return min(DPI, max(150.0, float(best.horizontal_dpi)))


def maybe_ocr_pages(path: Path, pages: list[ExtractedPage]) -> list[ExtractedPage]:
    """OCR trang ảnh / trang cho_ocr của PDF hoặc file ảnh. Không OCR đè trang chữ tốt.

    Thiếu OCR mà có trang cần OCR → OcrUnavailable. Lỗi một trang → ocr_status='loi_ocr'.
    """
    need = {p.page_no: p for p in pages if p.kind == "image" or p.ocr_status == "cho_ocr"}
    if not need:
        return pages
    st = ocr_status()
    if not st["ok"]:
        raise OcrUnavailable(st["message"])
    import pytesseract

    pytesseract.pytesseract.tesseract_cmd = st["tesseract_cmd"]
    # pytesseract trên Windows giữ nguyên dấu nháy trong config → đường dẫn có dấu cách đi qua biến môi trường
    os.environ["TESSDATA_PREFIX"] = st["tessdata"]
    cfg = "" if " " in st["tessdata"] else f"--tessdata-dir {st['tessdata']}"
    use_osd = "osd" in st["langs"]
    images = _page_images(path, sorted(need))
    while True:
        try:
            n, img = next(images)
        except StopIteration:
            break
        except Exception as e:  # không render/đọc được trang: đánh dấu các trang còn lại
            log.warning("Không đọc được ảnh trang từ %s: %s", path, e)
            for p in need.values():
                if p.ocr_status != "ocr_xong":
                    p.ocr_status = "loi_ocr"
            break
        p = need[n]
        try:
            text, conf = ocr_image(img, cfg, use_osd)
        except Exception as e:
            log.warning("OCR lỗi trang %s của %s: %s", n, path, e)
            p.ocr_status = "loi_ocr"
            continue
        if text.strip():
            p.text = text
            p.extraction_method = "ocr"
        p.ocr_status = "ocr_xong"
        p.ocr_conf = conf
    return pages
