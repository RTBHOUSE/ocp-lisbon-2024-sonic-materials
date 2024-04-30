import json
import yaml
import shutil
from pathlib import Path
import logging
from .models.config import Config
logger = logging.getLogger(__name__)

def generate_features(config, config_db, root_path):
    path = root_path / 'config' / 'default_features.json'
    features = json.loads(path.read_text())
    for name, cfg in features.items():
        if name == 'database':
            cfg['high_mem_alert'] = 'enabled'
            cfg['state'] = 'always_enabled' 
            cfg['auto_restart'] = 'always_enabled'
        elif name not in config.services:
            cfg['state'] = 'disabled'
            cfg['auto_restart'] = 'disabled'
        else:
            cfg['high_mem_alert'] = 'enabled'
            cfg['state'] = config.services.get(name).value
            cfg['auto_restart'] = 'enabled'
    config_db['FEATURE'] = features
        

def generate_ntp(config, config_db):
    config_db['NTP_SERVER'] = {
        config.vpn: {}
    }

def generate_device_metadata(config, config_db):
    config_db['DEVICE_METADATA'] = {
        'localhost': {
            'buffer_model': 'traditional',
            'default_bgp_status': 'up',
            'default_pfcwd_status': 'disable',
            'hostname': config.hostname,
            'hwsku': config.hwsku,
            'mac': config.mac,
            'platform': config.platform,
            'synchronous_mode': 'enable',
            'type': 'ToRRouter',
            'docker_routing_config_mode': 'split'
        }
    }

def generate_breakout_cfg(config, config_db):
    config_db['BREAKOUT_CFG'] = {
        'Ethernet' + str(port_id): {
            'brkout_mode': breakout.mode
        }
        for breakout in config.breakouts
        for port_id in breakout.ports
    }

def generate_ports(config, config_db, interfaces):
    config_db['PORT'] = {'Ethernet' + str(x): interfaces[x] for x in interfaces}
    for name, port_group in config.port_groups.items():
        logger.debug('Configuring ports in group %s' % name)
        ports = port_group.ports
        for portchannel_id in port_group.portchannels:
            portchannel = next(filter(lambda x: x.id == portchannel_id, config.portchannels))
            ports = ports + portchannel.ports
        for port_id in ports:
            ifname = 'Ethernet' + str(port_id)
            if port_group.fec is not None:
                config_db['PORT'][ifname]['fec'] = port_group.fec
            if port_group.mtu is not None:
                config_db['PORT'][ifname]['mtu'] = str(port_group.mtu)
            if port_group.admin_status is not None:
                config_db['PORT'][ifname]['admin_status'] = port_group.admin_status
    for ifname, port in config_db['PORT'].items():
        port_id = int(ifname.replace('Ethernet', ''))
        if 'admin_status' not in port:
            port['admin_status'] = 'down'
        if 'mtu' not in port:
            port['mtu'] = '9100'
        if 'autoneg' not in port:
            port['autoneg'] = 'off'
        if port_id in config.port_descriptions:
            port['description'] = config.port_descriptions[port_id]

def generate_static_routes(config, config_db):
    config_db['STATIC_ROUTE'] = {
        "Vrf%s|%s" % (route.vrfid, route.prefix): {
            "blackhole": "false",
            "distance": "0",
            "ifname": "",
            "nexthop": route.nexthop,
            "nexthop-vrf": "Vrf%s" % route.vrfid
        }
        for route in config.static_routes
        if "Vrf%s" % route.vrfid in config_db['VRF']
    }

def generate_vlans(config, config_db):
    config_db['VLAN'] = {
        "Vlan" + str(vlanid): {
            "vlanid": str(vlanid),
            'dhcp_servers': vlan.dhcp_servers
        }
        for vlanid, vlan in config.switched_vlans.items()
    }

def generate_vlan_interfaces(config, config_db):
    vlans = {}
    for vlanid, vlan in config.switched_vlans.items():
        vlans["Vlan" + str(vlanid)] = {
            "vrf_name": "Vrf" + str(vlan.vrfid)
        }
        for address in vlan.addresses:
            vlans["Vlan%s|%s" % (vlanid, address)] = {}
    config_db['VLAN_INTERFACE'] = vlans

