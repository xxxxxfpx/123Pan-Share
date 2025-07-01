import base64
from typing import Dict
import binascii

def base62_decode_to_hex(string):
    digits = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    result = 0

    # 先将 base62 字符串解码为整数
    for char in string:
        result = result * 62 + digits.index(char)

    # 将整数转换为十六进制字符串，并去掉前缀 '0x'
    hex_result = hex(result)[2:]
    return hex_result
def getSize(obj: Dict) -> int:
    info = next(obj.values().__iter__())
    if isinstance(info,  str):
        return decodeSign(info)[0]
    else:
        return 0
def getType(obj: Dict) -> int:
    info = next(obj.values().__iter__())
    if isinstance(info,  str):
        return 0
    else:
        return 1
def getEtag(obj: Dict) -> str:
    info = next(obj.values().__iter__())
    if isinstance(info,  str):
        return decodeSign(info)[1]
    else:
        return ''
def decodeSign(sign: str):
    assert len(sign) == 32, "sign长度必须为32"
    binary_data = base64.b64decode(sign, altchars=b'-_')  # 解码为二进制数据
    etag = binascii.hexlify(binary_data[:16]).decode('utf-8')  # 转换为十六进制字符串
    return int.from_bytes(binary_data[16:], byteorder='big', signed=False), etag
def encodeSign(size:int,  etag:str):
    assert len(etag) == 32, "etag长度必须为32"
    binary_data = binascii.unhexlify(etag)  # 转换为二进制数据
    return base64.b64encode(binary_data + int(size).to_bytes(8, byteorder='big', signed=False), altchars=b'-_').decode()
def process(nowInfo, handleFile=None, allFile=None):
    '''
    :param nowInfo:  输出信息
    :param handleFile:  已处理文件数
    :param allFile:    总文件数
    :return:
    '''
    return None
