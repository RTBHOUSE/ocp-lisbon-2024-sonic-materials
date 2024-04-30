from dataclasses import dataclass, field
from typing import List
from enum import Enum
from types import GeneratorType

class PortList(list):
    def __init__(self, val=None):
        super().__init__(PortList._parse_value(val))
    @staticmethod
    def _parse_value(val):
        if isinstance(val, GeneratorType) or isinstance(val, list):
            return val
        if val is None or len(str(val)) == 0:
            return []
        ports = []
        parts = str(val).split(',')
        for part in parts:
            if '-' in part:
                first, last = tuple([int(x) for x in part.split('-')])
                ports = ports + list(range(first, last + 1))
            else:
                ports.append(int(part))
        return ports

@dataclass
class PortBreakout:
    mode: str
    ports: PortList

@dataclass
class PortGroupConfig:
    admin_status: str = "down"
    fec: str = None
    mtu: int = 9100
    ports: PortList = field(default_factory=PortList)
    portchannels: PortList = field(default_factory=PortList)

@dataclass
class PortChannelConfig:
    ports: PortList
    id: int
