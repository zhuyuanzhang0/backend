from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import asyncio
import logging
import requests
import json
from pytz import timezone


logger = logging.getLogger(__name__)

# scheduler = AsyncIOScheduler()
scheduler = AsyncIOScheduler(timezone=timezone("Asia/Shanghai"))

async def qiandao_async():
    """
    异步执行签到逻辑
    """
    try:
        if asyncio.iscoroutinefunction(qiandao):
            await qiandao()
        else:
            # 同步函数，放入线程池执行，避免阻塞事件循环
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, qiandao)

        logger.info("qiandao 执行成功")
    except Exception as e:
        logger.exception(f"qiandao 执行失败: {e}")


def start_scheduler():
    """
    启动定时任务
    """
    scheduler.add_job(
        qiandao_async,
        CronTrigger(hour=9, minute=0),  # 每天 9:00
        id="qiandao_daily_job",
        replace_existing=True,
    )

    scheduler.start()

def qiandao():
        
    # 使用 Session 保持 Cookie
    session = requests.Session()

    # ========== 1. 登录接口 ==========
    login_url = "https://12.airtcp.me/denglu"

    login_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "*/*",
        "Origin": "https://12.airtcp.me",
        "Referer": "https://12.airtcp.me/",
    }

    login_data = {
        "email": "2930481971@qq.com",
        "passwd": "888675wsq",
        "code": ""
    }

    login_resp = session.post(
        login_url,
        headers=login_headers,
        data=login_data,
        timeout=10
    )

    print("登录状态码:", login_resp.status_code)
    print("登录响应:", login_resp.json())

    # 查看登录后拿到的 Cookie（调试用）
    print("登录后 Cookie:")
    for k, v in session.cookies.items():
        print(f"{k} = {v}")

    # ========== 2. 签到接口 ==========
    checkin_url = "https://12.airtcp.me/user/checkin"

    checkin_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Origin": "https://12.airtcp.me",
        "Referer": "https://12.airtcp.me/user",
    }

    checkin_resp = session.post(
        checkin_url,
        headers=checkin_headers,
        timeout=10
    )

    print("签到状态码:", checkin_resp.status_code)
    print("签到结果:", checkin_resp.json())
