"""
代理工厂类，用于创建动态代理对象
"""

import asyncio
import uuid
import logging
from typing import Any, Dict, List, Optional
from ..types.base import RpcTransport, Serializer, RpcConfig, InvocationException

logger = logging.getLogger(__name__)

class ProxyFactory:
    """
    代理工厂，用于创建服务代理。
    """
    def __init__(self, transport: RpcTransport, serializer: Serializer, config: RpcConfig, service_name: str) -> None:
        """
        初始化代理工厂。
        :param transport: 传输层
        :param serializer: 序列化器
        :param config: RPC配置
        :param service_name: 服务名称
        """
        self.transport = transport
        self.serializer = serializer
        self.config = config
        self.service_name = service_name
        self._pending_requests: Dict[str, asyncio.Future] = {}

    def create_proxy(self) -> Any:
        """
        创建服务代理对象。
        :return: 动态代理对象
        """
        return ServiceProxy(
            transport=self.transport,
            serializer=self.serializer,
            config=self.config,
            service_name=self.service_name,
            pending_requests=self._pending_requests
        )

class ServiceProxy:
    """
    服务代理类。
    """
    def __init__(self, transport: RpcTransport, serializer: Serializer, config: RpcConfig, service_name: str, pending_requests: Dict[str, asyncio.Future]) -> None:
        """
        初始化服务代理。
        :param transport: 传输层
        :param serializer: 序列化器
        :param config: RPC配置
        :param service_name: 服务名称
        :param pending_requests: 待处理请求字典
        """
        self.transport = transport
        self.serializer = serializer
        self.config = config
        self.service_name = service_name
        self._pending_requests = pending_requests
        self._method_cache: Dict[str, MethodCaller] = {}

    def __getattr__(self, method_name: str) -> Any:
        """
        动态获取方法属性。
        :param method_name: 方法名称
        :return: 方法调用器
        """
        # 检查缓存
        if method_name in self._method_cache:
            return self._method_cache[method_name]
        
        # 创建新的方法调用器并缓存
        method_caller = MethodCaller(
            transport=self.transport,
            serializer=self.serializer,
            config=self.config,
            service_name=self.service_name,
            method_name=method_name,
            pending_requests=self._pending_requests
        )
        self._method_cache[method_name] = method_caller
        return method_caller

class MethodCaller:
    """
    方法调用器。
    """
    def __init__(self, transport: RpcTransport, serializer: Serializer, config: RpcConfig, service_name: str, method_name: str, pending_requests: Dict[str, asyncio.Future]) -> None:
        """
        初始化方法调用器。
        :param transport: 传输层
        :param serializer: 序列化器
        :param config: RPC配置
        :param service_name: 服务名称
        :param method_name: 方法名称
        :param pending_requests: 待处理请求字典
        """
        self.transport = transport
        self.serializer = serializer
        self.config = config
        self.service_name = service_name
        self.method_name = method_name
        self._pending_requests = pending_requests

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """
        调用远程方法。
        :param args: 位置参数
        :param kwargs: 关键字参数
        :return: 协程对象（异步调用结果）
        """
        return self._call_async(*args, **kwargs)

    async def _call_async(self, *args: Any, **kwargs: Any) -> Any:
        """
        异步调用远程方法。
        :param args: 位置参数
        :param kwargs: 关键字参数
        :return: 远程方法调用结果
        :raises InvocationException: 调用失败
        """
        request_id = str(uuid.uuid4())
        request = {
            'method_name': self.method_name,
            'arguments': list(args),
            'kwargs': kwargs,
            'request_id': request_id
        }
        request_str = self.serializer.serialize_to_string(request)
        request_data = request_str.encode('utf-8')
        future = asyncio.Future()
        self._pending_requests[request_id] = future
        try:
            logger.debug(f"发送RPC请求: {request}")
            response_data = await self.transport.send_request(
                self.service_name, request_data
            )
            response_str = response_data.decode('utf-8')
            response = self.serializer.deserialize_from_string(response_str, dict)
            if response.get('error'):
                logger.error(f"RPC调用异常: {response['error']}")
                raise InvocationException(response['error'])
            future.set_result(response.get('result'))
            logger.debug(f"RPC调用成功: {response.get('result')}")
        except Exception as e:
            logger.exception("RPC调用失败")
            future.set_exception(InvocationException(str(e)))
        finally:
            self._pending_requests.pop(request_id, None)
        return await future 