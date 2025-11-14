import os

__version__ = '0.4.4'

HOME = os.getenv('HOME', os.getenv('USERPROFILE')) or os.path.expanduser('~')
XDG_CONF_DIR = os.getenv('XDG_CONFIG_HOME', os.path.join(HOME, '.config'))

CONF_DIR = os.path.join(XDG_CONF_DIR, 'hyprfloat')
SOCKET_PATH = f"{os.environ['XDG_RUNTIME_DIR']}/hypr/{os.environ['HYPRLAND_INSTANCE_SIGNATURE']}/.socket2.sock"
