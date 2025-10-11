import os
import json
from socket import socket, AF_UNIX, SOCK_STREAM
from .db_helper import DbHelper
from .utils import hyprctl
from .settings import CONF_DIR, SOCKET_PATH

class Hyprfloat:
	def __init__(self):
		'''Initialize the database and the list of windows to ignore.'''
		self.db = DbHelper()
		self.address_to_ignore = []

	def handle_open_window(self, event_data):
		'''Handle the `openwindow` event from Hyprland's socket.'''
		data = event_data.split(',')
		# If the window is a new window with empty title, add it to the ignore list.
		if data[3] == '':
			self.address_to_ignore.append(data[0])
			return True
		return False

	def handle_close_window(self, event_data):
		'''Handle the `closewindow` event from Hyprland's socket.'''
		data = event_data.split(',')
		# If the window is in the ignore list, remove it.
		if data[0] in self.address_to_ignore:
			self.address_to_ignore.remove(data[0])

	def handle_change_floating_mode(self, event_data, workspace_windows):
		'''Handle the `changefloatingmode` event from Hyprland's socket.'''
		window_address, _ = event_data.split(',')

		# Find the window that was changed.
		try:
			window = next(w for w in workspace_windows if w['address'] == f'0x{window_address}')
		except StopIteration:
			return

		terminals = self.db.get('terminal_classes')
		# If the window is a terminal, tag it.
		if window['class'] in terminals:
			hyprctl(['dispatch', 'tagwindow', 'hyprfloat:False'])

	def handle_change(self, workspace_windows, active_monitor, event_info=None):
		'''Handle the floating and tiling of windows.'''
		monitors = self.db.get('monitors')
		terminals = self.db.get('terminal_classes')
		ignore_titles = self.db.get('ignore_titles', [])
		event_type, event_data = event_info if event_info else (None, None)

		# If there is only one window in the workspace, float it.
		if len(workspace_windows) == 1:
			window = workspace_windows[0]
			# If the window is tagged as not floating, do nothing.
			if 'hyprfloat:False' in window['tags']:
				return

			# If the window is not in the terminal list, do nothing.
			if window['class'] not in terminals:
				return

			if window['title'] in ignore_titles:
				return

			width = monitors[active_monitor]['width']
			height = monitors[active_monitor]['height']
			offset = monitors[active_monitor]['offset']

			hyprctl(['dispatch', 'focuswindow', f'address:{window['address']}'])
			# If the window is not floating, float it.
			if not window['floating']:
				hyprctl(['dispatch', 'setfloating'])
			# Resize and center the window.
			hyprctl(['dispatch', 'resizeactive', 'exact', str(width), str(height)])
			hyprctl(['dispatch', 'centerwindow'])
			# Offset the window if needed.
			hyprctl(['dispatch', 'movewindowpixel', str(offset[0]), str(offset[1]), f',address:{window['address']}'])

		# If there are multiple windows in the workspace, tile them.
		elif len(workspace_windows) == 2 and event_type == 'openwindow':
			event_data = event_info[1]
			new_window_address = '0x' + event_data.split(',')[0]
			try:
				new_window = next(w for w in workspace_windows if w['address'] == new_window_address)
				existing_window = next(w for w in workspace_windows if w['address'] != new_window_address)
			except StopIteration:
				# If the window is not found, do nothing and let the default behavior handle it.
				pass
			else:
				# Float the new window, tile the existing one, then tile the new one.
				hyprctl(['dispatch', 'setfloating', f'address:{new_window["address"]}'])
				hyprctl(['dispatch', 'settiled', f'address:{existing_window["address"]}'])
				hyprctl(['dispatch', 'settiled', f'address:{new_window["address"]}'])

	def handle_event(self, event):
		'''Main event handler.'''
		event_type, event_data = event.split('>>', 1)
		# Get the current workspace and windows.
		workspace = json.loads(hyprctl(['activeworkspace', '-j']).stdout)
		workspace_id = workspace['id']
		active_monitor = workspace['monitor']
		clients = json.loads(hyprctl(['clients', '-j']).stdout)
		workspace_windows = [c for c in clients if c['workspace']['id'] == workspace_id]

		# Handle the event.
		if event_type == 'openwindow':
			if self.handle_open_window(event_data):
				return
			self.handle_change(workspace_windows, active_monitor, (event_type, event_data))
		elif event_type == 'closewindow':
			self.handle_close_window(event_data)
			self.handle_change(workspace_windows, active_monitor)
		elif event_type == 'changefloatingmode':
			self.handle_change_floating_mode(event_data, workspace_windows)
		elif event_type in ('workspace', 'movewindow'):
			self.handle_change(workspace_windows, active_monitor)

def main():
	'''Main function of the script.'''
	os.makedirs(CONF_DIR, exist_ok=True)
	hyprfloat = Hyprfloat()

	# Connect to Hyprland's socket and listen for events.
	with socket(AF_UNIX, SOCK_STREAM) as sock:
		sock.connect(SOCKET_PATH)
		while True:
			event = sock.recv(1024).decode().strip().split('\n')[0]
			if event:
				hyprfloat.handle_event(event)