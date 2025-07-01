"""
RPC服务器示例
"""

import asyncio
import logging
from ef_rpc import RpcServer, RpcService
from ef_rpc.transports import MqttTransport
from ef_rpc.serializers import JsonSerializer
from ef_rpc.types.mqtt import MqttOptions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@RpcService
class CalculatorService:
    """
    计算器服务
    """
    def add(self, a: int, b: int) -> int:
        """
        加法运算
        """
        result = a + b
        logger.info(f"计算: {a} + {b} = {result}")
        return result
    def multiply(self, a: int, b: int) -> int:
        """
        乘法运算
        """
        result = a * b
        logger.info(f"计算: {a} * {b} = {result}")
        return result
    def divide(self, a: int, b: int) -> float:
        """
        除法运算
        """
        if b == 0:
            raise ValueError("除数不能为零")
        result = a / b
        logger.info(f"计算: {a} / {b} = {result}")
        return result

@RpcService
class GreetingService:
    """
    问候服务
    """
    def hello(self, name: str) -> str:
        """
        问候方法
        """
        greeting = f"你好, {name}!"
        logger.info(f"问候: {greeting}")
        return greeting
    def goodbye(self, name: str) -> str:
        """
        告别方法
        """
        farewell = f"再见, {name}!"
        logger.info(f"告别: {farewell}")
        return farewell

async def main() -> None:
    """
    主函数，演示RPC服务器的基本用法。
    """
    # 创建MQTT配置
    mqtt_options = MqttOptions(
        broker_url="mqtt://localhost:1883",
        client_id="calculator-server"
    )
    # 创建传输层
    transport = MqttTransport(mqtt_options)
    # 创建序列化器
    serializer = JsonSerializer()
    # 创建RPC服务器
    server = RpcServer(transport, serializer)
    # 注册服务
    server.register_service(CalculatorService())
    server.register_service(GreetingService())
    try:
        logger.info("启动RPC服务器...")
        await server.start()
        logger.info("RPC服务器已启动")
        # 保持运行
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("正在停止服务器...")
        await server.stop()
        logger.info("服务器已停止")

if __name__ == "__main__":
    asyncio.run(main()) 