# Apple AI Assistant — 后端服务

基于 FastAPI 的图像/文本 AI 接口服务，包含图床、日程识别、记账、取件码识别和位置记录功能。

## 关键特性
- 图像上传（图床）和文件静态托管
- 从图片识别日程、账单、取件码等信息
- 账单入库与时间范围查询
- 位置记录管理接口
- 可选的 LLM 调用集成

## 要求
- Python 3.11+
- MySQL 8.x（或兼容）并使用 UTF-8 字符集
- 依赖在 `pyproject.toml` 中声明（项目使用 `uv` 作为运行/依赖管理工具）

## 本地开发：安装与运行
```powershell
# 安装依赖
uv sync

# 开发模式运行
uv run -m app.main
```

服务启动后，静态上传目录 `uploads/` 将在项目根生成并对外可访问。

## 初始化数据库
项目包含两个库：
- `bills`：账单表 `bill`
- `record_position`：位置表 `position_record`

## API 概览

- `POST /img` — 上传图片到图床，返回 JSON：`{ "message": "...", "filename": "...", "url": "..." }`
- `POST /cal` — 从日程/备忘类图片识别日程信息，返回标准化 JSON
- `POST /book` — 从账单图片识别并入库，表单字段包含 `pos`（位置描述）等
- `GET /bills` — 查询账单，支持查询参数 `start_time` 与 `end_time`
- `PUT /bill` — 更新账单，Body 示例：`[position, type, detail, title, amount, created_at, id]`
- `POST /location` — 新增位置记录，JSON 示例：`{ "name": "...", "lat": 0.0, "lon": 0.0, "detail": null }`
- `POST /code` — 从图片中识别取件/取餐码，返回提取的文本
- `POST /codetext` — 从纯文本中提取取件/取餐码

详细路由及参数说明请查看 `app/api/routes.py`。

## 代码结构

```
app/
  main.py          # FastAPI 入口，包含静态文件挂载与启动逻辑
  api/routes.py    # 路由定义与请求处理
  core/
    config.py      # 配置与常量
    logger.py      # 日志设置
  db/
    init.py        # DB 初始化函数
    tools.py       # DB 操作工具
  functions/
    alm/             # 与 LLM 交互的封装与提示词
    common/          # 图片保存、解析等通用工具
uploads/           # 运行时的上传目录
```
