from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Form, Body
from typing import Optional, List, Any
import os
import datetime
from pydantic import BaseModel
import json
from app.functions.common.img import save_image_file
from app.functions.alm.call_llm import calendar_llm, bill_llm, vcode_llm, vcode_llm_text
from app.core.config import UPLOAD_DIR
from app.db.tools import query_bills, update_bill, insert_position
import asyncio
router = APIRouter()


# 初始化上传目录
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

@router.post("/img",description="图床功能，上传图片并返回图片链接")
async def upload_image(img: UploadFile = File(...)):
    if not img.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="请上传图片文件")

    try:
        result = await save_image_file(img)
    except Exception as e:
        print("保存图片失败: %s", e)
        raise HTTPException(
            status_code=500,
            detail="图片保存失败，请稍后重试",
        )

    return result


@router.post("/cal")
async def calendar(img: UploadFile = File(...)):
    """
    自动识别用户图片中的事件类型
    将事件划分为日历事件calendar和提醒事件reminder
    并按指定格式输出标准化 JSON 结果
    """
    if not img.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="请上传图片文件")

    try:
        result = await calendar_llm(img)
    except Exception as e:
        print(str(e))
        raise HTTPException(
            status_code=500,
            detail= str(e),
        )

    return result


@router.post("/book")
async def book_bill(img: UploadFile = File(...), pos: str = Form(...)):
    """
    自动识别用户图片中的账单数据
    并按指定格式输出标准化 JSON 结果
    """
    if not img.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="请上传图片文件")

    img_bytes = await img.read()
    asyncio.create_task(bill_llm(img_bytes, pos))

    return {"message": "账单识别任务已启动，稍后请查看结果"}


@router.get("/bills")
async def get_bills(
    start_time: Optional[str] = Query(None),
    end_time: Optional[str] = Query(None)
):
    """
    GET /bills?start_time=xxxx&end_time=xxxx
    返回指定时间范围内的账单列表
    """

    # 参数校验
    if not start_time or not end_time:
        return {"error": "start_time and end_time are required"}

    rows = query_bills(start_time, end_time)
    data = [list(row) for row in rows]
    return data



@router.put("/bill", response_model=bool)
async def put_bill(
    bill: List[Any] = Body(..., description="要更新的一条账单：[position, type, detail, title, amount, created_at, id]")
):
    """
    更新单条账单，并返回更新前和更新后的数据。
    请求体是一维列表：
    [position, type, detail, title, amount, created_at, id]
    """
    if len(bill) != 7:
        return False
    position, type_, detail, title, amount, created_at, bill_id = bill

    data = {
        "position": position,
        "type": type_,
        "detail": detail,
        "title": title,
        "amount": amount,
        "time": created_at,   # 映射 SQL 的 created_at
    }

    # 调用 SQL 更新函数
    affected = update_bill(bill_id, data)

    # affected = 1 → 更新成功  
    # affected = 0 → id 不存在
    print(affected)
    return True if affected == 1 else False



class PositionBody(BaseModel):
    name: str
    lat: float
    lon: float
    detail: str | None = None   # 新增字段，可选
@router.post("/location")
async def add_position(body: PositionBody):
    """
    插入一条位置记录
    JSON 请求体格式:
    {
        "name": "...",
        "detail": "...",
        "lat": 39.123,
        "lon": 116.321
    }
    """
    print(body)
    asyncio.create_task(asyncio.to_thread(insert_position, body.name, body.lat, body.lon, body.detail))
    return {"message": "位置记录插入成功"}



@router.post("/code")
async def vcode(img: UploadFile = File(...)):
    """
    自动识别用户图片中的取餐吗
    并按指定格式输出
    """
    if not img.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="请上传图片文件")

    try:
        result = await vcode_llm(img)
    except Exception as e:
        print(str(e))
        raise HTTPException(
            status_code=500,
            detail= str(e),
        )

    return result


class PositionBody(BaseModel):
    detail: str | None = None   # 新增字段，可选
@router.post("/codetext")
async def add_position(body: PositionBody):
    """
    插入一条位置记录
    JSON 请求体格式:
    {
        "detail": "...",
    }
    """
    print(body)

    try:
        result = await vcode_llm_text(body.detail)
    except Exception as e:
        print(str(e))
        raise HTTPException(
            status_code=500,
            detail= str(e),
        )

    return result




