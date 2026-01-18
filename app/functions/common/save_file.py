from app.core.config import UPLOAD_DIR
from fastapi import  UploadFile
import os
import datetime
from typing import Optional

async def save_file(f: UploadFile, key: Optional[str] = None) -> dict:
    """
    保存上传的文件到本地，并返回相关信息
    """
    # 确保目录存在
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # 取扩展名
    ext = os.path.splitext(f.filename or "")[1]
    if not ext:
        ext = ".jpg"

    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

    # 生成文件名
    if key:
        base_name = key
        filename = f"{base_name}{ext}"
        file_path = os.path.join(UPLOAD_DIR, filename)

        # 如果重名，加时间戳
        if os.path.exists(file_path):
            filename = f"{base_name}_{timestamp}{ext}"
            file_path = os.path.join(UPLOAD_DIR, filename)
    else:
        filename = f"{timestamp}{ext}"
        file_path = os.path.join(UPLOAD_DIR, filename)

    # 读取文件内容
    content = await f.read()
    if not content:
        raise ValueError("上传文件内容为空")

    # 写入磁盘
    with open(file_path, "wb") as out:
        out.write(content)

    return {
        "message": "上传成功",
        "filename": filename,
        "url": f"/{UPLOAD_DIR}/{filename}",
    }


# async def save_file(f: UploadFile) -> dict:
#     """
#     保存上传的文件到本地，并返回相关信息
#     """
#     # 生成唯一文件名
#     ext = os.path.splitext(f.filename or "")[1]
#     if not ext:
#         ext = ".jpg"

#     filename = f"{datetime.datetime.now().timestamp():.0f}{ext}"
#     file_path = os.path.join(UPLOAD_DIR, filename)

#     # 确保目录存在
#     os.makedirs(UPLOAD_DIR, exist_ok=True)

#     # 保存文件
#     content = await f.read()
#     if not content:
#         # 空文件也可以当成错误处理
#         raise ValueError("上传文件内容为空")

#     with open(file_path, "wb") as f:
#         f.write(content)

#     return {
#         "message": "上传成功",
#         "filename": filename,
#         "url": f"/{UPLOAD_DIR}/{filename}",
#     }