def generate_vlan_members(config, config_db):
    members = {}
    for vlanid, vlan in config.switched_vlans.items():
        # Tagged ports
        ports = vlan.tagged_ports
        portchannels = vlan.tagged_portchannels
        for port_group in vlan.tagged_port_groups:
            ports = ports + config.port_groups[port_group].ports
            portchannels = portchannels + config.port_groups[port_group].portchannels
        for portid in ports:
            members["Vlan%s|Ethernet%s" % (vlanid, portid)] = { "tagging_mode": "tagged"}
        for portid in portchannels:
            members["Vlan%s|PortChannel%04d" % (vlanid, portid)] = { "tagging_mode": "tagged"}

        # Untagged ports
        ports = vlan.untagged_ports
        portchannels = vlan.untagged_portchannels
        for port_group in vlan.untagged_port_groups:
            ports = ports + config.port_groups[port_group].ports
            portchannels = portchannels + config.port_groups[port_group].portchannels
        for portid in ports:
            members["Vlan%s|Ethernet%s" % (vlanid, portid)] = { "tagging_mode": "untagged"}
        for portid in portchannels:
            members["Vlan%s|PortChannel%04d" % (vlanid, portid)] = { "tagging_mode": "untagged"}
    config_db['VLAN_MEMBER'] = members

def generate_portchannels(config, config_db):
    config_db['PORTCHANNEL'] = {
        "PortChannel%04d" % portid: {
            "admin_status": port_group.admin_status,
            "fast_rate": "false",
            "lacp_key": "auto",
            "min_links": "1",
            "mix_speed": "false",
            "mtu": str(port_group.mtu)
        }
        for port_group in config.port_groups.values()
        for portid in port_group.portchannels
    }

def generate_portchannel_members(config, config_db):
    config_db['PORTCHANNEL_MEMBER'] = {
        "PortChannel%04d|Ethernet%s" % (portchannel.id, portid): {}
        for portchannel in config.portchannels
        for portid in portchannel.ports
    }

def generate_vrfs(config, config_db):
    unique_vrfs = {
        vlan.vrfid for vlan in config.switched_vlans.values()
    }
    unique_vrfs.update({
        vlan.vrfid for vlan in config.routed_vlans.values()
    })
    config_db['VRF'] = {
        "Vrf%s" % vrfid: {}
        for vrfid in list(unique_vrfs)
    }

def generate_vlan_sub_interfaces(config, config_db):
    config_db['VLAN_SUB_INTERFACE'] = {
        "Ethernet%s.%s" % (portid, vlanid): {
            "vrf_name": "Vrf" + str(vlan.vrfid)
        }
        for vlanid, vlan in config.routed_vlans.items()
        for port_group_id in vlan.port_groups
        for portid in config.port_groups[port_group_id].ports
    }

def generate_frr_raw(config, config_db, state):
    config_db['BGP_RAW'] = {
        'ASIC-0': {
            "frr.conf": state['frr'][(config.hostname, config.datacenter)]
        }
    }

def run_step(root_path, state):
    gen_path = root_path / "_build/config_db"
    if gen_path.exists():
        shutil.rmtree(gen_path)
    gen_path.mkdir(parents=True)

    state['config_db'] = {}
    for config in state['parsed_configs']:
        switch = (config.hostname, config.datacenter)
        logger.info("Generating config_db for %s in %s" % switch)

        config_db = {}
        generate_ntp(config, config_db)
        generate_device_metadata(config, config_db)
        generate_breakout_cfg(config, config_db)
        generate_ports(config, config_db, state['interfaces'][switch])
        generate_features(config, config_db, root_path)
        generate_vlans(config, config_db)
        generate_vlan_interfaces(config, config_db)
        generate_vlan_members(config, config_db)
        generate_portchannels(config, config_db)
        generate_portchannel_members(config, config_db)
        generate_vrfs(config, config_db)
        generate_static_routes(config, config_db)
        generate_vlan_sub_interfaces(config, config_db)
        #generate_frr_raw(config, config_db, state)

        state['config_db'][switch] = config_db
        (gen_path / ('.'.join(switch) + '.json')).write_text(json.dumps(config_db, indent=4))
