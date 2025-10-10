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

	def handle_change(self, workspace_windows, active_monitor):
		'''Handle the floating and tiling of windows.'''
		monitors = self.db.get('monitors')
		terminals = self.db.get('terminal_classes')

		# If there is only one window in the workspace, float it.
		if len(workspace_windows) == 1:
			window = workspace_windows[0]
			# If the window is tagged as not floating, do nothing.
			if 'hyprfloat:False' in window['tags']:
				return

			# If the window is not in the terminal list, do nothing.
			if window['class'] not in terminals:
				return

			width = monitors[active_monitor]['width']
			height = monitors[active_monitor]['height']
			hyprctl(['dispatch', 'focuswindow', f'address:{window['address']}'])
			# If the window is not floating, float it.
			if not window['floating']:
				hyprctl(['dispatch', 'setfloating'])
			# Resize and center the window.
			hyprctl(['dispatch', 'resizeactive', 'exact', str(width), str(height)])
			hyprctl(['dispatch', 'centerwindow'])

		# If there are multiple windows in the workspace, tile them.
		else:
			active_window = hyprctl(['activewindow', '-j'])
			try:
				# Get the focused window.
				focus = json.loads(active_window.stdout)['address']
			except:
				focus = None

			# Tile all floating terminals.
			for window in workspace_windows:
				if window['class'] in terminals and window['floating'] and window['address'] != focus:
					hyprctl(['dispatch', 'focuswindow', f'address:{window['address']}'])
					hyprctl(['dispatch', 'settiled'])

			# If there is a focused window, tile it.
			if focus:
				new_win = next((w for w in workspace_windows if w['address'] == focus), None)
				# If the focused window is floating and in terminal list, tile it.
				if new_win and new_win['floating'] and new_win['class'] in terminals:
					hyprctl(['dispatch', 'focuswindow', f'address:{focus}'])
					hyprctl(['dispatch', 'movewindow', 'r'])
					hyprctl(['dispatch', 'focuswindow', f'address:{focus}'])
					hyprctl(['dispatch', 'settiled'])

			# Focus back the original window.
			hyprctl(['dispatch', 'focuswindow', f'address:{focus}'])

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
			self.handle_change(workspace_windows, active_monitor)
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