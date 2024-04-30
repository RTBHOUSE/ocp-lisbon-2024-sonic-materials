import json
import yaml
import shutil
import dataclasses
from pathlib import Path
import logging
from .models.config import Config
from .models.port import PortList
logger = logging.getLogger(__name__)

def load_default_sku_config(root_path):
    raw = (root_path / 'config' / 'platforms' / 'default_sku.csv').read_text()
    return {line.split(',')[1]: line.split(',')[0] for line in raw.split('\n') if len(line) > 0}

def find_hwsku(root_path, state):
    logger.info('Searching for hwsku for switches')
    default_sku = load_default_sku_config(root_path)
    for config in state['parsed_configs']:
        switch = (config.hostname, config.datacenter)
        logger.debug("Searching for hwsku for %s in %s" % switch)
        if config.hwsku is not None:
            logger.debug('Switch %s in %s already has hwsku set: %s' % (switch[0], switch[1], config.hwsku))
            continue
        hwsku = default_sku.get(config.platform)
        if hwsku is None:
            raise Exception('Cannot find hwsku for switch %s in %s' % switch)
        logger.debug('Setting hwsku: "%s" for %s in %s' % (hwsku, switch[0], switch[1]))
        config.hwsku = hwsku

def clean_ports_list(ports, interfaces):
    return [x for x in ports if x in interfaces]

def deep_clean_ports_lists(config, interfaces):
    if dataclasses.is_dataclass(config):
        iter_list = list(config.__dict__.items())
        for key, val in iter_list:
            if isinstance(val, PortList) and "portchannels" not in key:
                setattr(config, key, clean_ports_list(val, interfaces))
            else:
                setattr(config, key,deep_clean_ports_lists(val, interfaces))
    if isinstance(config, dict):
        for key, val in config.items():
            if isinstance(val, PortList) and "portchannels" not in key:
                config[key] = clean_ports_list(val, interfaces)
            else:
                config[key] = deep_clean_ports_lists(val, interfaces)
    if isinstance(config, list):
        config = [clean_ports_list(x) if isinstance(x, PortList) else deep_clean_ports_lists(x, interfaces) for x in config]
    return config

def run_step(root_path, state):
    logger.info('Running fixers')
    find_hwsku(root_path, state)
    for config in state['parsed_configs']:
        switch = (config.hostname, config.datacenter)
        logger.debug("Remove unused breakout ports for %s in %s" % switch)
        deep_clean_ports_lists(config, state['interfaces'][switch])
