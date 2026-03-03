#!/bin/bash
# 快速开始脚本

set -e

echo "🦞 TalentIntel - Digital Researcher Setup"
echo "=========================================="
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 请先安装 Python 3.9+"
    exit 1
fi

echo "✅ Python 已安装: $(python3 --version)"

# 创建虚拟环境
echo ""
echo "📦 创建虚拟环境..."
python3 -m venv venv
source venv/bin/activate

# 安装依赖
echo ""
echo "📦 安装依赖..."
pip install -q -r requirements.txt

# 安装 Playwright 浏览器
echo ""
echo "🌐 安装 Playwright Chromium..."
playwright install chromium

# 创建配置文件
echo ""
echo "⚙️  配置研究员..."
if [ ! -f config/researcher.yaml ]; then
    cp config/researcher.example.yaml config/researcher.yaml
    echo "✅ 已创建 config/researcher.yaml"
    echo "   请编辑该文件填入你的信息"
else
    echo "✅ 配置文件已存在"
fi

echo ""
echo "=========================================="
echo "🎉 设置完成！"
echo ""
echo "下一步:"
echo "1. 编辑 config/researcher.yaml 配置研究员"
echo "2. 设置密码: export LINKEDIN_PASSWORD='你的密码'"
echo "3. 运行测试: python -m src.main"
echo ""
echo "首次运行建议:"
echo "- 使用 headless=False 以便观察行为"
echo "- 准备好处理可能的验证挑战"
echo "=========================================="
