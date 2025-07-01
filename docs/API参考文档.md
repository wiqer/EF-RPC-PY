# EF-RPC-PY API参考文档

## 1. 核心类

### 1.1 RpcClient

RPC客户端，用于创建服务代理并管理客户端生命周期。

#### 构造函数

```python
RpcClient(
    transport: RpcTransport,
    serializer: Serializer,
    config: Optional[RpcConfig] = None
)
```

**参数:**
- `transport`: 传输层实现
- `serializer`: 序列化器
- `config`: RPC配置，可选

#### 方法

##### start()

启动客户端。

```python
async def start() -> None
```

**说明:**
- 启动传输层连接
- 初始化客户端状态

##### stop()

停止客户端。

```python
async def stop() -> None
```

**说明:**
- 关闭传输层连接
- 清理资源

##### create_service(service_name)

创建服务代理。

```python
def create_service(self, service_name: str) -> Any
```

**参数:**
- `service_name`: 服务名称

**返回:**
- 服务代理对象

**说明:**
- 如果服务代理已存在，返回缓存的代理
- 否则创建新的代理对象

##### is_connected()

检查连接状态。

```python
def is_connected(self) -> bool
```

**返回:**
- 连接状态

### 1.2 RpcServer

RPC服务器，用于注册服务并处理客户端请求。

#### 构造函数

```python
RpcServer(
    transport: RpcTransport,
    serializer: Serializer,
    config: Optional[RpcConfig] = None
)
```

**参数:**
- `transport`: 传输层实现
- `serializer`: 序列化器
- `config`: RPC配置，可选

#### 方法

##### register_service(service_instance, service_name)

注册服务。

```python
def register_service(
    self,
    service_instance: Any,
    service_name: Optional[str] = None
) -> None
```

**参数:**
- `service_instance`: 服务实例
- `service_name`: 服务名称，如果不指定则使用类名

##### start()

启动服务器。

```python
async def start() -> None
```

**说明:**
- 设置请求处理器
- 启动传输层
- 为每个服务启动消费者

##### stop()

停止服务器。

```python
async def stop() -> None
```

**说明:**
- 停止所有消费者
- 停止传输层

##### is_running()

检查服务器是否运行。

```python
def is_running(self) -> bool
```

**返回:**
- 服务器运行状态

## 2. 传输层

### 2.1 RpcTransport

传输层抽象接口。

#### 方法

##### start()

启动传输。

```python
async def start() -> None
```

##### stop()

停止传输。

```python
async def stop() -> None
```

##### send_request(service_name, data)

发送请求。

```python
async def send_request(self, service_name: str, data: bytes) -> bytes
```

**参数:**
- `service_name`: 服务名称
- `data`: 请求数据

**返回:**
- 响应数据

##### is_connected()

检查连接状态。

```python
def is_connected(self) -> bool
```

##### start_server(service_name)

启动服务端模式。

```python
async def start_server(self, service_name: str) -> None
```

**参数:**
- `service_name`: 服务名称

### 2.2 MqttTransport

MQTT传输实现。

#### 构造函数

```python
MqttTransport(options: MqttOptions)
```

**参数:**
- `options`: MQTT配置选项

#### 方法

##### set_request_handler(handler)

设置请求处理器。

```python
def set_request_handler(self, handler: RequestHandler) -> None
```

**参数:**
- `handler`: 请求处理器

## 3. 序列化器

### 3.1 Serializer

序列化器抽象接口。

#### 方法

##### serialize(obj)

序列化对象为字节数组。

```python
def serialize(self, obj: Any) -> bytes
```

**参数:**
- `obj`: 要序列化的对象

**返回:**
- 序列化后的字节数组

##### deserialize(data, target_type)

从字节数组反序列化对象。

```python
def deserialize(self, data: bytes, target_type: Type) -> Any
```

**参数:**
- `data`: 字节数组
- `target_type`: 目标类型

**返回:**
- 反序列化后的对象

##### serialize_to_string(obj)

序列化对象为字符串。

```python
def serialize_to_string(self, obj: Any) -> str
```

**参数:**
- `obj`: 要序列化的对象

**返回:**
- 序列化后的字符串

##### deserialize_from_string(data, target_type)

从字符串反序列化对象。

```python
def deserialize_from_string(self, data: str, target_type: Type) -> Any
```

**参数:**
- `data`: 字符串
- `target_type`: 目标类型

**返回:**
- 反序列化后的对象

### 3.2 JsonSerializer

JSON序列化器实现。

#### 构造函数

```python
JsonSerializer(
    ensure_ascii: bool = False,
    indent: Optional[int] = None
)
```

