import subprocess

def hyprctl(cmd):
	return subprocess.run(
		['hyprctl'] + cmd, 
		capture_output = True,
		text = True,
	)