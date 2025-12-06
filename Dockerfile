FROM python:3.11-slim

# 安装 uv，使用清华镜像安装
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple uv

# 让 uv 永远走国内镜像
ENV UV_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
ENV UV_EXTRA_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/

WORKDIR /app

# 先复制依赖文件（提高缓存命中率）
COPY pyproject.toml uv.lock ./

# uv sync 会自动读取 ENV 并使用国内源
RUN uv sync --frozen --index https://pypi.tuna.tsinghua.edu.cn/simple/
# 再复制源码
COPY . .

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9000"]
