import json
import os
import sys
import re
from time import sleep
import pexpect

def readrouterconfig(filename):
	'''
	readrouterconfig
	    1行目を JSON として解釈し、辞書にして タプルの第一要素として返す
		2行目以降を タプルの第二要素として返す

		1行目のJSONの 値 について、 $ で始まる値については環境変数を参照して展開する
	'''
	# 
	with open(filename, "r") as fp:
		jsonstr = fp.readline()
		sendlines = fp.readlines()
		jsonobj = json.loads(jsonstr)
		for k,v in jsonobj.items():
			if (v.startswith("$") and os.getenv(v[1::])):
				jsonobj[k] = os.getenv(v[1::])
		return (jsonobj, sendlines)


def rtx_ssh_login(routerconfig, sendlines, logfilename):
	'''
	rtx_ssh_login
	    RTX810, RTX1200 にコンフィグ送信し、送信状態をログファイルに記録する関数
		ファイルの中身は以下のような内容であるこのを期待している。1行目はJSON、2行目以降は ルータに送信したい内容
		"router": "10.0.0.1", "routertype": "rtx-ssh", "username": "ログインユーザー名", "password": "ログインパスワード", "adminpassword": "管理者パスワード" }
		show config
	'''
	sleepspan = 0.5
	timeout = 5
	logfp = open(logfilename, 'wb')
	child = pexpect.spawn('ssh -l ' +  routerconfig["username"] + " " + routerconfig["router"])
	child.logfile_read = logfp
	# child.logfile_read = sys.stderr.buffer # .buffer をつけるとバイナリ出力先になる
	try:
		# ユーザーログイン
		child.expect('password: ', timeout=timeout)
		sleep(sleepspan)
		child.send(routerconfig["password"] + "\n")
		child.expect('> ', timeout=timeout)

		# プロンプト文字列の取得
		sleep(sleepspan)
		child.send("# non-existent-lines\n") # ルータのヘッダー文字列に含まれない文字列をコメント送信することで、ヘッダーをスキップする
		child.expect('non-existent-lines', timeout=timeout) # この時点では改行コードを含まない
		prom = ""
		prom1 = ""
		while (prom1 != ">"):
			prom = prom + prom1
			c = child.read(1)
			prom1 = chr(c[0])
		
		# 管理者モードに変更
		sleep(sleepspan)
		child.send('administrator' + "\n")
		child.expect('Password: ', timeout=timeout)

		sleep(sleepspan)
		child.send(routerconfig["adminpassword"] + "\n")
		child.expect(prom + '# ', timeout=timeout)

		# config を送信する
		for line in sendlines:
			if (re.match(r"^\s*$", line)):
				continue
			sleep(sleepspan)
			child.send(line + "\n")
			child.expect(prom) # 標準のタイムアウト 30秒を利用する

		sleep(sleepspan)
		child.send('exit' + "\n")
		child.expect(prom + '> ', timeout=timeout)

		sleep(sleepspan)
		child.send('exit' + "\n")
		sleep(sleepspan)
	finally:
		logfp.flush()
		logfp.close()
		child.close()

		logfp = open(logfilename, 'r')
		for line in logfp.readlines():
			print(line, end="")
