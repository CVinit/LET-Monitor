#!/bin/bash
# Playwright 启动脚本（使用 Xvfb）
# 适用于无 GUI 的 Debian 服务器

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Playwright 监控启动脚本${NC}"
echo -e "${GREEN}================================${NC}\n"

# 检查 Xvfb
if ! command -v Xvfb &> /dev/null; then
    echo -e "${YELLOW}警告: 未检测到 Xvfb${NC}"
    echo "安装命令: sudo apt install xvfb -y"
    exit 1
fi

echo -e "${GREEN}✓ 检测到 Xvfb${NC}"

# 设置显示编号
DISPLAY_NUM=99

# 检查是否已经运行
if pgrep -f "Xvfb :$DISPLAY_NUM" > /dev/null; then
    echo -e "${YELLOW}Xvfb 已在运行，停止旧进程...${NC}"
    pkill -f "Xvfb :$DISPLAY_NUM"
    sleep 1
fi

# 启动 Xvfb
echo "启动 Xvfb 虚拟显示..."
Xvfb :$DISPLAY_NUM -screen 0 1920x1080x24 > /dev/null 2>&1 &
XVFB_PID=$!

# 设置 DISPLAY
export DISPLAY=:$DISPLAY_NUM

# 等待 Xvfb 启动
sleep 2

if ps -p $XVFB_PID > /dev/null; then
    echo -e "${GREEN}✓ Xvfb 已启动 (PID: $XVFB_PID, DISPLAY: :$DISPLAY_NUM)${NC}\n"
else
    echo -e "${YELLOW}警告: Xvfb 启动可能失败${NC}\n"
fi

# 获取起始页面
START_PAGE="${1:-340}"

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}启动 Playwright 监控${NC}"
echo -e "${GREEN}================================${NC}"
echo "起始页面: $START_PAGE"
echo "显示设置: $DISPLAY"
echo ""

# 清理函数
cleanup() {
    echo -e "\n${YELLOW}收到停止信号，清理资源...${NC}"
    
    if [ ! -z "$XVFB_PID" ]; then
        echo "停止 Xvfb..."
        kill $XVFB_PID 2>/dev/null
    fi
    
    echo -e "${GREEN}清理完成${NC}"
    exit 0
}

# 捕获退出信号
trap cleanup SIGINT SIGTERM

# 启动 Playwright 监控
python3 monitor_playwright.py --start-page $START_PAGE

# 程序结束后清理
cleanup
