from dotenv import load_dotenv
import os
import pymysql
from typing import Optional
from app.core import log


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


def has(key: str) -> bool:
    conn = get_conn("bills")
    try:

        with conn.cursor() as cur:
            cur.execute(f"USE `kv`;")
            cur.execute(
                f"SELECT 1 FROM `kv` WHERE `k`=%s LIMIT 1;",
                (key,),
            )
            return cur.fetchone() is not None
    except Exception as e:
        log(e)
    finally:
        conn.close()
def get(key: str) -> Optional[str]:
    conn = get_conn("bills")
    try:
        with conn.cursor() as cur:
            cur.execute(f"USE `kv`;")
            cur.execute(
                f"SELECT `v` FROM `kv` WHERE `k`=%s LIMIT 1;",
                (key,),
            )
            row = cur.fetchone()
            return None if row is None else row[0]
    except Exception as e:
        log(e)
    finally:
        conn.close()
def set(key: str, value: str) -> None:
    conn = get_conn("bills")
    try:
        with conn.cursor() as cur:
            cur.execute(f"USE `kv`;")
            cur.execute(
                f"""
                INSERT INTO `kv` (`k`, `v`)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE `v`=VALUES(`v`);
                """,
                (key, value),
            )
    except Exception as e:
        log(e)
    finally:
        conn.close()
def delete(key: str) -> bool:
    """删除成功返回 True；不存在返回 False"""
    conn = get_conn("bills")
    try:
        with conn.cursor() as cur:
            cur.execute(f"USE `kv`;")
            cur.execute(
                f"DELETE FROM `kv` WHERE `k`=%s;",
                (key,),
            )
            return cur.rowcount > 0

    except Exception as e:
        log(e)
    finally:
        conn.close()

