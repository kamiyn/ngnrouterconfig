# ngnrouterconfig
automate router configuration

開発環境では Ubuntu 18.04 を利用した。python venv 環境の作成までは以下のコマンドを実施

```shell:xl2config_venv.sh
sudo apt-get install python3-venv
cd ~
python3.6 -m venv xl2config
source ~/xl2config/bin/activate

pip3 install pexpect jinja2 xlrd ptvsd termcolor
```
