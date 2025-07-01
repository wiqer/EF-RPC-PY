"""
RPC客户端示例
"""

import asyncio
import logging
from ef_rpc import RpcClient
from ef_rpc.transports import MqttTransport
from ef_rpc.serializers import JsonSerializer
from ef_rpc.types.mqtt import MqttOptions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main() -> None:
    """
    主函数，演示RPC客户端的基本用法。
    """
    # 创建MQTT配置
    mqtt_options = MqttOptions(
        broker_url="mqtt://localhost:1883",
        client_id="calculator-client"
    )
    
    # 创建传输层
    transport = MqttTransport(mqtt_options)
    
    # 创建序列化器
    serializer = JsonSerializer()
    
    # 创建RPC客户端
    client = RpcClient(transport, serializer)
    
    try:
        # 启动客户端
        logger.info("启动RPC客户端...")
        await client.start()
        logger.info("RPC客户端已启动")
        
        # 创建服务代理
        calculator = client.create_service("CalculatorService")
        greeting = client.create_service("GreetingService")
        
        # 测试计算器服务
        logger.info("=== 测试计算器服务 ===")
        
        # 加法测试
        result = await calculator.add(10, 20)
        logger.info(f"10 + 20 = {result}")
        
        # 乘法测试
        result = await calculator.multiply(5, 6)
        logger.info(f"5 * 6 = {result}")
        
        # 除法测试
        result = await calculator.divide(15, 3)
        logger.info(f"15 / 3 = {result}")
        
        # 测试问候服务
        logger.info("=== 测试问候服务 ===")
        
        # 问候测试
        result = await greeting.hello("世界")
        logger.info(f"问候结果: {result}")
        
        # 告别测试
        result = await greeting.goodbye("世界")
        logger.info(f"告别结果: {result}")
        
        # 错误处理测试
        logger.info("=== 测试错误处理 ===")
        try:
            result = await calculator.divide(10, 0)
            logger.info(f"10 / 0 = {result}")
        except Exception as e:
            logger.warning(f"预期的错误: {e}")
        
        # 等待一段时间
        logger.info("等待5秒...")
        await asyncio.sleep(5)
        
    except Exception as e:
        logger.error(f"客户端错误: {e}")
        
    finally:
        # 停止客户端
        logger.info("正在停止客户端...")
        await client.stop()
        logger.info("客户端已停止")


if __name__ == "__main__":
    asyncio.run(main()) 