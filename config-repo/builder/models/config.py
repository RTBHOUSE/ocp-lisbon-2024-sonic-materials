from dataclasses import dataclass, field
from dacite import from_dict, Config as DaciteConfig
from typing import Dict, List, Optional
from enum import Enum
from .bgp import BGPConfig
from .port import PortBreakout, PortGroupConfig, PortChannelConfig, PortList
from .vlan import SwitchedVlan, RoutedVlan

class ServiceState(Enum):
    enabled = "enabled"
    disabled = "disabled"  

@dataclass
class StaticRoute:
    nexthop: str
    prefix: str
    vrfid: int

@dataclass
class Config:
    datacenter: str
    hostname: str
    mac: str
    hwsku: Optional[str]
    services: Dict[str, ServiceState]
    bgp: Dict[str, BGPConfig]
    frr_template: str
    breakouts: List[PortBreakout]
    platform: str
    port_descriptions: Dict[int, str]
    port_groups: Dict[str, PortGroupConfig]
    routed_vlans: Dict[int, RoutedVlan]
    switched_vlans: Dict[int, SwitchedVlan]
    vpn: str
    portchannels: List[PortChannelConfig] = field(default_factory=list)
    static_routes: List[StaticRoute] = field(default_factory=list)

    @staticmethod
    def load(path=None, obj=None):
        if path is not None:
            with open(path, 'r') as handle:
                obj = yaml.safe_load(handle)
        return from_dict(data_class=Config, data=obj, config=DaciteConfig(cast=[PortList, ServiceState]))
