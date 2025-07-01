import base64
import json
from typing import Union

from Share.entity import Entity
from Share.util import decodeSign, encodeSign, base62_decode_to_hex

def fastToEntity(fast: Union[str, bytes]) -> Entity:
    fast = json.loads(fast)
    entity = Entity()
    if 'commonPath' in fast and fast['commonPath'] != '':
        for k in fast['files']:
            k['path'] = fast['commonPath'] + k['path']
    for i in fast['files']:
        temp = entity
        parent = None
        for k in i['path'].split('/'):
            parent = (temp, k)
            if k in temp:
                temp = temp[k]
            else:
                temp[k] = Entity()
                temp = temp[k]
        parent[0][parent[1]] =  encodeSign(i['size'], base62_decode_to_hex(i['etag']).rjust(32, '0'))
    entity.verification()
    return entity
def fastToShare(j:Union[str, bytes]):
    obj = json.loads(j)
    s = Entity()
    s["?SIGN"] = "https://github.com/xxxxxfpx/123PanShare"
    if 'commonPath' in obj and obj['commonPath'] != '':
        for k in obj['files']:
            k['path'] = obj['commonPath'] + k['path']
    for i in obj['files']:
        temp = s
        parent = None
        for k in i['path'].split('/'):
            parent = (temp, k)
            if k in temp:
                temp = temp[k]
            else:
                temp[k] = Entity()
                temp = temp[k]
        if parent:
            parent[0][parent[1]] = encodeSign(i['size'], base62_decode_to_hex(i['etag']).rjust(32, '0'))
    return s
def entityToShare(o):
    parentId = startId = 1
    res = []

    def run(name, o, parentPath=''):
        nonlocal startId
        startId += 1
        oId = startId
        nowpath = parentPath + str(oId)
        if isinstance(o,  str):
            size, etag = decodeSign(o)
            type = 0
        else:
            size, etag, type = 0, '', 1

        resObj = {
            "FileId": oId,
            "Type": type,
            "Size": size,
            "Etag": etag,
            "FileName": name,
            "AbsPath": nowpath,
            "parentFileId": int(parentPath.split('/')[-2] if parentPath != '' else parentId),
        }
        res.append(resObj)
        if isinstance(o,  str):
            return
        for k, v in o.items():
            run(k, v, nowpath + "/")
    # run('根目录', o, '')
    for i, j in o.items():
        run(i, j)

    return base64.b64encode(json.dumps(res).encode())
def shareToEntity(title, share:str):
    share = json.loads(base64.b64decode(share.encode(), altchars=b'-_'))
    entity = Entity()
    entity[title] = Entity()
    recodeDirId = {}
    for i in share:
        recodeDirId[i["FileId"]] = i["FileName"]
    for i in share:
        temp = entity[title]
        parent = None
        for k in i['AbsPath'].split('/'):
            k = recodeDirId[int(k)]
            parent = (temp, k)
            if k in temp:
                temp = temp[k]
            else:
                temp[k] = Entity()
                temp = temp[k]
        if i["Type"] == 0:
            parent[0][parent[1]] = encodeSign(i['Size'],i['Etag'])
    entity.verification()
    return entity
