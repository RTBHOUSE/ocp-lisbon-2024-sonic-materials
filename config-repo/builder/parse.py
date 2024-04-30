import json
import yaml
import shutil
from pathlib import Path
import logging
from .models.config import Config
logger = logging.getLogger(__name__)


def run_step(root_path, state):
    state['parsed_configs'] = []
    for raw_config in state['merged_configs']['switches']:
        logger.info('Parsing config for switch %s in %s' % (raw_config['hostname'], raw_config['datacenter']))
        parsed = Config.load(obj=raw_config)
        state['parsed_configs'].append(parsed)
