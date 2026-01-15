from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Form, Body
from typing import Optional, List, Any, Literal
import os
import datetime
from pydantic import BaseModel
import json
from app.functions.common.img import save_image_file
from app.functions.alm.call_llm import calendar_llm, bill_llm, vcode_llm, vcode_llm_text
from app.db.agenda import insert_event, delete_event, update_event, list_events
from app.core.config import UPLOAD_DIR
from app.db.tools import query_bills, update_bill, insert_position
from app.db import kv_tools
import asyncio
router = APIRouter()


# 初始化上传目录
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)



class update_icsBody(BaseModel):
    name: str
@router.post("/update_ics",description="更新ics文件")
def save_upload_replace(body: update_icsBody):
    try:
        if not body.name:
            raise ValueError("名称为空")
        
        ics_text = export_ics(table_name=body.name, cal_name=body.name, tzid="Asia/Shanghai")
        with open("cal.ics", "wb", encoding="utf-8", newline="") as f:
            f.write(ics_text)

        return {"status":'ok'}
    except Exception as e:
        return {"status":'error',"message":str(e)}





# 2) Pydantic body
class AgendaEventCreateBody(BaseModel):
    uid: str
    kind: Literal["VEVENT", "VTODO"]

    recurrence_id: str | None = None
    summary: str | None = None
    description: str | None = None
    location: str | None = None

    dtstart: str | None = None
    dtend: str | None = None
    due: str | None = None
    all_day: int | None = None

    status: str | None = None
    percent_complete: int | None = None
    priority: int | None = None

    rrule: str | None = None
    exdate: str | None = None
    categories: str | None = None
    sequence: int | None = None


class AgendaEventUpdateBody(BaseModel):
    # 全部可选；用 exclude_unset 区分“没传” vs “显式传 null”
    uid: str | None = None
    kind: Literal["VEVENT", "VTODO"] | None = None

    recurrence_id: str | None = None
    summary: str | None = None
    description: str | None = None
    location: str | None = None

    dtstart: str | None = None
    dtend: str | None = None
    due: str | None = None
    all_day: int | None = None

    status: str | None = None
    percent_complete: int | None = None
    priority: int | None = None

    rrule: str | None = None
    exdate: str | None = None
    categories: str | None = None
    sequence: int | None = None


# 3) 四个接口：增/查/改/删

@router.post("/agenda/{table_name}/events", description="新增日程/待办（VEVENT/VTODO）")
async def create_agenda_event(table_name: str, body: AgendaEventCreateBody, db_name: str = "agenda"):
    try:
        new_id = await asyncio.to_thread(insert_event, table_name, body.model_dump(exclude_unset=True), db_name)
        return {"id": new_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agenda/{table_name}/events", description="获取全部日程/待办（按 dtstart/due/created_at 排序）")
async def get_agenda_events(table_name: str, db_name: str = "agenda"):
    try:
        rows = await asyncio.to_thread(list_events, table_name, db_name)
        return rows
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/agenda/{table_name}/events/{event_id}", description="更新日程/待办（按 id）")
async def patch_agenda_event(table_name: str, event_id: int, body: AgendaEventUpdateBody, db_name: str = "agenda"):
    try:
        payload = body.model_dump(exclude_unset=True)
        affected = await asyncio.to_thread(update_event, table_name, event_id, payload, db_name)
        return {"affected": affected}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/agenda/{table_name}/events/{event_id}", description="删除日程/待办（按 id）")
async def remove_agenda_event(table_name: str, event_id: int, db_name: str = "agenda"):
    try:
        affected = await asyncio.to_thread(delete_event, table_name, event_id, db_name)
        return {"affected": affected}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




@router.post("/img",description="图床功能，上传图片并返回图片链接")
async def upload_image(img: UploadFile = File(...)):
    if not img.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="请上传图片文件")

    try:
        result = await save_image_file(img)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="图片保存失败，请稍后重试",
        )

    return result


class KVSetBody(BaseModel):
    k: str
    v: str


class KVGetBody(BaseModel):
    k: str


@router.post("/kv/set")
async def kv_set(body: KVSetBody):
    kv_tools.set(body.k, body.v)
    return {"k": body.k, "v": body.v}


@router.post("/kv/get")
async def kv_get(body: KVGetBody):
    value = kv_tools.get(body.k)
    if value is None:
        raise HTTPException(status_code=404, detail="key not found")
    return {"k": body.k, "v": value}


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
        raise HTTPException(
            status_code=500,
            detail= str(e),
        )

    return result


class PositionBody(BaseModel):
    detail: str | None = None   # 新增字段，可选
@router.post("/codetext")
async def vcodetext(body: PositionBody):
    """
    插入一条位置记录
    JSON 请求体格式:
    {
        "detail": "...",
    }
    """

    try:
        result = await vcode_llm_text(body.detail)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail= str(e),
        )

    return result



