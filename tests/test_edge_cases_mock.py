#!/usr/bin/env python3
"""
边界情况和异常处理 Mock 单元测试
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from ef_rpc import RpcClient, RpcServer, RpcService
from ef_rpc.serializers.json_serializer import JsonSerializer
from ef_rpc.types.base import RpcTransport, RpcConfig, InvocationException, ConnectionException, TimeoutException
from ef_rpc.types.mqtt import MqttOptions


class FaultyTransport(RpcTransport):
    """故障传输层，用于测试异常情况"""
    
    def __init__(self, fail_on_start=False, fail_on_send=False, timeout_on_send=False):
        self.started = False
        self.stopped = False
        self.connected = True
        self.fail_on_start = fail_on_start
        self.fail_on_send = fail_on_send
        self.timeout_on_send = timeout_on_send
        self.request_handler = None
    
    async def start(self):
        if self.fail_on_start:
            raise ConnectionException("启动失败")
        self.started = True
    
    async def stop(self):
        self.stopped = True
    
    async def send_request(self, service_name: str, data: bytes) -> bytes:
        if self.fail_on_send:
            raise ConnectionException("发送失败")
        if self.timeout_on_send:
            raise TimeoutException("请求超时", 5000)
        return b'{"result": "success", "error": null}'
    
    def is_connected(self) -> bool:
        return self.connected
    
    async def start_server(self, service_name: str) -> None:
        pass
    
    def set_request_handler(self, handler):
        self.request_handler = handler


@RpcService
class FaultyService:
    """故障服务，用于测试服务端异常"""
    
    def normal_method(self):
        return "normal"
    
    def exception_method(self):
        raise ValueError("服务端异常")
    
    def slow_method(self):
        import time
        time.sleep(0.1)  # 模拟慢操作
        return "slow"
    
    async def async_exception_method(self):
        await asyncio.sleep(0.01)
        raise RuntimeError("异步异常")


class TestEdgeCases:
    """边界情况测试类"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.serializer = JsonSerializer()
        self.config = RpcConfig()
    
    @pytest.mark.asyncio
    async def test_client_start_failure(self):
        """测试客户端启动失败"""
        transport = FaultyTransport(fail_on_start=True)
        client = RpcClient(transport, self.serializer)
        
        with pytest.raises(ConnectionException, match="启动失败"):
            await client.start()
        
        assert not client.is_started
    
    @pytest.mark.asyncio
    async def test_client_send_failure(self):
        """测试客户端发送失败"""
        transport = FaultyTransport(fail_on_send=True)
        client = RpcClient(transport, self.serializer)
        await client.start()
        
        service = client.create_service("TestService")
        
        with pytest.raises(Exception, match="发送失败"):
            await service.test_method()
    
    @pytest.mark.asyncio
    async def test_client_timeout(self):
        """测试客户端超时"""
        transport = FaultyTransport(timeout_on_send=True)
        client = RpcClient(transport, self.serializer)
        await client.start()
        
        service = client.create_service("TestService")
        
        with pytest.raises(Exception, match="请求超时"):
            await service.test_method()
    
    @pytest.mark.asyncio
    async def test_server_service_exception(self):
        """测试服务端服务异常"""
        transport = FaultyTransport()
        server = RpcServer(transport, self.serializer)
        service = FaultyService()
        server.register_service(service)
        await server.start()
        
        # 确保请求处理器已设置
        assert transport.request_handler is not None
        
        # 构造异常请求
        request = {
            "method_name": "exception_method",
            "arguments": [],
            "request_id": "test-123"
        }
        request_data = self.serializer.serialize_to_string(request).encode('utf-8')
        
        # 处理请求
        response_data = await transport.request_handler.handle_request(
            "FaultyService", request_data
        )
        
        # 验证错误响应
        response_str = response_data.decode('utf-8')
        response = self.serializer.deserialize_from_string(response_str, dict)
        assert response['result'] is None
        assert "服务端异常" in response['error']
    
    @pytest.mark.asyncio
    async def test_server_nonexistent_service(self):
        """测试不存在的服务"""
        transport = FaultyTransport()
        server = RpcServer(transport, self.serializer)
        await server.start()
        
        # 确保请求处理器已设置
        assert transport.request_handler is not None
        
        request = {
            "method_name": "test_method",
            "arguments": [],
            "request_id": "test-456"
        }
        request_data = self.serializer.serialize_to_string(request).encode('utf-8')
        
        response_data = await transport.request_handler.handle_request(
            "NonexistentService", request_data
        )
        
        response_str = response_data.decode('utf-8')
        response = self.serializer.deserialize_from_string(response_str, dict)
        assert response['result'] is None
        assert "服务不存在" in response['error']
    
    @pytest.mark.asyncio
    async def test_server_nonexistent_method(self):
        """测试不存在的方法"""
        transport = FaultyTransport()
        server = RpcServer(transport, self.serializer)
        service = FaultyService()
        server.register_service(service)
        await server.start()
        
        # 确保请求处理器已设置
        assert transport.request_handler is not None
        
        request = {
            "method_name": "nonexistent_method",
            "arguments": [],
            "request_id": "test-789"
        }
        request_data = self.serializer.serialize_to_string(request).encode('utf-8')
        
        response_data = await transport.request_handler.handle_request(
            "FaultyService", request_data
        )
        
        response_str = response_data.decode('utf-8')
        response = self.serializer.deserialize_from_string(response_str, dict)
        assert response['result'] is None
        assert "方法不存在" in response['error']
    
    @pytest.mark.asyncio
    async def test_server_malformed_request(self):
        """测试格式错误的请求"""
        transport = FaultyTransport()
        server = RpcServer(transport, self.serializer)
        service = FaultyService()
        server.register_service(service)
        await server.start()
        
        # 确保请求处理器已设置
        assert transport.request_handler is not None
        
        # 发送格式错误的请求
        malformed_data = b'invalid json data'
        
        response_data = await transport.request_handler.handle_request(
            "FaultyService", malformed_data
        )
        
        response_str = response_data.decode('utf-8')
        response = self.serializer.deserialize_from_string(response_str, dict)
        assert response['result'] is None
        assert "处理请求失败" in response['error']
    
    def test_serializer_invalid_json(self):
        """测试序列化器处理无效JSON"""
        serializer = JsonSerializer()
        
        with pytest.raises(Exception):
            serializer.deserialize_from_string("invalid json", dict)
    
    def test_serializer_type_conversion_error(self):
        """测试序列化器类型转换错误"""
        serializer = JsonSerializer()
        
        with pytest.raises(ValueError):
            serializer._convert_type("not_a_number", int)
    
    @pytest.mark.asyncio
    async def test_client_double_start(self):
        """测试客户端重复启动"""
        transport = FaultyTransport()
        client = RpcClient(transport, self.serializer)
        
        await client.start()
        assert client.is_started
        
        # 重复启动应该被忽略
        await client.start()
        assert client.is_started
    
    @pytest.mark.asyncio
    async def test_client_double_stop(self):
        """测试客户端重复停止"""
        transport = FaultyTransport()
        client = RpcClient(transport, self.serializer)
        
        await client.start()
        await client.stop()
        assert not client.is_started
        
        # 重复停止应该被忽略
        await client.stop()
        assert not client.is_started
    
    @pytest.mark.asyncio
    async def test_server_double_start(self):
        """测试服务端重复启动"""
        transport = FaultyTransport()
        server = RpcServer(transport, self.serializer)
        service = FaultyService()
        server.register_service(service)
        
        await server.start()
        assert server.is_running()
        
        # 重复启动应该被忽略
        await server.start()
        assert server.is_running()
    
    @pytest.mark.asyncio
    async def test_server_double_stop(self):
        """测试服务端重复停止"""
        transport = FaultyTransport()
        server = RpcServer(transport, self.serializer)
        service = FaultyService()
        server.register_service(service)
        
        await server.start()
        await server.stop()
        assert not server.is_running()
        
        # 重复停止应该被忽略
        await server.stop()
        assert not server.is_running()
    
    def test_rpc_service_decorator_invalid_usage(self):
        """测试RPC服务装饰器无效使用"""
        # 测试装饰函数而不是类
        def test_function():
            pass
        
        with pytest.raises(TypeError, match="@RpcService只能用于类定义"):
            RpcService(test_function)  # type: ignore
    
    @pytest.mark.asyncio
    async def test_large_request_data(self):
        """测试大数据量请求"""
        transport = FaultyTransport()
        client = RpcClient(transport, self.serializer)
        await client.start()
        
        service = client.create_service("TestService")
        
        # 构造大数据量请求
        large_data = [{"id": i, "data": "x" * 1000} for i in range(100)]
        
        # 这应该能正常处理
        result = await service.process_large_data(large_data)
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """测试并发请求"""
        transport = FaultyTransport()
        client = RpcClient(transport, self.serializer)
        await client.start()
        
        service = client.create_service("TestService")
        
        # 并发发送多个请求
        tasks = [
            service.test_method() for _ in range(10)
        ]
        
        results = await asyncio.gather(*tasks)
        assert all(result == "success" for result in results)
    
    @pytest.mark.asyncio
    async def test_connection_loss_recovery(self):
        """测试连接丢失恢复"""
        transport = FaultyTransport()
        client = RpcClient(transport, self.serializer)
        await client.start()
        
        # 模拟连接丢失
        transport.connected = False
        assert not client.is_connected()
        
        # 模拟连接恢复
        transport.connected = True
        assert client.is_connected()


