import mutagen
from pbdl2 import TMDB

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
	def __init__(self, filepath='/media/monkey/usbhd/Media/Chappie (2015) [1080p]/Chappie.2015.1080p.BluRay.x264.YIFY.mp4'):
		self.FILEPATH = filepath
		self.MUTAGEN_OBJ = mutagen.File(filepath)
		self.TAGS = self.read()
		self.TMDB = TMDB()
		self.INFO = self.get_media_info(filepath)
		if self.INFO is not None:
			self.save(data=self.INFO)
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
		props['IMAEG'] = '0017'
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
	def read(self):
		props = self._get_props()
		t = self.MUTAGEN_OBJ.tags
		tags = {}
		for k, v in t.items():
			key = props[self._conv_to_dec(k)]
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



filepath = '/media/monkey/usbhd/Media/Chappie (2015) [1080p]/Chappie.2015.1080p.BluRay.x264.YIFY.mp4'
data = {'TITLE': 'Chappie', 'YEAR': '2015', 'FILEPATH': filepath}
t = Tag(filepath=filepath)
