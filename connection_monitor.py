#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
连接监控模块 - 监控网络连接和系统状态
"""

import time
import threading
import logging
import psutil
import subprocess
from typing import Optional, Callable, Dict, List

class ConnectionMonitor:
    """连接监控类"""
    
    def __init__(self, check_interval: float = 10.0):
        self.check_interval = check_interval
        self.is_monitoring = False
        self.monitor_thread = None
        
        # 状态信息
        self.network_status = {
            'connected': False,
            'interface': '',
            'ip': '',
            'last_check': 0
        }
        
        self.system_status = {
            'cpu_percent': 0.0,
            'memory_percent': 0.0,
            'disk_percent': 0.0,
            'temperature': 0.0,
            'last_check': 0
        }
        
        # 警告阈值
        self.thresholds = {
            'temp': 70.0,
            'memory': 80.0,
            'disk': 90.0
        }
        
        # 回调函数
        self.on_network_change: Optional[Callable] = None
        self.on_system_alert: Optional[Callable] = None
        
        # 日志设置
        self.logger = logging.getLogger(__name__)
        
    def set_thresholds(self, temp: float = None, memory: float = None, disk: float = None):
        """设置系统警告阈值"""
        if temp is not None:
            self.thresholds['temp'] = temp
        if memory is not None:
            self.thresholds['memory'] = memory
        if disk is not None:
            self.thresholds['disk'] = disk
            
        self.logger.info(f"警告阈值已设置: 温度={self.thresholds['temp']}°C, "
                        f"内存={self.thresholds['memory']}%, 磁盘={self.thresholds['disk']}%")
    
    def start_monitoring(self):
        """启动监控"""
        if self.is_monitoring:
            self.logger.warning("监控已在运行")
            return
            
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        self.logger.info("连接监控已启动")
    
    def stop_monitoring(self):
        """停止监控"""
        self.is_monitoring = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
        self.logger.info("连接监控已停止")
    
    def _monitor_loop(self):
        """监控循环"""
        while self.is_monitoring:
            try:
                # 检查网络状态
                self._check_network_status()
                
                # 检查系统状态
                self._check_system_status()
                
                # 检查警告条件
                self._check_alerts()
                
            except Exception as e:
                self.logger.error(f"监控循环错误: {e}")
            
            time.sleep(self.check_interval)
    
    def _check_network_status(self):
        """检查网络连接状态"""
        try:
            old_status = self.network_status.copy()
            
            # 获取网络接口信息
            interfaces = psutil.net_if_addrs()
            connected = False
            interface_name = ''
            ip_address = ''
            
            for interface, addrs in interfaces.items():
                if interface.startswith(('eth', 'wlan', 'enp', 'wlp')):
                    for addr in addrs:
                        if addr.family == 2:  # IPv4
                            if not addr.address.startswith('127.'):
                                connected = True
                                interface_name = interface
                                ip_address = addr.address
                                break
                    if connected:
                        break
            
            # 如果没有找到有效接口，尝试ping测试
            if not connected:
                try:
                    result = subprocess.run(
                        ['ping', '-c', '1', '-W', '3', '8.8.8.8'],
                        capture_output=True,
                        timeout=5
                    )
                    connected = result.returncode == 0
                except:
                    connected = False
            
            # 更新状态
            self.network_status.update({
                'connected': connected,
                'interface': interface_name,
                'ip': ip_address,
                'last_check': time.time()
            })
            
            # 检查状态变化
            if old_status['connected'] != connected:
                self.logger.info(f"网络状态变化: {old_status['connected']} -> {connected}")
                if self.on_network_change:
                    self.on_network_change(self.network_status)
                    
        except Exception as e:
            self.logger.error(f"检查网络状态错误: {e}")
    
    def _check_system_status(self):
        """检查系统状态"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 内存使用率
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # 磁盘使用率
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            
            # CPU温度 (树莓派)
            temperature = self._get_cpu_temperature()
            
            # 更新状态
            self.system_status.update({
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'disk_percent': disk_percent,
                'temperature': temperature,
                'last_check': time.time()
            })
            
        except Exception as e:
            self.logger.error(f"检查系统状态错误: {e}")
    
    def _get_cpu_temperature(self):
        """获取CPU温度"""
        try:
            # 尝试读取树莓派温度文件
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                temp = int(f.read().strip()) / 1000.0
                return temp
        except:
            try:
                # 尝试使用psutil获取温度
                temps = psutil.sensors_temperatures()
                if 'cpu_thermal' in temps:
                    return temps['cpu_thermal'][0].current
                elif 'coretemp' in temps:
                    return temps['coretemp'][0].current
            except:
                pass
        return 0.0
    
    def _check_alerts(self):
        """检查警告条件"""
        alerts = []
        
        # 检查温度
        if self.system_status['temperature'] > self.thresholds['temp']:
            alerts.append(f"CPU温度过高: {self.system_status['temperature']:.1f}°C")
        
        # 检查内存
        if self.system_status['memory_percent'] > self.thresholds['memory']:
            alerts.append(f"内存使用率过高: {self.system_status['memory_percent']:.1f}%")
        
        # 检查磁盘
        if self.system_status['disk_percent'] > self.thresholds['disk']:
            alerts.append(f"磁盘使用率过高: {self.system_status['disk_percent']:.1f}%")
        
        # 检查网络连接
        if not self.network_status['connected']:
            alerts.append("网络连接丢失")
        
        # 触发警告回调
        if alerts and self.on_system_alert:
            self.on_system_alert(alerts)
    
    def get_status(self) -> Dict:
        """获取完整状态信息"""
        return {
            'network': self.network_status.copy(),
            'system': self.system_status.copy(),
            'thresholds': self.thresholds.copy(),
            'monitoring': self.is_monitoring
        }
    
    def get_network_status(self) -> Dict:
        """获取网络状态"""
        return self.network_status.copy()
    
    def get_system_status(self) -> Dict:
        """获取系统状态"""
        return self.system_status.copy()
    
    def force_check(self):
        """强制执行一次检查"""
        try:
            self._check_network_status()
            self._check_system_status()
            self._check_alerts()
            self.logger.info("强制检查完成")
        except Exception as e:
            self.logger.error(f"强制检查错误: {e}")

# 使用示例
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    def on_network_change(status):
        print(f"网络状态变化: {status}")
    
    def on_system_alert(alerts):
        print(f"系统警告: {alerts}")
    
    monitor = ConnectionMonitor(check_interval=5.0)
    monitor.on_network_change = on_network_change
    monitor.on_system_alert = on_system_alert
    
    monitor.start_monitoring()
    
    try:
        while True:
            time.sleep(10)
            status = monitor.get_status()
            print(f"当前状态: {status}")
    except KeyboardInterrupt:
        monitor.stop_monitoring()
        print("监控已停止")
