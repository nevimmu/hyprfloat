import os
import json
from socket import socket, AF_UNIX, SOCK_STREAM
from .db_helper import DbHelper
from .utils import hyprctl
from .settings import CONF_DIR, SOCKET_PATH

def handle_event(event, db):
	if event.startswith('openwindow>>') \
	or event.startswith('workspace>>') \
	or event.startswith('closewindow>>') \
	or event.startswith('movewindow>>'):
		terminals = db.get('terminal_classes')
		monitors = db.get('monitors')

		workspace = json.loads(hyprctl(['activeworkspace', '-j']).stdout)
		workspace_id = workspace['id']
		active_monitor = workspace['monitor']

		clients = json.loads(hyprctl(['clients', '-j']).stdout)
		workspace_windows = [c for c in clients if c['workspace']['id'] == workspace_id]

		if len(workspace_windows) == 1:
			window = workspace_windows[0]
			if window['class'] in terminals:
				width = monitors[active_monitor]['width']
				height = monitors[active_monitor]['height']
				hyprctl(['dispatch', 'focuswindow', f'address:{window['address']}'])
				if not window['floating']:
					hyprctl(['dispatch', 'setfloating'])
				hyprctl(['dispatch', 'resizeactive', 'exact', str(width), str(height)])
				hyprctl(['dispatch', 'centerwindow'])
			
		else:
			active_window = hyprctl(['activewindow', '-j'])
			try:
				focus = json.loads(active_window.stdout)['address']
			except:
				focus = None

			for window in workspace_windows:
				if window['class'] in terminals and window['floating']:
					hyprctl(['dispatch', 'focuswindow', f'address:{window['address']}'])
					hyprctl(['dispatch', 'settiled'])

			hyprctl(['dispatch', 'focuswindow', f'address:{focus}'])

def main():
	os.makedirs(CONF_DIR, exist_ok=True)
	db = DbHelper()

	with socket(AF_UNIX, SOCK_STREAM) as sock:
		sock.connect(SOCKET_PATH)
		while True:
			event = sock.recv(1024).decode().strip()
			if event:
				handle_event(event, db)