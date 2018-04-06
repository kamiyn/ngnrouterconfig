import os
import ptvsd

# リモートデバッグテスト

if os.environ["PYTHON3_PTVSD_SECRET"]:
	ptvsd.enable_attach(os.environ['PYTHON3_PTVSD_SECRET'], address = ('0.0.0.0', 3000))
	ptvsd.wait_for_attach()
	ptvsd.break_into_debugger()

file = open('/etc/os-release')
content = file.read()
print(content)
file.close()
