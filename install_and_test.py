#!/usr/bin/env python3
"""
EF-RPC-PY 安装和测试脚本
"""

import subprocess
import sys
import os
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_command(command: str, description: str) -> bool:
    """
    运行命令并处理错误。
    :param command: shell命令
    :param description: 操作描述
    :return: 是否成功
    """
    logger.info(f"{description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        logger.info(f"✓ {description} 成功")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"✗ {description} 失败")
        logger.error(f"错误: {e.stderr}")
        return False

def check_python_version() -> bool:
    """
    检查Python版本。
    :return: 是否满足要求
    """
    logger.info("检查Python版本...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        logger.error(f"✗ Python版本过低: {version.major}.{version.minor}")
        logger.error("需要Python 3.8或更高版本")
        return False
    else:
        logger.info(f"✓ Python版本: {version.major}.{version.minor}.{version.micro}")
        return True

def install_dependencies() -> bool:
    """
    安装依赖。
    :return: 是否成功
    """
    logger.info("安装项目依赖...")
    if not Path("requirements.txt").exists():
        logger.error("✗ requirements.txt 文件不存在")
        return False
    return run_command("python3 -m pip install -r requirements.txt", "安装Python依赖")

def install_package() -> bool:
    """
    安装包。
    :return: 是否成功
    """
    logger.info("安装EF-RPC-PY包...")
    return run_command("python3 -m pip install -e . --user", "安装EF-RPC-PY包")

def test_imports() -> bool:
    """
    测试模块导入。
    :return: 是否成功
    """
    logger.info("测试模块导入...")
    try:
        import ef_rpc
        logger.info("✓ 成功导入 ef_rpc")
        from ef_rpc import RpcClient, RpcServer, RpcService
        logger.info("✓ 成功导入核心类")
        from ef_rpc.transports import MqttTransport
        logger.info("✓ 成功导入传输层")
        from ef_rpc.serializers import JsonSerializer
        logger.info("✓ 成功导入序列化器")
        from ef_rpc.types.mqtt import MqttOptions
        logger.info("✓ 成功导入类型定义")
        return True
    except ImportError as e:
        logger.error(f"✗ 导入失败: {e}")
        return False

def test_basic_functionality() -> bool:
    """
    测试基本功能。
    :return: 是否成功
    """
    logger.info("测试基本功能...")
    try:
        from ef_rpc import RpcService
        from ef_rpc.types.mqtt import MqttOptions
        from ef_rpc.serializers import JsonSerializer
        @RpcService
        class TestService:
            def test_method(self):
                return "test"
        options = MqttOptions(
            broker_url="mqtt://localhost:1883",
            client_id="test"
        )
        serializer = JsonSerializer()
        data = {"test": "value"}
        serialized = serializer.serialize_to_string(data)
        deserialized = serializer.deserialize_from_string(serialized, dict)
        assert deserialized == data
        logger.info("✓ 基本功能测试通过")
        return True
    except Exception as e:
        logger.error(f"✗ 基本功能测试失败: {e}")
        return False

def check_mqtt_broker() -> bool:
    """
    检查MQTT Broker。
    :return: 是否可用
    """
    logger.info("检查MQTT Broker...")
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 1883))
        sock.close()
        if result == 0:
            logger.info("✓ MQTT Broker 正在运行 (localhost:1883)")
            return True
        else:
            logger.warning("⚠ MQTT Broker 未运行")
            logger.warning("请启动MQTT Broker:")
            logger.warning("  docker run -d --name mosquitto -p 1883:1883 eclipse-mosquitto")
            logger.warning("  或者安装并启动 mosquitto")
            return False
    except Exception as e:
        logger.error(f"✗ 检查MQTT Broker失败: {e}")
        return False

def main() -> None:
    """
    主函数，执行安装和测试流程。
    """
    logger.info("=" * 50)
    logger.info("EF-RPC-PY 安装和测试")
    logger.info("=" * 50)
    if not check_python_version():
        sys.exit(1)
    if not install_dependencies():
        logger.error("请检查网络连接和pip配置")
        sys.exit(1)
    if not install_package():
        logger.error("请检查setup.py配置")
        sys.exit(1)
    if not test_imports():
        logger.error("请检查代码结构和依赖")
        sys.exit(1)
    if not test_basic_functionality():
        logger.error("请检查代码实现")
        sys.exit(1)
    mqtt_available = check_mqtt_broker()
    logger.info("=" * 50)
    logger.info("安装和测试完成!")
    logger.info("=" * 50)
    if mqtt_available:
        logger.info("✓ 所有测试通过!")
        logger.info("现在可以运行示例:")
        logger.info("  python examples/server_example.py")
        logger.info("  python examples/client_example.py")
        logger.info("  python test_framework.py server")
        logger.info("  python test_framework.py client")
    else:
        logger.warning("⚠ 基本功能正常，但需要启动MQTT Broker才能运行完整示例")
    logger.info("详细使用说明请参考 USAGE.md")

if __name__ == "__main__":
    main() 