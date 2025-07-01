#!/usr/bin/env python3
"""
代理工厂 Mock 单元测试
"""

import pytest
import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from ef_rpc.core.proxy_factory import ProxyFactory, ServiceProxy, MethodCaller
from ef_rpc.serializers.json_serializer import JsonSerializer
from ef_rpc.types.base import RpcTransport, RpcConfig


class MockTransport(RpcTransport):
    """Mock传输层实现"""
    
    def __init__(self):
        self.started = False
        self.stopped = False
        self.connected = True
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


class TestProxyFactory:
    """代理工厂测试类"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.transport = MockTransport()
        self.serializer = JsonSerializer()
        self.config = RpcConfig()
        self.service_name = "TestService"
        self.factory = ProxyFactory(
            transport=self.transport,
            serializer=self.serializer,
            config=self.config,
            service_name=self.service_name
        )
    
    def test_proxy_factory_initialization(self):
        """测试代理工厂初始化"""
        assert self.factory.transport is self.transport
        assert self.factory.serializer is self.serializer
        assert self.factory.config is self.config
        assert self.factory.service_name == self.service_name
        assert isinstance(self.factory._pending_requests, dict)
        assert len(self.factory._pending_requests) == 0
    
    def test_create_proxy(self):
        """测试创建服务代理"""
        proxy = self.factory.create_proxy()
        assert isinstance(proxy, ServiceProxy)
        assert proxy.transport is self.transport
        assert proxy.serializer is self.serializer
        assert proxy.config is self.config
        assert proxy.service_name == self.service_name
        assert proxy._pending_requests is self.factory._pending_requests
    
    def test_proxy_has_methods(self):
        """测试代理对象具有方法属性"""
        proxy = self.factory.create_proxy()
        
        # 验证代理对象具有可调用属性
        assert hasattr(proxy, '__getattr__')
        assert callable(getattr(proxy, '__getattr__'))
    
    def test_proxy_method_creation(self):
        """测试代理方法创建"""
        proxy = self.factory.create_proxy()
        
        # 模拟方法调用
        method = proxy.__getattr__('test_method')
        assert isinstance(method, MethodCaller)
        assert method.transport is self.transport
        assert method.serializer is self.serializer
        assert method.config is self.config
        assert method.service_name == self.service_name
        assert method.method_name == 'test_method'
        assert method._pending_requests is self.factory._pending_requests


class TestServiceProxy:
    """服务代理测试类"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.transport = MockTransport()
        self.serializer = JsonSerializer()
        self.config = RpcConfig()
        self.service_name = "CalculatorService"
        self.pending_requests = {}
        
        self.proxy = ServiceProxy(
            transport=self.transport,
            serializer=self.serializer,
            config=self.config,
            service_name=self.service_name,
            pending_requests=self.pending_requests
        )
    
    def test_service_proxy_initialization(self):
        """测试服务代理初始化"""
        assert self.proxy.transport is self.transport
        assert self.proxy.serializer is self.serializer
        assert self.proxy.config is self.config
        assert self.proxy.service_name == self.service_name
        assert self.proxy._pending_requests is self.pending_requests
    
    def test_getattr_creates_method_caller(self):
        """测试__getattr__创建方法调用器"""
        method_caller = self.proxy.__getattr__('add')
        assert isinstance(method_caller, MethodCaller)
        assert method_caller.method_name == 'add'
        assert method_caller.service_name == self.service_name
    
    def test_getattr_caching(self):
        """测试__getattr__缓存机制"""
        # 第一次调用
        method1 = self.proxy.__getattr__('add')
        # 第二次调用应该返回相同对象
        method2 = self.proxy.__getattr__('add')
        assert method1 is method2
    
    def test_getattr_different_methods(self):
        """测试不同方法的__getattr__"""
        add_method = self.proxy.__getattr__('add')
        multiply_method = self.proxy.__getattr__('multiply')
        
        assert add_method is not multiply_method
        assert add_method.method_name == 'add'
        assert multiply_method.method_name == 'multiply'


