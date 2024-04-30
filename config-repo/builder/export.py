import json
import shutil
from pathlib import Path
import logging
from .models.config import Config
logger = logging.getLogger(__name__)

def save_config(state, switch, path):
    logger.info("Exporting configuration for %s in %s" % (switch, path))
    path.mkdir(parents=True)

    config_db = state['config_db'][switch]
    (path / 'config_db.json').write_text(json.dumps(config_db, indent=4))

    frr_config = state['frr'][switch]
    (path / 'frr.conf').write_text(frr_config)

def run_step(root_path, state):
    dist_path = root_path / "dist"
    if dist_path.exists():
        shutil.rmtree(dist_path)
    dist_path.mkdir(parents=True)

    for config in state['parsed_configs']:
        switch = (config.hostname, config.datacenter)
        switch_path = dist_path / 'by-host' / config.datacenter / config.hostname
        save_config(state, switch, switch_path)
        by_mac_path = (dist_path / 'by-mac' / config.mac)
        save_config(state, switch, by_mac_path)
