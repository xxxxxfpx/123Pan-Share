import Pan123
from Share.sign import panToSign, signToPan


#============= 网盘登录 ===============
p = Pan123.Pan123("用户名", "用户密码")
try:
    p.login()
except Exception as e:
    print("登录失败", e)
    exit()
#=====================================

#============= 回调函数 ===============
# panToSign 与 signToPan 最后一个参数可传入回调函数监控运行进程
# def process(nowInfo, handleFile=None, allFile=None):
#     '''
#     :param nowInfo:     输出信息
#     :param handleFile:  已处理文件数
#     :param allFile:     总文件数
#     :return:
#     '''
#=====================================

#============= 创建分享 ===============
# sign = panToSign(p, 1)             # 目录Id或者文件Id
# sign = panToSign(p, [1,2,3,4])     # 目录Id或者文件Id列表
# sign = panToSign(p, "/转存/文件")    # 文件夹的分享路径
signIter = panToSign(p, 123)
defaultName = next(signIter)         # 生成的分享目录默认名称
sign = signIter.send(defaultName)    # 设置分享根目录名称
print(sign)                          # 生成的分享链
#=====================================

#============= 接收分享 ===============
# signToPan(网盘驱动, 分享连, 保存分享文件的位置Id)
# signToPan(网盘驱动, 分享连, 保存分享文件的位置路径)
# 支持的sign
# - ******[32位sign]**********
# - 32位sign******
signToPan(p, sign, 0)  # 为0时 保存分享文件的位置为网盘根目录
#=====================================
