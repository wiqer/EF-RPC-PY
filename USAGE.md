# EF-RPC-PY 使用指南

## 概述

EF-RPC-PY 是一个基于MQTT协议的Python RPC框架，提供高性能、易用的分布式服务调用解决方案。

## 安装

### 依赖要求

- Python 3.7+
- MQTT Broker (如 Mosquitto)

### 安装依赖

```bash
pip install -r requirements.txt
```

### 启动MQTT Broker

```bash
# 使用Docker启动Mosquitto
docker run -d --name mosquitto -p 1883:1883 -p 9001:9001 eclipse-mosquitto

# 或者使用系统包管理器
# Ubuntu/Debian
sudo apt-get install mosquitto mosquitto-clients

# macOS
brew install mosquitto

# 启动服务
mosquitto
```

## 快速开始

### 1. 定义RPC服务

```python
from ef_rpc import RpcService

@RpcService
class CalculatorService:
    def add(self, a: int, b: int) -> int:
        return a + b
    
    def multiply(self, a: int, b: int) -> int:
        return a * b
    
    def divide(self, a: int, b: int) -> float:
        if b == 0:
            raise ValueError("除数不能为零")
        return a / b
```

### 2. 启动RPC服务器

```python
import asyncio
from ef_rpc import RpcServer
from ef_rpc.transports import MqttTransport
from ef_rpc.serializers import JsonSerializer
from ef_rpc.types.mqtt import MqttOptions

async def main():
    # 创建MQTT配置
    mqtt_options = MqttOptions(
        broker_url="mqtt://localhost:1883",
        client_id="calculator-server"
    )
    
    # 创建传输层和序列化器
    transport = MqttTransport(mqtt_options)
    serializer = JsonSerializer()
    
    # 创建RPC服务器
    server = RpcServer(transport, serializer)
    
    # 注册服务
    server.register_service(CalculatorService())
    
    # 启动服务器
    await server.start()
    print("RPC服务器已启动")
    
    # 保持运行
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await server.stop()
        print("服务器已停止")

if __name__ == "__main__":
    asyncio.run(main())
```

### 3. 创建RPC客户端

```python
import asyncio
from ef_rpc import RpcClient
from ef_rpc.transports import MqttTransport
from ef_rpc.serializers import JsonSerializer
from ef_rpc.types.mqtt import MqttOptions

async def main():
    # 创建MQTT配置
    mqtt_options = MqttOptions(
        broker_url="mqtt://localhost:1883",
        client_id="calculator-client"
    )
    
    # 创建传输层和序列化器
    transport = MqttTransport(mqtt_options)
    serializer = JsonSerializer()
    
    # 创建RPC客户端
    client = RpcClient(transport, serializer)
    
    # 启动客户端
    await client.start()
    
    # 创建服务代理
    calculator = client.create_service("CalculatorService")
    
    # 调用远程方法
    result = await calculator.add(10, 20)
    print(f"10 + 20 = {result}")
    
    result = await calculator.multiply(5, 6)
    print(f"5 * 6 = {result}")
    
    # 停止客户端
    await client.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

## 配置选项

### MQTT配置

```python
from ef_rpc.types.mqtt import MqttOptions

mqtt_options = MqttOptions(
    broker_url="mqtt://localhost:1883",  # MQTT Broker地址
    client_id="my-client",               # 客户端ID
    username="user",                     # 用户名（可选）
    password="pass",                     # 密码（可选）
    keep_alive_interval=60,              # 保活间隔（秒）
    connection_timeout=30,               # 连接超时（秒）
    clean_session=True,                  # 清理会话
    max_inflight=1000,                   # 最大飞行消息数
    qos=1,                              # 服务质量
    reconnect_period=1000,               # 重连间隔（毫秒）
    connect_timeout=30000                # 连接超时（毫秒）
)
```

### RPC配置

```python
from ef_rpc.types.base import RpcConfig

config = RpcConfig(
    version="1.0",        # 协议版本
    timeout=30000,        # 超时时间（毫秒）
    retry_count=3,        # 重试次数
    retry_delay=1000      # 重试延迟（毫秒）
)
```

## 高级功能

### 自定义序列化器

```python
from ef_rpc.serializers.base import BaseSerializer
import pickle

class PickleSerializer(BaseSerializer):
    def _serialize_impl(self, obj):
        return pickle.dumps(obj)
    
    def _deserialize_impl(self, data, target_type):
        return pickle.loads(data)
    
    def _serialize_to_string_impl(self, obj):
        return pickle.dumps(obj).decode('latin1')
    
    def _deserialize_from_string_impl(self, data, target_type):
        return pickle.loads(data.encode('latin1'))

# 使用自定义序列化器
serializer = PickleSerializer()
```

### 错误处理

```python
from ef_rpc.types.base import RpcException, TimeoutException

try:
    result = await calculator.divide(10, 0)
except ValueError as e:
    print(f"业务逻辑错误: {e}")
except TimeoutException as e:
    print(f"请求超时: {e}")
except RpcException as e:
    print(f"RPC错误: {e}")
```

### 异步方法支持

```python
@RpcService
class AsyncService:
    async def async_method(self, data: str) -> str:
        # 模拟异步操作
        await asyncio.sleep(1)
        return f"处理完成: {data}"
```

## 测试

### 运行测试脚本

```bash
# 启动服务器
python test_framework.py server

# 在另一个终端启动客户端
python test_framework.py client
```

### 运行示例

```bash
# 启动服务器示例
python examples/server_example.py

# 启动客户端示例
python examples/client_example.py
```

## 最佳实践

1. **服务命名**: 使用有意义的服务名称，避免冲突
2. **错误处理**: 在服务方法中抛出有意义的异常
3. **超时设置**: 根据业务需求设置合适的超时时间
4. **连接管理**: 确保客户端和服务器正确启动和停止
5. **日志记录**: 在生产环境中添加适当的日志记录

## 故障排除

### 常见问题

1. **连接失败**: 检查MQTT Broker是否运行，网络连接是否正常
2. **超时错误**: 增加超时时间或检查网络延迟
3. **序列化错误**: 确保传递的数据可以被序列化
4. **服务未找到**: 检查服务名称是否正确注册

### 调试技巧

1. 启用MQTT客户端日志
2. 使用MQTT客户端工具（如MQTT Explorer）监控消息
3. 检查网络连接和防火墙设置

## 许可证

MIT License 