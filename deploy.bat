@echo off
REM AI智能题库查询系统 Docker一键部署脚本 (Windows版本)
REM 作者: Toni Wang (shell7@petalmail.com)

setlocal enabledelayedexpansion

REM 设置默认参数
set DEPLOY_MODE=dev
set FORCE_BUILD=false
set DETACH=false
set ACTION=start

REM 解析命令行参数
:parse_args
if "%~1"=="" goto :start_deploy
if "%~1"=="-h" goto :show_help
if "%~1"=="--help" goto :show_help
if "%~1"=="-m" (
    set DEPLOY_MODE=%~2
    shift
    shift
    goto :parse_args
)
if "%~1"=="--mode" (
    set DEPLOY_MODE=%~2
    shift
    shift
    goto :parse_args
)
if "%~1"=="-b" (
    set FORCE_BUILD=true
    shift
    goto :parse_args
)
if "%~1"=="--build" (
    set FORCE_BUILD=true
    shift
    goto :parse_args
)
if "%~1"=="-d" (
    set DETACH=true
    shift
    goto :parse_args
)
if "%~1"=="--detach" (
    set DETACH=true
    shift
    goto :parse_args
)
if "%~1"=="-s" (
    set ACTION=stop
    shift
    goto :parse_args
)
if "%~1"=="--stop" (
    set ACTION=stop
    shift
    goto :parse_args
)
if "%~1"=="-r" (
    set ACTION=restart
    shift
    goto :parse_args
)
if "%~1"=="--restart" (
    set ACTION=restart
    shift
    goto :parse_args
)
if "%~1"=="-l" (
    set ACTION=logs
    shift
    goto :parse_args
)
if "%~1"=="--logs" (
    set ACTION=logs
    shift
    goto :parse_args
)
if "%~1"=="-c" (
    set ACTION=clean
    shift
    goto :parse_args
)
if "%~1"=="--clean" (
    set ACTION=clean
    shift
    goto :parse_args
)
if "%~1"=="--monitoring" (
    set DEPLOY_MODE=full
    shift
    goto :parse_args
)
if "%~1"=="--nginx" (
    if "%DEPLOY_MODE%"=="dev" set DEPLOY_MODE=prod
    shift
    goto :parse_args
)
echo [ERROR] 未知选项: %~1
goto :show_help

:show_help
echo AI智能题库查询系统 Docker部署脚本
echo.
echo 用法: %~nx0 [选项]
echo.
echo 选项:
echo   -h, --help              显示此帮助信息
echo   -m, --mode MODE         部署模式: dev^|prod^|full (默认: dev)
echo   -b, --build             强制重新构建镜像
echo   -d, --detach            后台运行
echo   -s, --stop              停止服务
echo   -r, --restart           重启服务
echo   -l, --logs              查看日志
echo   -c, --clean             清理容器和镜像
echo   --monitoring            启用监控服务
echo   --nginx                 启用Nginx代理
echo.
echo 示例:
echo   %~nx0 --mode prod --build
echo   %~nx0 --stop
echo   %~nx0 --logs
echo   %~nx0 --clean
goto :eof

:start_deploy
REM 显示横幅
echo ================================================
echo   AI智能题库查询系统 Docker部署脚本
echo   版本: v2.0.0
echo   作者: Toni Wang (shell7@petalmail.com)
echo ================================================
echo.

REM 检查Docker
echo [INFO] 检查Docker...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker未安装，请先安装Docker Desktop
    pause
    exit /b 1
)

REM 检查Docker Compose
echo [INFO] 检查Docker Compose...
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker Compose未安装，请先安装Docker Compose
    pause
    exit /b 1
)

REM 检查Docker运行状态
echo [INFO] 检查Docker服务状态...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker服务未运行，请启动Docker Desktop
    pause
    exit /b 1
)

echo [SUCCESS] 系统要求检查通过

REM 初始化配置
echo [INFO] 初始化配置...

REM 创建必要的目录
if not exist "data" mkdir data
if not exist "data\databases" mkdir data\databases
if not exist "logs" mkdir logs

REM 检查配置文件
if not exist "config.yaml" (
    echo [WARNING] config.yaml不存在，请配置AI平台API密钥
)

REM 复制环境配置文件
if not exist ".env" (
    if exist "docker.env" (
        copy docker.env .env >nul
        echo [INFO] 已复制docker.env到.env
    ) else (
        echo [WARNING] .env文件不存在，请创建环境配置文件
    )
)

echo [SUCCESS] 配置初始化完成

REM 执行相应的操作
if "%ACTION%"=="start" (
    goto :start_services
) else if "%ACTION%"=="stop" (
    goto :stop_services
) else if "%ACTION%"=="restart" (
    goto :restart_services
) else if "%ACTION%"=="logs" (
    goto :show_logs
) else if "%ACTION%"=="clean" (
    goto :cleanup
) else (
    echo [ERROR] 未知操作: %ACTION%
    pause
    exit /b 1
)

:start_services
echo [INFO] 构建Docker镜像...
if "%FORCE_BUILD%"=="true" (
    docker-compose build --no-cache
) else (
    docker-compose build
)
echo [SUCCESS] 镜像构建完成

echo [INFO] 启动服务...
if "%DETACH%"=="true" (
    if "%DEPLOY_MODE%"=="dev" (
        docker-compose up -d
    ) else if "%DEPLOY_MODE%"=="prod" (
        docker-compose --profile production up -d
    ) else if "%DEPLOY_MODE%"=="full" (
        docker-compose --profile production --profile monitoring up -d
    )
    echo [SUCCESS] 服务已在后台启动
    echo [INFO] 使用 '%~nx0 --logs' 查看日志
) else (
    if "%DEPLOY_MODE%"=="dev" (
        docker-compose up
    ) else if "%DEPLOY_MODE%"=="prod" (
        docker-compose --profile production up
    ) else if "%DEPLOY_MODE%"=="full" (
        docker-compose --profile production --profile monitoring up
    )
)
goto :show_status

:stop_services
echo [INFO] 停止服务...
docker-compose down
echo [SUCCESS] 服务已停止
goto :eof

:restart_services
echo [INFO] 重启服务...
docker-compose down
timeout /t 2 /nobreak >nul
goto :start_services

:show_logs
echo [INFO] 查看服务日志...
docker-compose logs -f
goto :eof

:cleanup
echo [INFO] 清理容器和镜像...
docker-compose down -v --remove-orphans
if "%FORCE_BUILD%"=="true" (
    docker image prune -f
)
echo [SUCCESS] 清理完成
goto :eof

:show_status
echo.
echo [INFO] 服务状态:
docker-compose ps

echo.
echo [INFO] 服务访问地址:
echo   - API服务: http://localhost:8000
echo   - API文档: http://localhost:8000/docs

if "%DEPLOY_MODE%"=="prod" echo   - Nginx代理: http://localhost
if "%DEPLOY_MODE%"=="full" echo   - Prometheus监控: http://localhost:9090

echo.
pause