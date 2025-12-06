from app.core.config import UPLOAD_DIR
from fastapi import  UploadFile
import os
import datetime



async def save_image_file(img: UploadFile) -> dict:
    """
    保存上传的图片到本地，并返回相关信息
    """
    # 生成唯一文件名
    ext = os.path.splitext(img.filename or "")[1]
    if not ext:
        ext = ".jpg"

    filename = f"{datetime.datetime.now().timestamp():.0f}{ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    # 确保目录存在
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # 保存文件
    content = await img.read()
    if not content:
        # 空文件也可以当成错误处理
        raise ValueError("上传文件内容为空")

    with open(file_path, "wb") as f:
        f.write(content)

    return {
        "message": "上传成功",
        "filename": filename,
        "url": f"/{UPLOAD_DIR}/{filename}",
    }
