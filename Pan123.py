import base64
import datetime  # 导入 datetime 模块用于处理日期和时间
import time  # 导入 time 模块用于处理时间戳
import random  # 导入 random 模块用于生成随机数
import hashlib  # 导入 hashlib 模块用于哈希计算 (替代 md5, 虽然注释掉的代码里有md5)
import binascii  # 导入 binascii 模块用于 CRC32 校验
import urllib.parse  # 导入 urllib.parse 模块用于 URL 解析和构建
import re  # 导入 re 模块用于正则表达式 (例如，邮箱格式校验)
from typing import List, Dict, Any, Tuple, Optional, Callable, Union  # 导入类型提示

import requests  # 导入 requests 模块用于发送 HTTP 请求
from requests.adapters import HTTPAdapter  # 导入 HTTPAdapter 用于配置请求
from urllib3.util.retry import Retry  # 导入 Retry 用于配置重试策略
import logging  # 导入 logging 模块用于日志记录

# 配置日志记录器
logger = logging.getLogger(__name__)
WORD_SIZE = 10710
WORD_ETAG = "6b4947ca73ecced4a43418468a44caa2"

# 常量定义
API = "https://www.123pan.com/api"
A_API = "https://www.123pan.com/a/api"  # 拼写修正：AApi -> A_API
B_API = "https://www.123pan.com/b/api"  # 拼写修正：BApi -> B_API
LOGIN_API = "https://login.123pan.com/api"
MAIN_API = B_API  # 主要 API 端点
SIGN_IN = LOGIN_API + "/user/sign_in"  # 登录接口
LOGOUT = MAIN_API + "/user/logout"  # 登出接口
USER_INFO = MAIN_API + "/user/info"  # 用户信息接口
FILE_LIST = MAIN_API + "/file/list/new"  # 文件列表接口
Copy= MAIN_API + "/restful/goapi/v1/file/copy/async"
DOWNLOAD_INFO = MAIN_API + "/file/download_info"  # 下载信息接口
MKDIR = MAIN_API + "/file/upload_request"  # 创建文件夹接口 (与上传请求共用)
MOVE = MAIN_API + "/file/mod_pid"  # 移动文件接口
FILE_INFO = MAIN_API + "/file/info"  # 文件信息接口
RENAME = MAIN_API + "/file/rename"  # 重命名文件接口
TRASH = MAIN_API + "/file/trash"  # 回收站接口
UPLOAD_REQUEST = MAIN_API + "/file/upload_request"  # 上传请求接口
UPLOAD_COMPLETE = MAIN_API + "/file/upload_complete"  # 上传完成接口
S3_PRE_SIGNED_URLS = MAIN_API + "/file/s3_repare_upload_parts_batch"  # S3 预签名 URL 接口
S3_AUTH = MAIN_API + "/file/s3_upload_object/auth"  # S3 认证接口
UPLOAD_COMPLETE_V2 = MAIN_API + "/file/upload_complete/v2"  # V2 上传完成接口
S3_COMPLETE = MAIN_API + "/file/s3_complete_multipart_upload"  # S3 完成分片上传接口
def is_email_format(email_string: str) -> bool:
    """
    检查字符串是否为邮箱格式 (简单校验)
    """
    if not email_string:
        return False
    return bool(re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email_string))
def get_from_dict(data: Any, *keys: str, default: Any = None) -> Any:
    """
    从嵌套字典中安全地获取值
    """
    current = data
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key)
        elif isinstance(current, list) and key.isdigit():  # 尝试处理列表索引
            try:
                current = current[int(key)]
            except IndexError:
                return default
        else:
            return default
        if current is None:
            return default
    return current

def get_int_from_dict(data: Any, *keys: str, default: int = 0) -> int:
    """
    从嵌套字典中安全地获取整数值
    """
    val = get_from_dict(data, *keys, default=None)
    if val is None:
        return default
    try:
        return int(val)
    except (ValueError, TypeError):
        return default
