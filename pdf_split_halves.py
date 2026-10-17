#!/usr/bin/env python3

import sys
import os
import argparse
from pypdf import PdfReader, PdfWriter
from pypdf.generic import RectangleObject

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".tif"}
PDF_EXTS   = {".pdf"}
 
 
def detect_type(path: str) -> str:
    """拡張子とマジックバイトでファイル種別を返す ('pdf' | 'image')"""
    ext = os.path.splitext(path)[1].lower()
 
    with open(path, "rb") as f:
        header = f.read(8)
 
    is_pdf_magic = header[:4] == b"%PDF"
    is_image_magic = (
        header[:8] == b"\x89PNG\r\n\x1a\n"
        or header[:3] == b"\xff\xd8\xff"
        or header[:4] in (b"RIFF", b"WEBP")
        or header[:2] == b"BM"
        or header[:4] in (b"II\x2a\x00", b"MM\x00\x2a")
    )
 
    if ext in PDF_EXTS or is_pdf_magic:
        if not is_pdf_magic:
            print(f"警告: 拡張子は {ext} ですがPDFマジックバイトが見つかりません。PDFとして処理します。")
        return "pdf"
 
    if ext in IMAGE_EXTS or is_image_magic:
        return "image"
 
    print(f"エラー: 対応していないファイル形式です: {ext}")
    print(f"  対応形式: PDF ({', '.join(sorted(PDF_EXTS))}) / 画像 ({', '.join(sorted(IMAGE_EXTS))})")
    sys.exit(1)
 
 
# ------------------------------------------------------------------ #
# 共通: 分割境界座標の計算
# ------------------------------------------------------------------ #
 
def calc_segments(start: float, end: float, n: int) -> list[tuple[float, float]]:
    """[start, end] を n 等分した (lo, hi) のリストを返す。
    浮動小数点誤差で最終セグメントが微妙にずれないよう、
    最後だけ end を直接使う。
    """
    span = end - start
    segs = []
    for i in range(n):
        lo = start + span * i / n
        hi = start + span * (i + 1) / n if i < n - 1 else end
        segs.append((lo, hi))
    return segs
 
 
# ------------------------------------------------------------------ #
# PDF 処理
# ------------------------------------------------------------------ #
 
def _apply_crop(writer, page, x0: float, y0: float, x1: float, y1: float,
                w: float, h: float) -> None:
    from pypdf.generic import RectangleObject
    p = writer.add_blank_page(width=w, height=h)
    p.merge_page(page)
    p.cropbox  = RectangleObject([x0, y0, x1, y1])
    p.mediabox = RectangleObject([x0, y0, x1, y1])
 
 
def split_pdf(input_path: str, output_path: str, direction: str, n: int) -> None:
    from pypdf import PdfReader, PdfWriter
 
    reader = PdfReader(input_path)
    writer = PdfWriter()
 
    for i, page in enumerate(reader.pages):
        mb = page.mediabox
        x0, y0 = float(mb.left),  float(mb.bottom)
        x1, y1 = float(mb.right), float(mb.top)
        W, H = x1 - x0, y1 - y0
 
        if direction == "h":
            segs = calc_segments(x0, x1, n)
            for lo, hi in segs:
                _apply_crop(writer, page, lo, y0, hi, y1, hi - lo, H)
            seg_w = W / n
            print(f"  Page {i+1}: {W:.1f} x {H:.1f} pt  →  {n} 列 × {seg_w:.1f} x {H:.1f} pt")
        else:
            # PDF は Y 軸が下から上なので、上から順に取るには降順
            segs = calc_segments(y0, y1, n)[::-1]
            for lo, hi in segs:
                _apply_crop(writer, page, x0, lo, x1, hi, W, hi - lo)
            seg_h = H / n
            print(f"  Page {i+1}: {W:.1f} x {H:.1f} pt  →  {n} 行 × {W:.1f} x {seg_h:.1f} pt")
 
    with open(output_path, "wb") as f:
        writer.write(f)
 
 
# ------------------------------------------------------------------ #
# 画像処理
# ------------------------------------------------------------------ #
 
def _suffix_labels(direction: str, n: int) -> list[str]:
    """出力ファイル名のサフィックスリストを返す。
    n=2 のみ方向に合わせた固有名、それ以外はゼロ埋め連番。
    """
    if n == 2:
        return ["_left", "_right"] if direction == "h" else ["_top", "_bottom"]
    digits = len(str(n))
    return [f"_{str(k).zfill(digits)}" for k in range(1, n + 1)]
 
 
