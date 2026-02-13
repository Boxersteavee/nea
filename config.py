from configparser import ConfigParser, ExtendedInterpolation
import os

# Set default config values
def setup():
    config = ConfigParser(interpolation=ExtendedInterpolation()) # Allows the config to use nested variables.
    default = config['DEFAULT']
    default['user_data_dir'] = 'user_data'
    default['gedcom_dir'] = '${user_data_dir}/gedcom'
    default['db_dir'] = '${user_data_dir}/trees'
    default['api_port'] = '8085'
    default['session_ttl'] = '2'
    default['tree_name'] = 'SET_NAME'
    default['host_ip'] = '127.0.0.1'
    with open('config.ini', 'w') as configfile:
        config.write(configfile)

# Function used by other files to get a dictionary of the config
def get_cfg() -> dict[str, str]:
    config = ConfigParser(interpolation=ExtendedInterpolation())
    # Check if the config file exists, if not then run setup()
    if not os.path.exists('config.ini'):
        setup()
    # Read the config file, add each key to a dictionary then return the dictionary
    config.read('config.ini')
    cfg = {}
    for key in config['DEFAULT']:
        cfg[key] = config.get('DEFAULT', key)
    return cfg