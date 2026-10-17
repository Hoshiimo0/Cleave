# Cleave

pdfやpngなどのファイルを指定した方向に、２等分するスクリプト
引数なしで、左右に分割する。
`-d v`オプションをつけることで、上下に分割する。
```bash
# 左右に分割する場合
python3 pdf_split_halves.py [input]
# 左右分割を明示することもできる
python3 pdf_split_halves.py -d h [input]

# 上下に分割する場合
python3 pdf_split_halves.py -d v [input]
```