**参数:**
- `ensure_ascii`: 是否确保ASCII编码
- `indent`: 缩进空格数

## 4. 类型定义

### 4.1 RpcConfig

RPC配置类。

```python
@dataclass
class RpcConfig:
    version: str = "1.0"           # 版本号
    timeout: int = 30000           # 超时时间(毫秒)
    retry_count: int = 3           # 重试次数
    retry_delay: int = 1000        # 重试延迟(毫秒)
```

### 4.2 RpcInvocation

RPC调用信息。

```python
@dataclass
class RpcInvocation:
    service_name: str              # 服务名称
    method_name: str               # 方法名称
    arguments: List[Any]           # 参数列表
    argument_types: List[Type]     # 参数类型
    return_type: Type              # 返回类型
    version: str = "1.0"           # 版本号
    correlation_id: Optional[str] = None  # 关联ID
```

### 4.3 MqttOptions

MQTT配置选项。

```python
@dataclass
class MqttOptions:
    broker_url: str                # Broker URL
    client_id: str                 # 客户端ID
    username: Optional[str] = None # 用户名
    password: Optional[str] = None # 密码
    keep_alive_interval: int = 60  # 保活间隔
    connection_timeout: int = 30   # 连接超时
    clean_session: bool = True     # 清理会话
    max_inflight: int = 1000       # 最大飞行消息数
    qos: int = 1                   # 服务质量
    reconnect_period: int = 1000   # 重连周期
    connect_timeout: int = 30000   # 连接超时
```

### 4.4 MqttMessage

MQTT消息格式。

```python
@dataclass
class MqttMessage:
    id: str                        # 消息ID
    create_date: str               # 创建时间
    msg: List[Any]                 # 消息内容
    correlation_id: str            # 关联ID
    reply_to: str                  # 回复主题
    metadata: Optional[Dict[str, Any]] = None  # 元数据
```

## 5. 异常类

### 5.1 RpcException

RPC异常基类。

```python
class RpcException(Exception):
    def __init__(self, message: str, cause: Optional[Exception] = None):
        super().__init__(message)
        self.cause = cause
```

### 5.2 ConnectionException

连接异常。

```python
class ConnectionException(RpcException):
    pass
```

### 5.3 TimeoutException

超时异常。

```python
class TimeoutException(RpcException):
    def __init__(self, message: str, timeout_ms: int):
        super().__init__(f"{message} (超时: {timeout_ms}ms)")
        self.timeout_ms = timeout_ms
```

### 5.4 SerializationException

序列化异常。

```python
class SerializationException(RpcException):
    pass
```

### 5.5 InvocationException

调用异常。

```python
class InvocationException(RpcException):
    pass
```

## 6. 装饰器

### 6.1 RpcService

RPC服务装饰器。

```python
def RpcService(cls: Type[T]) -> Type[T]:
    """
    RPC服务装饰器
    
    用于标记RPC服务类，使其可以被RPC服务器注册和管理
    
    Args:
        cls: 要装饰的类
        
    Returns:
        装饰后的类
    """
```

**使用示例:**
```python
@RpcService
class CalculatorService:
    def add(self, a: int, b: int) -> int:
        return a + b
```

## 7. 核心组件

### 7.1 RpcProducer

RPC生产者，负责执行RPC调用。

#### 构造函数

```python
RpcProducer(
    transport: RpcTransport,
    serializer: Serializer,
    config: RpcConfig,
    service_name: str
)
```

#### 方法

##### invoke(invocation)

执行RPC调用。

```python
async def invoke(self, invocation: RpcInvocation) -> Any
```

**参数:**
- `invocation`: RPC调用信息

**返回:**
- 调用结果

### 7.2 RpcConsumer

RPC消费者，负责处理RPC请求。

#### 构造函数

```python
RpcConsumer(
    transport: RpcTransport,
    serializer: Serializer,
    config: RpcConfig,
    service_name: str,
    service_instance: Any
)
```

#### 方法

##### start()

启动消费者。

```python
async def start() -> None
```

##### stop()

停止消费者。

```python
async def stop() -> None
```

### 7.3 ProxyFactory

代理工厂，负责创建服务代理。

#### 构造函数

```python
ProxyFactory(
    transport: RpcTransport,
    serializer: Serializer,
    config: RpcConfig,
    service_name: str
)
```

#### 方法

##### create_proxy()

创建服务代理。

```python
def create_proxy(self) -> Any
```

**返回:**
- 服务代理对象

## 8. 请求处理器

### 8.1 RequestHandler

请求处理器抽象接口。

#### 方法

##### handle_request(service_name, data)

处理请求。

```python
async def handle_request(self, service_name: str, data: bytes) -> bytes
```

