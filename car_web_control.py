#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小车网页控制程序 - 增强版
结合Flask网页界面和摄像头流媒体
包含稳定性改进和自动重连功能
"""

import cv2
import time
import threading
import logging
from flask import Flask, render_template, Response, request, jsonify
from picamera2 import Picamera2
import numpy as np
import io
import base64
import os
import sys

# 导入自定义模块
from serial_handler import SerialHandler
from config_manager import config_manager

# 配置日志
logger = config_manager.setup_logging()

# 初始化Flask应用
app = Flask(__name__)

# 全局变量
serial_handler = None
picam2 = None
current_cmd = 'S'
camera_active = False
system_status = {
    'serial_connected': False,
    'camera_active': False,
    'last_command_time': 0
}

# 初始化串口处理器
def init_serial():
    global serial_handler, system_status
    try:
        # 从配置文件获取串口参数
        port = config_manager.get('serial', 'port', '/dev/ttyS0')
        baudrate = config_manager.getint('serial', 'baudrate', 9600)
        timeout = config_manager.getint('serial', 'timeout', 1)
        max_retries = config_manager.getint('serial', 'max_retries', 5)
        
        serial_handler = SerialHandler(
            port=port, 
            baudrate=baudrate, 
            timeout=timeout,
            max_retries=max_retries
        )
        
        # 尝试连接
        if serial_handler.connect():
            system_status['serial_connected'] = True
            logger.info(f"串口初始化成功: {port} @ {baudrate}")
            return True
        else:
            logger.error("串口初始化失败")
            return False
    except Exception as e:
        logger.error(f"串口初始化异常: {e}")
        return False

# 初始化摄像头
def init_camera():
    global picam2, camera_active, system_status
    try:
        # 优化的摄像头参数
        width = 640  # 降低分辨率减少延迟
        height = 480
        
        picam2 = Picamera2()
        config = picam2.create_preview_configuration(main={"size": (width, height)})
        picam2.configure(config)
        picam2.start()
        camera_active = True
        system_status['camera_active'] = True
        logger.info(f"摄像头初始化成功: {width}x{height}")
        time.sleep(1)  # 减少等待时间
        return True
    except Exception as e:
        logger.error(f"摄像头初始化失败: {e}")
        camera_active = False
        system_status['camera_active'] = False
        return False

# 发送控制命令 - 优化版本
def send_command(cmd):
    global serial_handler, current_cmd, system_status
    if serial_handler and serial_handler.is_connected:
        try:
            # 立即发送停止命令，其他命令检查重复
            if cmd != 'S' and current_cmd == cmd:
                return True  # 避免重复发送相同命令
            
            if serial_handler.send_command(cmd):
                current_cmd = cmd
                system_status['last_command_time'] = time.time()
                logger.debug(f"已发送命令: {cmd}")  # 改为debug级别减少日志
                return True
            else:
                logger.error("发送命令失败")
                return False
        except Exception as e:
            logger.error(f"发送命令异常: {e}")
            return False
    else:
        logger.warning("串口未连接，无法发送命令")
        return False

# 生成摄像头帧 - 优化版本
def generate_frames():
    global picam2, camera_active
    frame_count = 0
    error_count = 0
    max_errors = 10
    
    # 优化的视频参数
    jpeg_quality = 75  # 降低质量以减少延迟
    fps = 15  # 降低帧率
    frame_interval = 1.0 / fps
    
    logger.info(f"开始生成视频帧，质量: {jpeg_quality}, FPS: {fps}")
    
    while camera_active:
        start_time = time.time()
        try:
            if picam2:
                # 捕获帧
                frame = picam2.capture_array()
                
                # 检查帧是否有效
                if frame is None or frame.size == 0:
                    error_count += 1
                    if error_count < 5:  # 减少错误日志
                        logger.warning(f"捕获到空帧 (错误计数: {error_count})")
                    time.sleep(0.05)
                    continue
                
                # 降低分辨率以减少延迟
                height, width = frame.shape[:2]
                if width > 640:
                    scale = 640 / width
                    new_width = int(width * scale)
                    new_height = int(height * scale)
                    frame = cv2.resize(frame, (new_width, new_height))
                
                # 确保颜色空间转换正确
                if len(frame.shape) == 3:
                    if frame.shape[2] == 3:  # RGB
                        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    else:  # RGBA
                        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
                else:
                    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
                
                # 快速编码参数
                encode_param = [
                    cv2.IMWRITE_JPEG_QUALITY, jpeg_quality,
                    cv2.IMWRITE_JPEG_PROGRESSIVE, 0,
                    cv2.IMWRITE_JPEG_OPTIMIZE, 0  # 禁用优化以提高速度
                ]
                
                ret, buffer = cv2.imencode('.jpg', frame_bgr, encode_param)
                
                if ret and buffer is not None:
                    frame_bytes = buffer.tobytes()
                    
                    if len(frame_bytes) > 0:
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n'
                               b'\r\n' + frame_bytes + b'\r\n')
                        
                        frame_count += 1
                        error_count = 0
                        
                        # 减少日志频率
                        if frame_count % 300 == 0:
                            logger.info(f"已生成 {frame_count} 帧")
                    else:
                        error_count += 1
                else:
                    error_count += 1
                
        except Exception as e:
            error_count += 1
            if error_count < 5:  # 减少错误日志
                logger.error(f"摄像头帧生成错误: {e}")
            
            if error_count >= max_errors:
                logger.warning("摄像头错误过多，尝试重新初始化")
                if reinit_camera():
                    error_count = 0
                    frame_count = 0
                else:
                    logger.error("摄像头重新初始化失败")
                    break
        
        # 动态调整帧间隔
        elapsed = time.time() - start_time
        sleep_time = max(0, frame_interval - elapsed)
        if sleep_time > 0:
            time.sleep(sleep_time)

def reinit_camera():
    """重新初始化摄像头"""
    global picam2, camera_active
    try:
        if picam2:
            picam2.stop()
            picam2.close()
            time.sleep(1)
        
        return init_camera()
    except Exception as e:
        logger.error(f"重新初始化摄像头失败: {e}")
        return False

# 路由定义
@app.route('/')
def index():
    return render_template('car_control.html')

@app.route('/video_feed')
def video_feed():
    """视频流端点 - 提供MJPEG视频流"""
    try:
        # 优化的响应头
        response = Response(
            generate_frames(),
            mimetype='multipart/x-mixed-replace; boundary=frame',
            headers={
                'Cache-Control': 'no-cache, no-store, must-revalidate, max-age=0',
                'Pragma': 'no-cache',
                'Expires': '0',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': '*'
            }
        )
        return response
    except Exception as e:
        logger.error(f"视频流端点错误: {e}")
        return Response(
            "Video stream error",
            status=500,
            mimetype='text/plain'
        )

@app.route('/video_test')
def video_test():
    """测试视频流端点 - 生成简单的测试图像"""
    def generate_test_frames():
        import time
        import numpy as np
        
        frame_count = 0
        while True:
            try:
                # 创建一个简单的测试图像
                img = np.zeros((480, 640, 3), dtype=np.uint8)
                
                # 添加一些内容
                cv2.putText(img, f'Test Frame {frame_count}', (50, 100), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                cv2.putText(img, f'Time: {time.strftime("%H:%M:%S")}', (50, 150), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                # 绘制一个移动的圆
                x = int(320 + 200 * np.sin(frame_count * 0.1))
                y = int(240 + 100 * np.cos(frame_count * 0.1))
                cv2.circle(img, (x, y), 30, (0, 255, 0), -1)
                
                # 编码为JPEG
                ret, buffer = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 85])
                
                if ret:
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n'
                           b'Content-Length: ' + str(len(frame_bytes)).encode() + b'\r\n'
                           b'\r\n' + frame_bytes + b'\r\n')
                
                frame_count += 1
                time.sleep(1/30)  # 30 FPS
                
            except Exception as e:
                logger.error(f"测试视频流错误: {e}")
                break
    
    return Response(
        generate_test_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame',
        headers={
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
        }
    )

@app.route('/control', methods=['POST'])
def control():
    data = request.get_json()
    command = data.get('command', 'S')
    
    # 命令映射
    cmd_map = {
        'forward': 'F',
        'backward': 'B',
        'left': 'L',
        'right': 'R',
        'stop': 'S'
    }
    
    cmd = cmd_map.get(command, 'S')
    
    success = send_command(cmd)
    
    return jsonify({
        'success': success,
        'command': cmd,
        'current_cmd': current_cmd
    })

@app.route('/status')
def status():
    """获取系统状态"""
    global system_status
    
    # 更新运行时间
    system_status['uptime'] = time.time() - start_time
    
    # 获取串口状态
    serial_status = {}
    if serial_handler:
        serial_status = serial_handler.get_status()
    
    return jsonify({
        'current_cmd': current_cmd,
        'system_status': system_status,
        'serial_status': serial_status,
        'timestamp': time.time()
    })

@app.route('/health')
def health():
    """健康检查端点"""
    return jsonify({
        'status': 'ok',
        'timestamp': time.time(),
        'services': {
            'serial': system_status['serial_connected'],
            'camera': system_status['camera_active']
        }
    })

@app.route('/emergency_stop', methods=['POST'])
def emergency_stop():
    """紧急停止 - 立即停止所有动作"""
    success = send_command('S')
    logger.info("紧急停止命令已发送")
    return jsonify({
        'success': success,
        'command': 'S',
        'message': '紧急停止'
    })

# 添加新的路由用于手动重连
@app.route('/reconnect', methods=['POST'])
def reconnect():
    """手动重连串口"""
    global serial_handler
    if serial_handler:
        success = serial_handler.connect()
        return jsonify({
            'success': success,
            'message': '重连成功' if success else '重连失败'
        })
    return jsonify({'success': False, 'message': '串口处理器未初始化'})

@app.route('/video_debug')
def video_debug():
    """视频流诊断页面"""
    return render_template('video_debug.html')

# 添加拍照功能
@app.route('/capture_photo', methods=['POST'])
def capture_photo():
    """拍照功能 - 捕获当前帧并保存"""
    global picam2, camera_active
    
    try:
        if not camera_active or not picam2:
            return jsonify({
                'success': False,
                'message': '摄像头未激活',
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        # 生成照片文件名
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        photo_filename = f"photo_{timestamp}.jpg"
        photo_path = os.path.join('/home/lenovo/SWS/photos', photo_filename)
        
        # 确保photos目录存在
        os.makedirs('/home/lenovo/SWS/photos', exist_ok=True)
        
        # 捕获一帧
        frame = picam2.capture_array()
        
        if frame is None or frame.size == 0:
            return jsonify({
                'success': False,
                'message': '捕获帧失败',
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        # 确保颜色空间正确
        if len(frame.shape) == 3:
            if frame.shape[2] == 3:  # RGB
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            else:  # RGBA
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
        else:
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        
        # 保存照片
        cv2.imwrite(photo_path, frame_bgr, [cv2.IMWRITE_JPEG_QUALITY, 95])
        
        # 记录日志
        logger.info(f"照片已保存: {photo_path}")
        
        return jsonify({
            'success': True,
            'message': '拍照成功',
            'filename': photo_filename,
            'path': photo_path,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Exception as e:
        logger.error(f"拍照错误: {e}")
        return jsonify({
            'success': False,
            'message': f'拍照失败: {str(e)}',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        })

@app.route('/get_photos')
def get_photos():
    """获取照片列表"""
    try:
        photos_dir = '/home/lenovo/SWS/photos'
        if not os.path.exists(photos_dir):
            return jsonify({
                'success': True,
                'photos': [],
                'message': '照片目录不存在'
            })
        
        # 获取所有照片文件
        photo_files = []
        for filename in os.listdir(photos_dir):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                file_path = os.path.join(photos_dir, filename)
                file_stat = os.stat(file_path)
                photo_files.append({
                    'filename': filename,
                    'size': file_stat.st_size,
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S', 
                                            time.localtime(file_stat.st_mtime))
                })
        
        # 按时间排序（最新的在前）
        photo_files.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return jsonify({
            'success': True,
            'photos': photo_files,
            'count': len(photo_files)
        })
        
    except Exception as e:
        logger.error(f"获取照片列表错误: {e}")
        return jsonify({
            'success': False,
            'message': f'获取照片列表失败: {str(e)}',
            'photos': []
        })

@app.route('/view_photo/<filename>')
def view_photo(filename):
    """查看照片"""
    try:
        photos_dir = '/home/lenovo/SWS/photos'
        file_path = os.path.join(photos_dir, filename)
        
        if not os.path.exists(file_path):
            return Response("照片不存在", status=404)
        
        # 安全检查，确保文件在照片目录内
        if not os.path.abspath(file_path).startswith(os.path.abspath(photos_dir)):
            return Response("非法访问", status=403)
        
        with open(file_path, 'rb') as f:
            image_data = f.read()
        
        return Response(image_data, mimetype='image/jpeg')
        
    except Exception as e:
        logger.error(f"查看照片错误: {e}")
        return Response("照片加载失败", status=500)

@app.route('/delete_photo/<filename>', methods=['DELETE'])
def delete_photo(filename):
    """删除照片"""
    try:
        photos_dir = '/home/lenovo/SWS/photos'
        file_path = os.path.join(photos_dir, filename)
        
        if not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'message': '照片不存在'
            })
        
        # 安全检查
        if not os.path.abspath(file_path).startswith(os.path.abspath(photos_dir)):
            return jsonify({
                'success': False,
                'message': '非法访问'
            })
        
        os.remove(file_path)
        logger.info(f"照片已删除: {file_path}")
        
        return jsonify({
            'success': True,
            'message': '照片删除成功'
        })
        
    except Exception as e:
        logger.error(f"删除照片错误: {e}")
        return jsonify({
            'success': False,
            'message': f'删除照片失败: {str(e)}'
        })

@app.route('/photos')
def photos_page():
    """照片管理页面"""
    return render_template('photos.html')

# 初始化所有组件
def init_all():
    global start_time
    start_time = time.time()
    
    logger.info("正在初始化系统...")
    
    # 初始化各个组件
    serial_ok = init_serial()
    camera_ok = init_camera()
    
    if not serial_ok:
        logger.warning("串口初始化失败，控制功能将不可用")
    if not camera_ok:
        logger.warning("摄像头初始化失败，视频功能将不可用")
    
    # 至少要有一个组件成功初始化
    return serial_ok or camera_ok

# 清理资源
def cleanup():
    global serial_handler, picam2, camera_active
    
    logger.info("正在清理资源...")
    
    # 发送停止命令
    if serial_handler and serial_handler.is_connected:
        send_command('S')
        time.sleep(0.1)
        serial_handler.disconnect()
        logger.info("串口已关闭")
    
    # 停止摄像头
    if picam2:
        camera_active = False
        time.sleep(0.5)  # 等待帧生成线程结束
        try:
            picam2.stop()
            picam2.close()
            logger.info("摄像头已停止")
        except Exception as e:
            logger.error(f"停止摄像头时出错: {e}")

# 信号处理
def signal_handler(signum, frame):
    """处理系统信号"""
    logger.info(f"收到信号 {signum}，正在退出...")
    cleanup()
    sys.exit(0)

# 启动时间
start_time = 0

if __name__ == '__main__':
    import signal
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 显示系统信息
        system_name = config_manager.get('system', 'name', '小车远程控制系统')
        system_version = config_manager.get('system', 'version', '2.0')
        logger.info(f"=== {system_name} v{system_version} ===")
        
        if init_all():
            logger.info("系统初始化完成")
            
            # 从配置文件获取网络参数
            host = config_manager.get('network', 'host', '0.0.0.0')
            port = config_manager.getint('network', 'port', 5800)
            debug = config_manager.getboolean('network', 'debug', False)
            
            logger.info(f"网页控制界面: http://localhost:{port}")
            logger.info("按 Ctrl+C 退出")
            
            # 启动Flask应用
            app.run(host=host, port=port, debug=debug, threaded=True)
        else:
            logger.error("系统初始化失败")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("用户中断")
    except Exception as e:
        logger.error(f"运行时错误: {e}")
    finally:
        cleanup()