File = Dict[str, Any]  # 文件信息字典类型
# 签名函数
def sign_path(path: str, os_val: str, version: str) -> Tuple[str, str]:
    """
    为 API 请求路径生成签名
    :param path: 请求路径 (例如 /api/file/list/new 中的 /file/list/new)
    :param os_val: 操作系统标识 (例如 "web")
    :param version: 应用版本 (例如 "3")
    :return: (k, v) 签名键值对中的 k 和 v
    """
    table = ['a', 'd', 'e', 'f', 'g', 'h', 'l', 'm', 'y', 'i', 'j', 'n', 'o', 'p', 'k', 'q', 'r', 's', 't', 'u', 'b',
             'c', 'v', 'w', 's', 'z']

    # 生成随机数 (Go: math.Round(1e7*rand.Float64()))
    random_val_float = 1e7 * random.random()
    random_val = str(int(round(random_val_float)))  # 四舍五入到整数并转为字符串

    # 或者使用 UTC 时间然后调整，避免依赖 pytz
    now_utc = datetime.datetime.now(datetime.UTC)
    now_cst = now_utc + datetime.timedelta(hours=8)

    timestamp = str(int(now_cst.timestamp()))  # Unix 时间戳 (秒)

    # 格式化当前时间字符串 "200601021504"
    now_str_formatted = now_cst.strftime("%Y%m%d%H%M")

    now_str_bytes_list = []
    for char_digit in now_str_formatted:
        now_str_bytes_list.append(table[int(char_digit)])  # Go: table[nowStr[i]-48]

    # 计算 timeSign (CRC32)
    time_sign_input = "".join(now_str_bytes_list).encode('utf-8')
    time_sign = str(binascii.crc32(time_sign_input) & 0xffffffff)  # Python crc32 可能返回负数

    # 准备 data 字符串
    data_parts = [timestamp, random_val, path, os_val, version, time_sign]
    data_str = "|".join(data_parts)

    # 计算 dataSign (CRC32)
    data_sign = str(binascii.crc32(data_str.encode('utf-8')) & 0xffffffff)

    # 返回 k, v
    # k 是 timeSign
    # v 是 "timestamp-random-dataSign"
    k = time_sign
    v = f"{timestamp}-{random_val}-{data_sign}"
    return k, v
def get_api_url_with_signature(raw_url: str) -> str:
    """
    为给定的 URL 添加签名参数
    :param raw_url: 原始 URL
    :return: 包含签名的完整 URL
    """
    parsed_url = urllib.parse.urlparse(raw_url)
    query_params = urllib.parse.parse_qs(parsed_url.query)  # 解析现有查询参数


    sign_k, sign_v = sign_path(parsed_url.path, "web", "3")

    # 添加新的签名参数
    # parse_qs 返回的是 {'key': ['value']} 格式
    query_params[sign_k] = [sign_v]

    # 构建新的查询字符串
    new_query_string = urllib.parse.urlencode(query_params, doseq=True)

    # 构建最终 URL
    final_url = parsed_url._replace(query=new_query_string).geturl()
    return final_url

