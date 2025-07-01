#!/usr/bin/env python3
"""
客户端和服务端 Mock 单元测试
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from ef_rpc import RpcClient, RpcServer, RpcService
from ef_rpc.serializers.json_serializer import JsonSerializer
from ef_rpc.types.base import RpcTransport, RpcConfig, RequestHandler
from ef_rpc.types.mqtt import MqttOptions


class MockTransport(RpcTransport):
    """Mock传输层实现"""
    
    def __init__(self):
        self.started = False
        self.stopped = False
        self.connected = True
        self.request_handler = None
        self.sent_requests = []
        self.mock_responses = {}
    
    async def start(self):
        self.started = True
    
    async def stop(self):
        self.stopped = True
    
    async def send_request(self, service_name: str, data: bytes) -> bytes:
        self.sent_requests.append((service_name, data))
        # 返回模拟响应
        if service_name in self.mock_responses:
            return self.mock_responses[service_name]
        return b'{"result": "mock_response", "error": null}'
    
    def is_connected(self) -> bool:
        return self.connected
    
    async def start_server(self, service_name: str) -> None:
        pass
    
    def set_request_handler(self, handler: RequestHandler):
        self.request_handler = handler
    
    def set_mock_response(self, service_name: str, response: bytes):
        """设置模拟响应"""
        self.mock_responses[service_name] = response


@RpcService
class MockCalculatorService:
    """模拟计算器服务"""
    
    def add(self, a: int, b: int) -> int:
        return a + b
    
    def multiply(self, a: int, b: int) -> int:
        return a * b
    
    def divide(self, a: float, b: float) -> float:
        if b == 0:
            raise ValueError("除数不能为零")
        return a / b
    
    async def async_add(self, a: int, b: int) -> int:
        await asyncio.sleep(0.01)  # 模拟异步操作
        return a + b


class TestRpcClient:
    """RPC客户端测试类"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.transport = MockTransport()
        self.serializer = JsonSerializer()
        self.client = RpcClient(self.transport, self.serializer)
    
    @pytest.mark.asyncio
    async def test_client_lifecycle(self):
        """测试客户端生命周期"""
        # 初始状态
        assert not self.client.is_started
        # 注意：is_connected() 检查的是传输层状态，不是客户端启动状态
        assert self.client.is_connected()  # MockTransport 默认是连接的
        
        # 启动客户端
        await self.client.start()
        assert self.client.is_started
        assert self.transport.started
        assert self.client.is_connected()
        
        # 重复启动应该被忽略
        await self.client.start()
        assert self.client.is_started
        
        # 停止客户端
        await self.client.stop()
        assert not self.client.is_started
        assert self.transport.stopped
    
    @pytest.mark.asyncio
    async def test_create_service_before_start(self):
        """测试在启动前创建服务代理"""
        with pytest.raises(RuntimeError, match="客户端未启动"):
            self.client.create_service("TestService")
    
    @pytest.mark.asyncio
    async def test_create_service_after_start(self):
        """测试启动后创建服务代理"""
        await self.client.start()
        
        # 创建服务代理
        service = self.client.create_service("CalculatorService")
        assert service is not None
        assert "CalculatorService" in self.client.services
        
        # 重复创建应该返回相同实例
        service2 = self.client.create_service("CalculatorService")
        assert service is service2
    
    @pytest.mark.asyncio
    async def test_service_proxy_calls(self):
        """测试服务代理调用"""
        await self.client.start()
        
        # 设置模拟响应
        mock_response = b'{"result": 15, "error": null}'
        self.transport.set_mock_response("CalculatorService", mock_response)
        
        # 创建服务代理并调用
        calculator = self.client.create_service("CalculatorService")
        result = await calculator.add(10, 5)
        
        # 验证调用
        assert len(self.transport.sent_requests) == 1
        service_name, request_data = self.transport.sent_requests[0]
        assert service_name == "CalculatorService"
        
        # 验证请求数据格式
        request_str = request_data.decode('utf-8')
        request = self.serializer.deserialize_from_string(request_str, dict)
        assert request['method_name'] == 'add'
        assert request['arguments'] == [10, 5]
        assert 'request_id' in request
    
    @pytest.mark.asyncio
    async def test_client_with_custom_config(self):
        """测试使用自定义配置的客户端"""
        config = RpcConfig(
            version="2.0",
            timeout=5000,
            retry_count=2,
            retry_delay=500
        )
        
        client = RpcClient(self.transport, self.serializer, config)
        assert client.config.version == "2.0"
        assert client.config.timeout == 5000


