import json
import re
import time
from typing import Union, List

from Pan123 import Pan123
from Share.util import decodeSign, encodeSign, process

RE_SIGN = re.compile(r"^([a-zA-Z0-9_-]{32})$")
RE_SIGN1 = re.compile(r"\[([a-zA-Z0-9_-]{32})\]")
RE_SIGN2 = re.compile(r"([a-zA-Z0-9_-]{32})")

def signToPan(p:Pan123,sign:str,parentId:Union[str, int]=0, call=process):
    from Share.entity import Entity
    call("识别分享链")
    if reSign := RE_SIGN.search(sign):
        sign = reSign.group(1)
    elif reSign := RE_SIGN1.search(sign):
        sign = reSign.group(1)
    elif reSign := RE_SIGN2.search(sign):
        sign = reSign.group(1)
    else:
        raise Exception("无效的分享链")

    call("解码分享链")
    size, etag = decodeSign(sign)
    call("读取分享元数据")
    fileId, res = p.downloadInfo(size, etag)
    entity: Entity = Entity()
    entity.update(json.loads(res))
    call("元数据获取成功")
    call(f"文件名:{entity.name} - {entity.file}个文件, {entity.size}字节")
    try:
        p.rename(fileId, entity.get_filename())
    except:
        nowTime = str(time.time_ns())
        p.rename(fileId, entity.get_filename()[:256 - len(nowTime)] + nowTime)
    if isinstance(parentId, str):
        rootId = 0
        for i in parentId.strip('/').split('/'):
            rootId = p.mkDir(rootId, i)
        parentId = rootId
    entity.toPan123(p, parentId, call)
    call(f"文件名:{entity.name} - {entity.file}个文件, {entity.size}字节")
    call("分享链解析完成")


def panToSign(p:Pan123,fileId:Union[int,List[int],str], call=process):
    from Share.entity import Entity
    finish = 0
    def d(inLsInfo):
        entity = Entity()
        for i in inLsInfo:
            if i['Type'] == 1:
                entity[i['FileName']] = d(p.get_files(i['FileId']))
            else:
                entity[i['FileName']] = encodeSign(i['Size'], i['Etag'])
                nonlocal finish
                finish += 1
                call(i['FileName'], finish)
        return entity

    if isinstance(fileId, str):
        rootId = 0
        for i in fileId.strip('/').split('/'):
            rootId = p.mkDir(rootId, i)
        fileId = [rootId]
    if isinstance(fileId, int):
        fileId = [fileId]
    root = Entity()

    lsInfo = p.info(fileId)
    rootName = lsInfo[0]["FileName"]
    rootName = (yield rootName) or rootName
    assert rootName, "分享目录名称不能为空"
    assert set(rootName).isdisjoint(set(r'"\/:*?<>|')), "分享目录名称不能包含特殊字符"
    assert len(rootName) < 256, "分享目录名称不能超过256个字符"
    if len(lsInfo)==1 and lsInfo[0]["Type"]==1:
        lsInfo = p.get_files(lsInfo[0]["FileId"])
    root[rootName] = d(lsInfo)
    root.verification()
    assert root.file != 0 , "分享目录为空"
    get, create = p.getSharePath()
    data = json.dumps(root).encode('utf-8')
    filename = root.get_filename()
    p.upload(create, data, filename)
    yield filename

