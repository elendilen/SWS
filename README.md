# 小车控制系统 - 简化版本

一个简单的网页版小车控制系统，包含实时视频流和基本控制功能。

## 功能特性

- 🚗 **基本控制**: 前进、后退、左转、右转、停止
- 📹 **实时视频**: 基于PiCamera2的实时视频流
- 🌐 **网页控制**: 响应式Web界面，支持手机和电脑
- 📡 **串口通信**: 与Arduino/ESP32控制板通信
- 📊 **状态监控**: 实时显示系统状态

## 硬件要求

- 树莓派 (推荐4B或更新版本)
- 摄像头模块 (PiCamera或USB摄像头)
- 串口连接到控制板 (Arduino/ESP32)
- 小车硬件平台

## 快速开始

### 1. 启动系统
```bash
./start_simple.sh
```

### 2. 访问控制界面
打开浏览器访问: `http://树莓派IP:5800`

### 3. 控制说明
- 点击或按住方向按钮控制小车
- 释放按钮时小车自动停止
- 支持触摸屏操作

## 配置说明

编辑 `config_simple.ini` 文件来修改配置:

```ini
[serial]
port = /dev/ttyS0    # 串口设备
baudrate = 9600      # 波特率

[camera]
width = 640          # 视频宽度
height = 480         # 视频高度
fps = 15            # 帧率

[network]
host = 0.0.0.0      # 绑定地址
port = 5800         # 端口号
```

## 命令协议

系统通过串口发送单字符命令:

| 命令 | 功能 |
|------|------|
| F    | 前进 |
| B    | 后退 |
| L    | 左转 |
| R    | 右转 |
| S    | 停止 |

## Arduino代码示例

```cpp
void loop() {
  if (Serial.available() > 0) {
    char command = Serial.read();
    processCommand(command);
  }
}

void processCommand(char cmd) {
  switch(cmd) {
    case 'F': // 前进
      // 控制电机前进
      break;
    case 'B': // 后退
      // 控制电机后退
      break;
    case 'L': // 左转
      // 控制电机左转
      break;
    case 'R': // 右转
      // 控制电机右转
      break;
    case 'S': // 停止
      // 停止所有电机
      break;
  }
}
```

## 文件结构

```
SWS/
├── car_web_control_simple.py  # 主程序
├── serial_handler.py          # 串口处理
├── config_manager.py          # 配置管理
├── config_simple.ini          # 配置文件
├── start_simple.sh           # 启动脚本
├── templates/
│   └── car_control_simple.html # Web界面
└── README.md                 # 说明文档
```

## 故障排除

1. **串口连接失败**
   - 检查串口设备路径
   - 确认波特率设置正确
   - 检查串口权限

2. **摄像头无法启动**
   - 确认摄像头模块连接正常
   - 检查摄像头是否被其他程序占用

3. **网页无法访问**
   - 检查防火墙设置
   - 确认端口号未被占用

## 许可证

MIT License