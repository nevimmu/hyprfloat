import os
import json
from socket import socket, AF_UNIX, SOCK_STREAM
from .db_helper import DbHelper
from .utils import hyprctl
from .settings import CONF_DIR, SOCKET_PATH

ADDRESS_TO_IGNORE = []

def handle_event(event, db):
	global ADDRESS_TO_IGNORE

	if event.startswith('openwindow>>') \
	or event.startswith('workspace>>') \
	or event.startswith('changefloatingmode>>') \
	or event.startswith('closewindow>>') \
	or event.startswith('movewindow>>'):
		event_data = event.split('>>')[1]

		terminals = db.get('terminal_classes')
		monitors = db.get('monitors')

		workspace = json.loads(hyprctl(['activeworkspace', '-j']).stdout)
		workspace_id = workspace['id']
		active_monitor = workspace['monitor']

		clients = json.loads(hyprctl(['clients', '-j']).stdout)
		workspace_windows = [c for c in clients if c['workspace']['id'] == workspace_id]

		try:
			window_address = event_data.split(',')[0]
			window = next(w for w in workspace_windows if w['address'] == f'0x{window_address}')
		except:
			window = None

		data =  event_data.split(',')
		if event.startswith('openwindow>>'):
			if data[3] == '':
				ADDRESS_TO_IGNORE.append(data[0])
				return

		if event.startswith('closewindow>>'):
			if data[0] in ADDRESS_TO_IGNORE:
				ADDRESS_TO_IGNORE.remove(data[0])
				return

		if event.startswith('changefloatingmode>>'):
			event_data = event.split('>>')[1]
			window_address, float_mode = event_data.split(',')
			float_mode = int(float_mode)

			if not window:
				return
			
			if window['class'] in terminals:
				hyprctl(['dispatch', 'focuswindow', f'address:{window['address']}'])
				if not float_mode:
					hyprctl(['dispatch', 'tagwindow', 'hyprfloat:False' ])
				else:
					hyprctl(['dispatch', 'tagwindow', '' ])
			
			return

		
		if len(workspace_windows) == 1:
			window = workspace_windows[0]
			if window['tags'] == ['hyprfloat:False']:
				return

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
				if window['class'] in terminals \
				and window['floating'] \
				and window['address'] != focus:
					hyprctl(['dispatch', 'focuswindow', f'address:{window['address']}'])
					hyprctl(['dispatch', 'settiled'])
			
			if focus:
				new_win = next((w for w in workspace_windows if w['address'] == focus), None)
				if new_win and new_win['floating']:
					hyprctl(['dispatch', 'focuswindow', f'address:{focus}'])
					hyprctl(['dispatch', 'movewindow', 'r'])
					hyprctl(['dispatch', 'focuswindow', f'address:{focus}']) # Focus window to tile to the right
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