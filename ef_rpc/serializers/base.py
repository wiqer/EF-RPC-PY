"""
序列化器基类
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Type
from ..types.base import Serializer, SerializationException

logger = logging.getLogger(__name__)

class BaseSerializer(Serializer):
    """
    序列化器基类，定义序列化/反序列化通用接口和异常处理。
    """
    @abstractmethod
    def _serialize_impl(self, obj: Any) -> bytes:
        """
        具体序列化实现。
        :param obj: 任意对象
        :return: 字节数组
        :raises Exception: 序列化失败
        """
        pass
    
    @abstractmethod
    def _deserialize_impl(self, data: bytes, target_type: Type) -> Any:
        """
        具体反序列化实现。
        :param data: 字节数组
        :param target_type: 目标类型
        :return: 反序列化对象
        :raises Exception: 反序列化失败
        """
        pass
    
    @abstractmethod
    def _serialize_to_string_impl(self, obj: Any) -> str:
        """
        具体字符串序列化实现。
        :param obj: 任意对象
        :return: 字符串
        :raises Exception: 序列化失败
        """
        pass
    
    @abstractmethod
    def _deserialize_from_string_impl(self, data: str, target_type: Type) -> Any:
        """
        具体字符串反序列化实现。
        :param data: 字符串
        :param target_type: 目标类型
        :return: 反序列化对象
        :raises Exception: 反序列化失败
        """
        pass
    
    def serialize(self, obj: Any) -> bytes:
        """
        序列化对象为字节数组。
        :param obj: 任意对象
        :return: 字节数组
        :raises SerializationException: 序列化失败
        """
        try:
            result = self._serialize_impl(obj)
            logger.debug(f"序列化成功: {obj}")
            return result
        except Exception as e:
            logger.exception("序列化失败")
            raise SerializationException(f"序列化失败: {str(e)}", e)
    
    def deserialize(self, data: bytes, target_type: Type) -> Any:
        """
        从字节数组反序列化对象。
        :param data: 字节数组
        :param target_type: 目标类型
        :return: 反序列化对象
        :raises SerializationException: 反序列化失败
        """
        try:
            result = self._deserialize_impl(data, target_type)
            logger.debug(f"反序列化成功: {result}")
            return result
        except Exception as e:
            logger.exception("反序列化失败")
            raise SerializationException(f"反序列化失败: {str(e)}", e)
    
    def serialize_to_string(self, obj: Any) -> str:
        """
        序列化对象为字符串。
        :param obj: 任意对象
        :return: 字符串
        :raises SerializationException: 序列化失败
        """
        try:
            result = self._serialize_to_string_impl(obj)
            logger.debug(f"字符串序列化成功: {obj}")
            return result
        except Exception as e:
            logger.exception("字符串序列化失败")
            raise SerializationException(f"字符串序列化失败: {str(e)}", e)
    
    def deserialize_from_string(self, data: str, target_type: Type) -> Any:
        """
        从字符串反序列化对象。
        :param data: 字符串
        :param target_type: 目标类型
        :return: 反序列化对象
        :raises SerializationException: 反序列化失败
        """
        try:
            result = self._deserialize_from_string_impl(data, target_type)
            logger.debug(f"字符串反序列化成功: {result}")
            return result
        except Exception as e:
            logger.exception("字符串反序列化失败")
            raise SerializationException(f"字符串反序列化失败: {str(e)}", e) 