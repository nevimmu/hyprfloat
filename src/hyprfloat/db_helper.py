import os
import json
import math
from .settings import CONF_DIR

def get_defaults():
	'''Get a list of monitors with their size'''
	from .utils import hyprctl
	monitors_json = json.loads(hyprctl(['monitors', '-j']).stdout)

	resize = 0.71
	monitors = {}
	for m in monitors_json:

		transform = m['transform'] in [1, 3, 5, 7]
		w = m['width'] if not transform else m['height']
		h = m['height'] if not transform else m['width']

		monitors[m['name']] = {
			'width': math.ceil(w * resize),
			'height': math.ceil(h * resize)
		}
	
	return monitors

class DbHelper():
	'''
	A helper class to manage the JAMS database stored in a JSON file.
	'''

	def __init__(self):
		self._conf_name = 'hyprfloat.json'
		self._conf_file = os.path.join(CONF_DIR, self._conf_name)

		# If the config file doesn't exist, create it.
		if not os.path.isfile(self._conf_file):
			self.create_config()

	def create_config(self):
		self._write_config({
			'terminal_classes': ['kitty', 'alacritty', 'org.kde.konsole', 'com.mitchellh.ghostty'],
			'monitors': get_defaults(),
		})

	def _read_config(self):
		'''
		Reads the config file and returns the data as a dictionary.
		'''
		with open(self._conf_file, 'r') as f:
			return json.load(f)

	def _write_config(self, config):
		'''
		Writes the given config dictionary to the config file.
		'''
		with open(self._conf_file, 'w') as f:
			json.dump(config, f, indent='\t', separators=(',', ':'))

	def get(self, source):
		'''
		Retrieves a value from the config file.
		'''
		data = self._read_config()
		return data[source]

	def set(self, source, value):
		'''
		Sets a value in the config file.
		'''
		data = self._read_config()
		data[source] = value
		self._write_config(data)