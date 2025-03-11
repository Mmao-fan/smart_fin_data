#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Dict, List, Any, Optional, Union
import re
import logging
import hashlib
import json

class SensitiveInfoDetector:
    """敏感信息检测器"""
    
    def __init__(self):
        # 敏感信息模式
        self.patterns = {
            "ID_CARD": r'[1-9]\d{5}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx]',
            "PHONE": r'(?:\+\d{1,3}[-\s]?)?\d{3,4}[-\s]?\d{3,4}[-\s]?\d{4}',
            "EMAIL": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "BANK_CARD": r'\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}',
            "ADDRESS": r'[\u4e00-\u9fa5]{2,}(?:省|市|区|县|路|街|号|大厦|广场|小区)[\u4e00-\u9fa5\d]{2,}',
            "NAME": r'[\u4e00-\u9fa5]{2,4}(?:先生|女士|总经理|经理|主管)',
            "ACCOUNT": r'(?:账号|账户|卡号)[:：]?\s*[\w\d-]+',
            "IP": r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
            "PASSWORD": r'(?:密码|password)[:：]?\s*[\w\d@#$%^&*]+',
            "SSN": r'\d{3}-\d{2}-\d{4}'
        }
    
    def detect_sensitive_info(self, text: str) -> List[Dict[str, Any]]:
        """检测文本中的敏感信息"""
        sensitive_info = []
        
        for info_type, pattern in self.patterns.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                sensitive_info.append({
                    'type': info_type,
                    'value': match.group(),
                    'start': match.start(),
                    'end': match.end()
                })
                
        # 按位置排序
        sensitive_info.sort(key=lambda x: x['start'])
        return sensitive_info

class DataAnonymizer:
    """数据脱敏处理器"""
    
    def __init__(self, detector: SensitiveInfoDetector = None):
        self.detector = detector or SensitiveInfoDetector()
        self.salt = "smart_fin_data_2025"  # 加盐值
        
    def anonymize(self, text: str) -> str:
        """匿名化文本中的敏感信息"""
        if not text:
            return text
            
        # 检测敏感信息
        sensitive_info = self.detector.detect_sensitive_info(text)
        if not sensitive_info:
            return text
            
        # 从后向前替换，避免位置变化
        for info in reversed(sensitive_info):
            replacement = self._get_replacement(info['type'], info['value'])
            text = text[:info['start']] + replacement + text[info['end']:]
            
        return text
        
    def _get_replacement(self, info_type: str, value: str) -> str:
        """根据敏感信息类型生成替换值"""
        if info_type == "ID_CARD":
            return "**********" + value[-4:]
        elif info_type == "PHONE":
            return value[:3] + "****" + value[-4:]
        elif info_type == "EMAIL":
            parts = value.split("@")
            return parts[0][:3] + "***@" + parts[1]
        elif info_type == "BANK_CARD":
            return "**** **** **** " + value[-4:]
        elif info_type == "NAME":
            return value[0] + "*" * (len(value) - 1)
        elif info_type == "ADDRESS":
            return value[:6] + "****"
        elif info_type == "ACCOUNT":
            return "账号：****" + value[-4:]
        elif info_type == "PASSWORD":
            return "******"
        else:
            # 使用哈希值作为替换
            return self._hash_value(value)[:8]
            
    def _hash_value(self, value: str) -> str:
        """生成哈希值"""
        return hashlib.md5((value + self.salt).encode()).hexdigest()
        
    def anonymize_structured_data(self, data: Union[Dict, List]) -> Union[Dict, List]:
        """匿名化结构化数据"""
        if isinstance(data, dict):
            return self._anonymize_dict(data)
        elif isinstance(data, list):
            return [self._anonymize_dict(item) if isinstance(item, dict) else item for item in data]
        return data
        
    def _anonymize_dict(self, data: Dict) -> Dict:
        """匿名化字典数据"""
        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                result[key] = self.anonymize(value)
            elif isinstance(value, dict):
                result[key] = self._anonymize_dict(value)
            elif isinstance(value, list):
                result[key] = [
                    self._anonymize_dict(item) if isinstance(item, dict)
                    else self.anonymize(item) if isinstance(item, str)
                    else item
                    for item in value
                ]
            else:
                result[key] = value
        return result
        
    def _anonymize_tabular_data(self, data: List[Dict]) -> List[Dict]:
        """匿名化表格数据"""
        sensitive_columns = {
            'id_card', 'phone', 'email', 'address', 'name', 'account',
            'password', 'card_no', 'bank_card', 'ssn'
        }
        
        result = []
        for row in data:
            anonymized_row = {}
            for key, value in row.items():
                if any(col in key.lower() for col in sensitive_columns):
                    if isinstance(value, str):
                        anonymized_row[key] = self.anonymize(value)
                    else:
                        anonymized_row[key] = str(value)
                else:
                    anonymized_row[key] = value
            result.append(anonymized_row)
            
        return result 