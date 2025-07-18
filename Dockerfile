# 使用官方的Python 3.11 slim镜像作为基础
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装 WeasyPrint 和 PyMuPDF 所需的系统级依赖库
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY ./requirements.txt .

# 升级pip并使用requirements.txt安装Python依赖
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 复制您的应用代码
COPY . .

# 暴露您的API服务运行的端口
EXPOSE 8699

# 容器启动时运行的命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8699"]

