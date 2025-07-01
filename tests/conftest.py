#!/usr/bin/env python3
"""
Pytest 配置文件
"""

import pytest
import asyncio
from ef_rpc.serializers.json_serializer import JsonSerializer
from ef_rpc.types.base import RpcConfig


@pytest.fixture
def serializer():
    """提供序列化器实例"""
    return JsonSerializer()


@pytest.fixture
def config():
    """提供RPC配置实例"""
    return RpcConfig()


@pytest.fixture
def event_loop():
    """提供事件循环"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_transport():
    """提供Mock传输层"""
    # 延迟导入避免循环依赖
    class DummyTransport:
        def __init__(self):
            self.started = False
            self.stopped = False
            self._connected = True
        async def start(self):
            self.started = True
        async def stop(self):
            self.stopped = True
        async def send_request(self, service_name: str, data: bytes) -> bytes:
            return b''
        def is_connected(self) -> bool:
            return self._connected
        async def start_server(self, service_name: str) -> None:
            pass
    return DummyTransport()


@pytest.fixture
def mock_transport_with_handler():
    """提供带请求处理器的Mock传输层"""
    # 延迟导入避免循环依赖
    from ef_rpc.types.base import RpcTransport, RequestHandler
    
    class MockTransport(RpcTransport):
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
            if service_name in self.mock_responses:
                return self.mock_responses[service_name]
            return b'{"result": "mock_response", "error": null}'
        
        def is_connected(self) -> bool:
            return self.connected
        
        async def start_server(self, service_name: str) -> None:
            pass
        
        def set_request_handler(self, handler: RequestHandler):
            self.request_handler = handler
    
    return MockTransport()


# 测试标记
pytest_plugins = ["pytest_asyncio"]

# 测试配置
def pytest_configure(config):
    """配置测试环境"""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )


def pytest_collection_modifyitems(config, items):
    """修改测试项"""
    for item in items:
        # 为异步测试添加标记
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.asyncio)
        
        # 为集成测试添加标记
        if "integration" in item.name.lower():
            item.add_marker(pytest.mark.integration)
        
        # 为慢速测试添加标记
        if "slow" in item.name.lower() or "timeout" in item.name.lower():
            item.add_marker(pytest.mark.slow) 