**参数:**
- `service_name`: 服务名称
- `data`: 请求数据

**返回:**
- 响应数据

### 8.2 ServerRequestHandler

服务器请求处理器实现。

#### 构造函数

```python
ServerRequestHandler(
    services: Dict[str, Any],
    serializer: Serializer,
    config: RpcConfig
)
```

## 9. 使用示例

### 9.1 基本使用

```python
import asyncio
from ef_rpc import RpcClient, RpcServer, RpcService
from ef_rpc.transports import MqttTransport
from ef_rpc.serializers import JsonSerializer
from ef_rpc.types.mqtt import MqttOptions

# 定义服务
@RpcService
class CalculatorService:
    def add(self, a: int, b: int) -> int:
        return a + b

# 服务器端
async def server_main():
    mqtt_options = MqttOptions(
        broker_url="mqtt://localhost:1883",
        client_id="calculator-server"
    )
    
    transport = MqttTransport(mqtt_options)
    serializer = JsonSerializer()
    server = RpcServer(transport, serializer)
    
    server.register_service(CalculatorService())
    
    await server.start()
    
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await server.stop()

# 客户端
async def client_main():
    mqtt_options = MqttOptions(
        broker_url="mqtt://localhost:1883",
        client_id="calculator-client"
    )
    
    transport = MqttTransport(mqtt_options)
    serializer = JsonSerializer()
    client = RpcClient(transport, serializer)
    
    await client.start()
    
    calculator = client.create_service("CalculatorService")
    result = await calculator.add(10, 20)
    print(f"10 + 20 = {result}")
    
    await client.stop()

# 运行
if __name__ == "__main__":
    # 启动服务器
    asyncio.run(server_main())
    
    # 启动客户端
    asyncio.run(client_main())
```

### 9.2 自定义配置

```python
from ef_rpc.types.base import RpcConfig

# 创建自定义配置
config = RpcConfig(
    version="1.0",
    timeout=60000,      # 60秒超时
    retry_count=5,      # 重试5次
    retry_delay=2000    # 2秒重试延迟
)

# 使用自定义配置
client = RpcClient(transport, serializer, config)
server = RpcServer(transport, serializer, config)
```

### 9.3 错误处理

```python
from ef_rpc.types.base import (
    ConnectionException,
    TimeoutException,
    InvocationException
)

try:
    result = await calculator.add(10, 20)
except ConnectionException as e:
    print(f"连接错误: {e}")
except TimeoutException as e:
    print(f"超时错误: {e}")
except InvocationException as e:
    print(f"调用错误: {e}")
```

## 10. 最佳实践

### 10.1 配置管理

```python
import os
from ef_rpc.types.mqtt import MqttOptions

# 从环境变量读取配置
mqtt_options = MqttOptions(
    broker_url=os.getenv("MQTT_BROKER_URL", "mqtt://localhost:1883"),
    client_id=os.getenv("MQTT_CLIENT_ID", "ef-rpc-client"),
    username=os.getenv("MQTT_USERNAME"),
    password=os.getenv("MQTT_PASSWORD")
)
```

### 10.2 连接管理

```python
import asyncio
from contextlib import asynccontextmanager

@asynccontextmanager
async def rpc_client_context():
    """RPC客户端上下文管理器"""
    client = RpcClient(transport, serializer)
    try:
        await client.start()
        yield client
    finally:
        await client.stop()

# 使用上下文管理器
async def main():
    async with rpc_client_context() as client:
        calculator = client.create_service("CalculatorService")
        result = await calculator.add(10, 20)
        print(f"结果: {result}")
```

### 10.3 服务注册

```python
# 自动发现和注册服务
def auto_register_services(server: RpcServer, module_name: str):
    """自动注册模块中的所有RPC服务"""
    import importlib
    import inspect
    
    module = importlib.import_module(module_name)
    
    for name, obj in inspect.getmembers(module):
        if (inspect.isclass(obj) and 
            hasattr(obj, '_is_rpc_service') and 
            obj._is_rpc_service):
            server.register_service(obj())

# 使用自动注册
auto_register_services(server, "my_services")
```

### 10.4 监控和日志

```python
import logging
import time
from functools import wraps

def monitor_rpc_calls(func):
    """RPC调用监控装饰器"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            logging.info(f"RPC调用成功: {func.__name__}, 耗时: {duration:.3f}秒")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logging.error(f"RPC调用失败: {func.__name__}, 耗时: {duration:.3f}秒, 错误: {e}")
            raise
    return wrapper

# 使用监控装饰器
@monitor_rpc_calls
async def monitored_call():
    calculator = client.create_service("CalculatorService")
    return await calculator.add(10, 20)
``` 