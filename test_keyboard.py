#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
键盘控制测试脚本
"""

import time
import requests
import threading
from pynput import keyboard

class KeyboardTest:
    def __init__(self, base_url="http://localhost:5800"):
        self.base_url = base_url
        self.pressed_keys = set()
        self.running = False
        
    def test_command(self, command):
        """测试发送命令"""
        try:
            response = requests.post(
                f"{self.base_url}/control",
                json={"command": command},
                timeout=0.5
            )
            if response.status_code == 200:
                data = response.json()
                if data['success']:
                    print(f"✓ 命令发送成功: {command}")
                    return True
                else:
                    print(f"✗ 命令发送失败: {command}")
                    return False
            else:
                print(f"✗ 服务器响应错误: {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ 请求异常: {e}")
            return False
    
    def on_press(self, key):
        """按键按下处理"""
        try:
            key_char = key.char.lower() if hasattr(key, 'char') and key.char else str(key)
            
            if key_char in self.pressed_keys:
                return
                
            self.pressed_keys.add(key_char)
            
            command = None
            if key_char == 'w':
                command = 'forward'
            elif key_char == 's':
                command = 'backward'
            elif key_char == 'a':
                command = 'left'
            elif key_char == 'd':
                command = 'right'
            elif key_char == 'q':
                command = 'stop'
            elif key == keyboard.Key.space:
                print("📸 拍照命令（测试中跳过）")
                return
            elif key == keyboard.Key.esc:
                print("🚪 退出测试")
                self.running = False
                return False
            
            if command:
                print(f"🔽 按键: {key_char} -> 命令: {command}")
                self.test_command(command)
                
        except Exception as e:
            print(f"按键处理错误: {e}")
    
    def on_release(self, key):
        """按键释放处理"""
        try:
            key_char = key.char.lower() if hasattr(key, 'char') and key.char else str(key)
            
            if key_char in self.pressed_keys:
                self.pressed_keys.remove(key_char)
            
            # 检查是否还有移动键按下
            movement_keys = {'w', 's', 'a', 'd'}
            has_movement = any(k in self.pressed_keys for k in movement_keys)
            
            if key_char in movement_keys and not has_movement:
                print(f"🔼 释放: {key_char} -> 发送停止命令")
                self.test_command('stop')
                
        except Exception as e:
            print(f"按键释放处理错误: {e}")
    
    def start_test(self):
        """开始测试"""
        print("=" * 50)
        print("键盘控制测试")
        print("=" * 50)
        print("使用说明:")
        print("  W/S/A/D - 控制小车移动")
        print("  Q - 停止")
        print("  空格 - 拍照（测试中跳过）")
        print("  ESC - 退出测试")
        print("=" * 50)
        
        # 检查服务器连接
        try:
            response = requests.get(f"{self.base_url}/health", timeout=2)
            if response.status_code == 200:
                print("✓ 服务器连接正常")
            else:
                print("✗ 服务器连接异常")
                return False
        except:
            print("✗ 无法连接到服务器")
            print("请确保小车控制系统已启动")
            return False
        
        print("\n开始键盘监听（按ESC退出）...")
        self.running = True
        
        with keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release) as listener:
            
            while self.running:
                time.sleep(0.1)
            
            listener.stop()
        
        print("测试结束")
        return True

if __name__ == "__main__":
    # 检查是否安装了pynput
    try:
        import pynput
    except ImportError:
        print("需要安装pynput库:")
        print("pip install pynput")
        exit(1)
    
    test = KeyboardTest()
    test.start_test()
