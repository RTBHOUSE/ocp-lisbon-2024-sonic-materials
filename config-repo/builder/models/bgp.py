from dataclasses import dataclass, field
from typing import List, Dict, Union, Optional
from enum import Enum

@dataclass
class BGPRouteMap:
    action: str
    match: Dict[str, Union[str, int]] = field(default_factory=dict)
    set: Dict[str, Union[str, int]] = field(default_factory=dict)
    prefixes: List[str] = field(default_factory=list)

@dataclass
class BGPNeighbor:
    address: str
    description: str

@dataclass
class BGPPeerGroup:
    remote_type: str = "external"
    import_route_maps: List[BGPRouteMap] = field(default_factory=list)
    export_route_maps: List[BGPRouteMap] = field(default_factory=list)
    unnumbered_bgp_port_groups: List[str] = field(default_factory=list)
    neighbors: List[BGPNeighbor] = field(default_factory=list)

@dataclass
class BGPRedistribute:
    metric: Optional[int]
    route_maps: List[BGPRouteMap] = field(default_factory=list)

@dataclass
class BGPPrefixAggregate:
    prefix: str
    origin: Optional[str]
    route_map: Optional[BGPRouteMap]
    suppress_map: Optional[BGPRouteMap]
    as_set: bool = False
    summary_only: bool = False
    matching_med_only: bool = False

@dataclass
class BGPConfig:
    vrfid: int
    asn: int
    router_id: str
    peer_groups: Dict[str, BGPPeerGroup]
    redistribute: Dict[str, BGPRedistribute] = field(default_factory=dict)
    aggregated_addresses: List[BGPPrefixAggregate] = field(default_factory=list)
