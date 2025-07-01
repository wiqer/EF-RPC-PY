"""
MQTT相关类型定义
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class MqttOptions:
    """
    MQTT配置选项。
    :param broker_url: MQTT代理地址
    :param client_id: 客户端ID
    :param username: 用户名
    :param password: 密码
    :param keep_alive_interval: 保活间隔（秒）
    :param connection_timeout: 连接超时时间（秒）
    :param clean_session: 是否清理会话
    :param max_inflight: 最大未确认消息数
    :param qos: 服务质量等级
    :param reconnect_period: 重连间隔（毫秒）
    :param connect_timeout: 连接超时时间（毫秒）
    """
    broker_url: str
    client_id: str
    username: Optional[str] = None
    password: Optional[str] = None
    keep_alive_interval: int = 60
    connection_timeout: int = 30
    clean_session: bool = True
    max_inflight: int = 1000
    qos: int = 1
    reconnect_period: int = 1000
    connect_timeout: int = 30000


@dataclass
class MqttMessage:
    """
    MQTT消息格式。
    :param id: 消息唯一ID
    :param created_at: 创建时间（建议统一命名）
    :param msg: 消息体
    :param correlation_id: 关联ID
    :param reply_to: 回复目标
    :param metadata: 附加元数据
    """
    id: str
    created_at: str  # 原 create_date，统一命名
    msg: List[Any]
    correlation_id: str
    reply_to: str
    metadata: Optional[Dict[str, Any]] = None 