def split_image(input_path: str, output_path: str, direction: str, n: int) -> None:
    from PIL import Image
 
    img = Image.open(input_path)
    W, H = img.size
 
    ext = os.path.splitext(output_path)[1].lower().lstrip(".")
    fmt_map = {"jpg": "JPEG", "jpeg": "JPEG", "tif": "TIFF", "tiff": "TIFF"}
    fmt = fmt_map.get(ext, ext.upper())
 
    save_kwargs: dict = {}
    if fmt == "JPEG":
        save_kwargs["quality"] = 95
        save_kwargs["subsampling"] = 0
 
    base, suffix = os.path.splitext(output_path)
    labels = _suffix_labels(direction, n)
 
    if direction == "h":
        segs = calc_segments(0, W, n)
        for label, (lo, hi) in zip(labels, segs):
            lo_i, hi_i = int(round(lo)), int(round(hi))
            piece = img.crop((lo_i, 0, hi_i, H))
            path = f"{base}{label}{suffix}"
            piece.save(path, fmt, **save_kwargs)
            print(f"  {label.lstrip('_'):>8}: {hi_i - lo_i} x {H} px  →  {path}")
    else:
        segs = calc_segments(0, H, n)
        for label, (lo, hi) in zip(labels, segs):
            lo_i, hi_i = int(round(lo)), int(round(hi))
            piece = img.crop((0, lo_i, W, hi_i))
            path = f"{base}{label}{suffix}"
            piece.save(path, fmt, **save_kwargs)
            print(f"  {label.lstrip('_'):>8}: {W} x {hi_i - lo_i} px  →  {path}")
 
 
# ------------------------------------------------------------------ #
# エントリーポイント
# ------------------------------------------------------------------ #
 
def main():
    parser = argparse.ArgumentParser(
        prog="cleave",
        description="PDF・画像ファイルを N 等分します。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "例:\n"
            "  cleave input.pdf                      # PDF を左右 2 分割（デフォルト）\n"
            "  cleave -d v input.pdf                 # PDF を上下 2 分割\n"
            "  cleave -n 3 input.pdf                 # PDF を左右 3 分割\n"
            "  cleave -d v -n 4 input.pdf out.pdf    # PDF を上下 4 分割・出力先指定\n"
            "  cleave -n 3 photo.png                 # 画像を左右 3 分割\n"
            "  cleave -d v -n 2 photo.jpg out.jpg    # 画像を上下 2 分割\n"
        ),
    )
    parser.add_argument(
        "--direction", "-d",
        choices=["h", "v"],
        default="h",
        metavar="{h,v}",
        help="分割方向: h=左右（デフォルト）, v=上下",
    )
    parser.add_argument(
        "--number", "-n",
        type=int,
        default=2,
        metavar="N",
        help="分割数（デフォルト: 2）",
    )
    parser.add_argument("input",  help="入力ファイル（PDF または画像）")
    parser.add_argument("output", nargs="?", help="出力ファイル（省略時は input_split.<ext>）")
 
    args = parser.parse_args()
 
    if args.number < 1:
        print("エラー: -n には 1 以上の整数を指定してください。")
        sys.exit(1)
 
    input_path = args.input
    if not os.path.isfile(input_path):
        print(f"エラー: ファイルが見つかりません: {input_path}")
        sys.exit(1)
 
    file_type = detect_type(input_path)
 
    if args.output:
        output_path = args.output
    else:
        base, ext = os.path.splitext(input_path)
        output_path = base + "_split" + (ext if ext else ".pdf")
 
    direction_label = "左右（水平）" if args.direction == "h" else "上下（垂直）"
    type_label      = "PDF" if file_type == "pdf" else "画像"
    print(f"入力    : {input_path}  [{type_label}]")
    print(f"出力    : {output_path}")
    print(f"分割方向: {direction_label}")
    print(f"分割数  : {args.number}")
    print()
 
    if file_type == "pdf":
        split_pdf(input_path, output_path, args.direction, args.number)
        print(f"\n完了: {output_path}")
    else:
        split_image(input_path, output_path, args.direction, args.number)
        print("\n完了")
 
 
if __name__ == "__main__":
    main()
