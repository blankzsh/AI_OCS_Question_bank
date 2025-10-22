#!/bin/bash

# AI智能题库查询系统 Docker一键部署脚本
# 作者: Toni Wang (shell7@petalmail.com)

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 显示帮助信息
show_help() {
    echo "AI智能题库查询系统 Docker部署脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help              显示此帮助信息"
    echo "  -m, --mode MODE         部署模式: dev|prod|full (默认: dev)"
    echo "  -b, --build             强制重新构建镜像"
    echo "  -d, --detach            后台运行"
    echo "  -s, --stop              停止服务"
    echo "  -r, --restart           重启服务"
    echo "  -l, --logs              查看日志"
    echo "  -c, --clean             清理容器和镜像"
    echo "  --monitoring            启用监控服务"
    echo "  --nginx                 启用Nginx代理"
    echo ""
    echo "示例:"
    echo "  $0 --mode prod --build"
    echo "  $0 --stop"
    echo "  $0 --logs"
    echo "  $0 --clean"
}

# 检查系统要求
check_requirements() {
    print_info "检查系统要求..."

    # 检查Docker
    if ! command_exists docker; then
        print_error "Docker未安装，请先安装Docker"
        exit 1
    fi

    # 检查Docker Compose
    if ! command_exists docker-compose; then
        print_error "Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi

    # 检查Docker运行状态
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker服务未运行，请启动Docker服务"
        exit 1
    fi

    print_success "系统要求检查通过"
}

# 初始化配置
init_config() {
    print_info "初始化配置..."

    # 创建必要的目录
    mkdir -p data/databases
    mkdir -p logs

    # 检查配置文件
    if [ ! -f config.yaml ]; then
        print_warning "config.yaml不存在，请配置AI平台API密钥"
    fi

    # 复制环境配置文件
    if [ ! -f .env ]; then
        if [ -f docker.env ]; then
            cp docker.env .env
            print_info "已复制docker.env到.env"
        else
            print_warning ".env文件不存在，请创建环境配置文件"
        fi
    fi

    print_success "配置初始化完成"
}

# 构建镜像
build_images() {
    print_info "构建Docker镜像..."

    if [ "$FORCE_BUILD" = true ]; then
        docker-compose build --no-cache
    else
        docker-compose build
    fi

    print_success "镜像构建完成"
}

# 启动服务
start_services() {
    print_info "启动服务..."

    local compose_args=""
    if [ "$DETACH" = true ]; then
        compose_args="-d"
    fi

    # 根据模式启动不同的服务
    case "$DEPLOY_MODE" in
        "dev")
            print_info "启动开发环境..."
            docker-compose up $compose_args
            ;;
        "prod")
            print_info "启动生产环境..."
            docker-compose --profile production up $compose_args
            ;;
        "full")
            print_info "启动完整环境 (包含监控和Nginx)..."
            docker-compose --profile production --profile monitoring up $compose_args
            ;;
        *)
            print_error "未知的部署模式: $DEPLOY_MODE"
            exit 1
            ;;
    esac

    if [ "$DETACH" = true ]; then
        print_success "服务已在后台启动"
        print_info "使用 '$0 --logs' 查看日志"
    fi
}

# 停止服务
stop_services() {
    print_info "停止服务..."
    docker-compose down
    print_success "服务已停止"
}

# 重启服务
restart_services() {
    print_info "重启服务..."
    stop_services
    sleep 2
    start_services
}

# 查看日志
show_logs() {
    print_info "查看服务日志..."
    docker-compose logs -f
}

# 清理
cleanup() {
    print_info "清理容器和镜像..."

    # 停止并删除容器
    docker-compose down -v --remove-orphans

    # 删除镜像
    if [ "$FORCE_BUILD" = true ]; then
        docker image prune -f
        print_info "清理完成"
    fi

    print_success "清理完成"
}

# 显示状态
show_status() {
    print_info "服务状态:"
    docker-compose ps

    print_info "服务访问地址:"
    echo "  - API服务: http://localhost:8081"
    echo "  - API文档: http://localhost:8081/docs"

    if [[ "$DEPLOY_MODE" == "prod" || "$DEPLOY_MODE" == "full" ]]; then
        echo "  - Nginx代理: http://localhost"
    fi

    if [[ "$DEPLOY_MODE" == "full" ]]; then
        echo "  - Prometheus监控: http://localhost:9090"
    fi
}

# 主函数
main() {
    # 默认参数
    DEPLOY_MODE="dev"
    FORCE_BUILD=false
    DETACH=false
    ACTION="start"

    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -m|--mode)
                DEPLOY_MODE="$2"
                shift 2
                ;;
            -b|--build)
                FORCE_BUILD=true
                shift
                ;;
            -d|--detach)
                DETACH=true
                shift
                ;;
            -s|--stop)
                ACTION="stop"
                shift
                ;;
            -r|--restart)
                ACTION="restart"
                shift
                ;;
            -l|--logs)
                ACTION="logs"
                shift
                ;;
            -c|--clean)
                ACTION="clean"
                shift
                ;;
            --monitoring)
                DEPLOY_MODE="full"
                shift
                ;;
            --nginx)
                if [ "$DEPLOY_MODE" = "dev" ]; then
                    DEPLOY_MODE="prod"
                fi
                shift
                ;;
            *)
                print_error "未知选项: $1"
                show_help
                exit 1
                ;;
        esac
    done

    # 显示横幅
    echo "================================================"
    echo "  AI智能题库查询系统 Docker部署脚本"
    echo "  版本: v2.0.0"
    echo "  作者: Toni Wang (shell7@petalmail.com)"
    echo "================================================"
    echo ""

    # 执行相应的操作
    case $ACTION in
        "start")
            check_requirements
            init_config
            build_images
            start_services
            show_status
            ;;
        "stop")
            stop_services
            ;;
        "restart")
            restart_services
            show_status
            ;;
        "logs")
            show_logs
            ;;
        "clean")
            cleanup
            ;;
        *)
            print_error "未知操作: $ACTION"
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"