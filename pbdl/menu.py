import tkinter as tk
from tkinter import ttk
from pbdl.core import *


"""

import tkinter as tk
from tkinter import ttk

keys = {'Left': 113, 'Up': 111, 'Right': 114, 'Down': 116, 'KP_Subtract': 82, 'KP_Add': 86, 'KP_Add': 86, 'KP_1': 87, 'KP_2': 88, 'KP_3': 89, 'KP_4': 83, 'KP_5': 84, 'KP_6': 85, 'KP_7': 79, 'KP_8': 80, 'KP_9': 81}
self.SPEED_DOUBLE_VAR = tk.DoubleVar()

slider_l = ttk.Scale(self.MAIN_WINDOW, from_=0, to=100, orient='vertical', variable=self.SPEED_DOUBLE_VAR, command=lambda: press_key("MOTOR_L"))
slider_r = ttk.Scale(self.MAIN_WINDOW, from_=0, to=100, orient='vertical', variable=self.SPEED_DOUBLE_VAR, command=lambda: press_key("MOTOR_L"))

button_left = tk.Button(self.MAIN_WINDOW, text='Left', command=lambda: press_key("Left"))
button_up = tk.Button(self.MAIN_WINDOW, text='Forward', command=lambda: press_key("Up"))
button_right = tk.Button(self.MAIN_WINDOW, text='Right', command=lambda: press_key("Left"))
button_down = tk.Button(self.MAIN_WINDOW, text='Reverse', command=lambda: press_key("Left"))
button_subtract = tk.Button(self.MAIN_WINDOW, text='Throttle -', command=lambda: press_key("KP_Subtract"))
button_add = tk.Button(self.MAIN_WINDOW, text='Throttle +', command=lambda: press_key("KP_Add"))
button_1 = tk.Button(self.MAIN_WINDOW, text='1', command=lambda: press_key("KP_1"))
button_2 = tk.Button(self.MAIN_WINDOW, text='2', command=lambda: press_key("KP_2"))
button_3 = tk.Button(self.MAIN_WINDOW, text='3', command=lambda: press_key("KP_3"))
button_4 = tk.Button(self.MAIN_WINDOW, text='4', command=lambda: press_key("KP_4"))
button_5 = tk.Button(self.MAIN_WINDOW, text='5', command=lambda: press_key("KP_5"))
button_6 = tk.Button(self.MAIN_WINDOW, text='6', command=lambda: press_key("KP_6"))
button_7 = tk.Button(self.MAIN_WINDOW, text='7', command=lambda: press_key("KP_7"))
button_8 = tk.Button(self.MAIN_WINDOW, text='8', command=lambda: press_key("KP_8"))
button_9 = tk.Button(self.MAIN_WINDOW, text='9', command=lambda: press_key("KP_9"))



"""

class UITorrent(Torrent):
	def __init__(self, data):
		super().__init__(data=data)

