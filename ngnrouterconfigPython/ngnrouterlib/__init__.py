import json
import os
import sys
import re
from time import sleep
import time
import pexpect  # 追加ライブラリ
import jinja2  # 追加ライブラリ
from termcolor import colored, cprint # 追加ライブラリ

def doNgconf(filename):
    # config の中身を解析する
    routerconfig, sendlines = readrouterconfig(filename)
    # ログファイル名の作成
    nowstr = time.strftime('%Y%m%d%H%M%S')
    filewithoutext, fileext = os.path.splitext(filename)
    logfilename = filewithoutext + "_" + nowstr + ".log"
    if routerconfig["routertype"] == "rtx-ssh":
        rtx_ssh_login(routerconfig, sendlines, logfilename)
    elif routerconfig["routertype"] == "rtx-telnet":
        pass
    elif routerconfig["routertype"] == "ix-telnet":
        ix_telnet_login(routerconfig, sendlines, logfilename)
    elif routerconfig["routertype"] == "ix-direct":
        ix_direct_login(routerconfig, sendlines, logfilename)
    elif routerconfig["routertype"] == "century-direct":
        century_direct_login(routerconfig, sendlines, logfilename)
    else:
        print("unknown routertype: " + routerconfig["routertype"])
    return logfilename

class ConfigHolder(object):
    def __init__(self):
        self.configFile = ""
        self.outputFile = ""
        self.regexFile = []
        self.renotFile = []

    def __str__(self):
        return "configFile: " + self.configFile + "\tregexFile: " + ",".join(self.regexFile) + "\trenotFile: " + ",".join(self.renotFile)

    def confirmToRun(self):
        with open(self.configFile) as f1:
            print(colored("========投入 " + self.configFile, 'cyan'))
            print(f1.read())
        for r in self.regexFile:
            with open(r) as f2:
                print(colored("========検証 " + r, 'cyan'))
                print(f2.read())
        for r in self.renotFile:
            with open(r) as f2:
                print(colored("\n========存在しない検証 " + r, 'cyan'))
                print(f2.read())

        input(colored("実行するには Enter を押して下さい", 'cyan'))
        return True

    def Run(self):
        logfilename = doNgconf(self.configFile)
        for r in self.regexFile:
            with open(r) as f2:
                print(colored("\n========検証 " + r, 'cyan'))
                print(f2.read())
            if not checkre(r, logfilename):
                print(colored("XXXXXXXX検証に失敗しました " + r + "\n", 'red'))
                raise Exception()
            else:
                print(colored("========検証に成功しました " + r + "\n", 'green'))
        for r in self.renotFile:
            with open(r) as f2:
                print(colored("\n========存在しない検証 " + r, 'cyan'))
                print(f2.read())
            if checkre(r, logfilename):
                print(colored("XXXXXXXX検証に失敗しました " + r + "\n", 'red'))
                raise Exception()
            else:
                print(colored("========検証に成功しました " + r + "\n", 'green'))

    @staticmethod
    def appendFile(filename, result):
        resultlen = len(result)
        if filename.endswith(".re"):
            result[resultlen-1].regexFile.append(filename)
        elif filename.endswith(".nre"):
            result[resultlen-1].renotFile.append(filename)
        else:
            holder = ConfigHolder()
            holder.configFile = filename
            result.append(holder)
        return result

def expandTemplate(dict, templatedir, outputdir):
    '''
    expandTemplate
        templatedir にあるテンプレートファイルについて、
        dict をパラメータとして展開したファイルを
        outputdir に生成する
    '''
    templateLoader = jinja2.FileSystemLoader(searchpath=templatedir)
    templateEnv = jinja2.Environment(loader=templateLoader)
    result = []
    for templateFilename in [x for x in templateEnv.list_templates() if x.find("/") == -1]:
        outputpath = os.path.join(
            outputdir, dict["id"] + "_" + templateFilename)
        print(templateFilename)
        template = templateEnv.get_template(templateFilename)
        outputText = template.render(dict)
        with open(outputpath, "w") as fp:
            fp.write(outputText)
        # result.append(outputpath)
        result = ConfigHolder.appendFile(outputpath, result)
    return result


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
        for k, v in jsonobj.items():
            if (v.startswith("$") and os.getenv(v[1::])):
                jsonobj[k] = os.getenv(v[1::])
        return (jsonobj, sendlines)


def checkre(pfile, tfile):
    with open(pfile) as f:
        patternStr = f.readline().strip()
    with open(tfile) as f2:
        targetStr = f2.read()
    return re.search(patternStr, targetStr, re.DOTALL)


