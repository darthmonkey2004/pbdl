import pickle
import os
from pbdl2 import TMDB
import subprocess
import json
import mutagen
from mutagen.id3 import ID3, TIT2

class MKV():
	def __init__(self, filepath=None):
		self.FILEPATH = filepath
		self.TMDB = TMDB()
		self.INFO = self.get_media_info(filepath)
		self.MEDIA_TYPE = self.INFO['MEDIA_TYPE']
		if self.FILEPATH is not None:
			self.TAGS = self.read()
			if self.TAGS == {}:
				if self.INFO is not None:
					self.save(data=self.INFO)
					self.TAGS = self.read()
			else:
				self.TAGS = self.read()
		elif self.FILEPATH is None:
			print("Filepath is None!")
			self.TAGS = {}
			self.INFO = None
			self.MEDIA_TYPE = None
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
		self.MEDIA_TYPE = mdata['MEDIA_TYPE']
		if self.MEDIA_TYPE == 'Movies':
			data = self.TMDB.search_movies(mdata['TITLE'])
			out = data
			for i in data:
				if mdata['YEAR'] == i['year'] and mdata['TITLE'] == i['title']:
					out = i
					break
			for k in out:
				mdata[k] = out[k]
			return mdata
		elif self.MEDIA_TYPE == 'Series':
			en = int(mdata['EPISODE_NUMBER'])
			data = self.TMDB.search_episodes(series_name=mdata['SERIES_NAME'], season=mdata['SEASON'])[en]
			for k in data:
				key = str(k.upper())
				mdata[key] = data[k]
			return mdata
		
	def save(self, data=None, target_filepath=None):
		data = {}
		if self.TAGS != {}:
			for k in self.TAGS:
				key = k.upper()
				data[key] = self.TAGS[k]
		if self.INFO != {}:
			for k in self.INFO:
				key = k.upper()
				data[key] = self.INFO[k]
		if target_filepath is None:
			target_filepath = self.FILEPATH
		l = []
		for k in data:
			key = k.upper()
			v = data[k]
			l.append(f"{key}={v}")
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
			sstring, series_name, season, episode_number = self.TMDB.se_isin(filepath=self.FILEPATH, return_string_match=True)
			data['series_name'] = series_name
			data['season'] = season
			data['episode_number'] = episode_number
		elif media_type == 'Movies':
			_, data['title'], data['year'] = mdata
		data['media_type'] = media_type
		return data
	def read(self, filepath=None):
		def getProps(filepath):
			return json.loads(subprocess.check_output(f"mkvmerge -i '{filepath}' --identification-format json", shell=True).decode().strip())
		if filepath is not None:
			self.FILEPATH = filepath
		props = getProps(self.FILEPATH)
		duration = props['container']['properties']['duration']
		info = props['container']['properties']['title']
		return self.parse_info_string(info)

class Match():
	def __init__(self, filepath):
		self.FILEPATH = filepath
		self.DATA = self.get_media_info(filepath=self.FILEPATH)
		for k in self.DATA:
			v = self.DATA[k]
			key = k.upper()
			self.__dict__[key] = v

	def get_match_percentage(self, s1, match_key='TITLE'):
		def get_ct(obj):
			return len([pos + i for i in range(1, obj.span()[1]+1)])
		text = self.__dict__[match_key]
		m1 = re.match(s1, text)
		m2 = re.match(text, text)
		return round(get_ct(m1)/get_ct(m2) * 100, 2)



