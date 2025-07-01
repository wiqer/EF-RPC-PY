"""
JSON序列化器
"""

import json
import logging
from typing import Any, Type, Optional
from .base import BaseSerializer

logger = logging.getLogger(__name__)

class JsonSerializer(BaseSerializer):
    """
    JSON序列化器。
    支持对象与JSON字符串/字节的互转。
    """
    def __init__(self, ensure_ascii: bool = False, indent: Optional[int] = None) -> None:
        """
        初始化JSON序列化器。
        :param ensure_ascii: 是否确保ASCII编码
        :param indent: 缩进空格数
        """
        self.ensure_ascii = ensure_ascii
        self.indent = indent

    def _serialize_impl(self, obj: Any) -> bytes:
        """
        JSON序列化实现。
        :param obj: 任意对象
        :return: 字节数组
        :raises Exception: 序列化失败
        """
        json_str = json.dumps(obj, ensure_ascii=self.ensure_ascii, indent=self.indent)
        logger.debug(f"JSON序列化成功: {json_str}")
        return json_str.encode('utf-8')

    def _deserialize_impl(self, data: bytes, target_type: Type) -> Any:
        """
        JSON反序列化实现。
        :param data: 字节数组
        :param target_type: 目标类型
        :return: 反序列化对象
        :raises Exception: 反序列化失败
        """
        json_str = data.decode('utf-8')
        obj = json.loads(json_str)
        logger.debug(f"JSON反序列化成功: {obj}")
        if target_type != Any:
            return self._convert_type(obj, target_type)
        return obj

    def _serialize_to_string_impl(self, obj: Any) -> str:
        """
        JSON字符串序列化实现。
        :param obj: 任意对象
        :return: 字符串
        :raises Exception: 序列化失败
        """
        json_str = json.dumps(obj, ensure_ascii=self.ensure_ascii, indent=self.indent)
        logger.debug(f"JSON字符串序列化成功: {json_str}")
        return json_str

    def _deserialize_from_string_impl(self, data: str, target_type: Type) -> Any:
        """
        JSON字符串反序列化实现。
        :param data: 字符串
        :param target_type: 目标类型
        :return: 反序列化对象
        :raises Exception: 反序列化失败
        """
        obj = json.loads(data)
        logger.debug(f"JSON字符串反序列化成功: {obj}")
        if target_type != Any:
            return self._convert_type(obj, target_type)
        return obj

    def _convert_type(self, obj: Any, target_type: Type) -> Any:
        """
        类型转换。
        :param obj: 原始对象
        :param target_type: 目标类型
        :return: 转换后的对象
        """
        if target_type == str:
            return str(obj)
        elif target_type == int:
            return int(obj)
        elif target_type == float:
            return float(obj)
        elif target_type == bool:
            return bool(obj)
        elif target_type == list:
            return list(obj)
        elif target_type == dict:
            return dict(obj)
        else:
            # 对于复杂类型，直接返回对象
            return obj 