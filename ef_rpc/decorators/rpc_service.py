"""
RPC服务装饰器
"""

from typing import Type, TypeVar, cast
from functools import wraps

T = TypeVar('T')


def RpcService(cls: Type[T]) -> Type[T]:
    """
    RPC服务装饰器。
    用于标记RPC服务类，使其可以被RPC服务器注册和管理。

    :param cls: 要装饰的类，必须为class类型
    :return: 装饰后的类
    :raises TypeError: 如果cls不是类类型
    """
    if not isinstance(cls, type):
        raise TypeError("@RpcService只能用于类定义")
    
    # 添加RPC服务标记
    setattr(cls, '_is_rpc_service', True)
    
    # 添加服务名称
    if not hasattr(cls, '_service_name'):
        setattr(cls, '_service_name', cls.__name__)
    
    return cls 