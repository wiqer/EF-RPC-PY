"""
基础类型定义
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Type, Union
import uuid
from datetime import datetime


@dataclass
class RpcConfig:
    """
    RPC配置对象。
    :param version: 协议版本号
    :param timeout: 超时时间（毫秒）
    :param retry_count: 重试次数
    :param retry_delay: 重试间隔（毫秒）
    """
    version: str = "1.0"
    timeout: int = 30000
    retry_count: int = 3
    retry_delay: int = 1000


@dataclass
class RpcInvocation:
    """
    RPC调用信息。
    :param service_name: 服务名
    :param method_name: 方法名
    :param arguments: 参数列表
    :param argument_types: 参数类型列表
    :param return_type: 返回值类型
    :param version: 协议版本号
    :param correlation_id: 关联ID（唯一标识一次调用）
    """
    service_name: str
    method_name: str
    arguments: List[Any]
    argument_types: List[Type]
    return_type: Type
    version: str = "1.0"
    correlation_id: Optional[str] = None

    def __post_init__(self) -> None:
        """
        初始化时自动生成唯一correlation_id。
        """
        if self.correlation_id is None:
            self.correlation_id = str(uuid.uuid4())


class RpcException(Exception):
    """
    RPC异常基类。
    :param message: 异常信息
    :param cause: 原始异常
    """
    def __init__(self, message: str, cause: Optional[Exception] = None) -> None:
        super().__init__(message)
        self.cause = cause


class ConnectionException(RpcException):
    """
    连接异常。
    """
    pass


class TimeoutException(RpcException):
    """
    超时异常。
    :param message: 异常信息
    :param timeout_ms: 超时时间（毫秒）
    """
    def __init__(self, message: str, timeout_ms: int) -> None:
        super().__init__(f"{message} (超时: {timeout_ms}ms)")
        self.timeout_ms = timeout_ms


class SerializationException(RpcException):
    """
    序列化异常。
    """
    pass


class InvocationException(RpcException):
    """
    调用异常。
    """
    pass


class Serializer(ABC):
    """
    序列化器接口。
    """
    @abstractmethod
    def serialize(self, obj: Any) -> bytes:
        """
        序列化对象为字节数组。
        :param obj: 任意对象
        :return: 字节数组
        :raises SerializationException: 序列化失败
        """
        pass

    @abstractmethod
    def deserialize(self, data: bytes, target_type: Type) -> Any:
        """
        从字节数组反序列化对象。
        :param data: 字节数组
        :param target_type: 目标类型
        :return: 反序列化后的对象
        :raises SerializationException: 反序列化失败
        """
        pass

    @abstractmethod
    def serialize_to_string(self, obj: Any) -> str:
        """
        序列化对象为字符串。
        :param obj: 任意对象
        :return: 字符串
        :raises SerializationException: 序列化失败
        """
        pass

    @abstractmethod
    def deserialize_from_string(self, data: str, target_type: Type) -> Any:
        """
        从字符串反序列化对象。
        :param data: 字符串
        :param target_type: 目标类型
        :return: 反序列化后的对象
        :raises SerializationException: 反序列化失败
        """
        pass


class RpcTransport(ABC):
    """
    RPC传输接口。
    """
    @abstractmethod
    async def start(self) -> None:
        """
        启动传输。
        :raises ConnectionException: 启动失败
        """
        pass

    @abstractmethod
    async def stop(self) -> None:
        """
        停止传输。
        """
        pass

    @abstractmethod
    async def send_request(self, service_name: str, data: bytes) -> bytes:
        """
        发送请求。
        :param service_name: 服务名
        :param data: 请求数据
        :return: 响应数据
        :raises TimeoutException: 超时
        :raises ConnectionException: 连接异常
        """
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """
        检查连接状态。
        :return: 是否已连接
        """
        pass

    @abstractmethod
    async def start_server(self, service_name: str) -> None:
        """
        启动服务端模式。
        :param service_name: 服务名
        """
        pass

    @abstractmethod
    def set_request_handler(self, handler: 'RequestHandler') -> None:
        """
        设置请求处理器。
        :param handler: 请求处理器
        """
        pass


class RequestHandler(ABC):
    """
    请求处理器接口。
    """
    @abstractmethod
    async def handle_request(self, service_name: str, data: bytes) -> bytes:
        """
        处理请求。
        :param service_name: 服务名
        :param data: 请求数据
        :return: 响应数据
        :raises InvocationException: 处理失败
        """
        pass 