# Pan123 客户端类
class Pan123:
    S_root = None
    S_create = None
    S_get = None
    S_createTime = None
    S_getTime = None
    S_createNow = None
    S_getNow = None


    def __init__(self, username: Optional[str] = None, password: Optional[str] = None,
                 access_token: Optional[str] = None):
        """
        初始化 Pan123 客户端
        :param username: 用户名 (邮箱或手机号)
        :param password: 密码
        :param access_token: (可选) 已有的访问令牌
        """
        self.username = username
        self.password = password
        self.access_token = access_token

        # 创建一个 requests Session
        self.session = requests.Session()
        # 配置重试逻辑 (可选, 但推荐)
        retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
        self.session.mount("http://", HTTPAdapter(max_retries=retries))
        self.session.mount("https://", HTTPAdapter(max_retries=retries))

        # 默认请求头
        self.session.headers.update({
            "Origin": "https://www.123pan.com",
            "Referer": "https://www.123pan.com/",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) OpenList-Client/1.0",  # 更通用的 User-Agent
            "Platform": "web",
            "App-Version": "3",
        })

    def login(self) -> None:
        """
        登录到 123pan 并获取 access_token
        :raises: Exception 如果登录失败
        """
        if not self.username or not self.password:
            raise ValueError("用户名和密码不能为空")

        body_data: Dict[str, Any]
        if is_email_format(self.username):
            body_data = {
                "mail": self.username,
                "password": self.password,
                "type": 2,
            }
        else:
            body_data = {
                "passport": self.username,
                "password": self.password,
                "remember": True,
            }

        # 登录接口的 User-Agent 可能特定，这里沿用 Go 代码中的
        login_headers = {
            "origin": "https://www.123pan.com",
            "referer": "https://www.123pan.com/",
            "user-agent": "Dart/2.19(dart:io)-openlist",  # 与 Go 代码一致
            "platform": "web",
            "app-version": "3",
        }

        try:
            response = self.session.post(SIGN_IN, json=body_data, headers=login_headers)
            response.raise_for_status()  # 如果 HTTP 状态码是 4xx 或 5xx, 则抛出异常

            data = response.json()
            if get_int_from_dict(data, "code") != 200:  # 123pan 成功码通常是 0, 但登录是 200
                message = data["message"]
                raise Exception(f"登录失败: {message} (code: {get_int_from_dict(data, 'code')})")

            token = data["data"]["token"]
            if not token:
                raise Exception("登录成功，但未获取到 token")
            self.access_token = token
            logger.info("登录成功")
        except requests.exceptions.RequestException as e:
            logger.error(f"登录请求失败: {e}")
            raise Exception(f"登录请求失败: {e}")
        except Exception as e:
            logger.error(f"登录处理失败: {e}")
            raise
    def request(self, url: str, method: str,
                params: Optional[Dict[str, Any]] = None,
                data: Optional[Dict[str, Any]] = None,
                json_data: Optional[Dict[str, Any]] = None,
                custom_headers: Optional[Dict[str, str]] = None) :
        """
        发送一个经过签名的 API 请求
        :param url: 不带签名的 API URL
        :param method: HTTP 方法 (GET, POST, etc.)
        :param params: URL 查询参数
        :param data: 表单数据
        :param json_data: JSON 请求体
        :param custom_headers: 自定义请求头
        :return: (响应 JSON 数据, 错误对象)
        """
        is_retry = False
        while True:
            if not self.access_token and not (url.startswith(LOGIN_API) or url.startswith(SIGN_IN)):  # 登录接口不需要 token
                # 尝试自动登录
                if self.username and self.password:
                    logger.info("Access token 为空，尝试自动登录...")
                    self.login()

            headers = self.session.headers.copy()  # 获取会话的默认头
            if self.access_token:
                headers["Authorization"] = f"Bearer {self.access_token}"
            if custom_headers:
                headers.update(custom_headers)

            signed_url = get_api_url_with_signature(url)  # 对原始 URL 进行签名

            try:
                response = self.session.request(
                    method.upper(),
                    signed_url,
                    params=params,
                    data=data,
                    json=json_data,
                    headers=headers  # 使用合并后的请求头
                )
                response.raise_for_status()  # 检查 HTTP 错误

                response_data = response.json()
                # logger.debug(f"请求 {signed_url} 响应: {response_data}")

                code = response_data["code"] # Go 版本中成功是 0

                if code != 0:  # 假设 123pan API 成功的 code 是 0
                    message = response_data["message"]
                    if not is_retry and code == 401:  # 假设 401 是 token 失效
                        logger.warning("Token 可能已失效 (code 401)，尝试重新登录...")
                        self.login()
                        is_retry = True
                        continue  # 进入下一次循环重试请求
                    raise Exception(f"API 错误: {message} (code: {code})")

                return response_data # 成功返回数据

            except requests.exceptions.HTTPError as http_err:
                err_json = http_err.response.json()
                message = err_json["message"]
                code = get_int_from_dict(err_json, "code", http_err.response.status_code)

                if not is_retry and (http_err.response.status_code == 401 or code == 401):
                    logger.warning(
                        f"Token 可能已失效 (HTTP {http_err.response.status_code} / API code {code})，尝试重新登录...")
                    try:
                        self.login()
                        is_retry = True
                        continue  # 进入下一次循环重试请求
                    except Exception as login_err:
                        raise Exception(f"Token 失效后重新登录失败: {login_err}")
    def get_files(self, parent_id: int) -> Optional[List[File]]:
        """
        获取指定目录下的文件列表
        :param parent_id: 父文件夹 ID ("0" 通常表示根目录)
        :return: (文件列表, 错误对象)
        """
        page = 1
        all_files: List[File] = []

        # 2024-02-06 fix concurrency by 123pan - 这条注释表明官方可能有限制，Python 版也应注意
        # 这里的实现是串行的，所以并发问题不大，但频繁请求依然可能触发限制

        while True:
            # 调用未在 Go 代码中定义的 APIRateLimit
            # self._api_rate_limit(None, FILE_LIST) # ctx 设为 None

            query_params = {
                "driveId": "0",
                "limit": "100",  # 每页数量
                "next": "0",  # next 字段用于分页, 初始为0, 后续使用接口返回的 next 值
                "orderBy": "file_id",
                "orderDirection": "desc",
                "parentFileId": parent_id,
                "trashed": "false",
                "SearchData": "",
                "Page": str(page),  # Go 代码中用了 Page，但通常这类 API 用 next/offset
                "OnlyLookAbnormalFile": "0",
                "event": "homeListFile",
                "operateType": "4",
                "inDirectSpace": "false",
            }
            logger.debug(f"请求文件列表: parent_id={parent_id}, page={page}, params={query_params}")

            response_data= self.request(FILE_LIST, "GET", params=query_params)

            logger.debug(f"获取文件列表响应: {response_data}")

            data_field = response_data["data"]

            info_list: List[File] = data_field["InfoList"]
            total_count: int = data_field["Total"]
            next_page_indicator: str = data_field["Next"]  # 通常 -1 或空表示最后一页
            all_files.extend(info_list)

            if not info_list or next_page_indicator == "-1":  # 如果没有更多文件或 next 指示结束
                break

            page += 1
            # 简单的延时，避免过于频繁的请求
            time.sleep(0.1)

            # 检查文件数量是否匹配
        if len(all_files) != total_count and total_count > 0:  # 只有当 total_count > 0 时才警告
            logger.warning(f"从远程获取文件数量不一致 期望 {total_count}, 实际获取 {len(all_files)}")
        return all_files
    def mkDir(self, parent_id: int, dir_name: str) -> int:
        data = {
            "driveId": "0",
            "etag": "",
            "fileName": dir_name,
            "parentFileId": parent_id,
            "size": 0,
            "type": 1,
        }
        resp = self.request(MKDIR, "POST", json_data=data)
        return resp["data"]["Info"]["FileId"]
    def info(self, fileIds:Union[int,List[int]]):
        if isinstance(fileIds, int):
            fileIds = [fileIds]
        infoList = []
        for i in range(0, len(fileIds), 100):
            r = self.request(FILE_INFO, "POST", json_data={
            "fileIdList": [{"fileId": fid} for fid in fileIds[i:i+100]]
        })
        if r["data"]["infoList"]:
            infoList.extend(r["data"]["infoList"])
        return infoList
    def rename(self, srcId, newName):
        """重命名文件
        Args:
            srcId: 要重命名的文件ID
            newName: 新的文件名
        Returns:
            DataResponse: 返回重命名结果
        """
        data = {
            "driveId": 0,
            "fileId": srcId,
            "fileName": newName
        }
        return self.request(RENAME,"POST", json_data=data)
    def create(self, parentFileId, fileName, size, etag, duplicate):
        json_data = {
            "driveId": 0,
            "duplicate": duplicate,  # 2->覆盖 1->重命名 0->默认
            "etag": etag,
            "fileName": fileName,
            "parentFileId": parentFileId,
            "size": size,
            "type": 0,
        }
        time.sleep(0.2)
        return self.request(UPLOAD_REQUEST,"POST", json_data=json_data)
    def getS3PreSignedUrls(self, upReq: dict, start: int, end: int):
        json_data = {
            "bucket": upReq["data"]["Bucket"],
            "key": upReq["data"]["Key"],
            "partNumberEnd": end,
            "partNumberStart": start,
            "uploadId": upReq["data"]["UploadId"],
            "StorageNode": upReq["data"]["StorageNode"],
        }
        return self.request(S3_PRE_SIGNED_URLS,"POST", json_data=json_data)
    def getS3Auth(self, upReq: dict, start: int, end: int):
        json_data = {
            "bucket": upReq["data"]["Bucket"],
            "key": upReq["data"]["Key"],
            "partNumberEnd": end,
            "partNumberStart": start,
            "uploadId": upReq["data"]["UploadId"],
            "StorageNode": upReq["data"]["StorageNode"],
        }
        return self.request(S3_AUTH,"POST", json_data=json_data)
    def completeS3(self, upReq: dict, fileSize, isMultipart):
        json_data = {
            "StorageNode": upReq["data"]["StorageNode"],
            "bucket": upReq["data"]["Bucket"],
            "fileId": upReq["data"]["FileId"],
            "fileSize": fileSize,
            "isMultipart": isMultipart,
            "key": upReq["data"]["Key"],
            "uploadId": upReq["data"]["UploadId"],
        }
        return self.request(UPLOAD_COMPLETE_V2,"POST", json_data=json_data)
    def upload(self, parentFileId: int, data:bytes, fileName: str, *, duplicate=2):
        size = len(data)
        etag = hashlib.md5(data).hexdigest()
        res = self.create(parentFileId, fileName, size, etag, duplicate)
        if res["data"]["Reuse"] or res["data"]["Key"] == "":
            return res["data"]["Info"]["FileId"]
        if res["data"]["AccessKeyId"] is None or res["data"]["SecretAccessKey"] is None or res["data"][
            "SessionToken"] is None:
            chunkSize = min(size, 16*1024*1024)
            return self.uploadLocal(res, data, size, chunkSize)
        raise Exception("没有支持aws的上传方式")
    def uploadLocal(self,upReq: dict, data: bytes, size, chunkSize):
        chunkCount = (size + chunkSize - 1) // chunkSize
        if chunkCount == 1:
            s3UrlCall = self.getS3Auth
        else:
            s3UrlCall = self.getS3PreSignedUrls
        s3PreSignedUrls = s3UrlCall(upReq, 1, chunkCount)["data"]["presignedUrls"]
        for i in range(chunkCount):
            start = i * chunkSize
            end = min(start + chunkSize, size)
            index = i + 1
            dataChunk = data[start:end]
            self.session.put(s3PreSignedUrls[str(index)], data=dataChunk)
        return self.completeS3(upReq, size, chunkCount > 1)
    def getSharePath(self):
        if not self.S_root:
            self.S_root = self.mkDir(0, "🗂️ Share")
            self.mkDir(self.S_root, "⚠️ 为避免资源失效，请勿移动或删除当前目录！！！")
            self.create(self.S_root, "📄 使用须知.docx", WORD_SIZE, WORD_ETAG, duplicate=2)
        if not self.S_get:
            self.S_get = self.mkDir(self.S_root, "📥️ 接收记录")
        if not self.S_create:
            self.S_create = self.mkDir(self.S_root, "📤️ 分享记录")
        now = time.strftime("%Y-%m-%d")
        if self.S_getTime != now:
            self.S_getNow = self.mkDir(self.S_get, now)
            self.S_getTime = now
        if self.S_createTime!= now:
            self.S_createNow = self.mkDir(self.S_create, now)
            self.S_createTime = now
        return self.S_getNow, self.S_createNow
    def downloadInfo(self, size, etag):
        get, create = self.getSharePath()
        res = self.create(get, str(time.time_ns()), size, etag, duplicate=2)
        if not res["data"]["Reuse"]:
            raise Exception("123云盘种该资源已经没有源种【分享者和接收者都未保留该资源】")
        info = res["data"]["Info"]
        data = {
            "driveId": 0,
            "etag": info["Etag"],
            "fileId": info["FileId"],
            "s3keyFlag": info["S3KeyFlag"],
            "type": info["Type"],
            "fileName": info["FileName"],
            "size": info["Size"],
        }
        resp = self.request(DOWNLOAD_INFO,"POST", json_data=data)
        url = resp["data"]["DownloadUrl"].replace(r"\u0026", "&")
        url = re.search("params=(.*?)&", url).group(1)
        url = base64.b64decode(url).decode()
        resp = requests.get(url, allow_redirects=True)
        url = resp.json()["data"]["redirect_url"]
        return info["FileId"], requests.get(url).text