import base64
import json
import queue
from tkinter import NO
from typing import Dict
from Pan123 import Pan123
from Share.util import encodeSign, decodeSign, process


class Entity(Dict):
    pass

    def toShare(self):
        parentId = startId = 1
        res = []

        def run(name, o, parentPath=''):
            nonlocal startId
            startId += 1
            oId = startId
            nowPath = parentPath + str(oId)
            if isinstance(o, str):
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
                "AbsPath": nowPath,
                "parentFileId": int(parentPath.split('/')[-2] if parentPath != '' else parentId),
            }
            res.append(resObj)
            if isinstance(o, str):
                return
            for k, v in o.items():
                run(k, v, nowPath + "/")

        # run('根目录', self, '')
        for i, j in self.items():
            run(i, j)

        return base64.b64encode(json.dumps(res).encode(), altchars=b'-_')

    def toPan123(self, user:Pan123, parentId=0, call=process):
        if parentId != 0:
            parentInfo = user.info(parentId)
            if not parentInfo:
                raise Exception("目标ID不存在")
            if parentInfo[0]["Type"] != 1:
                raise Exception("目标ID不是目录")
        taskQueue = queue.Queue()
        fileFinish = 0
        call(self.name, fileFinish, self.file)
        resId = None
        for i in self:
            if not i.startswith("?"):
                taskQueue.put((parentId, i, self[i]))
        while not taskQueue.empty():
            workId, name, o = taskQueue.get()
            workId = user.mkDir(workId, name)
            if resId is None:
                resId = workId
            appendList = []
            for i, j in o.items():
                if isinstance(j, str):
                    size, etag = decodeSign(j)
                    file = {
                        "driveId": 0,
                        "etag": etag,
                        "fileName": i,
                        "size": size,
                        "type": 0
                    }
                    appendList.append(file)
                else:
                    taskQueue.put((workId, i, j))
            for i in appendList:
                user.create(workId, i["fileName"], i["size"], i["etag"],duplicate=2)  # 覆盖
                fileFinish += 1
                call(i["fileName"], fileFinish, self.file)
        assert fileFinish == self.file
        return resId

    def verification(self):
        info = None
        def calculate(entity: Entity):
            fNum = 0
            dNum = 0
            fSize = 0
            for k in entity.values():
                if isinstance(k, str):
                    fNum += 1
                    fSize += decodeSign(k)[0]
                else:
                    dNum += 1
                    res_fNum, res_dNum, res_fSize = calculate(k)
                    fNum += res_fNum
                    dNum += res_dNum
                    fSize += res_fSize
            return fNum, dNum, fSize
        for i in self:
            if not i.startswith("?"):
                info = self[i]
                break
        self['?file'], self['?dir'], self['?size'] = calculate(info)

    @property
    def name(self):
        return next(i for i in self.keys() if not i.startswith("?"))
    @property
    def size(self):
        return self['?size']
    @property
    def file(self):
        return self['?file']
    @property
    def dir(self):
        return self['?dir']

    def get_filename(self):
        return f"[{self.get_sign()}]{self.name}"[:256]

    def get_sign(self):
        import hashlib
        data = json.dumps(self).encode()
        size = len(data)
        etag = hashlib.md5(data).hexdigest()
        return encodeSign(size, etag)