import pymysql
import re
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

    finally:
        conn.close()



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

    finally:
        conn.close()

    


_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9_]{1,64}$")

def _safe_table_name(table_name: str) -> str:
    """
    MySQL 表名/字段名不能用参数化占位符，只能拼接。
    所以必须严格校验，仅允许 [A-Za-z0-9_] 且长度 <= 64。
    """
    if not table_name or not _IDENTIFIER_RE.fullmatch(table_name):
        raise ValueError(f"非法表名: {table_name!r}（仅允许字母数字下划线，长度<=64）")
    return table_name

def init_agenda_db(table_name: str, db_name: str = "agenda"):
    """
    初始化数据库 + 用户表（表名由参数传入）
    表内同时存 VEVENT（日程）和 VTODO（待办）
    """
    table_name = _safe_table_name(table_name)

    conn = pymysql.connect(
        host=HOST,
        port=PORT,
        user=USER,
        password=PASSWORD,
        charset="utf8mb4",
        autocommit=True,
    )

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
                "DEFAULT CHARACTER SET utf8mb4 "
                "COLLATE utf8mb4_unicode_ci;"
            )
            cursor.execute(f"USE `{db_name}`;")

            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS `{table_name}` (
                `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键ID',

                `uid` VARCHAR(255) NOT NULL COMMENT 'iCalendar UID',
                `recurrence_id` DATETIME NULL COMMENT '重复事件单次实例标识（可选）',
                `kind` ENUM('VEVENT','VTODO') NOT NULL COMMENT '类型：日程/待办',

                `summary` VARCHAR(255) NOT NULL COMMENT '标题',
                `description` TEXT NULL COMMENT '描述',
                `location` VARCHAR(255) NULL COMMENT '地点',

                `dtstart` DATETIME NULL COMMENT '开始时间（事件）',
                `dtend` DATETIME NULL COMMENT '结束时间（事件）',
                `due` DATETIME NULL COMMENT '截止时间（待办）',
                `all_day` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否全天',

                `status` VARCHAR(50) NULL COMMENT '状态（NEEDS-ACTION/IN-PROCESS/COMPLETED等）',
                `percent_complete` TINYINT UNSIGNED NULL COMMENT '进度 0-100（待办）',
                `priority` TINYINT UNSIGNED NULL COMMENT '优先级（待办）',

                `rrule` TEXT NULL COMMENT '重复规则 RRULE（可选）',
                `exdate` TEXT NULL COMMENT '例外日期 EXDATE（可选，字符串存储）',
                `categories` VARCHAR(255) NULL COMMENT '分类/标签（逗号分隔）',

                `sequence` INT NOT NULL DEFAULT 0 COMMENT '版本号（可选）',

                `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                    ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

                PRIMARY KEY (`id`),
                UNIQUE KEY `uniq_uid_kind_recur` (`uid`, `kind`, `recurrence_id`),
                KEY `idx_time` (`dtstart`, `due`),
                KEY `idx_status` (`status`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户日程/待办表';
            """
            cursor.execute(create_table_sql)

    finally:
        conn.close()
