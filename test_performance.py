#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统性能测试脚本
测试优化后的响应时间和延迟
"""

import time
import requests
import threading
import statistics
from datetime import datetime

class PerformanceTest:
    def __init__(self, base_url="http://localhost:5800"):
        self.base_url = base_url
        self.results = []
        
    def test_command_response(self, command="stop", iterations=10):
        """测试命令响应时间"""
        print(f"测试命令响应时间: {command} (执行{iterations}次)")
        response_times = []
        
        for i in range(iterations):
            start_time = time.time()
            try:
                response = requests.post(
                    f"{self.base_url}/control",
                    json={"command": command},
                    timeout=1
                )
                end_time = time.time()
                
                if response.status_code == 200:
                    response_time = (end_time - start_time) * 1000  # 转换为毫秒
                    response_times.append(response_time)
                    print(f"  第{i+1}次: {response_time:.2f}ms")
                else:
                    print(f"  第{i+1}次: 请求失败 ({response.status_code})")
                    
            except Exception as e:
                print(f"  第{i+1}次: 异常 ({e})")
            
            time.sleep(0.1)  # 间隔100ms
        
        if response_times:
            avg_time = statistics.mean(response_times)
            min_time = min(response_times)
            max_time = max(response_times)
            print(f"  平均响应时间: {avg_time:.2f}ms")
            print(f"  最快响应时间: {min_time:.2f}ms")
            print(f"  最慢响应时间: {max_time:.2f}ms")
            return avg_time
        else:
            print("  测试失败: 没有成功的请求")
            return None
    
    def test_emergency_stop(self, iterations=5):
        """测试紧急停止响应时间"""
        print(f"测试紧急停止响应时间 (执行{iterations}次)")
        response_times = []
        
        for i in range(iterations):
            start_time = time.time()
            try:
                response = requests.post(
                    f"{self.base_url}/emergency_stop",
                    timeout=1
                )
                end_time = time.time()
                
                if response.status_code == 200:
                    response_time = (end_time - start_time) * 1000
                    response_times.append(response_time)
                    print(f"  第{i+1}次: {response_time:.2f}ms")
                else:
                    print(f"  第{i+1}次: 请求失败 ({response.status_code})")
                    
            except Exception as e:
                print(f"  第{i+1}次: 异常 ({e})")
            
            time.sleep(0.2)
        
        if response_times:
            avg_time = statistics.mean(response_times)
            print(f"  平均紧急停止响应时间: {avg_time:.2f}ms")
            return avg_time
        else:
            print("  测试失败: 没有成功的请求")
            return None
    
    def test_status_update(self, iterations=10):
        """测试状态更新响应时间"""
        print(f"测试状态更新响应时间 (执行{iterations}次)")
        response_times = []
        
        for i in range(iterations):
            start_time = time.time()
            try:
                response = requests.get(
                    f"{self.base_url}/status",
                    timeout=1
                )
                end_time = time.time()
                
                if response.status_code == 200:
                    response_time = (end_time - start_time) * 1000
                    response_times.append(response_time)
                    print(f"  第{i+1}次: {response_time:.2f}ms")
                else:
                    print(f"  第{i+1}次: 请求失败 ({response.status_code})")
                    
            except Exception as e:
                print(f"  第{i+1}次: 异常 ({e})")
            
            time.sleep(0.1)
        
        if response_times:
            avg_time = statistics.mean(response_times)
            print(f"  平均状态更新响应时间: {avg_time:.2f}ms")
            return avg_time
        else:
            print("  测试失败: 没有成功的请求")
            return None
    
    def test_video_stream(self, duration=5):
        """测试视频流连接"""
        print(f"测试视频流连接 (持续{duration}秒)")
        start_time = time.time()
        
        try:
            response = requests.get(
                f"{self.base_url}/video_feed",
                stream=True,
                timeout=duration + 1
            )
            
            if response.status_code == 200:
                bytes_received = 0
                frames_received = 0
                
                for chunk in response.iter_content(chunk_size=1024):
                    bytes_received += len(chunk)
                    if b'--frame' in chunk:
                        frames_received += 1
                    
                    if time.time() - start_time > duration:
                        break
                
                elapsed_time = time.time() - start_time
                print(f"  接收数据: {bytes_received} 字节")
                print(f"  接收帧数: {frames_received}")
                print(f"  平均帧率: {frames_received/elapsed_time:.2f} fps")
                
                return frames_received / elapsed_time
            else:
                print(f"  视频流连接失败 ({response.status_code})")
                return None
                
        except Exception as e:
            print(f"  视频流测试异常: {e}")
            return None
    
    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 50)
        print("小车控制系统性能测试")
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)
        
        # 测试系统是否在线
        try:
            response = requests.get(f"{self.base_url}/health", timeout=2)
            if response.status_code == 200:
                print("✓ 系统在线")
            else:
                print("✗ 系统离线")
                return
        except:
            print("✗ 无法连接到系统")
            return
        
        print()
        
        # 测试各项功能
        control_time = self.test_command_response("stop", 10)
        print()
        
        emergency_time = self.test_emergency_stop(5)
        print()
        
        status_time = self.test_status_update(10)
        print()
        
        video_fps = self.test_video_stream(5)
        print()
        
        # 输出总结
        print("=" * 50)
        print("测试结果总结:")
        print("=" * 50)
        
        if control_time:
            print(f"控制命令响应时间: {control_time:.2f}ms")
            
        if emergency_time:
            print(f"紧急停止响应时间: {emergency_time:.2f}ms")
            
        if status_time:
            print(f"状态更新响应时间: {status_time:.2f}ms")
            
        if video_fps:
            print(f"视频流帧率: {video_fps:.2f} fps")
        
        print()
        
        # 性能评估
        print("性能评估:")
        if control_time and control_time < 100:
            print("✓ 控制响应: 优秀")
        elif control_time and control_time < 200:
            print("⚠ 控制响应: 良好")
        else:
            print("✗ 控制响应: 需要改进")
            
        if emergency_time and emergency_time < 50:
            print("✓ 紧急停止: 优秀")
        elif emergency_time and emergency_time < 100:
            print("⚠ 紧急停止: 良好")
        else:
            print("✗ 紧急停止: 需要改进")
            
        if video_fps and video_fps > 10:
            print("✓ 视频流: 优秀")
        elif video_fps and video_fps > 5:
            print("⚠ 视频流: 良好")
        else:
            print("✗ 视频流: 需要改进")

if __name__ == "__main__":
    test = PerformanceTest()
    test.run_all_tests()
