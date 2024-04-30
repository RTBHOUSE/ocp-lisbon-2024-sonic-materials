from dataclasses import dataclass, field
from typing import List
from enum import Enum
from .port import PortList

@dataclass
class RoutedVlan:
    vrfid: int
    port_groups: List[str] = field(default_factory=list)
    ports: PortList = field(default_factory=PortList)

@dataclass
class SwitchedVlan:
    vrfid: int
    addresses: List[str] = field(default_factory=list)
    untagged_ports: PortList = field(default_factory=PortList) 
    tagged_ports: PortList = field(default_factory=PortList)
    untagged_portchannels: PortList = field(default_factory=PortList) 
    tagged_portchannels: PortList = field(default_factory=PortList)
    untagged_port_groups: List[str] = field(default_factory=list)
    tagged_port_groups: List[str] = field(default_factory=list)
    dhcp_servers: List[str] = field(default_factory=list)
