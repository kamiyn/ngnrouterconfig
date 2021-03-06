#! /bin/sh
""":"
exec python "$0" ${1+"$@"}
"""

__doc__ = """The above defines the script's __doc__ string. You can fix it by like this."""

import collections
import os
import sys
import time
import xlrd # 追加ライブラリ
import re
from termcolor import colored, cprint # 追加ライブラリ
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
    print(colored("\n--------新しい物件の処理を開始します", 'yellow'))
    row = sheet.row_values(line)
    dict = {headertuple[1]:str(row[headertuple[0]]).strip() for headertuple in headerline} # パラメータ辞書作成
    dict.update({headertuple[1]+"escape":re.escape(str(row[headertuple[0]]).strip()) for headertuple in headerline}) # パラメータ辞書作成(正規表現 escape用)
    if not dict["id"]:
        continue
    outputfiles = ngnrouterlib.expandTemplate(dict, templatedir, outputdir)
    try:
        for holder in outputfiles:
            if holder.confirmToRun():
                holder.Run()
    except Exception as ex:
        print("この物件への処理を中断しました ", ex)

exit(0)
