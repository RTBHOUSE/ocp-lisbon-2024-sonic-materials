import json
import yaml
import shutil
from pathlib import Path
import logging
from .models.config import Config
from .breakout_utils import BreakoutCfg
logger = logging.getLogger(__name__)

def get_platform_interfaces(root_path, config):
    path = root_path / 'config' / 'platforms' / (config.platform + '.json')
    platform_cfg = json.loads(path.read_text())
    return platform_cfg['interfaces']

def run_step(root_path, state):
    state['interfaces'] = {}
    for config in state['parsed_configs']:
        switch = (config.hostname, config.datacenter)
        state['interfaces'][switch] = {}
        logger.info("Generating breakouts configuration for %s in %s" % switch)
        interfaces_config = get_platform_interfaces(root_path, config)
        for breakout in config.breakouts:
            breakouted = []
            for port_id in breakout.ports:
                ifname = 'Ethernet%s' % port_id
                if ifname not in interfaces_config:
                    continue
                breakouted.append(port_id)
                interface_properties = interfaces_config[ifname]
                cfg = BreakoutCfg(ifname, breakout.mode, interface_properties).get_config()
                for key,val in cfg.items():
                    state['interfaces'][switch][int(key.replace('Ethernet', ''))] = val
            breakout.ports = breakouted # Remove not used ports
