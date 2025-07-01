import pytest
import asyncio
from ef_rpc import RpcClient, RpcServer, RpcService
from ef_rpc.serializers.json_serializer import JsonSerializer
from ef_rpc.types.mqtt import MqttOptions
from unittest.mock import AsyncMock, MagicMock
from ef_rpc.types.base import RpcTransport

# mock transport
class DummyTransport(RpcTransport):
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
    def set_request_handler(self, handler):
        self.handler = handler

@pytest.mark.asyncio
async def test_json_serializer_basic():
    serializer = JsonSerializer()
    data = {"a": 1, "b": [1, 2, 3], "c": "测试"}
    s = serializer.serialize_to_string(data)
    d = serializer.deserialize_from_string(s, dict)
    assert d == data
    b = serializer.serialize(data)
    d2 = serializer.deserialize(b, dict)
    assert d2 == data


def test_rpc_service_decorator():
    @RpcService
    class Demo:
        pass
    assert hasattr(Demo, '_is_rpc_service')
    assert getattr(Demo, '_is_rpc_service') is True
    assert getattr(Demo, '_service_name') == 'Demo'

@pytest.mark.asyncio
async def test_rpc_client_lifecycle():
    transport = DummyTransport()
    serializer = JsonSerializer()
    client = RpcClient(transport, serializer)
    await client.start()
    assert client.is_started
    assert transport.started
    await client.stop()
    assert not client.is_started
    assert transport.stopped

def test_rpc_server_register_and_running():
    transport = DummyTransport()
    serializer = JsonSerializer()
    server = RpcServer(transport, serializer)
    class Demo:
        def foo(self):
            return "bar"
    server.register_service(Demo())
    assert 'Demo' in server.services
    assert not server.is_running()

@pytest.mark.asyncio
async def test_rpc_server_lifecycle():
    transport = DummyTransport()
    serializer = JsonSerializer()
    server = RpcServer(transport, serializer)
    server.register_service(object(), 'Obj')
    await server.start()
    assert server.is_running()
    await server.stop()
    assert not server.is_running() 