class MP4():
	def __init__(self, filepath='/media/monkey/usbhd/Media/Chappie (2015) [1080p]/Chappie.2015.1080p.BluRay.x264.YIFY.mp4', media_type=None):
		self.FILEPATH = filepath
		self.MUTAGEN_OBJ = mutagen.File(filepath)
		self.TAGS = self.read()
		self.TMDB = TMDB()
		if media_type is not None:
			self.MEDIA_TYPE = media_type
			if self.MEDIA_TYPE != 'Music':
				self.INFO = self.get_media_info(filepath)
			else:
				self.INFO = {}
		else:
			self.INFO = self.get_media_info(filepath)
		if self.INFO is not None:
			self.save(data=self.INFO)
	def get_media_info(self, filepath=None):
		out = {}
		if filepath is None:
			filepath = self.FILEPATH
		mdata = self.TMDB.guess_media_type(filepath)
		self.MEDIA_TYPE = mdata['MEDIA_TYPE']
		if self.MEDIA_TYPE == 'Movies':
			data = self.TMDB.search_movies(mdata['TITLE'])
			for i in data:
				try:
					if mdata['TITLE'] == i['title']:
						if mdata['YEAR'] == i['year']:
							out = i
							break
						else:
							print("title match, but not year.", i)
							out = i
							break
				except Exception as e:
					print(f"Error parsing data from movie search: {e}")
			for k in out:
				mdata[k] = out[k]
			return mdata
		elif self.MEDIA_TYPE == 'Series':
			en = int(mdata['EPISODE_NUMBER'])
			data = self.TMDB.search_episodes(series_name=mdata['SERIES_NAME'], season=mdata['SEASON'])[en]
			for k in data:
				key = str(k.upper())
				mdata[key] = data[k]
			return mdata
	def _get_props(self):
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
		props['0015'] = 'IMDBID'
		props['0016'] = 'RELEASE_DATE'
		props['0017'] = 'IMAGE'
		props['0018'] = 'TSSE'
		props['0019'] = 'COPYRIGHT'
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
		props['IMDBID'] = '0015'
		props['RELEASE_DATE'] = '0016'
		props['IMAGE'] = '0017'
		props['TSSE'] = '0018'#id3 mutagen 'title' info object tag
		props['COPYRIGHT'] = '0019'
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
		if '©' in s:
			return self._get_props()['COPYRIGHT']
		for c in s:
			out.append(str(chars.index(c.upper())))
		return "".join(out)
	def read(self):
		props = self._get_props()
		if self.MUTAGEN_OBJ is None:
			return {}
		if self.MUTAGEN_OBJ.tags is None:
			return {}
		t = self.MUTAGEN_OBJ.tags
		tags = {}
		for k, v in t.items():
			if k == 'TSSE':
				k = 'AABI'
			#print("k:", k)
			k = self._conv_to_dec(k)
			#print("new k:", k)
			if k not in list(props.keys()):
				print(f"Key not in props: {k}")
			else:

				key = props[k]
				self.__dict__[key] = v
				tags[key] = v
		self.TAGS = tags
		return tags
	def save(self, data=None, filepath=None):
		if data is None:
			data = self.TAGS
		if filepath is None:
			filepath = self.FILEPATH
		for prop in data:
			v = data[prop]
			self.update(prop=prop, v=data[prop])
		self.MUTAGEN_OBJ.save()
		print("Tag saved!")
	def update(self, prop, v):
		prop = prop.upper()
		if prop == 'MEDIA_TYPE' or prop == '0000':
			self.MUTAGEN_OBJ.update(AAAA=str(v))
		if prop == 'TITLE' or prop == '0001':	
			self.MUTAGEN_OBJ.update(AAAB=str(v))
		if prop == 'FILEPATH' or prop == '0002':
			self.MUTAGEN_OBJ.update(AAAC=str(v))
		if prop == 'YEAR' or prop == '0003':
			self.MUTAGEN_OBJ.update(AAAD=str(v))
		if prop == 'SERIES_NAME' or prop == '0004':
			self.MUTAGEN_OBJ.update(AAAE=str(v))
		if prop == 'SEASON' or prop == '0005':
			self.MUTAGEN_OBJ.update(AAAF=str(v))
		if prop == 'EPISODE_NUMBER' or prop == '0006':
			self.MUTAGEN_OBJ.update(AAAG=str(v))
		if prop == 'EPISODE_NAME' or prop == '0007':
			self.MUTAGEN_OBJ.update(AAAH=str(v))
		if prop == 'EXTENSION' or prop == '0008':
			self.MUTAGEN_OBJ.update(AAAI=str(v))
		if prop == 'ARTIST' or prop == '0009':
			self.MUTAGEN_OBJ.update(AAAJ=str(v))
		if prop == 'ALBUM' or prop == '0010':
			self.MUTAGEN_OBJ.update(AABA=str(v))
		if prop == 'TRACK_NUMBER' or prop == '0011':
			self.MUTAGEN_OBJ.update(AABB=str(v))
		if prop == 'DESCRIPTION' or prop == '0012':
			self.MUTAGEN_OBJ.update(AABC=str(v))
		if prop == 'POSTER_URL' or prop == '0013':
			self.MUTAGEN_OBJ.update(AABD=str(v))
		if prop == 'SUBTITLES_FILE' or prop == '0014':
			self.MUTAGEN_OBJ.update(AABE=str(v))
		if prop == 'IMDBID' or prop == '0015':
			self.MUTAGEN_OBJ.update(AABF=str(v))
		if prop == 'RELEASE_DATE' or prop == '0016':
			self.MUTAGEN_OBJ.update(AABG=str(v))
		if prop == 'IMAGE' or prop == '0017':
			self.MUTAGEN_OBJ.update(AABH=str(v))
	