class multifile(object):
    def __init__(self, files):
        self._files = files

    def __getattr__(self, attr, *args):
        return self._wrap(attr, *args)

    def _wrap(self, attr, *args):
        def g(*a, **kw):
            for f in self._files:
                res = getattr(f, attr, *args)(*a, **kw)
            return res
        return g


def ix_telnet_login(routerconfig, sendlines, logfilename):
    '''
    ix_telnet_login
        IX にコンフィグ送信し、送信状態をログファイルに記録する関数
            ファイルの中身は以下のような内容であるこのを期待している。1行目はJSON、2行目以降は ルータに送信したい内容
            "router": "10.0.0.1", "routertype": "ix_telnet_login", "username": "ログインユーザー名", "password": "ログインパスワード", "centerrouter":"", "centeruser":"", "centerpassword":"" }
            show config
    '''
    sleepspan = 0.5
    timeout = 5
    logfp1 = open(logfilename, 'wb')
    logfp = multifile([sys.stdout.buffer, logfp1])
    child = pexpect.spawn('telnet ' + routerconfig["centerrouter"])
    child.logfile_read = logfp
    child.ignore_sighup = True
    try:
        # center router login
        child.expect('login: ', timeout=timeout)
        sleep(sleepspan)
        child.send(routerconfig["centeruser"] + "\r")
        child.expect('Password: ', timeout=timeout)
        sleep(sleepspan)
        child.send(routerconfig["centerpassword"] + "\r")

        # ユーザーログイン
        child.expect('# ', timeout=timeout)
        sleep(sleepspan)
        child.send("telnet " + routerconfig["router"] + "\r")
        child.expect('login: ', timeout=timeout)
        sleep(sleepspan)
        child.send(routerconfig["username"] + "\r")
        child.expect('Password: ', timeout=timeout)
        sleep(sleepspan)
        child.send(routerconfig["password"] + "\r")
        child.expect('# ', timeout=timeout)

        # プロンプト文字列の取得
        sleep(sleepspan)
        # ルータのヘッダー文字列に含まれない文字列をコメント送信することで、ヘッダーをスキップする
        child.send("! non-existent-lines\r")
        child.expect('non-existent-lines', timeout=timeout)  # この時点では改行コードを含まない
        prom = ""
        prom1 = ""
        while (prom1 != "#"):
            prom = prom + prom1
            c = child.read(1)
            prom1 = chr(c[0])

        # 管理者モードに変更
        sleep(sleepspan)
        child.send('configure' + "\r")
        child.expect(prom, timeout=timeout)
        sleep(sleepspan)
        child.send('svintr-config' + "\r")
        child.expect(prom, timeout=timeout)

        # config を送信する
        for line in sendlines:
            if (re.match(r"^\s*$", line)):
                continue
            sleep(sleepspan)
            child.send(line + "\r")
            if (line.startswith("reload y")): # リロードはプロンプトを出力せず、先に進めない
                print(colored("========reload しています。ルータの起動を待って下さい ", 'yellow'))
                sleep(sleepspan * 10)
                return

            child.expect(prom)  # 標準のタイムアウト 30秒を利用する

        sleep(sleepspan)
        child.send('exit' + "\r")
        child.expect(prom, timeout=timeout)

        sleep(sleepspan)
        child.send('exit' + "\r")
        sleep(sleepspan)
        child.send('exit' + "\r")
        sleep(sleepspan)
    finally:
        logfp.flush()
        logfp1.close() # stdout は close したくない
        child.close()


def ix_direct_login(routerconfig, sendlines, logfilename):
    '''
    ix_direct_login
        IX にコンフィグ送信し、送信状態をログファイルに記録する関数 (ルーターを中継しない)
            ファイルの中身は以下のような内容であるこのを期待している。1行目はJSON、2行目以降は ルータに送信したい内容
            "router": "10.0.0.1", "routertype": "ix_direct_login", "username": "ログインユーザー名", "password": "ログインパスワード" }
            show config
    '''
    sleepspan = 0.5
    timeout = 5
    logfp1 = open(logfilename, 'wb')
    logfp = multifile([sys.stdout.buffer, logfp1])
    child = pexpect.spawn('telnet ' + routerconfig["router"])
    child.logfile_read = logfp
    try:
        # ユーザーログイン
        child.expect('login: ', timeout=timeout)
        sleep(sleepspan)
        child.send(routerconfig["username"] + "\r")
        child.expect('Password: ', timeout=timeout)
        sleep(sleepspan)
        child.send(routerconfig["password"] + "\r")
        child.expect('# ', timeout=timeout)

        # プロンプト文字列の取得
        sleep(sleepspan)
        # ルータのヘッダー文字列に含まれない文字列をコメント送信することで、ヘッダーをスキップする
        child.send("! non-existent-lines\r")
        child.expect('non-existent-lines', timeout=timeout)  # この時点では改行コードを含まない
        prom = ""
        prom1 = ""
        while (prom1 != "#"):
            prom = prom + prom1
            c = child.read(1)
            prom1 = chr(c[0])

        # 管理者モードに変更
        sleep(sleepspan)
        child.send('configure' + "\r")
        child.expect(prom, timeout=timeout)
        sleep(sleepspan)
        child.send('svintr-config' + "\r")
        child.expect(prom, timeout=timeout)

        # config を送信する
        for line in sendlines:
            if (re.match(r"^\s*$", line)):
                continue
            sleep(sleepspan)
            child.send(line + "\r")
            child.expect(prom)  # 標準のタイムアウト 30秒を利用する

        sleep(sleepspan)
        child.send('exit' + "\r")
        child.expect(prom, timeout=timeout)

        sleep(sleepspan)
        child.send('exit' + "\r")
        sleep(sleepspan)
        child.send('exit' + "\r")
        sleep(sleepspan)
    finally:
        logfp.flush()
        logfp1.close() # stdout は close したくない
        child.close()


