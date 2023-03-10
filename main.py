import codecs
import pkgutil
import re

from creart import create
from graia.ariadne.app import Ariadne
from graia.ariadne.connection.config import (
    HttpClientConfig,
    WebsocketClientConfig,
    config,
)

from graia.saya import Saya


def get_value(key):
    f = codecs.open(r'setting.yml', 'r', 'utf-8')
    lines = f.readlines()
    regex = '.*' + key + '[:]'
    for line in lines:
        if re.match(regex, line):
            value = line.split(':')[1].strip()
            return ''.join(value)
    f.close()


qq = int(get_value('qq'))
verify_key = get_value('verifyKey')
port = int(get_value('port'))

saya = create(Saya)
app = Ariadne(
    connection=config(
        qq,  # 你的机器人的 qq 号
        verify_key,  # 填入你的 mirai-api-http 配置中的 verifyKey
        # 以下两行（不含注释）里的 host 参数的地址
        # 是你的 mirai-api-http 地址中的地址与端口
        # 他们默认为 "http://localhost:8080"
        # 如果你 mirai-api-http 的地址与端口也是 localhost:8080
        # 就可以删掉这两行，否则需要修改为 mirai-api-http 的地址与端口
        HttpClientConfig(host=f"http://localhost:{port}"),
        WebsocketClientConfig(host=f"http://localhost:{port}"),
    ),
)

# 所有单独的模组文件
with saya.module_context():
    for module_info in pkgutil.iter_modules(["modules"]):
        if module_info.name.startswith("_"):
            # 假设模组是以 `_` 开头的，就不去导入
            # 根据 Python 标准，这类模组算是私有函数
            continue
        saya.require(f"modules.{module_info.name}")

app.launch_blocking()
