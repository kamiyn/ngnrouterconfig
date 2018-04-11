#!/usr/bin/python3 -u

import collections
import os
import sys
import time
import xlrd # 追加ライブラリ
import ngnrouterlib

if len(sys.argv) < 3:
    print("xl2config.py ＜パラメータExcel＞ ＜テンプレートフォルダ＞")
    print("引数にファイルとテンプレートフォルダを指定して下さい")
    exit(1)

filename = sys.argv[1]
templatedir = sys.argv[2]

# 出力フォルダの作成
nowstr = time.strftime('%Y%m%d%H%M%S')
filewithoutext, fileext = os.path.splitext(filename)
outputdir = filewithoutext + "_" + nowstr

if not os.path.isdir(outputdir):
    os.mkdir(outputdir)

book = xlrd.open_workbook(filename)
sheet = book.sheet_by_index(0)

if (sheet.nrows <= 1):
    print("2行以上あるファイルを指定して下さい")
    exit(1)

headerline = [(idx, str(cell.value).strip()) for idx,cell in enumerate(sheet.row(0)) if cell.value.strip()]

# ヘッダの重複調査
headerCnt = collections.Counter([header for idx,header in headerline])
dupheader = [header for header,cnt in headerCnt.items() if cnt > 1]
if dupheader:
    print("ヘッダ行に重複があります " + ",".join(dupheader))
if not [header for idx,header in headerline if header == "id"]:
    print("id 列を追加して下さい")
# /ヘッダの重複調査

for line in range(1, sheet.nrows):
    row = sheet.row_values(line)
    dict = {headertuple[1]:str(row[headertuple[0]]) for headertuple in headerline} # パラメータ辞書作成
    ngnrouterlib.expandTemplate(dict, templatedir, outputdir)

exit(0)