class Tag():
	def __init__(self, filepath):
		self.AUDIO_EXTS = ['.mp3', '.wav', '.pcm']
		self.VIDEO_EXTS = ['.mp4', '.mkv', '.wmv', '.avi', '.mov', '.mpg', '.flv']
		self.FILEPATH = filepath
		self.TAG = self._get_tag(filepath=self.FILEPATH)
	def _get_tag(self, filepath=None):
		if filepath is None:
			filepath = self.FILEPATH
		self.EXT = os.path.splitext(filepath)[1]
		if self.EXT == '.mp4':
			return MP4(filepath=filepath)
		elif self.EXT == '.mp3':
			return MP4(filepath=filepath, media_type='Music')
		elif self.EXT == '.mkv':
			return MKV(filepath=filepath)
		else:
			print("Unhandled extension:", self.EXT)
			return None
	def save(self):
		self.TAG.save()
	def read(self):
		return self.TAG.read()
	def update(self, data):
		for k in data:
			key = k.upper()
			self.TAG.update(key, data[k])
		self.TAG.save()

class Tagger():
	def __init__(self, media_path='/media/monkey/usbhd/Media'):
		self.MEDIADIR = media_path
		self.SAVEFILE = os.path.join(self.MEDIADIR, 'mediafiles.dat')
		self.AUDIO_EXTS = ['.mp3', '.wav', '.pcm']
		self.VIDEO_EXTS = ['.mp4', '.mkv', '.wmv', '.avi', '.mov', '.mpg', '.flv']
		self.MEDIA_FILES = []
	def _find_media(self, ext):
		com = f"find '{self.MEDIADIR}' -name '*{ext}'"
		return subprocess.check_output(com, shell=True).decode().strip().splitlines()
	def scanMedia(self):
		out = {}
		out['audio'] = []
		out['video'] = []
		print("Scanning for video files...")
		for ext in self.VIDEO_EXTS:
			print("searching extension:", ext)
			out['video'] += self._find_media(ext=ext)
		print("Scanning for audio files...")
		for ext in self.AUDIO_EXTS:
			print("searching extension:", ext)
			out['audio'] += self._find_media(ext=ext)
		print("Finished!")
		return out
	def saveFileData(self, data=None):
		if data is None:
			data = out
		with open(self.SAVEFILE, 'wb') as f:
			pickle.dump(data, f)
			f.close()
			print("File data saved!")
	def readFileData(self):
		try:
			with open(self.SAVEFILE, 'rb') as f:
				data = pickle.load(f)
				f.close()
		except Exception as e:
			print(f"Error reading file: {e}")
			return None
	def loadMediaTags(self):
		files = self.readFileData()
		if files is None:
			print("Save file not found! Scanning...")
			files = self.scanMedia()
			self.saveFileData(data=files)
		tags = []
		for mtype in files:
			for filepath in files[mtype]:
				print(f"tagging {mtype} file: {filepath}")
				tags.append(Tag(filepath=filepath))
		return tags
				
		
		
if __name__ == "__main__":
	mkvfile = '/media/monkey/usbhd/Media/Series/Rick and Morty/S8/Rick and Morty.s8e1.mkv'
	mp4file = '/media/monkey/usbhd/Media/Chappie (2015) [1080p]/Chappie.2015.1080p.BluRay.x264.YIFY.mp4'
	mp3file = '/media/monkey/usbhd/Media/Music/Beastie Boys - Sabotage [z5rRZdiu1UE].mp3'
	#t = Tagger()
	#tags = t.loadMediaTags()
	#print(tags)
	t = MP4('/media/monkey/usbhd/Media/Series/Red Dwarf/S10/Red Dwarf.S10E4.Entangled.mp4')
	print(dir(t))
