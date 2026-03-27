#!/bin/bash
#
# TalentIntel Quick Start Script
# 快速启动TalentIntel人才检索
#

set -e

TALENT_INTEL_DIR="$HOME/.openclaw/workspace/Project/TalentIntel"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  🎯 TalentIntel - 数字人才研究员快速启动${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# 检查目录
cd "$TALENT_INTEL_DIR" || {
    echo -e "${RED}错误: 找不到TalentIntel目录${NC}"
    exit 1
}

# 显示菜单
echo -e "${GREEN}请选择操作:${NC}"
echo ""
echo "  1) 📋 检索前回顾清单 (首次必读)"
echo "  2) 📚 阅读经验教训记录"
echo "  3) 🔍 运行完整检索流程"
echo "  4) 🏢 北美大厂人才挖掘"
echo "  5) 💻 GitHub开发者挖掘"
echo "  6) 🎓 学术界人才挖掘"
echo "  7) 👁️ 查看今日发现结果"
echo "  8) 📝 创建人工验证任务"
echo "  9) ⚙️  配置环境变量"
echo "  0) ❌ 退出"
echo ""
read -p "请输入选项 (0-9): " choice

case $choice in
    1)
        echo -e "\n${YELLOW}📋 检索前回顾清单${NC}\n"
        cat PRE_SEARCH_CHECKLIST.md | head -100
        echo -e "\n${GREEN}继续阅读完整清单? (y/n)${NC}"
        read -n 1 continue
        if [[ $continue == "y" ]]; then
            less PRE_SEARCH_CHECKLIST.md
        fi
        ;;
    2)
        echo -e "\n${YELLOW}📚 经验教训记录${NC}\n"
        cat LESSONS_LEARNED.md | head -150
        echo -e "\n${GREEN}继续阅读完整文档? (y/n)${NC}"
        read -n 1 continue
        if [[ $continue == "y" ]]; then
            less LESSONS_LEARNED.md
        fi
        ;;
    3)
        echo -e "\n${YELLOW}🔍 运行完整检索流程...${NC}\n"
        python3 coordinator.py
        ;;
    4)
        echo -e "\n${YELLOW}🏢 北美大厂人才挖掘...${NC}\n"
        python3 scripts/bigtech_talent_miner.py
        ;;
    5)
        echo -e "\n${YELLOW}💻 GitHub开发者挖掘...${NC}\n"
        read -p "请输入地点 (默认: California): " location
        location=${location:-California}
        python3 scripts/github_talent_miner.py --location "$location"
        ;;
    6)
        echo -e "\n${YELLOW}🎓 学术界人才挖掘...${NC}\n"
        python3 scripts/academic_talent_miner.py
        ;;
    7)
        TODAY=$(date +%Y-%m-%d)
        REPORT_FILE="data/daily/$TODAY/report.md"
        if [ -f "$REPORT_FILE" ]; then
            echo -e "\n${GREEN}📊 今日发现结果 ($TODAY)${NC}\n"
            cat "$REPORT_FILE"
        else
            echo -e "\n${RED}未找到今日报告。请先运行检索。${NC}"
        fi
        ;;
    8)
        TODAY=$(date +%Y-%m-%d)
        DATA_DIR="data/daily/$TODAY"
        if [ -d "$DATA_DIR" ]; then
            echo -e "\n${YELLOW}📝 待验证候选人:${NC}\n"
            ls -la "$DATA_DIR"/verify_*.json 2>/dev/null || echo "无待验证任务"
            echo ""
            read -p "输入候选人姓名进行验证: " name
            if [ -f "$DATA_DIR/verify_${name// /_}.json" ]; then
                echo -e "\n${GREEN}验证文件内容:${NC}"
                cat "$DATA_DIR/verify_${name// /_}.json"
                echo -e "\n${YELLOW}使用agent-browser打开Google搜索? (y/n)${NC}"
                read -n 1 confirm
                if [[ $confirm == "y" ]]; then
                    search_query="${name// /+}+LinkedIn"
                    echo -e "\n${BLUE}请手动运行: agent-browser open \"https://www.google.com/search?q=$search_query\"${NC}"
                fi
            else
                echo -e "\n${RED}未找到该候选人的验证文件${NC}"
            fi
        else
            echo -e "\n${RED}未找到今日数据目录${NC}"
        fi
        ;;
    9)
        echo -e "\n${YELLOW}⚙️  配置环境变量${NC}\n"
        echo "当前GITHUB_TOKEN: ${GITHUB_TOKEN:-未设置}"
        echo ""
        read -p "输入GitHub Token (直接回车跳过): " token
        if [ -n "$token" ]; then
            echo "export GITHUB_TOKEN=\"$token\"" >> ~/.zshrc
            echo -e "${GREEN}已添加到 ~/.zshrc${NC}"
            echo -e "${YELLOW}请运行: source ~/.zshrc${NC}"
        fi
        ;;
    0)
        echo -e "\n${GREEN}再见!${NC}"
        exit 0
        ;;
    *)
        echo -e "\n${RED}无效选项${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}完成!${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
