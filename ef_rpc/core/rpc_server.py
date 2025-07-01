"""
RPC服务器核心类
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from ..types.base import RpcConfig, RpcTransport, Serializer, RequestHandler
from .rpc_consumer import RpcConsumer

logger = logging.getLogger(__name__)

class RpcServer:
    """
    RPC服务器。
    管理服务注册、启动、停止等。
    """
    def __init__(self, transport: RpcTransport, serializer: Serializer, config: Optional[RpcConfig] = None) -> None:
        """
        初始化RPC服务器。
        :param transport: 传输层实现
        :param serializer: 序列化器
        :param config: RPC配置
        """
        self.transport = transport
        self.serializer = serializer
        self.config = config or RpcConfig()
        self.services: Dict[str, Any] = {}
        self.consumers: List[RpcConsumer] = []
        self.is_started = False

    def register_service(self, service_instance: Any, service_name: Optional[str] = None) -> None:
        """
        注册服务。
        :param service_instance: 服务实例
        :param service_name: 服务名称，未指定则用类名
        """
        if service_name is None:
            service_name = service_instance.__class__.__name__
        # 确保 service_name 不为 None
        assert service_name is not None
        self.services[service_name] = service_instance
        logger.info(f"服务已注册: {service_name}")

    async def start(self) -> None:
        """
        启动服务器。
        """
        if self.is_started:
            logger.info("服务器已启动，无需重复启动。")
            return
        self.transport.set_request_handler(ServerRequestHandler(
            services=self.services,
            serializer=self.serializer,
            config=self.config
        ))
        await self.transport.start()
        for service_name, service_instance in self.services.items():
            consumer = RpcConsumer(
                transport=self.transport,
                serializer=self.serializer,
                config=self.config,
                service_name=service_name,
                service_instance=service_instance
            )
            await consumer.start()
            self.consumers.append(consumer)
            logger.info(f"服务消费者已启动: {service_name}")
        self.is_started = True
        logger.info("RPC服务器启动成功。")

    async def stop(self) -> None:
        """
        停止服务器。
        """
        if not self.is_started:
            logger.info("服务器未启动，无需停止。")
            return
        for consumer in self.consumers:
            await consumer.stop()
        self.consumers.clear()
        await self.transport.stop()
        self.is_started = False
        logger.info("RPC服务器已停止。")

    def is_running(self) -> bool:
        """
        检查服务器是否运行。
        :return: 是否已启动
        """
        return self.is_started

class ServerRequestHandler(RequestHandler):
    """
    服务器请求处理器。
    """
    def __init__(self, services: Dict[str, Any], serializer: Serializer, config: RpcConfig) -> None:
        """
        初始化请求处理器。
        :param services: 服务字典
        :param serializer: 序列化器
        :param config: RPC配置
        """
        self.services = services
        self.serializer = serializer
        self.config = config

    async def handle_request(self, service_name: str, data: bytes) -> bytes:
        """
        处理请求。
        :param service_name: 服务名称
        :param data: 请求数据
        :return: 响应数据
        """
        try:
            request_str = data.decode('utf-8')
            request = self.serializer.deserialize_from_string(request_str, dict)
            service_instance = self.services.get(service_name)
            if not service_instance:
                logger.error(f"服务不存在: {service_name}")
                return self._create_error_response(f"服务不存在: {service_name}")
            method_name = request.get('method_name')
            if not method_name:
                logger.error("缺少方法名称")
                return self._create_error_response("缺少方法名称")
            method = getattr(service_instance, method_name, None)
            if not method or not callable(method):
                logger.error(f"方法不存在: {method_name}")
                return self._create_error_response(f"方法不存在: {method_name}")
            arguments = request.get('arguments', [])
            result = method(*arguments)
            response = {
                'result': result,
                'error': None
            }
            response_str = self.serializer.serialize_to_string(response)
            logger.debug(f"服务调用成功: {service_name}.{method_name} -> {result}")
            return response_str.encode('utf-8')
        except Exception as e:
            logger.exception("处理请求失败")
            return self._create_error_response(f"处理请求失败: {str(e)}")

    def _create_error_response(self, error_message: str) -> bytes:
        """
        创建错误响应。
        :param error_message: 错误信息
        :return: 错误响应字节
        """
        response = {
            'result': None,
            'error': error_message
        }
        response_str = self.serializer.serialize_to_string(response)
        return response_str.encode('utf-8') 