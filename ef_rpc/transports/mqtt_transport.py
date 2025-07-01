"""
MQTT传输实现
"""

import asyncio
import json
import uuid
import logging
from datetime import datetime
from typing import Dict, Optional, Callable, Any
import paho.mqtt.client as mqtt

from ..types.base import RpcTransport, RequestHandler, ConnectionException, TimeoutException
from ..types.mqtt import MqttOptions, MqttMessage

logger = logging.getLogger(__name__)

class MqttTransport(RpcTransport):
    """
    MQTT传输实现。
    实现基于MQTT协议的RPC消息收发。
    """
    def __init__(self, options: MqttOptions) -> None:
        """
        初始化MQTT传输。
        :param options: MQTT配置选项
        """
        self.options = options
        self.client: Optional[mqtt.Client] = None
        self.request_handler: Optional[RequestHandler] = None
        self.pending_requests: Dict[str, asyncio.Future] = {}
        self.is_started = False
        self.loop: Optional[asyncio.AbstractEventLoop] = None

    async def start(self) -> None:
        """
        启动MQTT传输。
        :raises ConnectionException: 连接失败
        """
        if self.is_started:
            logger.info("MQTT传输已启动，无需重复启动。")
            return
        self.loop = asyncio.get_event_loop()
        self.client = mqtt.Client(
            client_id=self.options.client_id,
            clean_session=self.options.clean_session
        )
        if self.options.username:
            self.client.username_pw_set(self.options.username, self.options.password)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
        try:
            if self.loop is None:
                logger.error("事件循环未初始化，无法执行MQTT操作。")
                raise ConnectionException("事件循环未初始化")
            if self.client is None:
                logger.error("MQTT客户端未初始化，无法执行MQTT操作。")
                raise ConnectionException("MQTT客户端未初始化")
            await self.loop.run_in_executor(
                None,
                self.client.connect,
                self.options.broker_url.replace('mqtt://', '').split(':')[0],
                int(self.options.broker_url.split(':')[-1]) if ':' in self.options.broker_url else 1883,
                self.options.connection_timeout
            )
            if self.loop is None:
                logger.error("事件循环未初始化，无法执行MQTT操作。")
                raise ConnectionException("事件循环未初始化")
            if self.client is None:
                logger.error("MQTT客户端未初始化，无法执行MQTT操作。")
                raise ConnectionException("MQTT客户端未初始化")
            await self.loop.run_in_executor(None, self.client.loop_start)
            await self._wait_for_connection()
            self.is_started = True
            logger.info(f"MQTT传输已连接到 {self.options.broker_url}")
        except Exception as e:
            logger.exception("MQTT连接失败")
            raise ConnectionException(f"MQTT连接失败: {str(e)}", e)

    async def stop(self) -> None:
        """
        停止MQTT传输。
        """
        if self.loop is None:
            logger.info("事件循环未初始化，MQTT传输未启动，无需停止。")
            return
        if self.client is None:
            logger.info("MQTT客户端未初始化，MQTT传输未启动，无需停止。")
            return
        for future in self.pending_requests.values():
            if not future.done():
                future.cancel()
        self.pending_requests.clear()
        await self.loop.run_in_executor(None, self.client.loop_stop)
        if self.client:
            await self.loop.run_in_executor(None, self.client.disconnect)
        self.is_started = False
        logger.info("MQTT传输已停止。")

    def set_request_handler(self, handler: RequestHandler) -> None:
        """
        设置请求处理器。
        :param handler: 请求处理器实例
        """
        self.request_handler = handler

    def is_connected(self) -> bool:
        """
        检查连接状态。
        :return: 是否已连接
        """
        return self.client is not None and self.client.is_connected()

    async def send_request(self, service_name: str, data: bytes) -> bytes:
        """
        发送RPC请求。
        :param service_name: 服务名
        :param data: 请求数据
        :return: 响应数据
        :raises ConnectionException: 未连接
        :raises TimeoutException: 超时
        """
        if not self.is_connected():
            logger.error("MQTT客户端未连接，无法发送请求。")
            raise ConnectionException("MQTT客户端未连接")
        correlation_id = str(uuid.uuid4())
        reply_topic = f"efrpc/reply/{correlation_id}"
        future = asyncio.Future()
        self.pending_requests[correlation_id] = future
        try:
            if self.loop is None:
                logger.error("事件循环未初始化，无法执行MQTT操作。")
                raise ConnectionException("事件循环未初始化")
            if self.client is None:
                logger.error("MQTT客户端未初始化，无法执行MQTT操作。")
                raise ConnectionException("MQTT客户端未初始化")
            await self.loop.run_in_executor(
                None,
                self.client.subscribe,
                reply_topic,
                self.options.qos
            )
            request_message = MqttMessage(
                id=str(uuid.uuid4()),
                created_at=datetime.now().isoformat(),
                msg=[data.decode('utf-8')],
                correlation_id=correlation_id,
                reply_to=reply_topic
            )
            request_topic = f"efrpc/request/{service_name}"
            request_data = json.dumps(request_message.__dict__)
            if self.loop is None:
                logger.error("事件循环未初始化，无法执行MQTT操作。")
                raise ConnectionException("事件循环未初始化")
            if self.client is None:
                logger.error("MQTT客户端未初始化，无法执行MQTT操作。")
                raise ConnectionException("MQTT客户端未初始化")
            await self.loop.run_in_executor(
                None,
                self.client.publish,
                request_topic,
                request_data,
                self.options.qos
            )
            try:
                response_data = await asyncio.wait_for(future, timeout=self.options.connect_timeout / 1000)
                logger.debug(f"收到RPC响应: {response_data}")
                return response_data.encode('utf-8')
            except asyncio.TimeoutError:
                logger.error(f"RPC请求超时: {service_name}")
                raise TimeoutException(f"RPC请求超时: {service_name}", self.options.connect_timeout)
        finally:
            self.pending_requests.pop(correlation_id, None)
            if self.loop is None:
                logger.error("事件循环未初始化，无法执行MQTT操作。")
                raise ConnectionException("事件循环未初始化")
            if self.client is None:
                logger.error("MQTT客户端未初始化，无法执行MQTT操作。")
                raise ConnectionException("MQTT客户端未初始化")
            await self.loop.run_in_executor(
                None,
                self.client.unsubscribe,
                reply_topic
            )

    async def start_server(self, service_name: str) -> None:
        """
        启动服务端模式，订阅请求主题。
        :param service_name: 服务名
        :raises ConnectionException: 未连接
        """
        if not self.is_connected():
            logger.error("MQTT客户端未连接，无法启动服务端模式。")
            raise ConnectionException("MQTT客户端未连接")
        request_topic = f"efrpc/request/{service_name}"
        if self.loop is None:
            logger.error("事件循环未初始化，无法执行MQTT操作。")
            raise ConnectionException("事件循环未初始化")
        if self.client is None:
            logger.error("MQTT客户端未初始化，无法执行MQTT操作。")
            raise ConnectionException("MQTT客户端未初始化")
        await self.loop.run_in_executor(
            None,
            self.client.subscribe,
            request_topic,
            self.options.qos
        )
        logger.info(f"服务端已订阅请求主题: {request_topic}")

    async def _wait_for_connection(self) -> None:
        """
        等待连接建立。
        :raises ConnectionException: 连接超时
        """
        for _ in range(50):
            if self.is_connected():
                return
            await asyncio.sleep(0.1)
        logger.error("MQTT连接超时")
        raise ConnectionException("MQTT连接超时")

    def _on_connect(self, client: mqtt.Client, userdata: Any, flags: Dict, rc: int) -> None:
        """
        连接回调。
        :param client: MQTT客户端
        :param userdata: 用户数据
        :param flags: 连接标志
        :param rc: 返回码
        """
        if rc == 0:
            logger.info(f"MQTT客户端已连接到 {self.options.broker_url}")
        else:
            logger.error(f"MQTT连接失败，错误码: {rc}")

    def _on_message(self, client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage) -> None:
        """
        消息回调。
        :param client: MQTT客户端
        :param userdata: 用户数据
        :param msg: 消息对象
        """
        try:
            message_str = msg.payload.decode('utf-8')
            mqtt_message = MqttMessage(**json.loads(message_str))
            logger.debug(f"收到MQTT消息: {mqtt_message}")
            # 处理回复消息或请求消息
            if mqtt_message.reply_to:
                self._handle_reply_message(mqtt_message)
            else:
                if self.loop is not None:
                    import asyncio as _asyncio
                    _asyncio.run_coroutine_threadsafe(
                        self._handle_request_message(msg.topic, mqtt_message),
                        self.loop  # 类型已保证
                    )
        except Exception as e:
            logger.exception("处理MQTT消息失败")

    def _on_disconnect(self, client: mqtt.Client, userdata: Any, rc: int) -> None:
        """
        断开连接回调。
        :param client: MQTT客户端
        :param userdata: 用户数据
        :param rc: 返回码
        """
        logger.info(f"MQTT客户端已断开连接，返回码: {rc}")

    def _handle_reply_message(self, mqtt_message: MqttMessage) -> None:
        """
        处理回复消息。
        :param mqtt_message: MQTT消息对象
        """
        future = self.pending_requests.get(mqtt_message.correlation_id)
        if future and not future.done():
            future.set_result(mqtt_message.msg[0])
            logger.debug(f"已处理回复消息: {mqtt_message}")

    async def _handle_request_message(self, topic: str, mqtt_message: MqttMessage) -> None:
        """
        处理请求消息。
        :param topic: 主题
        :param mqtt_message: MQTT消息对象
        """
        if not self.request_handler:
            logger.warning("未设置请求处理器，忽略请求消息。")
            return
        try:
            request_data = mqtt_message.msg[0].encode('utf-8')
            response_data = await self.request_handler.handle_request(topic, request_data)
            response_message = MqttMessage(
                id=str(uuid.uuid4()),
                created_at=datetime.now().isoformat(),
                msg=[response_data.decode('utf-8')],
                correlation_id=mqtt_message.correlation_id,
                reply_to=""
            )
            if self.loop is None:
                logger.error("事件循环未初始化，无法执行MQTT操作。")
                raise ConnectionException("事件循环未初始化")
            if self.client is None:
                logger.error("MQTT客户端未初始化，无法执行MQTT操作。")
                raise ConnectionException("MQTT客户端未初始化")
            await self.loop.run_in_executor(
                None,
                self.client.publish,
                mqtt_message.reply_to,
                json.dumps(response_message.__dict__),
                self.options.qos
            )
            logger.debug(f"已发送响应消息: {response_message}")
        except Exception as e:
            logger.exception("处理请求消息失败") 