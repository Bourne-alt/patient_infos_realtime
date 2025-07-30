#!/bin/bash

# LangChain 工作流演示启动脚本

echo "🚀 LangChain 链式工作流演示启动器"
echo "=================================="

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: Python3 未安装"
    exit 1
fi

echo "✅ Python3 已安装"

# 检查pip是否安装
if ! command -v pip3 &> /dev/null; then
    echo "❌ 错误: pip3 未安装"
    exit 1
fi

echo "✅ pip3 已安装"

# 检查是否存在requirements文件
if [ ! -f "requirements_langchain.txt" ]; then
    echo "❌ 错误: requirements_langchain.txt 文件不存在"
    exit 1
fi

echo "✅ requirements_langchain.txt 文件存在"

# 检查是否存在主程序文件
if [ ! -f "langchain_workflow_examples.py" ]; then
    echo "❌ 错误: langchain_workflow_examples.py 文件不存在"
    exit 1
fi

echo "✅ langchain_workflow_examples.py 文件存在"

# 询问用户是否要安装依赖
echo ""
read -p "📦 是否需要安装依赖包？(y/n): " install_deps

if [ "$install_deps" = "y" ] || [ "$install_deps" = "Y" ]; then
    echo "📦 正在安装依赖包..."
    pip3 install -r requirements_langchain.txt
    
    if [ $? -eq 0 ]; then
        echo "✅ 依赖包安装成功"
    else
        echo "❌ 依赖包安装失败"
        exit 1
    fi
fi

# 检查环境变量设置
echo ""
echo "🔧 检查环境变量设置..."

if [ -f ".env" ]; then
    echo "✅ .env 文件存在"
    source .env
elif [ -f "env_example.txt" ]; then
    echo "⚠️ .env 文件不存在，但找到了 env_example.txt"
    echo "💡 请复制 env_example.txt 到 .env 并填入您的配置"
    
    read -p "是否现在创建 .env 文件？(y/n): " create_env
    
    if [ "$create_env" = "y" ] || [ "$create_env" = "Y" ]; then
        cp env_example.txt .env
        echo "✅ .env 文件已创建，请编辑此文件并填入您的配置"
        echo "📝 特别是 OPENAI_API_KEY 配置"
    fi
else
    echo "⚠️ 环境变量配置文件不存在"
fi

# 检查OPENAI_API_KEY是否设置
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️ OPENAI_API_KEY 环境变量未设置"
    echo "💡 请设置此变量或在 .env 文件中配置"
    
    read -p "是否继续运行演示？(可能会失败) (y/n): " continue_demo
    
    if [ "$continue_demo" != "y" ] && [ "$continue_demo" != "Y" ]; then
        echo "❌ 用户取消运行"
        exit 1
    fi
else
    echo "✅ OPENAI_API_KEY 已设置"
fi

# 运行环境检查
echo ""
echo "🔍 运行环境检查..."
python3 test_setup.py

if [ $? -eq 0 ]; then
    echo "✅ 环境检查通过"
else
    echo "⚠️ 环境检查有警告，但仍可以尝试运行"
    
    read -p "是否继续运行演示？(y/n): " continue_with_warnings
    
    if [ "$continue_with_warnings" != "y" ] && [ "$continue_with_warnings" != "Y" ]; then
        echo "❌ 用户取消运行"
        exit 1
    fi
fi

# 运行主程序
echo ""
echo "🎬 启动 LangChain 工作流演示..."
echo "=================================="

python3 langchain_workflow_examples.py

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 演示运行完成！"
else
    echo ""
    echo "❌ 演示运行失败"
    echo "💡 请检查错误信息并解决相关问题"
    exit 1
fi

echo ""
echo "📚 更多信息请查看 README_langchain_workflows.md"
echo "�� 如有问题，请检查日志文件或联系支持" 