import pymysql

from dotenv import load_dotenv
import os
load_dotenv()

HOST = os.getenv("HOST")
PORT = int(os.getenv("PORT"))
USER = os.getenv("USER")
PASSWORD = os.getenv("PASSWORD")


def init_position_db():
    """初始化 record_position 数据库和 position_record 表"""
    conn = pymysql.connect(
        host=HOST,
        port=PORT,
        user=USER,
        password=PASSWORD,
        charset="utf8mb4",
        autocommit=True
    )

    try:
        with conn.cursor() as cursor:
            # 创建数据库
            cursor.execute("""
                CREATE DATABASE IF NOT EXISTS `record_position`
                DEFAULT CHARACTER SET utf8mb4
                COLLATE utf8mb4_unicode_ci;
            """)

            # 使用数据库
            cursor.execute("USE `record_position`;")

            # 创建表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS `position_record` (
                    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键',
                    `name` VARCHAR(255) NOT NULL COMMENT '名称',
                    `lat` DOUBLE NOT NULL COMMENT '纬度',
                    `lon` DOUBLE NOT NULL COMMENT '经度',
                    `detail` VARCHAR(500) DEFAULT NULL COMMENT '详情',
                    `time` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录时间',
                    PRIMARY KEY (`id`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='位置记录表';
            """)

            print("record_position 初始化完成")
    finally:
        conn.close()

def init_bills_db():
    # 连接到 MySQL
    conn = pymysql.connect(
        host=HOST,
        port=PORT,
        user=USER,
        password=PASSWORD,
        charset="utf8mb4",
        autocommit=True,  # 方便执行 DDL
    )

    try:
        with conn.cursor() as cursor:
            # 1. 创建数据库 bills（如果不存在）
            cursor.execute(
                "CREATE DATABASE IF NOT EXISTS `bills` "
                "DEFAULT CHARACTER SET utf8mb4 "
                "COLLATE utf8mb4_unicode_ci;"
            )
            print("数据库 bills 已确认存在/创建成功")

            # 2. 切换到 bills 数据库
            cursor.execute("USE `bills`;")

            # 3. 创建表 bill（如果不存在）
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS `bill` (
                `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键ID',
                `position` TEXT COMMENT '位置',
                `type` VARCHAR(50) NOT NULL COMMENT '类型',
                `detail` TEXT COMMENT '详情',
                `amount` DECIMAL(10,2) NOT NULL COMMENT '金额',
                `title` VARCHAR(255) NOT NULL COMMENT '标题',
                `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                PRIMARY KEY (`id`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='账单表';
            """
            cursor.execute(create_table_sql)
            print("数据表 bill 已确认存在/创建成功")

    finally:
        conn.close()
        print("连接已关闭")



def init_kv_db():
    # 连接到 MySQL
    conn = pymysql.connect(
        host=HOST,
        port=PORT,
        user=USER,
        password=PASSWORD,
        charset="utf8mb4",
        autocommit=True,  # 方便执行 DDL
    )

    try:
        with conn.cursor() as cursor:
            # 1. 创建数据库 kv（如果不存在）
            cursor.execute(
                "CREATE DATABASE IF NOT EXISTS `kv` "
                "DEFAULT CHARACTER SET utf8mb4 "
                "COLLATE utf8mb4_unicode_ci;"
            )
            print("数据库 kv 已确认存在/创建成功")

            # 2. 切换到 kv 数据库
            cursor.execute("USE `kv`;")

            # 3. 创建表 kv（如果不存在）

            create_table_sql = """
            CREATE TABLE IF NOT EXISTS `kv` (
                `k` VARCHAR(255) NOT NULL,
                `v` LONGTEXT NULL,
                `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                                ON UPDATE CURRENT_TIMESTAMP,
                PRIMARY KEY (`k`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
            cursor.execute(create_table_sql)
            print("数据表 kv 已确认存在/创建成功")

    finally:
        conn.close()
        print("连接已关闭")

    