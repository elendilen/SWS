#!/bin/bash

# 系统健康检查脚本
# 用于诊断树莓派断开连接的原因

echo "=== 树莓派系统健康检查 ==="
echo "检查时间: $(date)"
echo ""

# 1. 检查系统重启记录
echo "📋 1. 系统重启记录："
last reboot | head -10
echo ""

# 2. 检查系统温度
echo "🌡️  2. 系统温度："
if command -v vcgencmd &> /dev/null; then
    TEMP=$(vcgencmd measure_temp)
    echo "CPU温度: $TEMP"
    
    # 提取温度数值
    TEMP_VALUE=$(echo $TEMP | grep -o '[0-9]*\.[0-9]*')
    if (( $(echo "$TEMP_VALUE > 70" | bc -l) )); then
        echo "⚠️  警告: CPU温度过高 ($TEMP_VALUE°C)"
    else
        echo "✅ CPU温度正常"
    fi
else
    echo "❌ 无法获取CPU温度"
fi
echo ""

# 3. 检查内存使用情况
echo "💾 3. 内存使用情况："
free -h
echo ""

# 4. 检查磁盘空间
echo "💿 4. 磁盘空间："
df -h /
echo ""

# 5. 检查电源状态
echo "🔋 5. 电源状态："
if [ -f /sys/class/hwmon/hwmon0/in0_lcrit_alarm ]; then
    UNDER_VOLTAGE=$(cat /sys/class/hwmon/hwmon0/in0_lcrit_alarm)
    if [ "$UNDER_VOLTAGE" = "1" ]; then
        echo "⚠️  警告: 检测到电压不足"
    else
        echo "✅ 电源电压正常"
    fi
else
    echo "❓ 无法检测电源状态"
fi
echo ""

# 6. 检查系统日志中的关键错误
echo "📊 6. 系统错误检查："
echo "最近的关键错误信息："
sudo journalctl --since "1 hour ago" --priority=err --no-pager | tail -10
echo ""

# 7. 检查内存不足导致的进程终止
echo "🔍 7. OOM (内存不足) 检查："
sudo dmesg | grep -i "killed process\|out of memory\|oom" | tail -5
if [ $? -eq 0 ]; then
    echo "⚠️  发现内存不足导致的进程终止"
else
    echo "✅ 未发现内存不足问题"
fi
echo ""

# 8. 检查系统负载
echo "⚖️  8. 系统负载："
uptime
echo ""

# 9. 检查USB和串口设备
echo "🔌 9. USB和串口设备："
lsusb 2>/dev/null || echo "无法获取USB设备信息"
echo ""
echo "串口设备："
ls -l /dev/ttyS* /dev/ttyUSB* /dev/ttyACM* 2>/dev/null || echo "未找到串口设备"
echo ""

# 10. 检查网络连接
echo "🌐 10. 网络连接："
ping -c 3 8.8.8.8 > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ 网络连接正常"
else
    echo "❌ 网络连接异常"
fi
echo ""

# 11. 检查进程状态
echo "🔄 11. 相关进程状态："
ps aux | grep -E "(python|car_web|flask)" | grep -v grep
echo ""

# 12. 检查系统服务状态
echo "⚙️  12. 系统服务状态："
systemctl is-active ssh 2>/dev/null || echo "SSH服务状态未知"
echo ""

# 13. 生成诊断报告
echo "📋 13. 诊断结果总结："
echo "===================="

# 温度检查
if command -v vcgencmd &> /dev/null; then
    TEMP_VALUE=$(vcgencmd measure_temp | grep -o '[0-9]*\.[0-9]*')
    if (( $(echo "$TEMP_VALUE > 70" | bc -l) )); then
        echo "❌ 温度过高可能导致系统自动重启"
    fi
fi

# 内存检查
MEMORY_USAGE=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
if (( $(echo "$MEMORY_USAGE > 90" | bc -l) )); then
    echo "❌ 内存使用率过高 ($MEMORY_USAGE%)"
fi

# 磁盘空间检查
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 90 ]; then
    echo "❌ 磁盘空间不足 ($DISK_USAGE%)"
fi

# 检查最近重启
RECENT_REBOOT=$(last reboot | head -1 | awk '{print $5, $6, $7, $8}')
echo "最近重启时间: $RECENT_REBOOT"

echo ""
echo "💡 建议："
echo "1. 如果温度过高，请检查散热和风扇"
echo "2. 如果内存不足，考虑增加交换空间"
echo "3. 如果磁盘空间不足，清理无用文件"
echo "4. 如果频繁重启，检查电源供应"
echo "5. 定期检查系统日志: sudo journalctl -f"
echo ""
echo "=== 检查完成 ==="