#!/bin/bash
# LowEndTalk 监控启动脚本（使用 Xvfb）
# 适用于无 GUI 的 Debian/Ubuntu 服务器

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}LowEndTalk 监控启动脚本${NC}"
echo -e "${GREEN}================================${NC}\n"

# 检查是否安装了 Xvfb
if ! command -v Xvfb &> /dev/null; then
    echo -e "${YELLOW}警告: 未检测到 Xvfb${NC}"
    echo "安装命令: sudo apt install xvfb -y"
    echo ""
    read -p "是否继续无 Xvfb 运行？(y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
    USE_XVFB=false
else
    echo -e "${GREEN}✓ 检测到 Xvfb${NC}"
    USE_XVFB=true
fi

# 检查 Python 环境
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}错误: 未找到 Python3${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python3 已安装${NC}"

# 检查依赖
echo "检查 Python 依赖..."
python3 -c "import undetected_chromedriver" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}警告: 未安装 undetected-chromedriver${NC}"
    echo "安装命令: pip3 install -r requirements.txt"
    exit 1
fi

echo -e "${GREEN}✓ Python 依赖已安装${NC}\n"

# 设置显示编号
DISPLAY_NUM=99

# 如果使用 Xvfb，启动虚拟显示
if [ "$USE_XVFB" = true ]; then
    echo "启动 Xvfb 虚拟显示..."
    
    # 检查是否已经运行
    if pgrep -f "Xvfb :$DISPLAY_NUM" > /dev/null; then
        echo -e "${YELLOW}Xvfb 已在运行，停止旧进程...${NC}"
        pkill -f "Xvfb :$DISPLAY_NUM"
        sleep 1
    fi
    
    # 启动 Xvfb
    Xvfb :$DISPLAY_NUM -screen 0 1920x1080x24 > /dev/null 2>&1 &
    XVFB_PID=$!
    
    # 设置 DISPLAY 环境变量
    export DISPLAY=:$DISPLAY_NUM
    
    # 等待 Xvfb 启动
    sleep 2
    
    # 验证 Xvfb 是否运行
    if ps -p $XVFB_PID > /dev/null; then
        echo -e "${GREEN}✓ Xvfb 已启动 (PID: $XVFB_PID, DISPLAY: :$DISPLAY_NUM)${NC}\n"
    else
        echo -e "${YELLOW}警告: Xvfb 启动可能失败${NC}\n"
    fi
fi

# 获取起始页面参数
START_PAGE="${1:-245}"

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}启动监控程序${NC}"
echo -e "${GREEN}================================${NC}"
echo "起始页面: $START_PAGE"
echo "显示设置: $DISPLAY"
echo ""

# 清理函数
cleanup() {
    echo -e "\n${YELLOW}收到停止信号，清理资源...${NC}"
    
    if [ "$USE_XVFB" = true ] && [ ! -z "$XVFB_PID" ]; then
        echo "停止 Xvfb..."
        kill $XVFB_PID 2>/dev/null
    fi
    
    echo -e "${GREEN}清理完成${NC}"
    exit 0
}

# 捕获退出信号
trap cleanup SIGINT SIGTERM

# 启动监控程序
python3 monitor.py --start-page $START_PAGE

# 程序结束后清理
cleanup