class TestMethodCaller:
    """方法调用器测试类"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.transport = MockTransport()
        self.serializer = JsonSerializer()
        self.config = RpcConfig()
        self.service_name = "CalculatorService"
        self.method_name = "add"
        self.pending_requests = {}
        
        self.method_caller = MethodCaller(
            transport=self.transport,
            serializer=self.serializer,
            config=self.config,
            service_name=self.service_name,
            method_name=self.method_name,
            pending_requests=self.pending_requests
        )
    
    def test_method_caller_initialization(self):
        """测试方法调用器初始化"""
        assert self.method_caller.transport is self.transport
        assert self.method_caller.serializer is self.serializer
        assert self.method_caller.config is self.config
        assert self.method_caller.service_name == self.service_name
        assert self.method_caller.method_name == self.method_name
        assert self.method_caller._pending_requests is self.pending_requests
    
    def test_call_returns_coroutine(self):
        """测试__call__返回协程"""
        result = self.method_caller(10, 20)
        assert asyncio.iscoroutine(result)
    
    @pytest.mark.asyncio
    async def test_call_async_success(self):
        """测试异步调用成功"""
        # 设置模拟响应
        mock_response = b'{"result": 30, "error": null}'
        self.transport.mock_responses[self.service_name] = mock_response
        
        # 执行调用
        result = await self.method_caller._call_async(10, 20)
        
        # 验证结果
        assert result == 30
        
        # 验证请求发送
        assert len(self.transport.sent_requests) == 1
        service_name, request_data = self.transport.sent_requests[0]
        assert service_name == self.service_name
        
        # 验证请求格式
        request_str = request_data.decode('utf-8')
        request = self.serializer.deserialize_from_string(request_str, dict)
        assert request['method_name'] == 'add'
        assert request['arguments'] == [10, 20]
        assert 'request_id' in request
    
    @pytest.mark.asyncio
    async def test_call_async_with_kwargs(self):
        """测试带关键字参数的异步调用"""
        # 设置模拟响应
        mock_response = b'{"result": 50, "error": null}'
        self.transport.mock_responses[self.service_name] = mock_response
        
        # 执行调用
        result = await self.method_caller._call_async(10, 20, operation="add")
        
        # 验证结果
        assert result == 50
        
        # 验证请求格式
        request_str = self.transport.sent_requests[0][1].decode('utf-8')
        request = self.serializer.deserialize_from_string(request_str, dict)
        assert request['arguments'] == [10, 20]
        assert request['kwargs'] == {"operation": "add"}
    
    @pytest.mark.asyncio
    async def test_call_async_error_response(self):
        """测试错误响应的异步调用"""
        # 设置错误响应
        error_response = b'{"result": null, "error": "Calculation failed"}'
        self.transport.mock_responses[self.service_name] = error_response
        
        # 执行调用并验证异常
        with pytest.raises(Exception, match="Calculation failed"):
            await self.method_caller._call_async(10, 20)
    
    @pytest.mark.asyncio
    async def test_call_async_transport_error(self):
        """测试传输层错误的异步调用"""
        # 模拟传输层异常
        self.transport.send_request = AsyncMock(side_effect=Exception("Network error"))
        
        # 执行调用并验证异常
        with pytest.raises(Exception, match="Network error"):
            await self.method_caller._call_async(10, 20)
    
    @pytest.mark.asyncio
    async def test_call_async_request_id_generation(self):
        """测试请求ID生成"""
        # 设置模拟响应
        mock_response = b'{"result": 30, "error": null}'
        self.transport.mock_responses[self.service_name] = mock_response
        
        # 执行调用
        await self.method_caller._call_async(10, 20)
        
        # 验证请求ID
        request_str = self.transport.sent_requests[0][1].decode('utf-8')
        request = self.serializer.deserialize_from_string(request_str, dict)
        request_id = request['request_id']
        
        # 验证请求ID格式（UUID）
        try:
            uuid.UUID(request_id)
        except ValueError:
            pytest.fail("请求ID不是有效的UUID格式")
    
    @pytest.mark.asyncio
    async def test_call_async_pending_requests_cleanup(self):
        """测试待处理请求的清理"""
        # 设置模拟响应
        mock_response = b'{"result": 30, "error": null}'
        self.transport.mock_responses[self.service_name] = mock_response
        
        # 执行调用
        await self.method_caller._call_async(10, 20)
        
        # 验证待处理请求已被清理
        assert len(self.pending_requests) == 0


@pytest.mark.asyncio
async def test_proxy_factory_integration():
    """代理工厂集成测试"""
    # 创建组件
    transport = MockTransport()
    serializer = JsonSerializer()
    config = RpcConfig()
    service_name = "MathService"
    
    # 创建代理工厂
    factory = ProxyFactory(transport, serializer, config, service_name)
    
    # 创建服务代理
    proxy = factory.create_proxy()
    
    # 设置模拟响应
    transport.mock_responses[service_name] = b'{"result": 42, "error": null}'
    
    # 调用代理方法
    result = await proxy.calculate(10, 32)
    
    # 验证结果
    assert result == 42
    
    # 验证请求
    assert len(transport.sent_requests) == 1
    service_name_sent, request_data = transport.sent_requests[0]
    assert service_name_sent == service_name
    
    # 验证请求内容
    request_str = request_data.decode('utf-8')
    request = serializer.deserialize_from_string(request_str, dict)
    assert request['method_name'] == 'calculate'
    assert request['arguments'] == [10, 32] 