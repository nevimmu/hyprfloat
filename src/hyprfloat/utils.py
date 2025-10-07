import subprocess
import json
import math

def hyprctl(cmd):
	return subprocess.run(
		['hyprctl'] + cmd, 
		capture_output = True,
		text = True,
	)

def get_defaults():
	'''Get a list of monitors with their size'''
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