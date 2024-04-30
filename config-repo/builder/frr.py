import json
import yaml
import shutil
from pathlib import Path
import logging
from .models.config import Config
from .models.port import PortList
from dataclasses import asdict
import jinja2
logger = logging.getLogger(__name__)


def run_step(root_path, state):
    gen_path = root_path / "_build/frr"
    if gen_path.exists():
        shutil.rmtree(gen_path)
    gen_path.mkdir(parents=True)

    env = jinja2.Environment(loader=jinja2.FileSystemLoader(str(root_path / 'templates')))
    env.globals['enumerate'] = enumerate
    env.globals['len'] = len
    state['frr'] = {}
    for config in state['parsed_configs']:
        switch = (config.hostname, config.datacenter)
        logger.info("Generating configuration for %s in %s" % switch)
        template = env.get_template(config.frr_template)
        rendered = template.render(asdict(config, dict_factory=dict))
        rendered = prettify_frr(rendered)
        state['frr'][switch] = rendered
        (gen_path / ('.'.join(switch) + '.conf')).write_text(rendered)


def prettify_frr(cfg):
    output = []
    tabs = 0
    for line in cfg.split('\n'):
        line = line.strip()
        if len(line) == 0:
            continue

        for tag in ['exit']:
            if line.startswith(tag):
                tabs -= 1
                break
        output.append('  ' * tabs + line)
        for tag in ['router', 'address-family', 'route-map']:
            if line.startswith(tag):
                tabs += 1
                break

    return '\n'.join(output)
