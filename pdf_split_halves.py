#!/usr/bin/env python3

import sys
import os
import argparse
from pypdf import PdfReader, PdfWriter
from pypdf.generic import RectangleObject

def split_page_horizontal(writer: PdfWriter, page, page_num: int) -> None:
    """左右に分割（水平方向）"""
    media_box = page.mediabox
    x0 = float(media_box.left)
    y0 = float(media_box.bottom)
    x1 = float(media_box.right)
    y1 = float(media_box.top)
    width = x1 - x0
    height = y1 - y0
    mid_x = x0 + width / 2

    # 左半分
    left = writer.add_blank_page(width=width / 2, height=height)
    left.merge_page(page)
    left.cropbox  = RectangleObject([x0,    y0, mid_x, y1])
    left.mediabox = RectangleObject([x0,    y0, mid_x, y1])

    # 右半分
    right = writer.add_blank_page(width=width / 2, height=height)
    right.merge_page(page)
    right.cropbox  = RectangleObject([mid_x, y0, x1,   y1])
    right.mediabox = RectangleObject([mid_x, y0, x1,   y1])

    print(f"  Page {page_num + 1}: {width:.1f} x {height:.1f} pt  →  left/right {width / 2:.1f} x {height:.1f} pt")

def split_page_vertical(writer: PdfWriter, page, page_num: int) -> None:
    """上下に分割（垂直方向）"""
    media_box = page.mediabox
    x0 = float(media_box.left)
    y0 = float(media_box.bottom)
    x1 = float(media_box.right)
    y1 = float(media_box.top)
    width = x1 - x0
    height = y1 - y0
    mid_y = y0 + height / 2

    # 上半分（PDFの座標系はY軸が下から上なので、mid_y〜y1 が上）
    top = writer.add_blank_page(width=width, height=height / 2)
    top.merge_page(page)
    top.cropbox  = RectangleObject([x0, mid_y, x1, y1])
    top.mediabox = RectangleObject([x0, mid_y, x1, y1])

    # 下半分
    bottom = writer.add_blank_page(width=width, height=height / 2)
    bottom.merge_page(page)
    bottom.cropbox  = RectangleObject([x0, y0, x1, mid_y])
    bottom.mediabox = RectangleObject([x0, y0, x1, mid_y])

    print(f"  Page {page_num + 1}: {width:.1f} x {height:.1f} pt  →  top/bottom {width:.1f} x {height / 2:.1f} pt")

def split_pdf(input_path: str, output_path: str, direction: str) -> None:
    reader = PdfReader(input_path)
    writer = PdfWriter()

    split_fn = split_page_horizontal if direction == "h" else split_page_vertical

    for page_num, page in enumerate(reader.pages):
        split_fn(writer, page, page_num)

    with open(output_path, "wb") as f:
        writer.write(f)

def main():
    parser = argparse.ArgumentParser(
        description="Splits each page of a PDF in half.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Example:\n"
            "  python pdf_split_halves.py input.pdf               # 左右分割（デフォルト）\n"
            "  python pdf_split_halves.py --direction v input.pdf # 上下分割\n"
            "  python pdf_split_halves.py -d h input.pdf out.pdf  # 左右分割・出力先指定\n"
        ),
    )
    parser.add_argument(
        "--direction", "-d",
        choices=["h", "v"],
        default="h",
        metavar="{h,v}",
        help="Split direction: h=left/right (default), v=top/bottom",
    )
    parser.add_argument("input", help="Input PDF file")
    parser.add_argument("output", nargs="?", help="Output PDF file (default: input_split.pdf)")

    args = parser.parse_args()

    input_path = args.input
    if not os.path.isfile(input_path):
        print(f"Error: File not found: {input_path}")
        sys.exit(1)
    if not input_path.lower().endswith(".pdf"):
        print(f"Warning: Extension is not .pdf: {input_path}")

    if args.output:
        output_path = args.output
    else:
        base, ext = os.path.splitext(input_path)
        output_path = base + "_split" + (ext if ext else ".pdf")

    direction_label = "Left and right (horizontal)" if args.direction == "h" else "Up and down (vertical)"
    print(f"Input    : {input_path}")
    print(f"Output   : {output_path}")
    print(f"Split direction: {direction_label}")
    print()

    split_pdf(input_path, output_path, args.direction)

    print(f"\nCOMPLETED: {output_path}")

if __name__ == "__main__":
    main()
