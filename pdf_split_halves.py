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
 
    # まずマジックバイトで確認（拡張子詐称対策・警告用）
    with open(path, "rb") as f:
        header = f.read(8)
 
    is_pdf_magic   = header[:4] == b"%PDF"
    is_image_magic = (
        header[:8] == b"\x89PNG\r\n\x1a\n"          # PNG
        or header[:3] == b"\xff\xd8\xff"             # JPEG
        or header[:4] in (b"RIFF", b"WEBP")          # WebP (RIFF....WEBP)
        or header[:2] in (b"BM",)                    # BMP
        or header[:4] in (b"II\x2a\x00", b"MM\x00\x2a")  # TIFF
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
# PDF 処理
# ------------------------------------------------------------------ #
 
def _apply_crop(writer, page, x0, y0, x1, y1, w, h):
    from pypdf.generic import RectangleObject
    p = writer.add_blank_page(width=w, height=h)
    p.merge_page(page)
    p.cropbox  = RectangleObject([x0, y0, x1, y1])
    p.mediabox = RectangleObject([x0, y0, x1, y1])
 
 
def split_pdf(input_path: str, output_path: str, direction: str) -> None:
    from pypdf import PdfReader, PdfWriter
 
    reader = PdfReader(input_path)
    writer = PdfWriter()
 
    for i, page in enumerate(reader.pages):
        mb = page.mediabox
        x0, y0 = float(mb.left), float(mb.bottom)
        x1, y1 = float(mb.right), float(mb.top)
        W, H = x1 - x0, y1 - y0
 
        if direction == "h":
            mid = x0 + W / 2
            _apply_crop(writer, page, x0,  y0, mid, y1, W / 2, H)   # 左
            _apply_crop(writer, page, mid, y0, x1,  y1, W / 2, H)   # 右
            print(f"  Page {i+1}: {W:.1f} x {H:.1f} pt  →  left/right {W/2:.1f} x {H:.1f} pt")
        else:
            mid = y0 + H / 2
            _apply_crop(writer, page, x0, mid, x1, y1, W, H / 2)    # 上
            _apply_crop(writer, page, x0, y0,  x1, mid, W, H / 2)   # 下
            print(f"  Page {i+1}: {W:.1f} x {H:.1f} pt  →  top/bottom {W:.1f} x {H/2:.1f} pt")
 
    with open(output_path, "wb") as f:
        writer.write(f)
 
 
# ------------------------------------------------------------------ #
# 画像処理
# ------------------------------------------------------------------ #
 
def split_image(input_path: str, output_path: str, direction: str) -> None:
    from PIL import Image
 
    img = Image.open(input_path)
    W, H = img.size
 
    # 出力フォーマットを拡張子から決定（Pillow の save() に渡す）
    ext = os.path.splitext(output_path)[1].lower().lstrip(".")
    fmt_map = {"jpg": "JPEG", "jpeg": "JPEG", "tif": "TIFF", "tiff": "TIFF"}
    fmt = fmt_map.get(ext, ext.upper())  # png→PNG, webp→WEBP, bmp→BMP, ...
 
    # 保存オプション（JPEG は品質維持、PNG は無損失）
    save_kwargs: dict = {}
    if fmt == "JPEG":
        save_kwargs["quality"] = 95
        save_kwargs["subsampling"] = 0
 
    base, suffix = os.path.splitext(output_path)
 
    if direction == "h":
        mid = W // 2
        left  = img.crop((0,   0, mid, H))
        right = img.crop((mid, 0, W,   H))
 
        left_path  = f"{base}_left{suffix}"
        right_path = f"{base}_right{suffix}"
        left.save(left_path,  fmt, **save_kwargs)
        right.save(right_path, fmt, **save_kwargs)
 
        print(f"  {W} x {H} px  →  left: {mid} x {H} / right: {W - mid} x {H} px")
        print(f"  左 : {left_path}")
        print(f"  右 : {right_path}")
 
    else:
        mid = H // 2
        top    = img.crop((0, 0,   W, mid))
        bottom = img.crop((0, mid, W, H  ))
 
        top_path    = f"{base}_top{suffix}"
        bottom_path = f"{base}_bottom{suffix}"
        top.save(top_path,    fmt, **save_kwargs)
        bottom.save(bottom_path, fmt, **save_kwargs)
 
        print(f"  {W} x {H} px  →  top: {W} x {mid} / bottom: {W} x {H - mid} px")
        print(f"  上 : {top_path}")
        print(f"  下 : {bottom_path}")
 
 
# ------------------------------------------------------------------ #
# エントリーポイント
# ------------------------------------------------------------------ #
 
def main():
    parser = argparse.ArgumentParser(
        prog="cleave",
        description="PDF・画像ファイルを半分に分割します。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "例:\n"
            "  cleave input.pdf                   # PDF を左右分割（デフォルト）\n"
            "  cleave -d v input.pdf              # PDF を上下分割\n"
            "  cleave -d h photo.png              # 画像を左右分割\n"
            "  cleave -d v photo.jpg out.jpg      # 画像を上下分割・出力先指定\n"
        ),
    )
    parser.add_argument(
        "--direction", "-d",
        choices=["h", "v"],
        default="h",
        metavar="{h,v}",
        help="分割方向: h=左右（デフォルト）, v=上下",
    )
    parser.add_argument("input",          help="入力ファイル（PDF または画像）")
    parser.add_argument("output", nargs="?", help="出力ファイル（省略時は input_split.<ext>）")
 
    args = parser.parse_args()
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
    print()
 
    if file_type == "pdf":
        split_pdf(input_path, output_path, args.direction)
        print(f"\n完了: {output_path}")
    else:
        split_image(input_path, output_path, args.direction)
        print("\n完了")
 
 
if __name__ == "__main__":
    main()
