import os
import json
from socket import socket, AF_UNIX, SOCK_STREAM
from .db_helper import DbHelper
from .utils import hyprctl
from .settings import CONF_DIR, SOCKET_PATH

class Hyprfloat:
	def __init__(self):
		self.db = DbHelper()
		self.address_to_ignore = []

	def handle_open_window(self, event_data):
		data = event_data.split(',')
		if data[3] == '':
			self.address_to_ignore.append(data[0])
			return True
		return False

	def handle_close_window(self, event_data):
		data = event_data.split(',')
		if data[0] in self.address_to_ignore:
			self.address_to_ignore.remove(data[0])

	def handle_change_floating_mode(self, event_data, workspace_windows):
		window_address, float_mode = event_data.split(',')
		float_mode = int(float_mode)
		try:
			window = next(w for w in workspace_windows if w['address'] == f'0x{window_address}')
		except StopIteration:
			return

		terminals = self.db.get('terminal_classes')
		if window['class'] in terminals:
			hyprctl(['dispatch', 'focuswindow', f'address:{window['address']}'])
			if not float_mode:
				hyprctl(['dispatch', 'tagwindow', 'hyprfloat:False'])
			else:
				hyprctl(['dispatch', 'tagwindow', ''])

	def handle_change(self, workspace_windows, active_monitor):
		monitors = self.db.get('monitors')
		terminals = self.db.get('terminal_classes')

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
				if window['class'] in terminals and window['floating'] and window['address'] != focus:
					hyprctl(['dispatch', 'focuswindow', f'address:{window['address']}'])
					hyprctl(['dispatch', 'settiled'])

			if focus:
				new_win = next((w for w in workspace_windows if w['address'] == focus), None)
				if new_win and new_win['floating'] and new_win['class'] in terminals:
					hyprctl(['dispatch', 'focuswindow', f'address:{focus}'])
					hyprctl(['dispatch', 'movewindow', 'r'])
					hyprctl(['dispatch', 'focuswindow', f'address:{focus}'])
					hyprctl(['dispatch', 'settiled'])

			hyprctl(['dispatch', 'focuswindow', f'address:{focus}'])

	def handle_event(self, event):
		event_type, event_data = event.split('>>', 1)
		workspace = json.loads(hyprctl(['activeworkspace', '-j']).stdout)
		workspace_id = workspace['id']
		active_monitor = workspace['monitor']
		clients = json.loads(hyprctl(['clients', '-j']).stdout)
		workspace_windows = [c for c in clients if c['workspace']['id'] == workspace_id]

		if event_type == 'openwindow':
			if self.handle_open_window(event_data):
				return
			self.handle_change(workspace_windows, active_monitor)
		elif event_type == 'closewindow':
			self.handle_close_window(event_data)
			self.handle_change(workspace_windows, active_monitor)
		elif event_type == 'changefloatingmode':
			self.handle_change_floating_mode(event_data, workspace_windows)
		elif event_type in ('workspace', 'movewindow'):
			self.handle_change(workspace_windows, active_monitor)

def main():
	os.makedirs(CONF_DIR, exist_ok=True)
	hyprfloat = Hyprfloat()

	with socket(AF_UNIX, SOCK_STREAM) as sock:
		sock.connect(SOCKET_PATH)
		while True:
			event = sock.recv(1024).decode().strip()
			if event:
				hyprfloat.handle_event(event)