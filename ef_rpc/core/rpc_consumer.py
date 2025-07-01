"""
RPC消费者类
"""

import logging
from typing import Any
from ..types.base import RpcConfig, RpcTransport, Serializer

logger = logging.getLogger(__name__)

class RpcConsumer:
    """
    RPC消费者。
    负责服务端消息的消费与处理。
    """
    def __init__(self, transport: RpcTransport, serializer: Serializer,
                 config: RpcConfig, service_name: str, service_instance: Any) -> None:
        """
        初始化RPC消费者。
        :param transport: 传输层
        :param serializer: 序列化器
        :param config: RPC配置
        :param service_name: 服务名称
        :param service_instance: 服务实例
        """
        self.transport = transport
        self.serializer = serializer
        self.config = config
        self.service_name = service_name
        self.service_instance = service_instance
        self.is_started = False
    
    async def start(self) -> None:
        """
        启动消费者。
        """
        if self.is_started:
            logging.info(f"消费者已启动: {self.service_name}")
            return
        
        # 启动服务端模式
        await self.transport.start_server(self.service_name)
        self.is_started = True
        logging.info(f"消费者启动成功: {self.service_name}")
    
    async def stop(self) -> None:
        """
        停止消费者。
        """
        if not self.is_started:
            logging.info(f"消费者未启动: {self.service_name}")
            return
        
        self.is_started = False 
        logging.info(f"消费者已停止: {self.service_name}") 