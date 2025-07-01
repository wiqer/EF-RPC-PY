#!/usr/bin/env python3
"""
EF-RPC-PY 框架测试脚本
"""

import asyncio
import time
import logging
from ef_rpc import RpcClient, RpcServer, RpcService
from ef_rpc.transports import MqttTransport
from ef_rpc.serializers import JsonSerializer
from ef_rpc.types.mqtt import MqttOptions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@RpcService
class TestService:
    """
    测试服务
    """
    def echo(self, message: str) -> str:
        """
        回显消息
        """
        return f"Echo: {message}"
    def add(self, a: int, b: int) -> int:
        """
        加法运算
        """
        return a + b
    def get_timestamp(self) -> float:
        """
        获取当前时间戳
        """
        return time.time()

async def run_server() -> None:
    """
    启动测试服务端。
    """
    logger.info("启动测试服务端...")
    mqtt_options = MqttOptions(
        broker_url="mqtt://localhost:1883",
        client_id="test-server"
    )
    transport = MqttTransport(mqtt_options)
    serializer = JsonSerializer()
    server = RpcServer(transport, serializer)
    server.register_service(TestService())
    try:
        await server.start()
        logger.info("测试服务端已启动")
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("正在停止服务端...")
        await server.stop()
        logger.info("服务端已停止")

async def run_client() -> None:
    """
    启动测试客户端。
    """
    logger.info("启动测试客户端...")
    mqtt_options = MqttOptions(
        broker_url="mqtt://localhost:1883",
        client_id="test-client"
    )
    transport = MqttTransport(mqtt_options)
    serializer = JsonSerializer()
    client = RpcClient(transport, serializer)
    try:
        await client.start()
        logger.info("测试客户端已启动")
        test_service = client.create_service("TestService")
        logger.info("=== 测试RPC调用 ===")
        result = await test_service.echo("Hello, EF-RPC!")
        logger.info(f"Echo结果: {result}")
        result = await test_service.add(10, 20)
        logger.info(f"加法结果: 10 + 20 = {result}")
        result = await test_service.get_timestamp()
        logger.info(f"时间戳: {result}")
        logger.info("所有测试完成!")
    except Exception as e:
        logger.error(f"客户端错误: {e}")
    finally:
        await client.stop()
        logger.info("客户端已停止")

async def main() -> None:
    """
    主函数，根据命令行参数选择运行服务端或客户端。
    """
    import sys
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        if mode == "server":
            await run_server()
        elif mode == "client":
            await run_client()
        else:
            logger.info("用法: python test_framework.py [server|client]")
    else:
        logger.info("用法: python test_framework.py [server|client]")
        logger.info("请先启动MQTT Broker (如 mosquitto)")

if __name__ == "__main__":
    asyncio.run(main()) 