class TestPerformanceEdgeCases:
    """性能边界情况测试"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.serializer = JsonSerializer()
        self.config = RpcConfig()
    
    @pytest.mark.asyncio
    async def test_many_services(self):
        """测试大量服务注册"""
        transport = FaultyTransport()
        server = RpcServer(transport, self.serializer)
        
        # 注册大量服务
        for i in range(100):
            service = FaultyService()
            server.register_service(service, f"Service{i}")
        
        assert len(server.services) == 100
        await server.start()
        assert len(server.consumers) == 100
        await server.stop()
    
    @pytest.mark.asyncio
    async def test_many_methods(self):
        """测试大量方法调用"""
        transport = FaultyTransport()
        client = RpcClient(transport, self.serializer)
        await client.start()
        
        service = client.create_service("TestService")
        
        # 调用大量不同方法
        for i in range(50):
            method_name = f"method_{i}"
            result = await getattr(service, method_name)()
            assert result == "success"
    
    @pytest.mark.asyncio
    async def test_memory_usage(self):
        """测试内存使用情况"""
        import gc
        import sys
        
        # 记录初始内存
        gc.collect()
        initial_memory = sys.getsizeof([])
        
        transport = FaultyTransport()
        client = RpcClient(transport, self.serializer)
        await client.start()
        
        # 创建大量服务代理
        services = []
        for i in range(1000):
            service = client.create_service(f"Service{i}")
            services.append(service)
        
        # 检查内存增长是否合理
        gc.collect()
        final_memory = sys.getsizeof(services)
        memory_growth = final_memory - initial_memory
        
        # 内存增长应该在合理范围内（小于1MB）
        assert memory_growth < 1024 * 1024
        
        await client.stop() 