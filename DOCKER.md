# 🐳 Docker 部署指南

AI智能题库查询系统完整的Docker化部署方案，支持多种部署模式和监控配置。

## 📋 目录

- [🚀 快速开始](#-快速开始)
- [🏗️ 部署模式](#️-部署模式)
- [⚙️ 配置说明](#️-配置说明)
- [📁 目录结构](#-目录结构)
- [🔧 环境配置](#-环境配置)
- [🌐 网络配置](#-网络配置)
- [📊 监控配置](#-监控配置)
- [🔒 安全配置](#-安全配置)
- [🚨 故障排除](#-故障排除)
- [🔄 更新升级](#-更新升级)

## 🚀 快速开始

### 系统要求

- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **内存**: 最小 2GB，推荐 4GB+
- **磁盘空间**: 最小 5GB 可用空间

### 一键部署

**Linux/macOS:**
```bash
# 克隆项目
git clone https://github.com/blankzsh/AI_OCS_Question_bank.git
cd AI_OCS_Question_bank

# 赋予执行权限
chmod +x deploy.sh

# 启动开发环境
./deploy.sh

# 启动生产环境
./deploy.sh --mode prod --build
```

**Windows:**
```cmd
# 克隆项目
git clone https://github.com/blankzsh/AI_OCS_Question_bank.git
cd AI_OCS_Question_bank

# 启动开发环境
deploy.bat

# 启动生产环境
deploy.bat --mode prod --build
```

### 访问服务

部署完成后，可通过以下地址访问：

- **API服务**: http://localhost:8081
- **API文档**: http://localhost:8081/docs
- **健康检查**: http://localhost:8081/health

## 🏗️ 部署模式

### 1. 开发模式 (dev)

```bash
./deploy.sh --mode dev
```

**包含服务:**
- AI问答系统应用
- Redis缓存 (可选)

**特点:**
- 开启调试模式
- 支持热重载
- 详细日志输出

### 2. 生产模式 (prod)

```bash
./deploy.sh --mode prod --build
```

**包含服务:**
- AI问答系统应用
- Redis缓存
- Nginx反向代理

**特点:**
- 关闭调试模式
- Nginx负载均衡
- 生产级配置

### 3. 完整模式 (full)

```bash
./deploy.sh --mode full --build
```

**包含服务:**
- AI问答系统应用
- Redis缓存
- Nginx反向代理
- Prometheus监控

**特点:**
- 完整监控体系
- 性能指标收集
- 可视化监控面板

## ⚙️ 配置说明

### 环境变量配置

编辑 `docker.env` 文件：

```env
# 应用基础配置
APP_NAME=AI智能题库查询系统
SERVER_HOST=0.0.0.0
SERVER_PORT=8081

# 数据库配置
DATABASE_URL=sqlite:///./data/app.db

# Redis配置
REDIS_URL=redis://redis:6379/0

# AI平台配置 (在config.yaml中配置具体API密钥)
OPENAI_API_KEY=your_openai_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key
ALIBABA_API_KEY=your_alibaba_api_key
GOOGLE_API_KEY=your_google_api_key

# 安全配置
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS配置
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080
```

### AI平台密钥配置

编辑 `config.yaml` 文件：

```yaml
app:
  name: "AI智能题库查询系统"
  version: "2.0.0"

server:
  host: "0.0.0.0"
  port: 8081
  reload: false

ai_providers:
  openai:
    api_key: "${OPENAI_API_KEY}"
    api_base: "https://api.openai.com/v1"
    model: "gpt-3.5-turbo"

  deepseek:
    api_key: "${DEEPSEEK_API_KEY}"
    api_base: "https://api.deepseek.com/v1"
    model: "deepseek-chat"

  alibaba:
    api_key: "${ALIBABA_API_KEY}"
    api_base: "https://dashscope.aliyuncs.com/api/v1"
    model: "qwen-plus"

  google:
    api_key: "${GOOGLE_API_KEY}"
    api_base: "https://generativelanguage.googleapis.com/v1"
    model: "gemini-pro"

database:
  url: "sqlite:///./data/app.db"
  echo: false
  pool_size: 10
  max_overflow: 20

redis:
  url: "${REDIS_URL}"
  decode_responses: true
  socket_timeout: 5
  connection_pool_max_connections: 50

logging:
  level: "INFO"
  format: "json"
  file: "logs/app.log"
```

## 📁 目录结构

```
AI_wenda/
├── Dockerfile                 # 应用镜像构建文件
├── docker-compose.yml         # 服务编排文件
├── docker.env                 # 环境变量配置
├── .dockerignore             # Docker忽略文件
├── deploy.sh                 # Linux/macOS部署脚本
├── deploy.bat                # Windows部署脚本
├── DOCKER.md                 # Docker部署文档
├── config.yaml               # 应用配置文件
├── nginx/
│   └── nginx.conf            # Nginx配置
├── monitoring/
│   └── prometheus.yml        # Prometheus监控配置
├── data/                     # 数据持久化目录
│   └── databases/            # 数据库文件
├── logs/                     # 日志目录
└── app/                      # 应用代码目录
```

## 🔧 环境配置

### 数据持久化

以下目录会自动挂载到容器外部：

- `./data/databases` → `/app/databases` (数据库文件)
- `./data` → `/app/data` (应用数据)
- `./logs` → `/app/logs` (日志文件)

### 端口映射

| 服务 | 容器端口 | 主机端口 | 说明 |
|------|----------|----------|------|
| AI问答系统 | 8081 | 8081 | API服务 |
| Redis | 6379 | 6379 | 缓存服务 |
| Nginx | 80/443 | 80/443 | 反向代理 |
| Prometheus | 9090 | 9090 | 监控服务 |

## 🌐 网络配置

### 内部网络

所有服务运行在自定义的Docker网络 `ai-wenda-network` 中：

- **网络名称**: `ai-wenda-network`
- **网络类型**: `bridge`
- **服务发现**: 容器名称作为主机名

### 服务间通信

```yaml
# 应用连接Redis示例
services:
  ai-wenda:
    depends_on:
      - redis
    environment:
      REDIS_URL: redis://redis:6379/0
```

## 📊 监控配置

### Prometheus监控

启用完整模式后，Prometheus会自动收集以下指标：

- **应用指标**: 请求量、响应时间、错误率
- **系统指标**: CPU、内存、磁盘使用率
- **Redis指标**: 连接数、命中率、内存使用

### 监控面板

访问 http://localhost:9090 查看Prometheus监控界面：

1. 查看预定义的监控指标
2. 创建自定义查询
3. 设置告警规则
4. 查看服务状态

### 指标说明

| 指标名称 | 说明 | 类型 |
|----------|------|------|
| `http_requests_total` | HTTP请求总数 | Counter |
| `http_request_duration_seconds` | 请求耗时 | Histogram |
| `process_cpu_seconds_total` | CPU使用时间 | Counter |
| `process_resident_memory_bytes` | 内存使用量 | Gauge |

## 🔒 安全配置

### 容器安全

1. **非root用户**: 应用运行在普通用户下 (UID: 1000)
2. **最小权限**: 只授予必要的系统权限
3. **资源限制**: 可配置CPU和内存限制

### 网络安全

1. **内部网络**: 服务间通信通过内部网络
2. **端口控制**: 只暴露必要的端口
3. **HTTPS支持**: Nginx配置SSL证书

### 数据安全

1. **密钥管理**: 敏感信息通过环境变量传递
2. **数据加密**: 数据库文件可配置加密
3. **备份策略**: 定期备份数据目录

## 🚨 故障排除

### 常见问题

#### 1. 容器启动失败

```bash
# 查看容器日志
docker-compose logs ai-wenda

# 检查容器状态
docker-compose ps

# 重新构建镜像
docker-compose build --no-cache
```

#### 2. 端口冲突

```bash
# 检查端口占用
netstat -tulpn | grep :8081

# 修改docker-compose.yml中的端口映射
ports:
  - "8002:8081"  # 改为其他端口
```

#### 3. 数据库连接失败

```bash
# 检查数据目录权限
ls -la data/databases/

# 重新初始化数据库
docker-compose exec ai-wenda python -c "from app.models.database import init_db; init_db()"
```

#### 4. 内存不足

```bash
# 查看容器资源使用
docker stats

# 清理未使用的镜像
docker image prune -f
```

### 日志查看

```bash
# 查看所有服务日志
docker-compose logs

# 查看特定服务日志
docker-compose logs ai-wenda
docker-compose logs redis

# 实时查看日志
docker-compose logs -f
```

### 性能调优

#### 1. 应用层调优

```yaml
# docker-compose.yml
services:
  ai-wenda:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
```

#### 2. 数据库调优

```yaml
# config.yaml
database:
  pool_size: 20
  max_overflow: 30
  pool_timeout: 30
  pool_recycle: 3600
```

#### 3. Redis调优

```yaml
# redis.conf (如果需要)
maxmemory 512mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
```

## 🔄 更新升级

### 应用更新

```bash
# 拉取最新代码
git pull origin main

# 重新构建并启动
./deploy.sh --mode prod --build

# 查看更新状态
docker-compose ps
```

### 数据迁移

```bash
# 备份数据
cp -r data/databases data/databases.backup

# 执行迁移
docker-compose exec ai-wenda python -c "from alembic import command; command.upgrade('head')"

# 验证迁移
docker-compose exec ai-wenda python -c "from app.models.database import check_db; check_db()"
```

### 版本回滚

```bash
# 查看历史版本
git tag --list

# 回滚到指定版本
git checkout v2.0.0

# 重新部署
./deploy.sh --mode prod --build
```

## 📞 技术支持

如遇到问题，可通过以下方式获取帮助：

1. **查看文档**: [项目README.md](README.md)
2. **提交Issue**: [GitHub Issues](https://github.com/blankzsh/AI_OCS_Question_bank/issues)
3. **技术支持**: shell7@petalmail.com

---

**🎯 部署成功后，您将拥有一个完整的、生产就绪的AI智能题库查询系统！**