def century_direct_login(routerconfig, sendlines, logfilename):
    '''
    century_direct_login
        Century にコンフィグ送信し、送信状態をログファイルに記録する関数 (ルーターを中継しない)
            ファイルの中身は以下のような内容であるこのを期待している。1行目はJSON、2行目以降は ルータに送信したい内容
            "router": "10.0.0.1", "routertype": "century_direct_login", "username": "ログインユーザー名", "password": "ログインパスワード" }
            show config
    '''
    sleepspan = 0.5
    timeout = 5
    logfp1 = open(logfilename, 'wb')
    logfp = multifile([sys.stdout.buffer, logfp1])
    child = pexpect.spawn('telnet ' + routerconfig["router"])
    child.logfile_read = logfp
    try:
        # ユーザーログイン
        child.expect('login: ', timeout=timeout)
        sleep(sleepspan)
        child.send(routerconfig["username"] + "\r")
        child.expect('Password: ', timeout=timeout)
        sleep(sleepspan)
        child.send(routerconfig["password"] + "\r")
        child.expect('# ', timeout=timeout)

        # プロンプト文字列の取得
        sleep(sleepspan)
        # ルータのヘッダー文字列に含まれない文字列をコメント送信することで、ヘッダーをスキップする
        child.send("! non-existent-lines\r")
        child.expect('non-existent-lines', timeout=timeout)  # この時点では改行コードを含まない
        prom = ""
        prom1 = ""
        while (prom1 != "#"):
            prom = prom + prom1
            c = child.read(1)
            prom1 = chr(c[0])

        # 管理者モードに変更
        sleep(sleepspan)
        child.send('configure terminal' + "\r")
        child.expect(prom, timeout=timeout)

        # config を送信する
        for line in sendlines:
            if (re.match(r"^\s*$", line)):
                continue
            sleep(sleepspan)
            child.send(line + "\r")
            child.expect(prom)  # 標準のタイムアウト 30秒を利用する

        sleep(sleepspan)
        child.send('exit' + "\r")
        child.expect(prom, timeout=timeout)

        sleep(sleepspan)
        child.send('exit' + "\r")
        sleep(sleepspan)
        child.send('exit' + "\r")
        sleep(sleepspan)
    finally:
        logfp.flush()
        logfp1.close() # stdout は close したくない
        child.close()


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

    logfp1 = open(logfilename, 'wb')
    logfp = multifile([sys.stdout.buffer, logfp1])
    child = pexpect.spawn('ssh -l ' + routerconfig["username"] + " " + routerconfig["router"])
    child.logfile_read = logfp
    try:
        # ユーザーログイン
        child.expect('password: ', timeout=timeout)
        sleep(sleepspan)
        child.send(routerconfig["password"] + "\n")
        child.expect('> ', timeout=timeout)

        # プロンプト文字列の取得
        sleep(sleepspan)
        # ルータのヘッダー文字列に含まれない文字列をコメント送信することで、ヘッダーをスキップする
        child.send("# non-existent-lines\n")
        child.expect('non-existent-lines', timeout=timeout)  # この時点では改行コードを含まない
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
        child.expect(prom, timeout=timeout)

        # config を送信する
        for line in sendlines:
            if (re.match(r"^\s*$", line)):
                continue
            sleep(sleepspan)
            child.send(line + "\n")
            child.expect(prom)  # 標準のタイムアウト 30秒を利用する

        sleep(sleepspan)
        child.send('exit' + "\n")
        child.expect(prom + '> ', timeout=timeout)

        sleep(sleepspan)
        child.send('exit' + "\n")
        sleep(sleepspan)
    finally:
        logfp.flush()
        logfp1.close() # stdout は close したくない
        child.close()
