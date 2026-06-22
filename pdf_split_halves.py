#!/usr/bin/env python3

import sys
import os
from pypdf import PdfReader, PdfWriter
from pypdf.generic import RectangleObject

def split_pdf_halves(input_path: str, output_path: str) -> None:
    reader = PdfReader(input_path)
    writer = PdfWriter()

    for page_num, page in enumerate(reader.pages):
        # MediaBox から実際のページサイズを取得
        media_box = page.mediabox
        x0 = float(media_box.left)
        y0 = float(media_box.bottom)
        x1 = float(media_box.right)
        y1 = float(media_box.top)

        width = x1 - x0
        mid_x = x0 + width / 2

        # --- 左半分 ---
        left_page = writer.add_blank_page(width=width / 2, height=(y1 - y0))
        left_page.merge_page(page)
        # CropBox で左半分のみ表示
        left_page.cropbox = RectangleObject([x0, y0, mid_x, y1])
        left_page.mediabox = RectangleObject([x0, y0, mid_x, y1])

        # --- 右半分 ---
        right_page = writer.add_blank_page(width=width / 2, height=(y1 - y0))
        right_page.merge_page(page)
        right_page.cropbox = RectangleObject([mid_x, y0, x1, y1])
        right_page.mediabox = RectangleObject([mid_x, y0, x1, y1])

        print(f"  Page {page_num + 1}: {width:.1f} x {y1 - y0:.1f} pt  →  left/right {width / 2:.1f} x {y1 - y0:.1f} pt")

    with open(output_path, "wb") as f:
        writer.write(f)

def main():
    if len(sys.argv) < 2:
        print("Usage: python pdf_split_halves.py input.pdf [output.pdf]")
        sys.exit(1)
 
    input_path = sys.argv[1]
 
    if not os.path.isfile(input_path):
        print(f"Erorr: file not found: {input_path}")
        sys.exit(1)
 
    if not input_path.lower().endswith(".pdf"):
        print(f"Warning: the file extension is not pdf: {input_path}")
 
    if len(sys.argv) >= 3:
        output_path = sys.argv[2]
    else:
        base, ext = os.path.splitext(input_path)
        output_path = base + "_split" + (ext if ext else ".pdf")
 
    print(f"INPUT: {input_path}")
    print(f"OUTPUT: {output_path}")
 
    split_pdf_halves(input_path, output_path)
 
    print(f"\nFINISH: {output_path}")

if __name__ == "__main__":
    main()
