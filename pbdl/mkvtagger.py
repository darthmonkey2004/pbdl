import os
from pbdl2 import TMDB
import subprocess
import json
import mutagen

class MKV():
	def __init__(self, filepath=None):
		self.FILEPATH = filepath
		self.TMDB = TMDB()
		if self.FILEPATH is not None:
			self.TAGS = self.read()
			if self.TAGS == {}:
				self.INFO = self.get_media_info(filepath)
				if self.INFO is not None:
					self.save(data=self.INFO)
					self.TAGS = self.read()
			else:
				self.TAGS = self.read()
		elif self.FILEPATH is None:
			print("Filepath is None!")
			self.TAGS = {}
			self.INFO = None
	def get_tagid(self, key):
		return self.get_props()[key.upper()]
	def get_props(self):
		props = {}
		props['0000'] = 'MEDIA_TYPE'
		props['0001'] = 'TITLE'
		props['0002'] = 'FILEPATH'
		props['0003'] = 'YEAR'
		props['0004'] = 'SERIES_NAME'
		props['0005'] = 'SEASON'
		props['0006'] = 'EPISODE_NUMBER'
		props['0007'] = 'EPISODE_NAME'
		props['0008'] = 'EXTENSION'
		props['0009'] = 'ARTIST'
		props['0010'] = 'ALBUM'
		props['0011'] = 'TRACK_NUMBER'
		props['0012'] = 'DESCRIPTION'
		props['0013'] = 'POSTER_URL'
		props['0014'] = 'SUBTITLES_FILE'
		props['MEDIA_TYPE'] = '0000'
		props['TITLE'] = '0001'
		props['FILEPATH'] = '0002'
		props['YEAR'] = '0003'
		props['SERIES_NAME'] = '0004'
		props['SEASON'] = '0005'
		props['EPISODE_NUMBER'] = '0006'
		props['EPISODE_NAME'] = '0007'
		props['EXTENSION'] = '0008'
		props['ARTIST'] = '0009'
		props['ALBUM'] = '0010'
		props['TRACK_NUMBER'] = '0011'
		props['DESCRIPTION'] = '0012'
		props['POSTER_URL'] = '0013'
		props['SUBTITLES_FILE'] = '0014'
		return props
	def _conv_to_text(self, s):
		chars = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
		out = []
		for c in str(s):
			out.append(chars[int(c)])
		return "".join(out)
	def _conv_to_dec(self, s='AAAD'):
		chars = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
		out = []
		for c in s:
			out.append(str(chars.index(c.upper())))
		return "".join(out)
	def get_media_info(self, filepath=None):
		if filepath is None:
			filepath = self.FILEPATH
		mdata = self.TMDB.guess_media_type(filepath)
		print("mdata:", mdata)
		if mdata['MEDIA_TYPE'] == 'Movies':
			data = self.TMDB.search_movies(mdata['TITLE'])
			for i in data:
				print("i:", i)
				if mdata['YEAR'] == i['year'] and mdata['TITLE'] == i['title']:
					out = i
					break
			for k in out:
				mdata[k] = out[k]
			return mdata
		elif mdata['MEDIA_TYPE'] == 'Series':
			data = self.TMDB.search_episodes(series_name=mdata['SERIES_NAME'], season=mdata['SEASON'])[mdata['EPISODE_NUMBER']]
			print(data)
		
	def save(self, data=None, target_filepath=None):
		if target_filepath is None:
			target_filepath = self.FILEPATH
		if data is None:
			data = self.TAGS
		l = []
		for k in data:
			v = data[k]
			l.append(f"{k}={v}")
		string = "|".join(l)
		com = f"mkvpropedit '{target_filepath}' --edit info --set 'title={string}'"
		return subprocess.check_output(com, shell=True).decode().strip()
	def update(self, k, v):
		tagid = self.get_tagid(k)
		tagcode = self._conv_to_text(tagid)
		self.TAGS[tagcode] = v
	def delete(self, filepath=None):
		"""
		TODO - clear method
		"""
		if filepath is None:
			filepath = self.FILEPATH
		com = f"mkvpropedit '{filepath}' --edit info --delete 'title'"
		return subprocess.check_output(com, shell=True).decode().strip()
	def parse_info_string(self, info):
		data = {}
		mdata = info.split('|')
		for item in mdata:
			if '=' in item:
				k = item.split('=')[0]
				v = item.split('=')[1]
			else:
				k = item
				v = None
			key = k.upper()
			self.__dict__[key] = v
			data[key] = v
		try:
			media_type = self.MEDIA_TYPE
		except Exception as e:
			print("Couln't get media type:", e)
			info = self.TMDB.guess_media_type(self.FILEPATH)
			media_type = info['MEDIA_TYPE']
		if media_type == 'Series':
			for item in mdata:
				k = item.split('=')[0]
				v = item.split('=')[1]
				key = k.upper()
				data[k] = v
			sstring = self.TMDB.se_isin(filepath=self.FILEPATH)
			fname = os.path.basename(self.FILEPATH)
			data['series_name'] = fname.split(f".{sstring}.")[0]
			data['season'] = int(sstring.split('S')[1].split('E')[0])
			data['episode_number'] = int(sstring.split('E')[1])
		elif media_type == 'Movies':
			_, data['title'], data['year'] = mdata
		return data
	def read(self, filepath=None):
		def getProps(filepath):
			return json.loads(subprocess.check_output(f"mkvmerge -i '{filepath}' --identification-format json", shell=True).decode().strip())
		if filepath is not None:
			self.FILEPATH = filepath
		props = getProps(self.FILEPATH)
		duration = props['container']['properties']['duration']
		info = props['container']['properties']['title']
		print("info:", info)
		return self.parse_info_string(info)

if __name__ == "__main__":
	t = MKV(filepath='/media/monkey/usbhd/Media/Series/Rick and Morty/S8/Rick and Morty.s8e1.mkv')
	#t.update("EPISODE_NAME", "Summer of All Fears")
	#t.write()
	print(t.TAGS)
