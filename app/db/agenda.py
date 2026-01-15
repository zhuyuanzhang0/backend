import re
from app.core.logger import log
from dotenv import load_dotenv
import os
import pymysql
from typing import Optional


load_dotenv()

HOST = os.getenv("HOST")
PORT = int(os.getenv("PORT"))
USER = os.getenv("USER")
PASSWORD = os.getenv("PASSWORD")


def get_conn(DB_NAME):
    """获取一个连接到 bills 数据库的连接"""
    conn = pymysql.connect(
        host=HOST,
        port=PORT,
        user=USER,
        password=PASSWORD,
        database=DB_NAME,
        charset="utf8mb4",
        autocommit=True,  # 简化操作，不用手动 commit
    )
    return conn


_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9_]{1,64}$")

def _safe_table_name(table_name: str) -> str:
    """
    MySQL 表名/字段名不能用参数化占位符，只能拼接。
    所以必须严格校验，仅允许 [A-Za-z0-9_] 且长度 <= 64。
    """
    if not table_name or not _IDENTIFIER_RE.fullmatch(table_name):
        raise ValueError(f"非法表名: {table_name!r}（仅允许字母数字下划线，长度<=64）")
    return table_name

_ALLOWED_FIELDS = {
    "uid", "recurrence_id", "kind",
    "summary", "description", "location",
    "dtstart", "dtend", "due", "all_day",
    "status", "percent_complete", "priority",
    "rrule", "exdate", "categories", "sequence",
    # created_at/updated_at 通常不让外部写；如果你要允许也可加进去
}

def insert_event(table_name: str, data: dict, db_name: str = "agenda"):
    """
    插入一条日程/待办

    data 示例：
    {
        "uid": "xxx-uid",
        "kind": "VEVENT" or "VTODO",
        "summary": "标题",
        "description": "...",
        "location": "...",
        "dtstart": "2025-01-01 10:00:00",
        "dtend": "2025-01-01 11:00:00",
        "due": None,
        "all_day": 0,
        "status": "NEEDS-ACTION",
        "percent_complete": 0,
        "priority": 5,
        "rrule": "FREQ=WEEKLY;BYDAY=MO",
        "exdate": "20250101T100000Z,20250108T100000Z",
        "categories": "work,meeting",
        "sequence": 0,
        "recurrence_id": None
    }

    返回：新插入记录 id
    """
    table_name = _safe_table_name(table_name)

    # 只允许白名单字段
    clean = {k: v for k, v in (data or {}).items() if k in _ALLOWED_FIELDS}

    # 必填校验（按你业务可再加强）
    if not clean.get("uid"):
        raise ValueError("uid 不能为空")
    if clean.get("kind") not in ("VEVENT", "VTODO"):
        raise ValueError("kind 必须是 'VEVENT' 或 'VTODO'")


    cols = ", ".join(f"`{k}`" for k in clean.keys())
    placeholders = ", ".join(["%s"] * len(clean))
    sql = f"INSERT INTO `{table_name}` ({cols}) VALUES ({placeholders})"

    conn = get_conn(db_name)
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, tuple(clean.values()))
            return cursor.lastrowid
    except Exception as e:
        log(e)
        raise
    finally:
        conn.close()

def delete_event(table_name: str, event_id: int, db_name: str = "agenda") -> int:
    """
    删除一条记录（按 id）
    返回：受影响行数
    """
    table_name = _safe_table_name(table_name)

    conn = get_conn(db_name)
    try:
        with conn.cursor() as cursor:
            sql = f"DELETE FROM `{table_name}` WHERE `id`=%s"
            cursor.execute(sql, (event_id,))
            return cursor.rowcount
    except Exception as e:
        log(e)
        raise
    finally:
        conn.close()

def update_event(table_name: str, event_id: int, data: dict, db_name: str = "agenda") -> int:
    """
    更新一条记录（按 id）
    data：可传任意可更新字段（白名单内）
    返回：受影响行数
    """
    table_name = _safe_table_name(table_name)

    clean = {k: v for k, v in (data or {}).items() if k in _ALLOWED_FIELDS}
    if not clean:
        return 0

    # 可选：禁止修改 kind/uid（按你业务）
    # clean.pop("uid", None)
    # clean.pop("kind", None)

    set_clause = ", ".join([f"`{k}`=%s" for k in clean.keys()])
    sql = f"UPDATE `{table_name}` SET {set_clause} WHERE `id`=%s"

    conn = get_conn(db_name)
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, tuple(clean.values()) + (event_id,))
            return cursor.rowcount
    except Exception as e:
        log(e)
        raise
    finally:
        conn.close()

def list_events(table_name: str, db_name: str = "agenda"):
    """
    获取所有记录（按时间排序：事件按 dtstart，待办按 due，再按 created_at）
    返回：list[dict]
    """
    table_name = _safe_table_name(table_name)

    conn = get_conn(db_name)
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            sql = f"""
                SELECT *
                FROM `{table_name}`
                ORDER BY
                    COALESCE(`dtstart`, `due`) ASC,
                    `created_at` ASC
            """
            cursor.execute(sql)
            return cursor.fetchall()
    except Exception as e:
        log(e)
        raise
    finally:
        conn.close()