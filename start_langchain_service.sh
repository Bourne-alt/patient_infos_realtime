#!/bin/bash
# 医疗报告分析API - LangChain集成版本启动脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_status() {
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

# 检查Python版本
check_python() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed."
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    print_status "Python version: $PYTHON_VERSION"
}

# 检查PostgreSQL连接
check_postgres() {
    print_status "Checking PostgreSQL connection..."
    
    # 从环境变量获取配置，或使用默认值
    POSTGRES_HOST=${POSTGRES_HOST:-"10.1.27.65"}
    POSTGRES_PORT=${POSTGRES_PORT:-"5432"}
    POSTGRES_USER=${POSTGRES_USER:-"postgres"}
    POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-"admin123"}
    POSTGRES_DATABASE=${POSTGRES_DATABASE:-"medical_reports"}
    
    # 尝试连接PostgreSQL
    if command -v psql &> /dev/null; then
        if PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER -d $POSTGRES_DATABASE -c "SELECT 1;" &> /dev/null; then
            print_success "PostgreSQL connection successful"
        else
            print_error "Cannot connect to PostgreSQL"
            print_warning "Please check your database configuration"
        fi
    else
        print_warning "psql not found, skipping database connection test"
    fi
}

# 安装依赖
install_dependencies() {
    print_status "Installing Python dependencies..."
    
    if [ -f "requirements.txt" ]; then
        pip3 install -r requirements.txt
        print_success "Dependencies installed successfully"
    else
        print_error "requirements.txt not found"
        exit 1
    fi
}

# 检查LangChain配置
check_langchain_config() {
    print_status "Checking LangChain configuration..."
    
    if [ -n "$OPENAI_API_KEY" ]; then
        print_success "OpenAI API key configured"
    else
        print_warning "OpenAI API key not configured, will use local model"
    fi
    
    # 检查本地模型服务
    if curl -s http://localhost:11434/api/tags &> /dev/null; then
        print_success "Local Ollama service is running"
    else
        print_warning "Local Ollama service is not running"
        print_warning "You may need to start Ollama service or configure OpenAI API"
    fi
}

# 显示配置信息
show_config() {
    print_status "Current configuration:"
    echo "  - Database Host: ${POSTGRES_HOST:-10.1.27.65}"
    echo "  - Database Port: ${POSTGRES_PORT:-5432}"
    echo "  - Database Name: ${POSTGRES_DATABASE:-medical_reports}"
    echo "  - OpenAI API Key: ${OPENAI_API_KEY:+Configured}"
    echo "  - OpenAI Model: ${OPENAI_MODEL:-gpt-3.5-turbo}"
    echo "  - Local Model: ${LLM_MODEL:-llama3.1}"
}

# 启动服务
start_service() {
    print_status "Starting Medical Report Analysis API with LangChain integration..."
    
    # 设置环境变量
    export PYTHONPATH="${PYTHONPATH}:."
    
    # 启动服务
    if [ "$1" = "dev" ]; then
        print_status "Starting in development mode..."
        python3 -m uvicorn api:app --host 0.0.0.0 --port 7700 --reload
    else
        print_status "Starting in production mode..."
        python3 -m uvicorn api:app --host 0.0.0.0 --port 7700 --workers 5
    fi
}

# 运行测试
run_tests() {
    print_status "Running integration tests..."
    
    # 等待服务启动
    sleep 5
    
    if [ -f "test_langchain_integration.py" ]; then
        python3 test_langchain_integration.py
    else
        print_warning "Test file not found, skipping tests"
    fi
}

# 显示帮助信息
show_help() {
    echo "医疗报告分析API - LangChain集成版本启动脚本"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  start          Start the service (default)"
    echo "  dev            Start in development mode with auto-reload"
    echo "  test           Run integration tests"
    echo "  check          Check system dependencies and configuration"
    echo "  install        Install Python dependencies"
    echo "  help           Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  POSTGRES_HOST        PostgreSQL host (default: 10.1.27.65)"
    echo "  POSTGRES_PORT        PostgreSQL port (default: 5432)"
    echo "  POSTGRES_USER        PostgreSQL user (default: postgres)"
    echo "  POSTGRES_PASSWORD    PostgreSQL password (default: admin123)"
    echo "  POSTGRES_DATABASE    PostgreSQL database (default: medical_reports)"
    echo "  OPENAI_API_KEY      OpenAI API key (optional)"
    echo "  OPENAI_MODEL        OpenAI model (default: gpt-3.5-turbo)"
    echo "  LLM_MODEL           Local model name (default: llama3.1)"
    echo ""
    echo "Examples:"
    echo "  $0 start                 # Start in production mode"
    echo "  $0 dev                   # Start in development mode"
    echo "  $0 check                 # Check system configuration"
    echo "  OPENAI_API_KEY=xxx $0 start  # Start with OpenAI API"
}

# 主函数
main() {
    echo "================================"
    echo "医疗报告分析API - LangChain集成版"
    echo "================================"
    echo ""
    
    case "${1:-start}" in
        "start")
            check_python
            check_postgres
            check_langchain_config
            show_config
            start_service
            ;;
        "dev")
            check_python
            check_postgres
            check_langchain_config
            show_config
            start_service dev
            ;;
        "test")
            check_python
            run_tests
            ;;
        "check")
            check_python
            check_postgres
            check_langchain_config
            show_config
            ;;
        "install")
            check_python
            install_dependencies
            ;;
        "help")
            show_help
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@" 