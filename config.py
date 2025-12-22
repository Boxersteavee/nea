from configparser import ConfigParser, ExtendedInterpolation
import os

def setup():
    config = ConfigParser(interpolation=ExtendedInterpolation())
    default = config['DEFAULT']
    default['user_data_dir'] = 'user_data'
    default['gedcom_dir'] = '${user_data_dir}/gedcom'
    default['db_dir'] = '${user_data_dir}/sql'
    default['api_port'] = '8085'
    default['session_ttl'] = '2'
    with open('config.ini', 'w') as configfile:
        config.write(configfile)

def get_cfg() -> dict[str, str]:
    config = ConfigParser(interpolation=ExtendedInterpolation())
    if not os.path.exists('config.ini'):
        setup()
    config.read('config.ini')
    cfg = {}
    for key in config['DEFAULT']:
        cfg[key] = config.get('DEFAULT', key)
    return cfg