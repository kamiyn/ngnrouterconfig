#! /bin/sh
""":"
exec python "$0" ${1+"$@"}
"""

__doc__ = """The above defines the script's __doc__ string. You can fix it by like this."""

import sys
import os
import ptvsd  # 追加ライブラリ
import pexpect  # 追加ライブラリ
import time
import ngnrouterlib

# 環境変数 PYTHON3_PTVSD_SECRET がある場合は リモートデバッグを有効にする
if ("PYTHON3_PTVSD_SECRET" in os.environ):
    ptvsd.enable_attach(os.environ['PYTHON3_PTVSD_SECRET'], address=('0.0.0.0', 3000))
    ptvsd.wait_for_attach()
    ptvsd.break_into_debugger()

if len(sys.argv) < 2:
    print("パラメータファイルを指定して下さい")
    exit(1)

ngnrouterlib.doNgconf(sys.argv[1])

exit(0)
