# Cleave

pdfやpngなどのファイルを指定した方向に、任意の数で等分するスクリプト
引数なしで、左右に分割する。
`-d v`オプションをつけることで、上下に分割する。
`-n [int]`オプションをつけることで、分割数を変更できる。

## オプション引数
- `-d h`, `--direction h`: 左右に分割（デフォルト）
- `-d v`, `--direction v`: 上下に分割
- `-n N`, `--number N`: 分割数を変更（デフォルトは２, 1以上の整数をサポート）

**出力ファイル名を省略した場合は、`input_split.<ext>`として保存される。**

## 対応フォーマット
- PDF: `.pdf`
- 画像: `.png`, `.jpg`, `.jpeg`, `.webp`, `.bmp`, `.tiff`, `.tif`

## 使用例
```bash
cleave [-d {h, v}] [-n N] input [output]

# 左右に分割する場合
cleave input.pdf

# 上下に分割する場合
cleave -d v input.pdf output.pdf

# PDFを左右に３分割
cleave -n 3 input.pdf

# 画像を上下に４分割
cleave -d v -n 4 photo.png
```
