#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
串口处理模块 - 简化版本
"""

import serial
import time
import threading
import logging
from typing import Optional, Callable

class SerialHandler:
    """简化的串口处理类"""
    
    def __init__(self, port: str = '/dev/ttyS0', baudrate: int = 9600, 
                 timeout: int = 1, max_retries: int = 3):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.max_retries = max_retries
        
        self.serial_conn: Optional[serial.Serial] = None
        self.is_connected = False
        self.retry_count = 0
        
        # 线程锁
        self.lock = threading.Lock()
        
        # 状态回调
        self.on_connected: Optional[Callable] = None
        self.on_disconnected: Optional[Callable] = None
        
        # 日志设置
        self.logger = logging.getLogger(__name__)
        
    def connect(self) -> bool:
        """连接串口"""
        with self.lock:
            try:
                if self.serial_conn and self.serial_conn.is_open:
                    self.serial_conn.close()
                    
                self.serial_conn = serial.Serial(
                    port=self.port,
                    baudrate=self.baudrate,
                    timeout=self.timeout
                )
                
                self.is_connected = True
                self.retry_count = 0
                
                self.logger.info(f"串口连接成功: {self.port}")
                
                if self.on_connected:
                    self.on_connected()
                    
                return True
                
            except Exception as e:
                self.logger.error(f"串口连接失败: {e}")
                self.is_connected = False
                if self.serial_conn:
                    try:
                        self.serial_conn.close()
                    except:
                        pass
                    self.serial_conn = None
                return False
    
    def disconnect(self):
        """断开连接"""
        with self.lock:
            if self.serial_conn and self.serial_conn.is_open:
                try:
                    self.serial_conn.close()
                except:
                    pass
            self.serial_conn = None
            self.is_connected = False
            
        if self.on_disconnected:
            self.on_disconnected()
            
        self.logger.info("串口已断开")
    
    def send_command(self, command: str) -> bool:
        """发送命令"""
        if not self.is_connected:
            self.logger.warning("串口未连接，无法发送命令")
            return False
            
        with self.lock:
            try:
                if self.serial_conn and self.serial_conn.is_open:
                    data = command.encode()
                    self.serial_conn.write(data)
                    self.serial_conn.flush()
                    self.logger.debug(f"已发送命令: {command}")
                    return True
                else:
                    self.logger.warning("串口连接无效")
                    self.is_connected = False
                    return False
                    
            except Exception as e:
                self.logger.error(f"发送命令失败: {e}")
                self.is_connected = False
                return False
    
    def get_status(self) -> dict:
        """获取连接状态"""
        return {
            'connected': self.is_connected,
            'port': self.port,
            'baudrate': self.baudrate,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries
        }
    
    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.disconnect()
