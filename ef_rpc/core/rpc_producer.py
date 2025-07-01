"""
RPC生产者类
"""

import asyncio
import logging
from typing import Any, List, Type
from ..types.base import RpcConfig, RpcTransport, Serializer, RpcInvocation, InvocationException

logger = logging.getLogger(__name__)

class RpcProducer:
    """
    RPC生产者。
    负责RPC请求的发送与重试。
    """
    def __init__(self, transport: RpcTransport, serializer: Serializer,
                 config: RpcConfig, service_name: str) -> None:
        """
        初始化RPC生产者。
        :param transport: 传输层
        :param serializer: 序列化器
        :param config: RPC配置
        :param service_name: 服务名称
        """
        self.transport = transport
        self.serializer = serializer
        self.config = config
        self.service_name = service_name

    async def invoke(self, invocation: RpcInvocation) -> Any:
        """
        执行RPC调用。
        :param invocation: RPC调用信息
        :return: 调用结果
        :raises InvocationException: 调用失败
        """
        last_error = None
        for attempt in range(self.config.retry_count + 1):
            try:
                logger.debug(f"第{attempt+1}次RPC调用: {invocation}")
                return await self._do_invoke(invocation)
            except Exception as e:
                last_error = e
                logger.warning(f"RPC调用失败，准备重试: {e}")
                if attempt == self.config.retry_count:
                    break
                if not self._should_retry(e):
                    break
                await asyncio.sleep(self.config.retry_delay / 1000)
        logger.error(f"RPC调用最终失败: {last_error}")
        raise InvocationException(f"RPC调用失败: {str(last_error)}", last_error)

    async def _do_invoke(self, invocation: RpcInvocation) -> Any:
        """
        执行具体的RPC调用。
        :param invocation: RPC调用信息
        :return: 调用结果
        :raises InvocationException: 服务端错误
        """
        request_data = self.serializer.serialize_to_string(invocation.__dict__)
        response_data = await self.transport.send_request(
            invocation.service_name,
            request_data.encode('utf-8')
        )
        response_str = response_data.decode('utf-8')
        response = self.serializer.deserialize_from_string(response_str, dict)
        if 'error' in response and response['error']:
            logger.error(f"服务端错误: {response['error']}")
            raise InvocationException(f"服务端错误: {response['error']}")
        logger.debug(f"RPC调用成功: {response.get('result')}")
        return response.get('result')

    def _should_retry(self, error: Exception) -> bool:
        """
        判断是否应该重试。
        :param error: 异常对象
        :return: 是否重试
        """
        # 可根据错误类型判断是否重试，这里简单实现为全部重试
        return True 