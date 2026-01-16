from dotenv import load_dotenv
import os
import pymysql

from app.core.logger import log

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

def insert_bill(data: dict):
    """
    插入一条账单记录

    data = {
        "title": "...",
        "amount": 123.45,
        "type": "...",
        "detail": "...",
        "time": "2025-01-01 12:00:00",  # 或 "2025-01-01"
        "position": "xxxx"
    }

    返回：新插入记录的 id
    """
    conn = get_conn("bills")
    try:
        with conn.cursor() as cursor:
            sql = """
                INSERT INTO bill (title, amount, type, detail, created_at, position)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(
                sql,
                (
                    data.get("title"),
                    data.get("amount"),
                    data.get("type"),
                    data.get("detail"),
                    data.get("time"),       # 映射到 created_at
                    data.get("position"),
                ),
            )
    except Exception as e:
        log(e)
    finally:
        conn.close()




def update_bill(bill_id: int, data: dict) -> int:
    """
    按 id 修改一条账单记录（直接覆盖所有字段）

    data 格式同 insert_bill：
    {
        "title": "...",
        "amount": 123.45,
        "type": "...",
        "detail": "...",
        "time": "2025-01-01 12:00:00",
        "position": "xxxx"
    }

    """
    conn = get_conn("bills")

    try:
        with conn.cursor() as cursor:
            sql = """
                UPDATE bill
                SET title = %s,
                    amount = %s,
                    type = %s,
                    detail = %s,
                    created_at = %s,
                    position = %s
                WHERE id = %s
            """
            rows = cursor.execute(
                sql,
                (
                    data.get("title"),
                    data.get("amount"),
                    data.get("type"),
                    data.get("detail"),
                    data.get("time"),   # 映射到 created_at
                    data.get("position"),
                    bill_id,
                ),
            )
        return rows 
    except Exception as e:
        log(e)
    finally:
        conn.close()



def query_bills(start_time: str, end_time: str):
    """
    查询账单（按 created_at 时间范围）

    参数:
        start_time: "2024-01-01T00:00:00"
        end_time:   "2026-01-31T23:59:59"

    返回:
        list[dict]
    """
    conn = get_conn("bills")
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT position, type, detail, title, amount, created_at, id

                FROM bill
                WHERE created_at BETWEEN %s AND %s
                ORDER BY created_at ASC;
            """
            cursor.execute(sql, (start_time, end_time))
            rows = cursor.fetchall()
            return rows
    except Exception as e:
        log(e)
    finally:
        conn.close()

def insert_position(name: str, lat: float, lon: float, detail: str = None):
    """插入一条位置记录，返回新 id"""
    conn = get_conn("record_position")

    try:
        with conn.cursor() as cursor:
            sql = """
                INSERT INTO position_record (name, lat, lon, detail)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(sql, (name, lat, lon, detail))
    except Exception as e:
        log(e)
    finally:
        conn.close()


