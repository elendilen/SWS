#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志分析工具
帮助分析小车控制系统的日志，找出连接断开的原因
"""

import re
import sys
from datetime import datetime
import argparse

def analyze_log_file(log_file='car_web_control.log'):
    """分析日志文件"""
    
    print(f"=== 分析日志文件: {log_file} ===")
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"❌ 日志文件 {log_file} 不存在")
        return
    except Exception as e:
        print(f"❌ 读取日志文件失败: {e}")
        return
    
    print(f"📊 日志文件总行数: {len(lines)}")
    
    # 分析统计
    error_count = 0
    warning_count = 0
    connection_events = []
    serial_events = []
    camera_events = []
    system_events = []
    
    # 关键词匹配
    error_patterns = [
        r'ERROR',
        r'CRITICAL',
        r'Exception',
        r'Traceback',
        r'失败',
        r'异常',
        r'错误'
    ]
    
    warning_patterns = [
        r'WARNING',
        r'警告',
        r'重连',
        r'重试'
    ]
    
    connection_patterns = [
        r'连接',
        r'断开',
        r'重连',
        r'connect',
        r'disconnect'
    ]
    
    serial_patterns = [
        r'串口',
        r'serial',
        r'ttyS0'
    ]
    
    camera_patterns = [
        r'摄像头',
        r'camera',
        r'picamera'
    ]
    
    system_patterns = [
        r'系统',
        r'监控',
        r'温度',
        r'内存',
        r'磁盘'
    ]
    
    # 分析每一行
    for i, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
        
        # 检查错误
        for pattern in error_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                error_count += 1
                print(f"❌ 错误 (行{i}): {line}")
                break
        
        # 检查警告
        for pattern in warning_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                warning_count += 1
                print(f"⚠️  警告 (行{i}): {line}")
                break
        
        # 检查连接事件
        for pattern in connection_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                connection_events.append((i, line))
                break
        
        # 检查串口事件
        for pattern in serial_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                serial_events.append((i, line))
                break
        
        # 检查摄像头事件
        for pattern in camera_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                camera_events.append((i, line))
                break
        
        # 检查系统事件
        for pattern in system_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                system_events.append((i, line))
                break
    
    # 输出统计结果
    print(f"\n📈 统计结果:")
    print(f"🔴 错误数量: {error_count}")
    print(f"🟡 警告数量: {warning_count}")
    print(f"🔗 连接事件: {len(connection_events)}")
    print(f"📡 串口事件: {len(serial_events)}")
    print(f"📹 摄像头事件: {len(camera_events)}")
    print(f"🖥️  系统事件: {len(system_events)}")
    
    # 显示最近的连接事件
    if connection_events:
        print(f"\n🔗 最近的连接事件:")
        for i, (line_num, line) in enumerate(connection_events[-10:]):
            print(f"  {i+1}. (行{line_num}): {line}")
    
    # 显示最近的串口事件
    if serial_events:
        print(f"\n📡 最近的串口事件:")
        for i, (line_num, line) in enumerate(serial_events[-10:]):
            print(f"  {i+1}. (行{line_num}): {line}")
    
    # 显示最近的摄像头事件
    if camera_events:
        print(f"\n📹 最近的摄像头事件:")
        for i, (line_num, line) in enumerate(camera_events[-5:]):
            print(f"  {i+1}. (行{line_num}): {line}")
    
    # 显示最近的系统事件
    if system_events:
        print(f"\n🖥️  最近的系统事件:")
        for i, (line_num, line) in enumerate(system_events[-5:]):
            print(f"  {i+1}. (行{line_num}): {line}")
    
    # 显示最近的日志（过滤HTTP请求）
    print(f"\n📋 最近的系统日志 (过滤HTTP请求):")
    recent_lines = []
    for line in lines[-50:]:
        if 'werkzeug' not in line and 'HTTP' not in line:
            recent_lines.append(line.strip())
    
    if recent_lines:
        for i, line in enumerate(recent_lines[-20:], 1):
            print(f"  {i}. {line}")
    else:
        print("  (没有找到非HTTP请求的日志)")

def show_realtime_log(log_file='car_web_control.log'):
    """实时显示日志"""
    import time
    
    print(f"=== 实时日志监控: {log_file} ===")
    print("按 Ctrl+C 停止监控")
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            # 移动到文件末尾
            f.seek(0, 2)
            
            while True:
                line = f.readline()
                if line:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"[{timestamp}] {line.strip()}")
                else:
                    time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n📋 监控已停止")
    except Exception as e:
        print(f"❌ 监控失败: {e}")

def search_log(log_file='car_web_control.log', keyword=''):
    """搜索日志中的关键词"""
    if not keyword:
        print("❌ 请提供搜索关键词")
        return
    
    print(f"=== 搜索关键词: {keyword} ===")
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"❌ 日志文件 {log_file} 不存在")
        return
    except Exception as e:
        print(f"❌ 读取日志文件失败: {e}")
        return
    
    matches = []
    for i, line in enumerate(lines, 1):
        if keyword.lower() in line.lower():
            matches.append((i, line.strip()))
    
    if matches:
        print(f"🔍 找到 {len(matches)} 个匹配项:")
        for i, (line_num, line) in enumerate(matches[-20:], 1):
            print(f"  {i}. (行{line_num}): {line}")
    else:
        print(f"❌ 未找到关键词 '{keyword}' 的匹配项")

def main():
    parser = argparse.ArgumentParser(description='小车控制系统日志分析工具')
    parser.add_argument('--log', default='car_web_control.log', help='日志文件路径')
    parser.add_argument('--analyze', action='store_true', help='分析日志文件')
    parser.add_argument('--realtime', action='store_true', help='实时监控日志')
    parser.add_argument('--search', help='搜索关键词')
    
    args = parser.parse_args()
    
    if args.analyze:
        analyze_log_file(args.log)
    elif args.realtime:
        show_realtime_log(args.log)
    elif args.search:
        search_log(args.log, args.search)
    else:
        # 默认执行分析
        analyze_log_file(args.log)

if __name__ == '__main__':
    main()
