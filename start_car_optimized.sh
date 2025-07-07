#!/bin/bash

# 优化后的小车控制系统启动脚本
echo "正在启动优化后的小车控制系统..."

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "错误: Python3 未安装"
    exit 1
fi

# 设置工作目录
cd /home/lenovo/SWS

# 使用优化后的配置文件
export CONFIG_FILE=config_optimized.ini

# 启动系统
echo "使用优化配置启动系统..."
python3 car_web_control.py

echo "系统已退出"
