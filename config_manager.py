#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块
"""

import configparser
import os
import logging

class ConfigManager:
    """配置管理类"""
    
    def __init__(self, config_file='config.ini'):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        
        # 默认配置
        self.defaults = {
            'serial': {
                'port': '/dev/ttyS0',
                'baudrate': '9600',
                'timeout': '1',
                'max_retries': '5',
                'reconnect_interval': '2.0'
            },
            'camera': {
                'width': '960',
                'height': '720',
                'fps': '30',
                'jpeg_quality': '85'
            },
            'network': {
                'host': '0.0.0.0',
                'port': '5800',
                'debug': 'false'
            },
            'monitor': {
                'check_interval': '10.0',
                'temp_threshold': '70.0',
                'memory_threshold': '80.0',
                'disk_threshold': '90.0'
            },
            'logging': {
                'level': 'INFO',
                'log_file': 'car_web_control.log',
                'console_output': 'true',
                'max_file_size': '10',
                'backup_count': '5'
            },
            'system': {
                'name': '小车远程控制系统',
                'version': '2.0',
                'author': 'CarControl Team',
                'last_update': '2025-07-06'
            }
        }
        
        self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                self.config.read(self.config_file, encoding='utf-8')
                print(f"配置文件已加载: {self.config_file}")
            else:
                print(f"配置文件不存在，使用默认配置")
                self.create_default_config()
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            self.use_defaults()
    
    def create_default_config(self):
        """创建默认配置文件"""
        try:
            for section, options in self.defaults.items():
                self.config.add_section(section)
                for key, value in options.items():
                    self.config.set(section, key, value)
            
            self.save_config()
            print(f"默认配置文件已创建: {self.config_file}")
        except Exception as e:
            print(f"创建默认配置文件失败: {e}")
            self.use_defaults()
    
    def use_defaults(self):
        """使用默认配置"""
        self.config.clear()
        for section, options in self.defaults.items():
            self.config.add_section(section)
            for key, value in options.items():
                self.config.set(section, key, value)
        print("使用默认配置")
    
    def save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                self.config.write(f)
            print(f"配置文件已保存: {self.config_file}")
        except Exception as e:
            print(f"保存配置文件失败: {e}")
    
    def get(self, section, option, fallback=None):
        """获取配置值"""
        try:
            return self.config.get(section, option, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError):
            if fallback is not None:
                return fallback
            # 尝试从默认配置获取
            if section in self.defaults and option in self.defaults[section]:
                return self.defaults[section][option]
            return None
    
    def getint(self, section, option, fallback=None):
        """获取整数配置值"""
        try:
            return self.config.getint(section, option, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            if fallback is not None:
                return fallback
            if section in self.defaults and option in self.defaults[section]:
                try:
                    return int(self.defaults[section][option])
                except ValueError:
                    return fallback
            return None
    
    def getfloat(self, section, option, fallback=None):
        """获取浮点数配置值"""
        try:
            return self.config.getfloat(section, option, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            if fallback is not None:
                return fallback
            if section in self.defaults and option in self.defaults[section]:
                try:
                    return float(self.defaults[section][option])
                except ValueError:
                    return fallback
            return None
    
    def getboolean(self, section, option, fallback=None):
        """获取布尔配置值"""
        try:
            return self.config.getboolean(section, option, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            if fallback is not None:
                return fallback
            if section in self.defaults and option in self.defaults[section]:
                try:
                    return self.defaults[section][option].lower() in ('true', '1', 'yes', 'on')
                except AttributeError:
                    return fallback
            return None
    
    def set(self, section, option, value):
        """设置配置值"""
        try:
            if not self.config.has_section(section):
                self.config.add_section(section)
            self.config.set(section, option, str(value))
            return True
        except Exception as e:
            print(f"设置配置值失败: {e}")
            return False
    
    def get_all_config(self):
        """获取所有配置"""
        config_dict = {}
        for section in self.config.sections():
            config_dict[section] = dict(self.config.items(section))
        return config_dict
    
    def setup_logging(self):
        """根据配置设置日志"""
        level_str = self.get('logging', 'level', 'INFO')
        level = getattr(logging, level_str.upper(), logging.INFO)
        
        log_file = self.get('logging', 'log_file', 'car_web_control.log')
        console_output = self.getboolean('logging', 'console_output', True)
        
        handlers = []
        
        # 文件处理器
        if log_file:
            from logging.handlers import RotatingFileHandler
            max_size = self.getint('logging', 'max_file_size', 10) * 1024 * 1024  # MB to bytes
            backup_count = self.getint('logging', 'backup_count', 5)
            
            file_handler = RotatingFileHandler(
                log_file, 
                maxBytes=max_size, 
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(level)
            handlers.append(file_handler)
        
        # 控制台处理器
        if console_output:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(level)
            handlers.append(console_handler)
        
        # 设置日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        for handler in handlers:
            handler.setFormatter(formatter)
        
        # 配置根日志器
        logging.basicConfig(
            level=level,
            handlers=handlers,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        return logging.getLogger(__name__)

# 全局配置管理器实例
config_manager = ConfigManager()

# 便捷函数
def get_config(section, option, fallback=None):
    """获取配置值的便捷函数"""
    return config_manager.get(section, option, fallback)

def get_int_config(section, option, fallback=None):
    """获取整数配置值的便捷函数"""
    return config_manager.getint(section, option, fallback)

def get_float_config(section, option, fallback=None):
    """获取浮点数配置值的便捷函数"""
    return config_manager.getfloat(section, option, fallback)

def get_bool_config(section, option, fallback=None):
    """获取布尔配置值的便捷函数"""
    return config_manager.getboolean(section, option, fallback)
