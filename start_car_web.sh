#!/bin/bash

# 小车网页控制系统启动脚本 - 增强版
# 包含稳定性检查和自动重启功能

echo "=== 小车网页控制系统 - 增强版 ==="
echo "正在检查系统环境..."

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: Python3 未安装"
    exit 1
fi

# 设置日志文件
LOG_FILE="car_web_control.log"
PID_FILE="car_web_control.pid"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 激活虚拟环境（如果存在）
if [ -d "../project/keyenv" ]; then
    echo "🔄 激活虚拟环境..."
    source ../project/keyenv/bin/activate
fi

# 检查依赖
echo "🔍 检查依赖..."
python3 -c "import serial, cv2, flask, threading, logging" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ 依赖检查失败，正在尝试安装..."
    pip3 install pyserial opencv-python flask
fi

# 检查硬件
echo "🔍 检查硬件..."
if [ ! -c "/dev/ttyS0" ]; then
    echo "⚠️  警告: 串口设备 /dev/ttyS0 不存在，串口功能将不可用"
fi

# 检查摄像头
if python3 -c "import picamera2" 2>/dev/null; then
    echo "✅ Picamera2 已安装，将使用真实摄像头"
    USE_REAL_CAMERA=true
else
    echo "⚠️  警告: Picamera2 未安装，摄像头功能将不可用"
    USE_REAL_CAMERA=false
fi

# 停止现有进程
stop_existing_process() {
    if [ -f "$PID_FILE" ]; then
        OLD_PID=$(cat "$PID_FILE")
        if ps -p "$OLD_PID" > /dev/null 2>&1; then
            echo "🛑 停止现有进程 (PID: $OLD_PID)..."
            kill "$OLD_PID"
            sleep 2
            if ps -p "$OLD_PID" > /dev/null 2>&1; then
                echo "🔨 强制停止进程..."
                kill -9 "$OLD_PID"
            fi
        fi
        rm -f "$PID_FILE"
    fi
    
    # 停止系统监控进程
    if [ -f "system_monitor.pid" ]; then
        MONITOR_PID=$(cat "system_monitor.pid")
        if ps -p "$MONITOR_PID" > /dev/null 2>&1; then
            echo "🛑 停止系统监控进程 (PID: $MONITOR_PID)..."
            kill "$MONITOR_PID"
        fi
    fi
}

# 启动程序
start_program() {
    echo "🚀 启动小车控制系统..."
    echo "📊 日志文件: $LOG_FILE"
    echo "🌐 Web界面: http://localhost:5800"
    echo "按 Ctrl+C 停止程序"
    echo ""
    
    # 启动系统监控
    echo "📡 启动系统监控..."
    "$SCRIPT_DIR/system_monitor.sh" &
    MONITOR_PID=$!
    echo "✅ 系统监控已启动 (PID: $MONITOR_PID)"
    
    # 启动主程序
    python3 "$SCRIPT_DIR/car_web_control.py" &
    MAIN_PID=$!
    echo $MAIN_PID > "$PID_FILE"
    
    # 等待主程序启动
    sleep 3
    
    # 检查进程是否正常运行
    if ps -p "$MAIN_PID" > /dev/null 2>&1; then
        echo "✅ 系统启动成功! (PID: $MAIN_PID)"
        
        # 监控进程状态
        monitor_process "$MAIN_PID"
    else
        echo "❌ 系统启动失败"
        rm -f "$PID_FILE"
        # 停止监控进程
        kill $MONITOR_PID 2>/dev/null
        exit 1
    fi
}

# 监控进程
monitor_process() {
    local pid=$1
    local restart_count=0
    local max_restarts=3
    
    while true; do
        if ps -p "$pid" > /dev/null 2>&1; then
            sleep 5
        else
            echo "⚠️  进程已停止，检查是否需要重启..."
            
            if [ $restart_count -lt $max_restarts ]; then
                restart_count=$((restart_count + 1))
                echo "🔄 第 $restart_count 次重启尝试..."
                
                # 重启程序
                python3 "$SCRIPT_DIR/car_web_control.py" &
                pid=$!
                echo $pid > "$PID_FILE"
                
                sleep 3
                
                if ps -p "$pid" > /dev/null 2>&1; then
                    echo "✅ 重启成功! (PID: $pid)"
                else
                    echo "❌ 重启失败"
                fi
            else
                echo "❌ 达到最大重启次数，停止监控"
                rm -f "$PID_FILE"
                exit 1
            fi
        fi
    done
}

# 清理函数
cleanup() {
    echo ""
    echo "🛑 正在停止系统..."
    stop_existing_process
    echo "✅ 系统已停止"
    exit 0
}

# 捕获中断信号
trap cleanup SIGINT SIGTERM

# 主菜单
show_menu() {
    echo ""
    echo "=== 启动选项 ==="
    echo "1. 启动系统 (自动重启)"
    echo "2. 启动系统 (单次运行)"
    echo "3. 查看应用日志"
    echo "4. 查看系统监控日志"
    echo "5. 停止系统"
    echo "6. 系统状态"
    echo "7. 运行系统健康检查"
    echo "8. 退出"
    echo ""
}

# 主循环
while true; do
    show_menu
    read -p "请选择操作 (1-8): " choice
    
    case $choice in
        1)
            stop_existing_process
            start_program
            ;;
        2)
            stop_existing_process
            echo "🚀 启动小车控制系统 (单次运行)..."
            python3 "$SCRIPT_DIR/car_web_control.py"
            ;;
        3)
            if [ -f "$LOG_FILE" ]; then
                echo "📋 最近的应用日志:"
                tail -n 20 "$LOG_FILE"
            else
                echo "📋 应用日志文件不存在"
            fi
            ;;
        4)
            if [ -f "system_monitor.log" ]; then
                echo "📋 最近的系统监控日志:"
                tail -n 20 "system_monitor.log"
            else
                echo "📋 系统监控日志文件不存在"
            fi
            ;;
        5)
            stop_existing_process
            echo "✅ 系统已停止"
            ;;
        6)
            if [ -f "$PID_FILE" ]; then
                PID=$(cat "$PID_FILE")
                if ps -p "$PID" > /dev/null 2>&1; then
                    echo "✅ 系统正在运行 (PID: $PID)"
                    echo "🌐 Web界面: http://localhost:5800"
                else
                    echo "❌ 系统未运行"
                    rm -f "$PID_FILE"
                fi
            else
                echo "❌ 系统未运行"
            fi
            ;;
        7)
            echo "🔍 运行系统健康检查..."
            "$SCRIPT_DIR/system_health_check.sh"
            ;;
        8)
            stop_existing_process
            echo "👋 再见!"
            exit 0
            ;;
        *)
            echo "❌ 无效选择"
            ;;
    esac
    
    echo ""
    read -p "按 Enter 继续..." -r
done
