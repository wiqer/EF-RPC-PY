#!/usr/bin/env python3
"""
序列化器 Mock 单元测试
"""

import pytest
import json
from typing import Dict, List, Any
from ef_rpc.serializers.json_serializer import JsonSerializer
from ef_rpc.types.base import SerializationException


class TestJsonSerializer:
    """JSON序列化器测试类"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.serializer = JsonSerializer()
    
    def test_basic_types(self):
        """测试基本数据类型序列化"""
        test_cases = [
            ("字符串", "hello world"),
            ("数字", 42),
            ("浮点数", 3.14),
            ("布尔值", True),
            ("空值", None),
            ("列表", [1, 2, 3, "test"]),
            ("字典", {"key": "value", "num": 123}),
        ]
        
        for name, data in test_cases:
            # 测试字符串序列化
            serialized = self.serializer.serialize_to_string(data)
            deserialized = self.serializer.deserialize_from_string(serialized, type(data))
            assert deserialized == data
            
            # 测试字节序列化
            serialized_bytes = self.serializer.serialize(data)
            deserialized_bytes = self.serializer.deserialize(serialized_bytes, type(data))
            assert deserialized_bytes == data
    
    def test_complex_nested_structures(self):
        """测试复杂嵌套结构"""
        complex_data = {
            "users": [
                {"id": 1, "name": "Alice", "active": True},
                {"id": 2, "name": "Bob", "active": False},
            ],
            "metadata": {
                "version": "1.0.0",
                "timestamp": 1234567890,
                "tags": ["test", "mock", "unit"]
            }
        }
        
        serialized = self.serializer.serialize_to_string(complex_data)
        deserialized = self.serializer.deserialize_from_string(serialized, dict)
        assert deserialized == complex_data
    
    def test_chinese_unicode(self):
        """测试中文字符序列化"""
        chinese_data = {
            "message": "你好，世界！",
            "description": "这是一个测试消息",
            "tags": ["中文", "测试", "序列化"]
        }
        
        serialized = self.serializer.serialize_to_string(chinese_data)
        deserialized = self.serializer.deserialize_from_string(serialized, dict)
        assert deserialized == chinese_data
    
    def test_serializer_configuration(self):
        """测试序列化器配置选项"""
        # 测试 ensure_ascii=False
        serializer_utf8 = JsonSerializer(ensure_ascii=False)
        chinese_text = "你好世界"
        serialized = serializer_utf8.serialize_to_string(chinese_text)
        assert "你好世界" in serialized
        
        # 测试缩进配置
        serializer_indent = JsonSerializer(indent=2)
        data = {"a": 1, "b": 2}
        serialized = serializer_indent.serialize_to_string(data)
        assert "\n" in serialized  # 应该包含换行符
    
    def test_type_conversion(self):
        """测试类型转换功能"""
        # 字符串转数字
        result = self.serializer._convert_type("123", int)
        assert result == 123
        assert isinstance(result, int)
        
        # 数字转字符串
        result = self.serializer._convert_type(456, str)
        assert result == "456"
        assert isinstance(result, str)
        
        # 字符串转布尔值
        result = self.serializer._convert_type("true", bool)
        assert result is True
        
        # 列表转换
        result = self.serializer._convert_type([1, 2, 3], list)
        assert result == [1, 2, 3]
        assert isinstance(result, list)
    
    def test_error_handling(self):
        """测试错误处理"""
        # 测试无效JSON
        with pytest.raises(Exception):
            self.serializer.deserialize_from_string("invalid json", dict)
        
        # 测试类型转换错误
        with pytest.raises(ValueError):
            self.serializer._convert_type("not_a_number", int)
    
    def test_empty_structures(self):
        """测试空结构序列化"""
        empty_cases = [
            ("空字典", {}),
            ("空列表", []),
            ("空字符串", ""),
            ("零值", 0),
        ]
        
        for name, data in empty_cases:
            serialized = self.serializer.serialize_to_string(data)
            deserialized = self.serializer.deserialize_from_string(serialized, type(data))
            assert deserialized == data
    
    def test_large_data(self):
        """测试大数据量序列化"""
        large_data = {
            "items": [{"id": i, "value": f"item_{i}"} for i in range(1000)]
        }
        
        serialized = self.serializer.serialize_to_string(large_data)
        deserialized = self.serializer.deserialize_from_string(serialized, dict)
        assert len(deserialized["items"]) == 1000
        assert deserialized["items"][0]["id"] == 0
        assert deserialized["items"][-1]["id"] == 999 