class PBDL_UI():
	"""
	TODO - add start_on_add to settings.json file (save_settings)
	TODO - bughunt:
		1. 
	"""
	def __init__(self, host='192.168.1.151'):
		self.HOST = host
		self.STATES = self._get_states()
		self.PBDL = PBDL()
		self.REMOTE = TransmissionRemote(host=self.HOST)
		self.TORRENT_IDS = []
		self.TORRENTS = self.REMOTE.getTorrents()
		#self.TAGGER = Tagger()
	def _get_states(self):
		d = {}
		d[4] = 'Downloading'
		d[3] = 'Seeding'
		d[2] = 'Queued'
		d[1] = 'Paused'
		d[0] = 'Unknown'
		return d
	def _get_state(self, code):
		return self.STATES[code]
	def getTorrents(self):
		self.TORRENTS = self.REMOTE.getTorrents()
		return self.TORRENTS
	def get_torrents_tree(self, parent=None):
		if parent is None:
			self.MAIN_WINDOW = tk.Tk()
		self.torrents_tree = ttk.Treeview(self.MAIN_WINDOW)
		self.torrents_tree.pack(side=tk.TOP, fill=tk.BOTH, pady=5)
		return self.torrents_tree
	def update(self):
		ids = list(self.getTorrents().keys())
		torrents = {}
		for tid in ids:
			data = self._get_info(tid=tid)
			data['HOST'] = self.HOST
			t = Torrent(data=data)
			torrents[tid] = t
		return torrents
	def update_torrents(self, repeat=True):
		for iid in self.torrents_tree.get_children():
			try:
				self.torrents_tree.delete(iid)
			except Exception as e:
				print(f"Couldn't remove item {iid} from tree: {e}")
		self.UPDATE = repeat
		torrents = self.update()
		for tid in torrents:
			t = torrents[tid]
			#iid = self.torrents_tree.selection()
			#self.torrents_tree.delete(iid)
			tl = self.torrents_tree.insert("", tk.END, text=t.__str__())
			keys = t.KEYS
			for key in keys:
				self.torrents_tree.insert(tl, tk.END, text=f"{key}: {t.__dict__[key]}")
		if self.UPDATE:
			self.MAIN_WINDOW.after(30000, self.update_torrents)
		return self.torrents_tree
	def get_query(self):
		query = self.entry.get()
		print("Query:", query)
		return query

	def search(self, query=None):
		self.results_var = tk.StringVar()
		self.results.delete(0, tk.END)#clear results list
		if query is None:
			query = self.get_query()
		ret = self.PBDL.search(query)
		lines = ret.__str__().splitlines()
		for line in lines:
			self.results.insert(tk.END, line)
		return ret

	def get_selected_torrent(self):
		idx = self.torrents_tree.focus()
		t = self.torrents_tree.item(idx)
		tid = t['text'].split(' - ')[0].split('ID:')[1]
		self.update_torrents()
		return tid

	def start(self):
		tid = self.get_selected_torrent()
		self.REMOTE.startTorrent(tid)
		self.update_torrents()

	def stop(self):
		tid = self.get_selected_torrent()
		self.REMOTE.stopTorrent(tid)
		self.update_torrents()

	def remove(self):
		tid = self.get_selected_torrent()
		ts[tid].remove()
		ts = self.REMOTE.getTorrents()
		tids = [tid for tid in ts]
		if tid in tids:
			_ = tids.pop(tids.index(tid))
			print("Torrent removed:", tid)
		else:
			print("Id not in ids:", tid)
		self.update_torrents()

	def remove_and_delete(self):
		tid = int(self.get_selected_torrent())
		ts = self.REMOTE.getTorrents()
		tids = [int(t) for t in ts]
		if tid in tids:
			try:
				ts[tid].purge()
				_ = tids.pop(tids.index(tid))
				print("Torrent deleted:", tid)
			except Exception as e:
				print(f"Error removing torrent: {e}")
		self.update_torrents()

	def start_all(self):
		self.REMOTE.startAllTorrents()
		self.update_torrents()

	def stop_all(self):
		self.REMOTE.stopAllTorrents()
		self.update_torrents()

	def download(self, did=None, start_on_add=True):
		if did is None:
			idx = self.results.curselection()
			did = self.results.get(idx).split(':')[0]
			print(f"Download id grabbed from UI: {did}")
		ret = [d for d in self.PBDL.RESULTS.ITEMS if d.id == did]
		if len(ret) == 1:
			thash = ret[0].get_hash()
			self.REMOTE.addTorrent(thash, start_on_add=start_on_add)
			print("Torrents updated!")
		else:
			print("Multiple found:")
			ditem = ret[len(ret)-1]
			thash = ditem.get_hash()
			self.REMOTE.addTorrent(thash, start_on_add=start_on_add)
		self.update_torrents()

	def _get_info_(self, tid=None, host='192.168.1.151'):
		return subprocess.check_output(f"transmission-remote {host} -t {tid} --info", shell=True).decode().strip()
	def _get_splitters(self):
		splitters = []
		splitters.append('Id: ')
		splitters.append('Name: ')
		splitters.append('Hash: ')
		splitters.append('Magnet: ')
		splitters.append('State: ')
		splitters.append('Location: ')
		splitters.append('Percent Done: ')
		splitters.append('ETA: ')
		splitters.append('Download Speed: ')
		splitters.append('Upload Speed: ')
		splitters.append('Have: ')
		splitters.append('Availability: ')
		splitters.append('Total size: ')
		splitters.append('Downloaded: ')
		splitters.append('Uploaded: ')
		splitters.append('Ratio: ')
		#splitters.append('Error: ')
		splitters.append('Peers: ')
		splitters.append('connected to ')
		splitters.append('uploading to ')
		splitters.append('downloading from ')
		return splitters
	def _get_info(self, tid):
		out = {}
		data = self._get_info_(tid=tid)
		splitters = self._get_splitters()
		for s in splitters:
			if ':' in s:
				key = s.split(':')[0].upper()
			else:
				if 'connected to ' in s:
					key = 'PEERSCONNECTED'
				elif 'uploading to ' in s:
					key = 'RATEUPLOAD'
				elif 'downloading from ' in s:
					key = 'RATEDOWNLOAD'
			try:
				if s in data:
					value = data.split(s)[1].split("\n")[0]
					if key == 'ETA':
						value = value.split(' ')[0]
					out[key] = value
				else:
					print(f"splitter not in data: {s}")
					print(f"'{data}'")
			except Exception as e:
				print(f"{data}\n\n{key}\n\nError parsing key: {e}")
				out[key] = value
		return out
	def enable_start_on_add(self):
		self.REMOTE.START_TORRENT_ON_ADD = True
		self.start_on_add.set(f"Start on add: {self.REMOTE.START_TORRENT_ON_ADD}")
		print(f"Toggled start on add: {self.REMOTE.START_TORRENT_ON_ADD}")
	def disable_start_on_add(self):
		self.REMOTE.START_TORRENT_ON_ADD = False
		self.start_on_add.set(f"Start on add: {self.REMOTE.START_TORRENT_ON_ADD}")
		print(f"Toggled start on add: {self.REMOTE.START_TORRENT_ON_ADD}")

	def _get_season_strings(self):
		out = []
		for i in range(0, 300):
			if i < 10:
				i = f"0{i}"
			out.append(f"S{i}")
		return out

	def _get_en_strings(self):
		out = []
		for i in range(0, 100):
			if i < 10:
				i = f"0{i}"
			out.append(f"E{i}")
		return out

	def _get_year_strings(self):
		out = []
		for i in range(1900, 2050):
			out.append(str(i))
		return out

	def test_for_year(self, filepath):
		years = self._get_year_strings()
		for year in years:
			if year in filepath:
				return year
		return None

	def test_for_seasons(self, filepath):
		seasons = self._get_season_strings()
		for s in seasons:
			if s in filepath:
				return s
		return None

	def test_for_en(self, filepath):
		ens = self._get_en_strings()
		for en in ens:
			if en in filepath:
				return en
		return None


	def should_ignore(self, filepath):
		ignore = ['.txt', '.jpg', '.nfo']
		for ig in ignore:
			if ig in filepath:
				return True
		return False

	def get_series_name(self, filepath, season):
		sn = filepath.split(season)[0].replace('.', ' ').strip().title()
		return os.path.basename(sn)

	def build_fname_series(self, filepath, series_name, season, episode_number, episode_name=None):
		dest = os.path.join(self.REMOTE.FINISHED_SAVE_PATH, 'Series', series_name, season)
		ext = os.path.splitext(filepath)[1].replace('.', '')
		s = f"{series_name.title()}.{season}{episode_number}"
		fname = f"{s}.{ext}"
		out = f"{dest}/{fname}"
		return out

	def build_fname_movies(self, filepath, title, year):
		dest = os.path.join(self.REMOTE.FINISHED_SAVE_PATH, 'Movies', f"{title} ({year})")
		ext = os.path.splitext(filepath)[1].replace('.', '')
		s = f"{title} ({year}).{ext}"
		return os.path.join(dest, s)

	def removeTorrent(self, tid, delete=False):
		if type(tid) == int:
			t = self.getTorrents()[tid]
		else:
			t = tid
			tid = t.ID
		if delete:
			t.purge()
		else:
			t.remove()
		print("Torrent removed:", tid)

	def migrate(self):
		def move(filepath, destination):
			path = os.path.dirname(destination)
			os.makedirs(path, exist_ok=True)
			com = f"mv -f '{filepath}' '{destination}'"
			print("command:", com)
			try:
				return subprocess.check_output(com, shell=True).decode().strip()
			except Exception as e:
				print(f"Unable to move file ('{filepath}'): {e}")
				return None
			if os.path.exists(destination):
				try:
					print("Copy successful! Removing original...")
					os.remove(filepath)
					return True
				except Exception as e:
					print(f"File copied, but couldn't delete parent! Reason: {e}")
					input()
					return False
			else:
				print(f"Error moving file: '{filepath}' >> '{destination}': file not at destination!")
				return False
		torrents = self.getTorrents()
		finished = [t for t in list(torrents.values()) if t.ISFINISHED]
		for t in finished:
			info = t.get_info()
			if type(t) == list:
				parent_dir = t[0]['LOCATION']
			else:
				parent_dir = t.LOCATION
			if type(t) == list:
				name = t[0]['NAME']
			else:
				name = t.NAME
			orig_path = os.path.join(parent_dir, name)
			pos = 0
			files = [f for f in t.get_files() if '.txt' not in f]
			for filepath in files:
				pos += 1
				print(f"{pos}/{len(files)} - {filepath}")
				if not os.path.exists(filepath):
					print("File not found:", filepath)
				else:
					if not self.should_ignore(filepath):
						season = self.test_for_seasons(filepath)
						en = self.test_for_en(filepath)
						year = self.test_for_year(filepath)
						if year is None and season is not None:
							media_type = 'Series'
						elif year is not None and season is None:
							media_type = 'Movies'
						if media_type == 'Series':
							series_name = self.get_series_name(filepath, season=season)
							if '0' in season:
								season = season.replace('0', '')
							if '0' in str(en):
								en = en.replace('0', '')
							dest = self.build_fname_series(filepath=filepath, series_name=series_name, season=season, episode_number=en)
						elif media_type == 'Movies':
							title = filepath.split(f"({year})")[0].strip().title()
							print("title, year:", title, year)
							dest = self.build_fname_movies(filepath=filepath, title=title, year=year)
						ret = move(filepath, dest)
			if os.path.exists(orig_path):
				print("Success! Removing torrent...")
				print(t.purge())
				print("Done!")

	def get_menubar(self, root=None):
		if root is None:
			root = self.MAIN_WINDOW
		self.menubar = tk.Menu(root)
		self.torrentsmenu = tk.Menu(self.menubar, tearoff=1)
		self.torrentsmenu.add_command(label="Start Selected", command=self.start)
		self.torrentsmenu.add_command(label="Stop Selected", command=self.stop)
		self.torrentsmenu.add_separator()
		self.torrentsmenu.add_command(label="Start All", command=self.start_all)
		self.torrentsmenu.add_command(label="Stop All", command=self.stop_all)
		self.torrentsmenu.add_separator()
		self.torrentsmenu.add_command(label="Remove Torrent", command=self.remove)
		self.torrentsmenu.add_command(label="Remove and Delete Data", command=self.remove_and_delete)
		self.torrentsmenu.add_separator()
		self.torrentsmenu.add_command(label="Refresh Torrents", command=self.update_torrents)
		self.torrentsmenu.add_separator()
		self.torrentsmenu.add_command(label="Start Torrent on Add: Enable", command=self.enable_start_on_add)
		self.torrentsmenu.add_command(label="Start Torrent on Add: Disable", command=self.disable_start_on_add)
		self.torrentsmenu.add_separator()
		self.torrentsmenu.add_command(label="Migrate finished...", command=self.migrate)
		self.menubar.add_cascade(label="Torrents", menu=self.torrentsmenu)
		self.helpmenu = tk.Menu(self.menubar, tearoff=0)
		self.helpmenu.add_command(label="Help Index")
		self.helpmenu.add_command(label="About...")
		self.menubar.add_cascade(label="Help", menu=self.helpmenu)
		return self.menubar

	def main(self):
		self.MAIN_WINDOW = tk.Tk()
		self.MAIN_WINDOW.geometry('960x720')
		self.MAIN_WINDOW.config(width=960, height=720, menu=self.get_menubar(self.MAIN_WINDOW))
		self.title_label = tk.Label(self.MAIN_WINDOW, text='Pirate Bay Downloader:', width=60)
		self.start_on_add = tk.StringVar()
		self.start_on_add.set(f"Start on add: {self.REMOTE.START_TORRENT_ON_ADD}")
		self.start_on_add_label = tk.Label(self.MAIN_WINDOW, textvariable=self.start_on_add)
		#btn2 = tk.Button(win, text='fart2')
		self.torrents_tree = self.get_torrents_tree(parent=self.MAIN_WINDOW)
		self.results = tk.Listbox(self.MAIN_WINDOW, width=100)
		self.entry = tk.Entry(self.MAIN_WINDOW)
		self.search_btn = tk.Button(self.MAIN_WINDOW, text='Search!', command=self.search)
		self.download_btn = tk.Button(self.MAIN_WINDOW, text='Download!', command=self.download)
		self.title_label.pack(side=tk.TOP, fill=tk.BOTH, pady=5)
		self.start_on_add_label.pack(side=tk.TOP, fill=tk.BOTH, pady=5)
		self.torrents_tree.pack(side=tk.BOTTOM, fill=tk.BOTH, pady=5)
		self.results.pack(side=tk.RIGHT, fill=tk.BOTH, pady=5)
		self.entry.pack(side=tk.TOP, fill=tk.BOTH, pady=5)
		self.search_btn.pack(side=tk.TOP, fill=tk.Y, pady=5)
		self.download_btn.pack(side=tk.TOP, fill=tk.Y, pady=5)
		self.update_torrents()
		self.start_on_add.set(f"Start on add: {self.REMOTE.START_TORRENT_ON_ADD}")
		self.MAIN_WINDOW.mainloop()

if __name__ == "__main__":
	ui = PBDL_UI()
	ui.main()
	#t = MediaTagger()
	#t.TAGGER_WINDOW.mainloop()
