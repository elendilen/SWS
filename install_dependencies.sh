#!/bin/bash

# 小车控制系统安装脚本

echo "=== 小车控制系统安装脚本 ==="
echo "正在检查系统环境..."

# 检查操作系统
if [ -f /etc/os-release ]; then
    . /etc/os-release
    echo "操作系统: $NAME $VERSION"
else
    echo "⚠️  无法检测操作系统版本"
fi

# 检查Python版本
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
    echo "Python版本: $PYTHON_VERSION"
else
    echo "❌ Python3 未安装"
    exit 1
fi

# 检查pip
if command -v pip3 &> /dev/null; then
    echo "✅ pip3 已安装"
else
    echo "❌ pip3 未安装"
    exit 1
fi

# 创建虚拟环境
echo "📦 创建虚拟环境..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ 虚拟环境创建成功"
else
    echo "✅ 虚拟环境已存在"
fi

# 激活虚拟环境
echo "🔄 激活虚拟环境..."
source venv/bin/activate

# 更新pip
echo "📦 更新pip..."
pip install --upgrade pip

# 安装依赖
echo "📦 安装Python依赖..."
pip install flask pyserial opencv-python numpy configparser

# 检查树莓派相关包
echo "📦 检查树莓派相关包..."
if python3 -c "import picamera2" 2>/dev/null; then
    echo "✅ picamera2 已安装"
else
    echo "⚠️  picamera2 未安装，如果在树莓派上运行，请手动安装"
    echo "   sudo apt update && sudo apt install -y python3-picamera2"
fi

# 检查摄像头
echo "📦 检查摄像头..."
if [ -e /dev/video0 ]; then
    echo "✅ 摄像头设备已检测到"
else
    echo "⚠️  未检测到摄像头设备"
fi

# 检查串口
echo "📦 检查串口..."
if [ -e /dev/ttyS0 ]; then
    echo "✅ 串口设备已检测到"
else
    echo "⚠️  未检测到串口设备 /dev/ttyS0"
fi

# 设置权限
echo "🔒 设置文件权限..."
chmod +x start_car_web.sh
chmod +x install_dependencies.sh

# 创建日志目录
echo "📁 创建日志目录..."
mkdir -p logs

# 测试配置
echo "🔧 测试配置..."
python3 -c "
import sys
sys.path.append('.')
from config_manager import config_manager
print('配置管理器测试通过')
"

echo ""
echo "🎉 安装完成!"
echo ""
echo "使用说明:"
echo "1. 启动系统: ./start_car_web.sh"
echo "2. 打开浏览器访问: http://localhost:5800"
echo "3. 查看日志: tail -f car_web_control.log"
echo ""
echo "注意事项:"
echo "- 如果在树莓派上运行，请确保已安装 picamera2"
echo "- 串口设备需要正确权限，可能需要 sudo"
echo "- 摄像头需要在树莓派配置中启用"
echo ""
echo "故障排除:"
echo "- 检查配置文件: cat config.ini"
echo "- 查看完整日志: cat car_web_control.log"
echo "- 重启系统: sudo reboot"