class TestRpcServer:
    """RPC服务端测试类"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.transport = MockTransport()
        self.serializer = JsonSerializer()
        self.server = RpcServer(self.transport, self.serializer)
    
    def test_register_service(self):
        """测试服务注册"""
        # 注册服务实例
        service = MockCalculatorService()
        self.server.register_service(service)
        assert "MockCalculatorService" in self.server.services
        assert self.server.services["MockCalculatorService"] is service
        
        # 使用自定义服务名注册
        another_service = MockCalculatorService()
        self.server.register_service(another_service, "CustomCalculator")
        assert "CustomCalculator" in self.server.services
        assert self.server.services["CustomCalculator"] is another_service
    
    def test_server_initial_state(self):
        """测试服务端初始状态"""
        assert not self.server.is_running()
        assert len(self.server.services) == 0
        assert len(self.server.consumers) == 0
    
    @pytest.mark.asyncio
    async def test_server_lifecycle(self):
        """测试服务端生命周期"""
        # 注册服务
        service = MockCalculatorService()
        self.server.register_service(service)
        
        # 启动服务端
        await self.server.start()
        assert self.server.is_running()
        assert self.transport.started
        assert self.transport.request_handler is not None
        assert len(self.server.consumers) == 1
        
        # 重复启动应该被忽略
        await self.server.start()
        assert self.server.is_running()
        
        # 停止服务端
        await self.server.stop()
        assert not self.server.is_running()
        assert self.transport.stopped
        assert len(self.server.consumers) == 0
    
    @pytest.mark.asyncio
    async def test_server_request_handling(self):
        """测试服务端请求处理"""
        # 注册服务并启动
        service = MockCalculatorService()
        self.server.register_service(service)
        await self.server.start()
        
        # 确保请求处理器已设置
        assert self.transport.request_handler is not None
        
        # 构造请求数据
        request = {
            "method_name": "add",
            "arguments": [10, 20],
            "request_id": "test-123"
        }
        request_data = self.serializer.serialize_to_string(request).encode('utf-8')
        
        # 模拟请求处理
        response_data = await self.transport.request_handler.handle_request(
            "MockCalculatorService", request_data
        )
        
        # 验证响应
        response_str = response_data.decode('utf-8')
        response = self.serializer.deserialize_from_string(response_str, dict)
        assert response['result'] == 30  # 10 + 20
        assert response['error'] is None
    
    @pytest.mark.asyncio
    async def test_server_error_handling(self):
        """测试服务端错误处理"""
        # 注册服务并启动
        service = MockCalculatorService()
        self.server.register_service(service)
        await self.server.start()
        
        # 确保请求处理器已设置
        assert self.transport.request_handler is not None
        
        # 测试不存在的方法
        request = {
            "method_name": "non_existent_method",
            "arguments": [],
            "request_id": "test-456"
        }
        request_data = self.serializer.serialize_to_string(request).encode('utf-8')
        
        response_data = await self.transport.request_handler.handle_request(
            "MockCalculatorService", request_data
        )
        
        response_str = response_data.decode('utf-8')
        response = self.serializer.deserialize_from_string(response_str, dict)
        assert response['result'] is None
        assert "方法不存在" in response['error']
    
    @pytest.mark.asyncio
    async def test_server_with_custom_config(self):
        """测试使用自定义配置的服务端"""
        config = RpcConfig(
            version="2.0",
            timeout=10000,
            retry_count=5,
            retry_delay=1000
        )
        
        server = RpcServer(self.transport, self.serializer, config)
        assert server.config.version == "2.0"
        assert server.config.timeout == 10000


class TestRpcServiceDecorator:
    """RPC服务装饰器测试类"""
    
    def test_rpc_service_decorator(self):
        """测试RPC服务装饰器"""
        @RpcService
        class TestService:
            def method1(self):
                return "result1"
            
            def method2(self, param):
                return f"result2: {param}"
        
        # 验证装饰器标记
        assert hasattr(TestService, '_is_rpc_service')
        assert getattr(TestService, '_is_rpc_service') is True
        assert getattr(TestService, '_service_name') == 'TestService'
        
        # 验证服务功能正常
        service = TestService()
        assert service.method1() == "result1"
        assert service.method2("test") == "result2: test"
    
    def test_rpc_service_decorator_error(self):
        """测试RPC服务装饰器错误情况"""
        # 测试装饰非类对象
        def test_function():
            pass
        
        with pytest.raises(TypeError, match="@RpcService只能用于类定义"):
            RpcService(test_function)  # type: ignore


@pytest.mark.asyncio
async def test_integration_scenario():
    """集成测试场景"""
    # 创建传输层
    transport = MockTransport()
    serializer = JsonSerializer()
    
    # 创建服务端
    server = RpcServer(transport, serializer)
    calculator_service = MockCalculatorService()
    server.register_service(calculator_service)
    await server.start()
    
    # 创建客户端
    client = RpcClient(transport, serializer)
    await client.start()
    
    # 创建服务代理
    calculator = client.create_service("MockCalculatorService")
    
    # 设置正确的模拟响应
    transport.set_mock_response("MockCalculatorService", b'{"result": 8, "error": null}')
    
    # 测试各种计算操作
    assert await calculator.add(5, 3) == 8
    
    # 设置其他操作的响应
    transport.set_mock_response("MockCalculatorService", b'{"result": 24, "error": null}')
    assert await calculator.multiply(4, 6) == 24
    
    transport.set_mock_response("MockCalculatorService", b'{"result": 5.0, "error": null}')
    assert await calculator.divide(10, 2) == 5.0
    
    transport.set_mock_response("MockCalculatorService", b'{"result": 15, "error": null}')
    # 测试异步方法
    result = await calculator.async_add(7, 8)
    assert result == 15
    
    # 清理
    await client.stop()
    await server.stop() 