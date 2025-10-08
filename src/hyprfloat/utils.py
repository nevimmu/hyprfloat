import subprocess

def hyprctl(cmd):
	'''A wrapper for the hyprctl command.'''
	return subprocess.run(
		['hyprctl'] + cmd, 
		capture_output = True,
		text = True,
	)