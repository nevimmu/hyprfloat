import os
import json
import re
from socket import socket, AF_UNIX, SOCK_STREAM
from .db_helper import DbHelper
from .utils import hyprctl
from .settings import CONF_DIR, SOCKET_PATH

class Hyprfloat:
	def __init__(self):
		'''Initialize the database and the list of windows to ignore.'''
		self.db = DbHelper()
		self.address_to_ignore = []
		self.user_tiled_windows = []

	def handle_open_window(self, event_data):
		'''Handle the `openwindow` event from Hyprland's socket.'''
		ignore_titles = self.db.get('ignore_titles', []) or []
		data = event_data.split(',')
		address = f'0x{data[0]}'

		data_empty = data[3] == ''
		data_ignore = any(re.match(pattern, data[3]) for pattern in ignore_titles)

		# If the window is a new window with empty title, add it to the ignore list.
		if data_empty or data_ignore:
			self.address_to_ignore.append(address)
			return True
		return False

	def handle_close_window(self, event_data):
		'''Handle the `closewindow` event from Hyprland's socket.'''
		address = f'0x{event_data}'
		# If the window is in the ignore list, remove it.
		if address in self.address_to_ignore:
			self.address_to_ignore.remove(address)
		if address in self.user_tiled_windows:
			self.user_tiled_windows.remove(address)

	def handle_change_floating_mode(self, event_data, workspace_windows):
		'''Handle the `changefloatingmode` event from Hyprland's socket.'''
		window_address, floating = event_data.split(',')
		address = f'0x{window_address}'

		# Find the window that was changed.
		try:
			window = next(w for w in workspace_windows if w['address'] == address)
		except StopIteration:
			return

		terminals = self.db.get('terminal_classes') or []
		# If the window is a terminal, add or remove it from the user_tiled_windows list.
		if window['class'] in terminals:
			if floating == '0':  # tiled
				if address not in self.user_tiled_windows:
					self.user_tiled_windows.append(address)
			else:  # floating
				if address in self.user_tiled_windows:
					self.user_tiled_windows.remove(address)

	def handle_change(self, workspace_windows, active_monitor, event_info=None):
		'''Handle the floating and tiling of windows.'''
		monitors = self.db.get('monitors') or {}
		terminals = self.db.get('terminal_classes') or []
		ignore_titles = self.db.get('ignore_titles', []) or []
		event_type, event_data = event_info if event_info else (None, None)
		visible_windows = [w for w in workspace_windows if not w['hidden']]

		# If there is only one visible window in the workspace, float it.
		if len(visible_windows) == 1:
			window = visible_windows[0]
			# If the window is tagged as not floating, do nothing.
			if window['address'] in self.user_tiled_windows:
				return

			# If the window is not in the terminal list, do nothing.
			if window['class'] not in terminals:
				return

			if window['title'] in ignore_titles:
				return

			# Check if monitor configuration exists
			if active_monitor not in monitors:
				return

			width = monitors[active_monitor]['width']
			height = monitors[active_monitor]['height']
			offset = monitors[active_monitor]['offset']

			# If the window is not floating, float it.
			if not window['floating']:
				hyprctl(['dispatch', 'setfloating', f'address:{window['address']}'])
			# Resize and center the window.
			hyprctl(['dispatch', 'resizewindowpixel', 'exact', str(width), str(height), f',address:{window['address']}'])
			hyprctl(['dispatch', 'centerwindow', f',address:{window['address']}'])
			# Offset the window if needed.
			hyprctl(['dispatch', 'movewindowpixel', str(offset[0]), str(offset[1]), f',address:{window['address']}'])

		# If there are multiple windows in the workspace, tile them.
		elif len(workspace_windows) >= 2 and event_type in {'openwindow', 'movewindow'} and event_data:
			new_window_address = '0x' + event_data.split(',')[0]
			try:
				new_window = next(w for w in workspace_windows if w['address'] == new_window_address)
				existing_window = next(w for w in workspace_windows if w['address'] != new_window_address)
			except StopIteration:
				# If the window is not found, do nothing and let the default behavior handle it.
				pass
			else:
				if (
					existing_window['title'] in ignore_titles or
					new_window['title'] in ignore_titles or
					(new_window['floating'] == True and event_type != 'movewindow')
				):
					return
				# Float the new window, center it and move it to the right then
				# tile the existing one, finally tile the new one.
				hyprctl(['dispatch', 'setfloating', f'address:{new_window['address']}'])
				hyprctl(['dispatch', 'centerwindow', f',address:{new_window['address']}'])
				hyprctl(['dispatch', 'movewindow', 'r'])
				hyprctl(['dispatch', 'settiled', f'address:{existing_window['address']}'])
				hyprctl(['dispatch', 'focuswindow', f'address:{new_window['address']}'])
				hyprctl(['dispatch', 'settiled'])

		elif len(visible_windows) >= 2 and event_type == 'workspace':
			# On workspace change, ensure all floating terminal windows are tiled.
			# Prioritize by focus history to tile the most recently focused windows first.
			for window in sorted(workspace_windows, key=lambda w: w['focusHistoryID'], reverse=True):
				if (
					window['class'] in terminals and
					window['floating'] and
					window['address'] not in self.user_tiled_windows
				):
					hyprctl(['dispatch', 'centerwindow', f',address:{window['address']}'])
					hyprctl(['dispatch', 'focuswindow', f'address:{window['address']}'])
					hyprctl(['dispatch', 'movewindow', 'r'])
					hyprctl(['dispatch', 'focuswindow', f'address:{window['address']}'])
					hyprctl(['dispatch', 'settiled'])

	def handle_event(self, event):
		'''Main event handler.'''
		try:
			event_type, event_data = event.split('>>', 1)
		except:
			return
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
			self.handle_change(workspace_windows, active_monitor, (event_type, event_data))
		elif event_type == 'changefloatingmode':
			self.handle_change_floating_mode(event_data, workspace_windows)
		elif event_type in ('workspace', 'movewindow', 'activewindow', 'windowtitle'):
			self.handle_change(workspace_windows, active_monitor, (event_type, event_data))

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