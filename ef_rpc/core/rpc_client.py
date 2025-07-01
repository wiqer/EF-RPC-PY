"""
RPC客户端核心类
"""

import asyncio
import logging
from typing import Any, Dict, Type, TypeVar, Optional
from ..types.base import RpcConfig, RpcTransport, Serializer, InvocationException
from .proxy_factory import ProxyFactory

T = TypeVar('T')

logger = logging.getLogger(__name__)

class RpcClient:
    """
    RPC客户端。
    管理传输、序列化、服务代理等。
    """
    def __init__(self, transport: RpcTransport, serializer: Serializer, config: Optional[RpcConfig] = None) -> None:
        """
        初始化RPC客户端。
        :param transport: 传输层实现
        :param serializer: 序列化器
        :param config: RPC配置
        """
        self.transport = transport
        self.serializer = serializer
        self.config = config or RpcConfig()
        self.is_started = False
        self.services: Dict[str, Any] = {}

    async def start(self) -> None:
        """
        启动客户端。
        :raises ConnectionException: 启动失败
        """
        if self.is_started:
            logger.info("客户端已启动，无需重复启动。")
            return
        await self.transport.start()
        self.is_started = True
        logger.info("RPC客户端启动成功。")

    async def stop(self) -> None:
        """
        停止客户端。
        """
        if not self.is_started:
            logger.info("客户端未启动，无需停止。")
            return
        await self.transport.stop()
        self.is_started = False
        logger.info("RPC客户端已停止。")

    def create_service(self, service_name: str) -> Any:
        """
        创建服务代理。
        :param service_name: 服务名称
        :return: 服务代理对象
        :raises RuntimeError: 客户端未启动
        """
        if not self.is_started:
            logger.error("客户端未启动，无法创建服务代理。")
            raise RuntimeError("客户端未启动")
        if service_name in self.services:
            return self.services[service_name]
        # 创建代理工厂
        proxy_factory = ProxyFactory(
            transport=self.transport,
            serializer=self.serializer,
            config=self.config,
            service_name=service_name
        )
        # 创建服务代理
        service_proxy = proxy_factory.create_proxy()
        self.services[service_name] = service_proxy
        logger.info(f"服务代理已创建: {service_name}")
        return service_proxy

    def is_connected(self) -> bool:
        """
        检查连接状态。
        :return: 是否已连接
        """
        return self.transport.is_connected() 