import os
import json
import math
from .settings import CONF_DIR

def get_defaults():
	'''Get a list of monitors with their size'''
	from .utils import hyprctl
	# Get the list of monitors from hyprctl.
	monitors_json = json.loads(hyprctl(['monitors', '-j']).stdout)

	resize = 0.71
	monitors = {}
	# For each monitor, get the size and calculate the new size.
	for m in monitors_json:

		# Check if the monitor is transformed.
		transform = m['transform'] in [1, 3, 5, 7]
		w = m['width'] if not transform else m['height']
		h = m['height'] if not transform else m['width']

		# Calculate the new size.
		monitors[m['name']] = {
			'width': math.ceil(w * resize),
			'height': math.ceil(h * resize),
			'offset': [0, 0]
		}
	
	return monitors

class DbHelper():
	'''A helper class to manage the JAMS database stored in a JSON file.'''

	def __init__(self):
		'''Initialize the database.'''
		self._conf_name = 'hyprfloat.json'
		self._conf_file = os.path.join(CONF_DIR, self._conf_name)

		# If the config file doesn't exist, create it.
		if not os.path.isfile(self._conf_file):
			self.create_config()
		else:
			# Check if the config file needs to be updated.
			config = self._read_config()
			updated = False
			for monitor in config['monitors'].values():
				if 'offset' not in monitor:
					monitor['offset'] = [0, 0]
					updated = True
			
			if updated:
				self._write_config(config)

	def create_config(self):
		'''Create the config file.'''
		self._write_config({
			'terminal_classes': ['kitty', 'alacritty', 'org.kde.konsole', 'com.mitchellh.ghostty'],
			'ignore_titles': [],
			'monitors': get_defaults(),
		})

	def _read_config(self):
		'''Reads the config file and returns the data as a dictionary.'''
		with open(self._conf_file, 'r') as f:
			return json.load(f)

	def _write_config(self, config):
		'''Writes the given config dictionary to the config file.'''
		with open(self._conf_file, 'w') as f:
			json.dump(config, f, indent='\t', separators=(',', ':'))

	def get(self, source, default=None):
		'''Retrieves a value from the config file.'''
		data = self._read_config()
		try:
			return data[source]
		except:
			return default

	def set(self, source, value):
		'''Sets a value in the config file.'''
		data = self._read_config()
		data[source] = value
		self._write_config(data)