from configparser import ConfigParser
import os

config = ConfigParser()

def setup():
    default = config['DEFAULT']
    default['user_data_dir'] = 'user_data'
    default['gedcom_dir'] = '${user_data_dir}/gedcom'
    default['db_dir'] = '${user_data_dir}/sql'
    default['api_port'] = '8085'
    with open('config.ini', 'w') as configfile:
        config.write(configfile)

def get_cfg() -> dict[str, str]:
    if not os.path.exists('config.ini'):
        setup()
    config.read('config.ini')
    cfg = dict(config.defaults())
    return cfg