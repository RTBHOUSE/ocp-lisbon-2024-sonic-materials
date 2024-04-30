import json
import yaml
import shutil
from pathlib import Path
import logging
logger = logging.getLogger(__name__)


def selective_merge(base_obj, delta_obj):
    if not isinstance(base_obj, dict) or not isinstance(delta_obj, dict):
        return delta_obj
    common_keys = set(base_obj).intersection(delta_obj)
    new_keys = set(delta_obj).difference(common_keys)
    ret = dict(base_obj)
    for k in common_keys:
        if k in delta_obj and delta_obj[k] is None:
            del ret[k]
        else:
            ret[k] = selective_merge(base_obj[k], delta_obj[k])
    for k in new_keys:
        if k in delta_obj and delta_obj[k] is None:
            continue
        ret[k] = delta_obj[k]
    return ret


def run_step(root_path, state):
    # Prepare build directory
    gen_path = root_path / "_build/merged_config"
    if gen_path.exists():
        shutil.rmtree(gen_path)
    gen_path.mkdir(parents=True)
    
    gen_dc_path = gen_path / "dc"
    gen_dc_path.mkdir()
    gen_switch_path = gen_path / "switch"
    gen_switch_path.mkdir()

    config_path = root_path / "config"
    global_config = yaml.safe_load(Path(config_path / "global.yaml").read_text())
    dc_config_paths = (config_path / 'dc').glob('*.yaml')
    
    state['merged_configs'] = {'datacenters': [], 'switches': []}
    for dc_config_path in dc_config_paths:
        dc = dc_config_path.stem.split('.')[0]
        logger.info('Merging config for DC: ' + dc)

        dc_config = yaml.safe_load(dc_config_path.read_text())
        dc_config = selective_merge(global_config, dc_config)
        dc_config['datacenter'] = dc

        state['merged_configs']['datacenters'].append(dc_config)
        (gen_dc_path / (dc + '.yaml')).write_text(yaml.dump(dc_config))
        
        (gen_switch_path / dc).mkdir()
    
        for switch_config_path in (config_path / 'switches' / dc).glob('./*.yaml'):
            hostname = switch_config_path.stem.split('.')[0]
            logger.info('Merging config for %s in %s' % (hostname, dc))
            switch_delta_config = yaml.safe_load(switch_config_path.read_text())
            switch_config = selective_merge(dc_config, switch_delta_config)
            switch_config['datacenter'] = dc
            switch_config['hostname'] = hostname
            state['merged_configs']['switches'].append(switch_config)
            (gen_switch_path / dc / (hostname + '.yaml')).write_text(yaml.dump(switch_config))
