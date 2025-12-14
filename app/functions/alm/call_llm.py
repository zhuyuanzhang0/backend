import os
import datetime
from fastapi import  UploadFile, HTTPException
from app.functions.alm.prompts.prompts import CALENDAR_IMG_PROMPT, BILL_IMG_PROMPT, VCODE_IMG_PROMPT, VCODE_TEXT_PROMPT
import base64
from dotenv import load_dotenv
import requests
import json
import asyncio
import httpx
from app.db.tools import insert_bill
import logging
logger = logging.getLogger("app")  # 自定义一个 logger 名称

# 默认会加载当前工作目录下的 .env 文件
load_dotenv()

async def calendar_llm(img: UploadFile) -> dict:
    try:

        content = await img.read()
        b64 = base64.b64encode(content).decode("utf-8")

        payload = {
            "model": "Qwen/Qwen3-VL-235B-A22B-Instruct",
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "text",
                            "text":  CALENDAR_IMG_PROMPT,
                        }
                    ]
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{b64}"
                            },
                        },
                    ],
                }
            ],
            "stream": False,
            "temperature": 0,
        }

        api_key = os.getenv("SILICONFLOW_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="服务器未配置 API 密钥")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        url = "https://api.siliconflow.cn/v1/chat/completions"

        response = requests.post(url, json=payload, headers=headers, timeout=60)
        resp_json = response.json()
        content = resp_json["choices"][0]["message"]["content"]
        json_obj = json.loads(content)
        return json_obj


    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail= str(e) ,
        )



async def vcode_llm(img: UploadFile):
    try:

        content = await img.read()
        b64 = base64.b64encode(content).decode("utf-8")

        payload = {
            "model": "Qwen/Qwen3-VL-235B-A22B-Instruct",
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "text",
                            "text":  VCODE_IMG_PROMPT,
                        }
                    ]
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{b64}"
                            },
                        },
                    ],
                }
            ],
            "stream": False,
            "temperature": 0,
        }

        api_key = os.getenv("SILICONFLOW_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="服务器未配置 API 密钥")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        url = "https://api.siliconflow.cn/v1/chat/completions"

        response = requests.post(url, json=payload, headers=headers, timeout=60)
        resp_json = response.json()
        content = resp_json["choices"][0]["message"]["content"]
        return content


    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail= str(e) ,
        )




async def vcode_llm_text(text):
    try:

        payload = {
            "model": "deepseek-ai/DeepSeek-V3.1-Terminus",
            "messages": [
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "text",
                            "text":  VCODE_IMG_PROMPT,
                        }
                    ]
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text":  text,
                        }
                    ],
                }
            ],
            "stream": False,
            "temperature": 0,
        }

        api_key = os.getenv("SILICONFLOW_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="服务器未配置 API 密钥")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        url = "https://api.siliconflow.cn/v1/chat/completions"

        response = requests.post(url, json=payload, headers=headers, timeout=60)
        resp_json = response.json()
        content = resp_json["choices"][0]["message"]["content"]
        return content


    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail= str(e) ,
        )




async def bill_llm(content, position):

    try:

        b64 = base64.b64encode(content).decode("utf-8")

        payload = {
            "model": "Qwen/Qwen3-VL-235B-A22B-Instruct",
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "text",
                            "text":  BILL_IMG_PROMPT,
                        }
                    ]
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{b64}"
                            },
                        },
                    ],
                }
            ],
            "stream": False,
            "temperature": 0,
        }

        api_key = os.getenv("SILICONFLOW_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="服务器未配置 API 密钥")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        url = "https://api.siliconflow.cn/v1/chat/completions"

        # 使用异步 HTTP 客户端避免在事件循环中阻塞
        for _ in range(3):
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(url, json=payload, headers=headers)
                break
            except httpx.TimeoutException:
                logger.error("TimeoutException")
                continue
        logger.info("bill : " + str(response.json()) )


        # async with httpx.AsyncClient(timeout=60.0) as client:
        #     response = await client.post(url, json=payload, headers=headers)
        resp_json = response.json()
        json_obj = json.loads(content)
        json_obj['position'] = position
        # 将同步的数据库插入放到线程池中执行，防止阻塞事件循环
        await asyncio.to_thread(insert_bill, json_obj)
        return json_obj


    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )
