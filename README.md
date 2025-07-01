# EF-RPC-PY

基于MQTT协议的Python RPC框架，提供高性能、易用的分布式服务调用解决方案。

## 特性

- 🚀 **高性能**: 基于MQTT协议，支持异步调用
- 🔧 **易用性**: 简洁的API设计，支持装饰器模式
- 🔌 **可扩展**: 支持多种序列化方式和传输协议
- 🛡️ **可靠性**: 内置重试机制和错误处理
- 📦 **轻量级**: 最小化依赖，快速部署

## 快速开始

### 安装

```bash
pip install ef-rpc-py
```

### 基本使用

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
    
    def multiply(self, a: int, b: int) -> int:
        return a * b

# 服务端
async def run_server():
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
async def run_client():
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
    # 先启动服务端
    asyncio.run(run_server())
    # 再启动客户端
    asyncio.run(run_client())
```

## 测试

项目包含完整的单元测试套件，使用 pytest 框架：

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_core_mock.py

# 运行带详细输出的测试
pytest -v

# 运行特定测试类
pytest tests/test_client_server_mock.py::TestRpcClient

# 运行特定测试方法
pytest tests/test_serializer_mock.py::TestJsonSerializer::test_basic_types
```

### 测试覆盖范围

- **核心功能测试** (`test_core_mock.py`): 基础序列化、装饰器、客户端服务端生命周期
- **客户端服务端测试** (`test_client_server_mock.py`): 完整的客户端服务端交互测试
- **代理工厂测试** (`test_proxy_factory_mock.py`): 动态代理创建和方法调用
- **序列化器测试** (`test_serializer_mock.py`): JSON序列化的各种场景
- **边界情况测试** (`test_edge_cases_mock.py`): 异常处理、性能测试、错误场景

### 测试特点

- 使用 Mock 对象，无需真实 MQTT Broker
- 异步测试支持
- 完整的错误场景覆盖
- 性能边界测试
- 并发测试

## 开发

### 环境设置

```bash
# 克隆仓库
git clone https://github.com/ef-rpc/ef-rpc-py.git
cd ef-rpc-py

# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 代码格式化
black ef_rpc/ tests/

# 类型检查
mypy ef_rpc/
```

### 项目结构

```
ef-rpc-py/
├── ef_rpc/                 # 主包
│   ├── core/              # 核心组件
│   ├── decorators/        # 装饰器
│   ├── serializers/       # 序列化器
│   ├── transports/        # 传输层
│   └── types/             # 类型定义
├── tests/                 # 测试套件
│   ├── test_core_mock.py
│   ├── test_client_server_mock.py
│   ├── test_proxy_factory_mock.py
│   ├── test_serializer_mock.py
│   └── test_edge_cases_mock.py
├── examples/              # 示例代码
├── docs/                  # 文档
└── requirements.txt       # 依赖
```

## 贡献

欢迎贡献代码！请遵循以下步骤：

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

### 开发规范

- 遵循 PEP 8 代码风格
- 添加类型注解
- 编写单元测试
- 更新文档

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 联系方式

- 项目主页: https://github.com/ef-rpc/ef-rpc-py
- 问题反馈: https://github.com/ef-rpc/ef-rpc-py/issues
- 邮箱: team@ef-rpc.com 