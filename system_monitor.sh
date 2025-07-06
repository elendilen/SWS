#!/bin/bash

# 系统稳定性监控脚本
# 用于实时监控系统状态，预防突然断开连接

LOG_FILE="/home/lenovo/SWS/system_monitor.log"
PID_FILE="/home/lenovo/SWS/system_monitor.pid"
CHECK_INTERVAL=30  # 检查间隔（秒）

# 创建日志文件
touch $LOG_FILE

# 日志记录函数
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a $LOG_FILE
}

# 检查是否已有监控进程在运行
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat $PID_FILE)
    if ps -p $OLD_PID > /dev/null 2>&1; then
        log_message "监控进程已在运行 (PID: $OLD_PID)"
        exit 1
    fi
fi

# 记录当前PID
echo $$ > $PID_FILE

# 清理函数
cleanup() {
    log_message "监控进程停止"
    rm -f $PID_FILE
    exit 0
}

# 捕获信号
trap cleanup SIGINT SIGTERM

log_message "=== 系统稳定性监控启动 ==="

# 监控循环
while true; do
    # 检查温度
    if command -v vcgencmd &> /dev/null; then
        TEMP=$(vcgencmd measure_temp | grep -o '[0-9]*\.[0-9]*')
        if (( $(echo "$TEMP > 70" | bc -l) )); then
            log_message "警告: CPU温度过高 ($TEMP°C)"
        fi
    fi
    
    # 检查内存使用率
    MEMORY_USAGE=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
    if (( $(echo "$MEMORY_USAGE > 85" | bc -l) )); then
        log_message "警告: 内存使用率过高 ($MEMORY_USAGE%)"
    fi
    
    # 检查磁盘空间
    DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ "$DISK_USAGE" -gt 90 ]; then
        log_message "警告: 磁盘空间不足 ($DISK_USAGE%)"
    fi
    
    # 检查网络连接
    if ! ping -c 1 8.8.8.8 > /dev/null 2>&1; then
        log_message "警告: 网络连接异常"
    fi
    
    # 检查小车控制程序是否运行
    if ! pgrep -f "car_web_control.py" > /dev/null; then
        log_message "警告: 小车控制程序未运行"
    fi
    
    # 检查系统负载
    LOAD=$(uptime | awk '{print $10}' | sed 's/,//')
    if (( $(echo "$LOAD > 2.0" | bc -l) )); then
        log_message "警告: 系统负载过高 ($LOAD)"
    fi
    
    # 每10分钟记录一次正常状态
    if [ $(($(date +%s) % 600)) -lt $CHECK_INTERVAL ]; then
        log_message "状态正常 - 温度:${TEMP}°C 内存:${MEMORY_USAGE}% 磁盘:${DISK_USAGE}% 负载:${LOAD}"
    fi
    
    sleep $CHECK_INTERVAL
done
