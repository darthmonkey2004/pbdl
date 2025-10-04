import mutagen
import threading
import time
import re
import os
import json
import subprocess
from urllib.parse import quote, unquote
from bs4 import BeautifulSoup as bs
import requests

"""
look in Media folder for any loose files (not in unfinished, completed)
create function to write settings.json
create start function to run transmission-daemon with the provided settings file
if possible, inherit download object into Torrent object (unless read locally)

need update method inside torrent object, called when string method called.

setings file:
	load defaults first
	if user settings exist ('/home/user/.pbdl/settings.json'), then load it (overwrite values)
	create setSettings function that autocreates directory and settings.json from defaults + changes.
	use custom settings in init onLoad if available.
"""

class Tag():
	def __init__(self, filepath):
		self.FILEPATH = filepath
		self.EXTENSION = os.path.splitext(self.FILEPATH)[1]
		self.TagWriter, self.TagDeleter, self.TagReader = self._set_funcs(ext=self.EXTENSION)
		if self.TagReader is not None:
			self.DATA = self.read()
		else:
			print(f"Error! No data read from file: {self.FILEPATH}!")
			self.DATA = None
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
	def update(self, data=None, **args):
		if data is not None:
			for k in data:
				args[k] = data[k]
		return self.TagWriter(data=args, filepath=self.FILEPATH)
	def read(self):
		return self.TagReader(filepath=self.FILEPATH)
	def clear(self):
		return self.TagDeleter(filepath=self.FILEPATH)
	def delete(self, key):
		return self.TagDeleter(filepath=self.FILEPATH, key=key)
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
	def _set_funcs(self, ext=None):
		if ext is None:
			ext = self.EXTENSION
		if ext == '.mkv':
			w = self.write_info_mkv
			d = self.delete_info_mkv
			r = self.get_info_mkv
		elif ext == '.mp4':
			w = self.write_info_mp4
			d = self.delete_info_mp4
			r = self.get_info_mp4
		elif ext == '.mp3':
			w = None
			d = None
			r = None
		else:
			print("Weirdo extension:", ext)
			return None, None, None
		return w, d, r
	def get_tagid(self, key):
		return self.get_props()[key.upper()]
	def write_info_mp4(self, data, filepath=None):
		if filepath is None:
			filepath = self.FILEPATH
		f = mutagen.File(filepath)
		props = self.get_props()
		for k in data:
			#code = self.encode(props[k])
			f.update(props[k], data[k])
		f.save()
		print("Updated tag data:", filepath)
	def delete_info_mp4(filepath=None):
		if filepath is None:
			filepath = self.FILEPATH
		f = mutagen.File(filepath)
		f.clear()
		f.save()
		print("Deleted tag data:", filepath)
	def get_info_mp4(self, filepath=None):
		if filepath is None:
			filepath = self.FILEPATH
		f = mutagen.File(filepath)
		props = self.get_props()
		out = {}
		if f.tags is None:
			print("No tags found! Initilizing new mp4 metadata tag...")
			fname = os.path.basename(filepath)#init new tag with filename as title. Updating this will be done later on in Media Scanner/Tagger
			f.update(title=fname)
			f.save()
		for t in f.tags:
			dec = self._conv_to_dec(t)
			prop = props[dec]
			out[prop] = f.tags[t]
		print("Read tag data from mp4:", filepath, out.keys())
		return out
	def write_info_mkv(data, target_filepath):
		l = []
		for k in data:
			tagid = get_tagid(k)
			tagcode = self._convert_to_text(tagid)
			v = data[k]
			l.append(f"{tagcode}={v}")
		string = "|".join(l)
		com = f"mkvpropedit '{target_filepath}' --edit info --set 'title={string}'"
		return subprocess.check_output(com, shell=True).decode().strip()
	def delete_info_mkv(filepath):
		com = f"mkvpropedit '{filepath}' --edit info --delete 'title'"
		return suubprocess.check_output(com, shell=True).decode().strip()
	def parse_info_string(self, info):
		mdata = info.split('|')
		media_type = mdata[0]
		data = {}
		data['media_type'] = media_type
		if media_type == 'Series':
			_, series_name, sstring = mdata
			data['series_name'] = series_name
			data['season'] = int(sstring.split('S')[1].split('E')[0])
			data['episode_number'] = int(sstring.split('E')[1])
		elif media_type == 'Movies':
			_, data['title'], data['year'] = mdata
		return data
	def get_info_mkv(filepath='/media/monkey/usbhd/Media/Series/Rick and Morty/S8/Rick and Morty.s8e1.mkv'):
		def getProps(filepath):
			return json.loads(subprocess.check_output(f"mkvmerge -i '{filepath}' --identification-format json", shell=True).decode().strip())
		props = getProps(filepath)
		duration = props['container']['properties']['duration']
		info = props['container']['properties']['title']
		return self.parse_info_string(info)

class MediaTagger():
	def __init__(self, media_path=None):
		if media_path is None:
			user = os.path.expanduser("~").split('/')[1]
			media_path = os.path.join('media', user, 'Media')
		self.MEDIA_PATH = media_path
		if not os.path.exists(self.MEDIA_PATH):
			os.makedirs(media_path, exist_ok=True)
		if media_path is not None:
			print(f"TODO - make media scanner for target directory!")
	def getTag(self, filepath):
		return Tag(filepath=filepath)

class Subs():
	def __init__(self, query=None, imdbid=None, language='en'):
		self.LANG = language
		self.QUERY = query
		self.IMDBID = imdbid
		if self.QUERY is not None:
			self.RESULTS = self.search_subs(query=self.QUERY, lang=self.LANG)
		else:
			self.RESULTS = {}
	def _get_headers(self):
		api_key = "SdfkxlC3R7iXTQGxqg5Ik9Av4sWs0LlR"
		return {"User-Agent": "PBDL v0.1", "Api-Key": api_key}
	def _get(self, url, querystring):
		r = requests.get(url, headers=self._get_headers(), params=querystring)
		try:
			return r.json()
		except Exception as e:
			print(f"Couldn't get response json: {e}")
			return r.text
	def search_subs(self, query=None, imdbid=None, lang=None):
		url = "https://api.opensubtitles.com/api/v1/subtitles"
		q = {}
		if lang is None:
			lang = self.LANG
		q["languages"] = lang
		if query is not None:
			q['query'] = query
		else:
			q['query'] = self.QUERY
		if imdbid is not None:
			q["imdb_id"] = imdbid
		else:
			q['imdb_id'] = imdbid
		return self._get(url, q)



class TMDB():
	def __init__(self, query=None, category='TV'):
		self.CATEGORY = category
		self.QUERY = None
		self.RESULTS = None
		self.CATEGORIES = ['MOVIE', 'NAME', 'TV', 'TV_EPISODE', 'INTEREST', 'VIDEO_GAME', 'PODCAST_SERIES']
	def guess_media_type(self, filepath):
		series_name, s, en = self.test_isSeries(filepath)
		title, year = self.test_isMovie(filepath=filepath)
		out = {}
		if s is not None:
			out['SERIES_NAME'] = series_name
			out['SEASON'] = s
			out['MEDIA_TYPE'] = 'Series'
			if en is not None:
				out['EPISODE_NUMBER'] = en
			elif en is None:
				print("TODO - add section to add season and episode_number to object!")
				print("if season is set and episode_number is not, we can assume entire season/anthology")
				print("TODO - find entire series/anthology to download and use this.")
			print("Series found!")
			return out
		elif title is not None and year is not None:
			out['MEDIA_TYPE'] = 'Movies'
			out['TITLE'] = title
			out['YEAR'] = year
			print("Movie found:", out['TITLE'], out['YEAR'])
		else:
			videxts = ['.mp4', '.avi', '.mpg', '.mpeg', '.wmv', '.mkv', '.swf']
			audioexts = ['.mp3', '.wav', '.pcm']
			for ext in videxts:
				if ext in filepath:
					out['MEDIA_TYPE'] = 'Video - Unknown type'
					return out
			for ext in audioexts:
				if ext in filepath:
					out['MEDIA_TYPE'] = 'Audio'
					return out
			out['MEDIA_TYPE'] = 'Unknown'
		return out
	def test_isMovie(self, filepath, return_results=True):
		txt = filepath
		dates = []
		for i in range(1900, 2025):
			if str(i) in txt:
				if return_results:
					title = os.path.basename(txt.split(str(i))[0].replace(' (', ''))
					year = i
					return title, year
				else:
					return True
		if return_results:
			return None, None
		else:
			return False

	def get_strings(self):
		l = []
		for i in range(0, 100):
			for j in range(0, 100):
				l.append(f"S{i}E{j}")
		return l

	def se_isin(self, filepath, return_string_match=False):
		strings = self.get_strings()
		try:
			string = [s for s in strings if s in filepath.upper()][0]
		except Exception as e:
			print("No string found in filepath:", filepath)
			return None, None
		season = string.split('S')[1].split('E')[0]
		en = string.split('E')[1]
		fname, ext = os.path.splitext(os.path.basename(filepath))
		if f".{string}" in fname:
			series_name = fname.split(f".{string}")[0]
		else:
			series_name = fname.split(string)[0]
		if return_string_match:
			return string, series_name, season, en#return string match also if flag set
		else:
			return series_name, season, en#else return parsed data as tuple

	def test_isSeries(self, filepath, return_results=True):
		txt = filepath.upper()
		try:
			series_name, s, en = self.se_isin(filepath=filepath)
		except Exception as e:
			print(f"Error testing series: {e}, {filepath}")
			return None, None, None
		if s is not None and en is not None:
			if return_results:
				return series_name, s, en
			else:
				return True
		x = re.findall('\.''S..E..''\.', txt)
		if len(x) > 0:
			if '[' in x[0] and ']' in x[0]:
				print("contained brackets, not season info. Removing element...")
				_ = x.pop(0)
			if len(x) == 0:
				if return_results:
					return None, None
				else:
					return False
			if return_results:
				season = x[0].split('S')[1].split('E')[0]
				if '0' in season:
					season = season[1:]
				else:
					try:
						season = int(season)
					except Exception as e:
						print("error in test_isSeries():", e)
						print(x[0])
				episode_number = x[0].split('E')[1].replace('.', '')
				if '0' in episode_number:
					episode_number = episode_number[1:]
				else:
					episode_number = int(episode_number)
				return series_name, season, episode_number
			else:
				return True
		else:
			if 'Season ' in txt:
				if ', ' not in txt:
					season = int(txt.split('Season ')[1].split(' ')[0])
					if return_results:
						return series_name, season, None
					else:
						return False
				else:
					seasons = txt.split('Season ')[1].replace('&', ', ').split(', ')
					if return_results:
						return (series_name, seasons, None)
					else:
						return True
			else:
				if return_results:
					return None, None
				else:
					return False
	def get_headers(self):
		return {"x-rapidapi-key": "TiV3k10QNXmshRyyCcCXPKyq1gYJp1oKBNKjsn3ICR7bpX3yAB", "x-rapidapi-host": "imdb232.p.rapidapi.com"}
	def _get(self, url, querystring):
		response = requests.get(url, headers=self.get_headers(), params=querystring)
		return response.json()
	def _search_movies(self, query):
		try:
			ret = self._get("https://imdb232.p.rapidapi.com/api/search", {"count":200,"type":"MOVIE","q":query})
			return ret
		except Exception as e:
			print(f"Unable to query imdb: {e}")
			ret = {}
			ret['MEDIA_TYPE'] = 'Movie'
			ret['TITLE'] = query
			return ret
	def _parse_movie_data(self, data):
		output = []
		try:
			edges = data['data']['mainSearch']['edges']
		except Exception as e:
			print("No data (empty):", e, data)
			out['title'] = data['TITLE']
			out['media_type'] = data['MEDIA_TYPE']
			return out
		for edge in edges:
			out = {}
			out['imdbid'] = edge['node']['entity']['id']
			out['title'] = edge['node']['entity']['titleText']['text']
			if edge['node']['entity']['releaseYear'] is not None:
				try:
					out['year'] = edge['node']['entity']['releaseYear']['year']
					month = edge['node']['entity']['releaseDate']['month']
					day = edge['node']['entity']['releaseDate']['day']
					out['release_date'] = f"{month}/{day}/{out['year']}"
				except Exception as e:
					pass
			if edge['node']['entity']['primaryImage'] is not None:
				out['image'] = edge['node']['entity']['primaryImage']['url']
			output.append(out)
		return output
	def _search_series(self, query, episode_name=None):
		if episode_name is not None:
			t = 'TV_EPISODE'
		else:
			t = 'TV'
		return self._get("https://imdb232.p.rapidapi.com/api/search", {"count":"25","type":t,"q":query})
	def _get_seasons(self, imdbid):
		data = self._get("https://imdb232.p.rapidapi.com/api/title/get-seasons", {"limit":"200","tt":imdbid})
		return data['data']['title']['episodes']['displayableSeasons']['total']	
	def _get_episodes(self, imdbid, season):
		if 'tt' not in imdbid:
			query = imdbid
			imdbid = self.get_imdbid(query)
		return self._get("https://imdb232.p.rapidapi.com/api/title/get-episodes-by-season", {"limit":"200","season":season,"tt":imdbid})
	def _parse_episodes(self, data):
		output = {}
		ct = data['data']['title']['episodes']['episodes']['total']
		edges = data['data']['title']['episodes']['episodes']['edges']
		for edge in edges:
			out = {}
			en = edge['position']
			out['episode_number'] = en
			out['imdbid'] = edge['node']['id']
			plot = edge['node']['plot']
			if plot is not None:
				out['plot_id'] = plot['id']
				out['description'] = plot['plotText']['plainText']
				output[en] = out
		return output
	def _parse_series_data(self, data):
		output = []
		edges = data['data']['mainSearch']['edges']
		for edge in edges:
			out = {}
			keys = [k for k in edge['node']['entity'] if '__' not in k]
			for key in keys:
				d = edge['node']['entity'][key]
				if d is None:
					pass
				else:
					if key == 'id':
						out[key] = d
					elif key == 'titleType':
						t = d['categories'][0]['text']
						if t == 'TV':
							t = 'Series'
						else:
							t = 'Movies'
						out['media_type'] = t
					elif key == 'titleText':
						out['title'] = d['text']
					elif key == 'releaseYear':
						out['year'] = d['year']
					elif key == 'releaseDate':
						month = d['month']
						day = d['day']
						year = d['year']
						country = d['country']['id']
						rest = d['restriction']
						out['release_date'] = f"{month}/{day}/{year}"
						out['country'] = country
						out['restriction'] = rest
					elif key == 'primaryImage':
						out['img'] = d['url']
					elif key == 'episodes':
						out['episodes_ct'] = d['episodes']['total']
			output.append(out)
		return output
	def searchSeries(self, query):
		data = self._search_series(query)
		return self._parse_series_data(data)
	def get_imdbid(self, query, media_type='Series', first_result_only=True):
		if media_type == 'Movies':
			return self.get_movie_id(query)
		elif media_type == 'Series':
			data = self.searchSeries(query)
			if first_result_only:
				return data[0]['id']
			else:
				return [d['id'] for d in data]
	def search_episodes(self, season, imdbid=None, series_name=None):
		if imdbid is None:
			imdbid = self.get_imdbid(series_name)
		eps = self._get_episodes(imdbid, season=season)
		return self._parse_episodes(eps)
	def search_movies(self, title):
		mdata = self._search_movies(query=title)
		return self._parse_movie_data(mdata)
	def get_movie_id(self, title, first_result_only=True):
		data = self.search_movies(title=title)
		if first_result_only:
			return data[0]['imdbid']
		else:
			return [d['id'] for d in data]
	def get_episode_id(self, imdbid, season, episode_number=None):
		if 'tt' not in imdbid:
			query = imdbid
			imdbid = self.get_imdbid(query)
		out = self.search_episodes(imdbid=imdbid, season=season)
		if episode_number is None:
			d = []
			for en in out:
				d.append(out[en]['imdbid'])
			return d
		else:
			return out[episode_number]['imdbid']


class Setting():
	def __init__(self, key, value, dtype=None):
		self.KEY = key
		self.VALUE = value
		self.DATA_TYPE = dtype
	def _set_value(self, new_value):
		self.VALUE = new_value
	def _set_data_type(self, dtype):
		self.DATA_TYPE = dtype
	def _get_value(self):
		return self.VALUE
	def get_dict(self):
		if self.DATA_TYPE == bool and type(self.VALUE) != bool:
			return {self.KEY: bool(self.VALUE)}
		elif self.DATA_TYPE == int and type(self.VALUE) != int:
			return {self.KEY: int(self.VALUE)}
		elif self.DATA_TYPE == str and type(self.VALUE) != str:
			return {self.KEY: str(self.VALUE)}
		elif self.DATA_TYPE == list and type(self.VALUE) != list:
			return {self.KEY: list(self.VALUE)}

class Download():
	def __init__(self, data={}, **args):
		keys = ['id', 'name', 'info_hash', 'leechers', 'seeders', 'num_files', 'size', 'username', 'added', 'status', 'category', 'imdb']
		self.CAT = 0
		self.RESULTS = None
		self.test_keys(data)
		if data != {}:
			for k in data:
				args[k] = data[k]
		for k in args:
			if k == 'size':#if size key encountered,convert to human readable and store.
				self.size = self.convert_size_to_string(args[k])
				self.bytes = args[k]
			else:
				self.__dict__[k] = args[k]
	def clean_file_name(self):
		name = self.name
		if '[' in name and ']' in name:
			name = name.split('[')[0]
	def _test_key(self, key, data):
		try:
			return data[key]
		except Exception as e:
			print(f"Error getting value from key - {e}! Key={key}, data={data}")
			return "Unknown"
	def test_keys(self, data):
		self.seeders = self._test_key(key='seeders', data=data)
		self.name = self._test_key(key='name', data=data)
		self.leechers = self._test_key(key='leechers', data=data)
	def get_id(self):
		return self.id
	def get_name(self):
		return self.name
	def get_hash(self):
		return self.info_hash
	def get_leechers(self):
		return self.leechers
	def get_seeders(self):
		return self.seeders
	def get_files_count(self):
		return self.num_files
	def get_size(self):
		return self.size
	def get_uploader(self):
		return self.username
	def get_date_added(self):
		return self.added
	def get_status(self):
		return self.status
	def get_category(self):
		return self.category
	def get_imdbid(self):
		return self.imdb
	def convert_size_to_string(self, size=None, fmt=None):
		"""
		converts crazy size in bites to a more human readable format
		Set fmt as optional second argument, or None for auto
		"""
		if type(size) == str:#if size number is a string (weirdos ;-)), convert to int.
			size = int(size)
		kb = size / 1024
		if kb <= 1 or fmt == 'b':
			return size
		mb = kb / 1024
		if mb <= 1 or fmt == 'kb':
			return f"{round(kb, 2)} Kb"
		gb = mb / 1024
		if gb <= 1 or fmt == 'mb':
			return f"{round(mb, 2)} MB"
		tb = gb / 1024
		if tb <= 1 or fmt == 'gb':
			return f"{round(gb, 2)} GB"
		if tb >= 1 or fmt == 'tb':
			return f"{round(tb, 2)} TB"
	def __str__(self):
		try:
			return f"{self.id}: {self.name} - Seeders:{self.seeders}, Leechers:{self.leechers}, Season info:S{self.season}E{self.episode_number} - size:{self.size} - ID: {self.id}"
		except Exception as e:
			return f"{self.id}: {self.name} - Seeders:{self.seeders}, Leechers:{self.leechers}, size:{self.size} - ID: {self.id}"


class Results():
	def __init__(self, data, sortby='seeders'):
		self.SORTBY = sortby
		self.ITEMS = []
		for obj in data:
			if type(obj) == dict:
				obj = Download(data=obj)
			obj = self.guess_media_type(obj)
			self.ITEMS.append(obj)
		if sortby is not None:
			self.ITEMS = self.sortby(data=data, key=self.SORTBY)
	def guess_media_type(self, obj):
		s, en = self.test_isSeries(obj)
		title, year = self.test_isMovie(obj=obj)
		if s is not None:
			obj.SEASON = s
			obj.MEDIA_TYPE = 'Series'
			if en is not None:
				obj.EPISODE_NUMBER = en
			elif en is None:
				print("TODO - add section to add season and episode_number to object!")
				print("if season is set and episode_number is not, we can assume entire season/anthology")
				print("TODO - find entire series/anthology to download and use this.")
			print("Series found!")
			return obj
		elif title is not None and year is not None:
			obj.MEDIA_TYPE = 'Movies'
			obj.TITLE = title
			obj.YEAR = year
			print("Movie found:", obj.TITLE, obj.YEAR)
		else:
			videxts = ['.mp4', '.avi', 'mpg', 'mpeg', 'wmv', 'mkv', 'swf']
			audioexts = ['.mp3', 'wav', 'pcm']
			for ext in videxts:
				if ext in obj.get_name():
					obj.MEDIA_TYPE = 'Video - Unknown type'
					return obj
			for ext in audioexts:
				if ext in obj.get_name():
					obj.MEDIA_TYPE = 'Audio'
					return obj
			obj.MEDIA_TYPE = 'Unknown'
		return obj

	def test_isMovie(self, obj, return_results=True):
		txt = obj.__str__()
		dates = []
		for i in range(1900, 2025):
			if str(i) in txt:
				if return_results:
					title = txt.split(str(i))[0]
					year = i
					return title, year
				else:
					return True
		if return_results:
			return None, None
		else:
			return False
					
			
	def test_isSeries(self, obj, return_results=True):
		txt = obj.__str__()
		x = re.findall('\.''S..E..''\.', txt)
		if len(x) > 0:
			if '[' in x[0] and ']' in x[0]:
				print("contained brackets, not season info. Removing element...")
				_ = x.pop(0)
			if len(x) == 0:
				if return_results:
					return None, None
				else:
					return False
			if return_results:
				season = x[0].split('S')[1].split('E')[0]
				if '0' in season:
					season = season[1:]
				else:
					try:
						season = int(season)
					except Exception as e:
						print("error in test_isSeries():", e)
						print(x[0])
				episode_number = x[0].split('E')[1].replace('.', '')
				if '0' in episode_number:
					episode_number = episode_number[1:]
				else:
					episode_number = int(episode_number)
				return season, episode_number
			else:
				return True
		else:
			if 'Season ' in txt:
				if ', ' not in txt:
					season = int(txt.split('Season ')[1].split(' ')[0])
					if return_results:
						return season, None
					else:
						return False
				else:
					seasons = txt.split('Season ')[1].replace('&', ', ').split(', ')
					if return_results:
						return (seasons, None)
					else:
						return True
			else:
				if return_results:
					return None, None
				else:
					return False
	def getDownloadById(self, did):
		for item in self.ITEMS:
			if str(item.id) == str(did):
				return item
		return None
	def sortby(self, data, key='value', reverse=False):
		"""
		if reverse is False:
			THIS WILL REVERSE THE LIST, AND IS SUPPOSED TO DO THAT!
				because of weirdo method for sorting, sorting needs reversed in reverse is FALSE.
				it orders it backward because of the loop structure taking from last in list and adding to first.
				TODO - find a less backwards way to do this.
		if reverse is True:
			DONT'T sort, as it is alrerady in reverse.
		"""
		out = []
		try:
			old = [i.__dict__[key] for i in self.ITEMS]
		except Exception as e:
			print(f"Werid! {e}")
			print([i.__dict__ for i in self.ITEMS][0])
		new = sorted(old)
		for i in new:
			idx = old.index(i)
			obj = self.ITEMS[idx]
			out.append(obj)
		if not reverse:
			out.reverse()
		self.ITEMS = out
		return out
	def __str__(self):
		return "\n".join([i.__str__() for i in self.ITEMS])

class PBDL():
	def __init__(self, query=None, cat=200, sortby='seeders'):
		self.SORT_BY = sortby
		self.CATS = self.get_cats()
		if type(cat) == int:
			self.CATID = cat
			self.CAT = self.CATS[self.CATID]
		elif type(cat) == str:
			self.CAT = cat
			self.CATID = self.get_cat_code_from_name(cat)
		if query is not None:
			if ' ' in query:
				query = query.replace(' ', '+')
		self.QUERY = query
		if self.QUERY is not None:
			self.RESULTS = self.search(query=self.QUERY, category=self.CATID)

	def searchSeason(self, season):
		if '0' not in str(season) and season < 10:
			season = f"0{season}"
		return self.filter_by(key=f".S{season}E")

	def searchEpisodeNumber(self, episode_number):
		if '0' not in str(episode_number) and episode_number < 10:
			episode_number = f"0{episode_number}"
		return self.filter_by(key=f"E{episode_number}")

	def searchSeriesName(self, series_name):
		return self.filter_by(key=series_name)	

	def searchSeries(self, series_name=None, season=None, episode_number=None):
		pass

	def filter_by(self, key, set_as_attribute=True):
		out = []
		oldlist = self.RESULTS.__str__().splitlines()
		for i in oldlist:
			if str(key).upper() in i.upper():
				did = int(i.split('ID: ')[1].split(' ')[0])
				obj = self.RESULTS.getDownloadById(did)
				out.append(obj)
		if len(out) == 0:
			print(f"No results found!")
			return self.RESULTS
		elif len(out) > 0:
			ret = Results(data=out)
			if set_as_attribute:
				self.RESULTS = ret
				print("Results attribute updated!")
			return ret

	def get_cats(self):
		cats = {}
		cats[0] = "All"
		cats[100] = "Audio"
		cats[101] = "Music"
		cats[102] = "Audio books"
		cats[103] = "Sound clips"
		cats[104] = "FLAC"
		cats[199] = "Other"
		cats[200] = "Video"
		cats[201] = "Movies"
		cats[202] = "Movies DVDR"
		cats[203] = "Music videos"
		cats[204] = "Movie clips"
		cats[205] = "TV shows"
		cats[206] = "Handheld"
		cats[207] = "HD - Movies"
		cats[208] = "HD - TV shows"
		cats[209] = "3D"
		cats[210] = "CAM/TS"
		cats[211] = "UHD/4k - Movies"
		cats[212] = "UHD/4k - TV shows"
		cats[299] = "Other"
		cats[300] = "Applications"
		cats[301] = "Windows"
		cats[302] = "Mac"
		cats[303] = "UNIX"
		cats[304] = "Handheld"
		cats[305] = "IOS (iPad/iPhone)"
		cats[306] = "Android"
		cats[399] = "Other OS"
		cats[400] = "Games"
		cats[401] = "PC"
		cats[402] = "Mac"
		cats[403] = "PSx"
		cats[404] = "XBOX360"
		cats[405] = "Wii"
		cats[406] = "Handheld"
		cats[407] = "IOS (iPad/iPhone)"
		cats[408] = "Android"
		cats[499] = "Other"
		cats[500] = "Porn"
		cats[501] = "Movies"
		cats[502] = "Movies DVDR"
		cats[503] = "Pictures"
		cats[504] = "Games"
		cats[505] = "HD - Movies"
		cats[506] = "Movie clips"
		cats[507] = "UHD/4k - Movies"
		cats[599] = "Other"
		cats[600] = "Other"
		cats[601] = "E-books"
		cats[602] = "Comics"
		cats[603] = "Pictures"
		cats[604] = "Covers"
		cats[605] = "Physibles"
		cats[699] = "Other"
		return cats

	def get_cat_code_from_name(self, name=None):
		if name is None:
			name = self.CAT
		search_cat = name.upper()
		names = [n.upper() for n in list(self.CATS.values())]
		vals = list(self.CATS.keys())
		if search_cat in names:
			idx = names.index(search_cat)
			return vals[idx]
		else:
			print("Bad category:", name)
			return None

	def test_cats(self, cat):
		if cat not in self.CATS:
			print(f"Error - bad cat - {cat}")
			return False
		else:
			return True


	def get_url(self, query, cat='video'):
		if not self.test_cats(cat):
			print("Bad category! Choosing 'all'...")
			catid = 0
			cat = self.CATS[catid]
		if type(cat) == str:
			catid = self.get_cat_code_from_name(cat)
			cat = self.CATS[catid]
		elif type(cat) == int:
			catid = cat
			cat = self.CATS[catid]
		self.CATID = catid
		self.CAT = cat
		self.QUERY = quote(query)
		l = []
		self.URL = f"https://apibay.org/q.php?q={self.QUERY}&cat={self.CATID}"
		print("Url:", self.URL)
		return self.URL

	def _get(self, query, cat):
		url = self.get_url(query, cat)
		r = requests.get(url)
		if r.status_code == 200:
			try:
				out = r.json()
			except:
				out = bs(r.text, 'html.parser')
		return out

	def get(self, query=None, cat=None):
		if cat is not None:
			if type(cat) == str:
				self.CAT = cat
				self.CATID = self.get_cat_code_from_name(name=self.CAT)
			elif type(cat) == int:
				self.CATID = cat
				self.CAT = self.CATS[self.CATID]
		cat = self.CATID
		if query is None:
			query = self.QUERY
		data = self._get(query=query, cat=cat)
		return data

	def search(self, query, category='video', sort_by=None):
		if sort_by is not None:
			self.SORT_BY = sort_by
		if type(category) == str:
			category = self.get_cat_code_from_name(category)
		data = self.get(query=query, cat=category)
		out = []
		self.RESULTS = Results(data=data, sortby=self.SORT_BY)
		return self.RESULTS

class Torrent():
	def __init__(self, data):
		self.KEYS = []
		for k in data:
			key = k.upper()
			self.KEYS.append(key)
			if key == 'ETA':
				if ' seconds' in str(data[k]):
					data[k] = data[k].split(' seconds')[0]
				value = int(data[k])
				self.__dict__[key] = time.strftime('%H:%M:%S', time.gmtime(value))
			else:
				self.__dict__[key] = data[k]
		try:
			self.FILES = self.get_files()
		except Exception as e:
			print(f"Error getting files (incomplete???)")
			self.FILES = []
	def _get_tree_data(self, parent=None):
		if parent is None:
			parent = self.torrents_tree
		sv = tk.StringVar(parent)
		sv.set(t.__str__())
		tl = parent.insert("", tk.END, textvariable=sv)
		keys = t.KEYS
		for key in keys:
				ssv = tk.StringVar(tl)
				text = f"{key}: {t.__dict__[key]}"
				ssv.set(text)
				parent.insert(tl, tk.END, textvariable=ssv)
		return parent
	def _convert_rate(self, val):
		if ',' in str(val):
			val = val.split(',')[0]
		ret = int(val) / 1024#get kb
		if ret < 0:#if less than 0, return bits
			val = round(val, 2)
		else:#else set KBs
			val = round(ret, 2)
			out = f"{val} Kbps"
		if val > 1024:#if enough for MBs...
			val = val / 1024
			out = f"{val} Mbps"
		if val > 1024:#if enough for GBs...
			val = val / 1024
			out = f"{val} Gbps"
		return out
	def _send(self, com):
		return subprocess.check_output(f"transmission-remote {self.HOST} --json -t {self.ID} {com}", shell=True).decode().strip()
	def get_info(self):
		out = []
		info = json.loads(self._send("--info"))
		for tor in info['arguments']['torrents']:
			d = {}
			for k in tor:
				key = k.upper()
				v = tor[k]
				if key == 'DOWNLOADDIR':
					key = 'LOCATION'
				self.__dict__[key] = v
				d[key] = v
			out.append(d)
		return out
	def get_files(self):
		files = []
		info = self.get_info()
		for d in json.loads(self._send("--files"))['arguments']['torrents'][0]['files']:
			filepath = d['name']
			files.append(os.path.join(self.LOCATION, filepath))
		return files
	def remove(self):
		return self._send("-r")
	def purge(self):
		return self._send("--remove-and-delete")
	def start(self):
		return self._send("--start")
	def stop(self):
		return self._send("--stop")
	def _is_int(self, var):
		try:
			v = float(var)
			return True
		except:
			try:
				v = int(var)
				return True
			except:
				return False
	def _get_states(self):
		d = {}
		d[4] = 'Downloading'
		d[3] = 'Seeding'
		d[2] = 'Queued'
		d[1] = 'Paused'
		d[0] = 'Unknown'
		return d
	def _is_int(self, var):
		try:
			i = int(var)
			return True
		except:
			return False
	def __str__(self):
		states = self._get_states()
		status = 'Unknown'
		if type(self.ETA) == str:
			if self.ETA == '00:00:00':
				self.ETA = 0
				self.LEFTUNTILDONE = 0
		if self.ETA == -1:
			self.ETA = 'N/A'
			self.LEFTUNTILDONE = 'Unknown'
			#try:
			status = self.STATE
		#	except Exception as e:
		#		print("Updated torrent status!")
		#		status = self.STATE
		#		print("status:", status)
		#		print("Rate download, rate upload:", self.RATEDOWNLOAD, self.RATEUPLOAD)
		return f"ID:{self.ID} - Name: {self.NAME} - Status: {status} - ETA: {self.ETA}) - DL: {self._convert_rate(self.RATEDOWNLOAD)} UL: {self._convert_rate(self.RATEUPLOAD)}"
		#except Exception as e:
		#	print("error in torrent string method:", e)
		#	print(self.__dict__)

class TransmissionRemote():
	def __init__(self, host=None, port=9091, temporary_save_folder="/media/monkey/usbhd/Media/unfinished_downloads", do_not_seed=True, start_torrent_on_add=False, loglevel='debug', start_monitor=False):
		self.START_TORRENT_ON_ADD = start_torrent_on_add
		self.TRACKERS = self._get_default_trackers()
		if do_not_seed:
			self.SEED_RATIO = 0
		else:
			self.SEED_RATIO = 2
		self.LOG_LEVEL = loglevel
		self.DATA_DIR = os.path.join(os.path.expanduser("~"), '.pbdl')
		self.SETTINGS_FILE = os.path.join(self.DATA_DIR, 'settings.json')
		self.LOG_FILE = os.path.join(self.DATA_DIR, 'transmission-daemon-log.txt')
		if host is None:
			host = self.getlocalip()
		self.HOST = host
		self.PORT = port
		self.FINISHED_SAVE_PATH = os.path.dirname(temporary_save_folder)
		self.PARTIAL_SAVE_PATH = temporary_save_folder
		self.SERVER_STARTED = self.is_running()
		self.SETTINGS = Settings(data_dir=self.DATA_DIR, settings_file=self.SETTINGS_FILE, logfile=self.LOG_FILE, loglevel=self.LOG_LEVEL)
		if not self.is_running():
			self.startTransmission()
		self.TORRENTS = self.getTorrents()
		if start_monitor:
			self.startLoop()
	def get_files(self, tid):
		torrents = self.getTorrents()
		files = torrents[tid].get_files()
		torrents[tid].FILES = files
		return files
	def _get_default_trackers(self):
		trackers = []
		trackers.append('udp://tracker.openbittorrent.com:80')
		trackers.append('udp://tracker.leechers-paradise.org:6969')
		trackers.append('udp://tracker.coppersurfer.tk:6969')
		trackers.append('udp://glotorrents.pw:6969')
		trackers.append('udp://tracker.opentrackr.org:1337')
		trackers.append('http://tracker2.istole.it:60500/announce')
		return trackers
	def __str__(self):
		l = []
		for t in list(self.TORRENTS.values()):
			l.append(t.__str__())
		return "\n".join(l)
	def save_settings(self, settings=None):
		if self.SERVER_STARTED:
			self.stopTransmission()
	def getlocalip(self):
		ret = subprocess.check_output("ifconfig | grep '192.168.'", shell=True).decode().strip()
		return ret.split('inet ')[1].split(' ')[0]
	def _send(self, com):
		if not self.is_running():
			print(f"Server not started! Starting now..")
			self.startTransmission()
		com = f"transmission-remote {self.HOST} --json {com}"
		try:
			ret = subprocess.check_output(com, shell=True).decode().strip()
			return ret
		except Exception as e:
			print(f"Failed to send command: {e}")
			return None
	def _list_torrents(self):
		ret = self._send(f"--list")
		if ret is None:
			return []
		else:
			return ret
	def getTorrents(self):
		self.TORRENTS = {}
		torrents = self._list_torrents()
		if torrents is not None and torrents != []:
			data = json.loads(torrents)
			torrents = data['arguments']['torrents']
			for tdata in torrents:
				tdata['HOST'] = self.HOST
				tdata['PARTIAL_SAVE_PATH'] = self.PARTIAL_SAVE_PATH
				torrent = Torrent(data=tdata)
				self.TORRENTS[tdata['id']] = torrent
		return self.TORRENTS

	def addTorrent(self, target, destination_path=None, start_on_add=None):
		"""
		add torrent to transmission-daemon
		target may be a magnet link, torrent file url, or just the hash (with DHT peer discovery enabled and UPnP forwarding on router[???])
		destination_path, if None, will be set by class attribute.
		"""
		if start_on_add is not None:
			print("Start torrents on add set:", start_on_add)
			self.START_TORRENT_ON_ADD = start_on_add
		ts = self.getTorrents()
		tids = [t for t in ts]
		if type(target) != str:
			try:
				target = target.info_hash
			except Exception as e:
				print("Error getting hash from target!", e)
				print(dir(target))
		if destination_path is None:
			destination_path = self.PARTIAL_SAVE_PATH
		print("Adding...", target)
		ret = self._send(f"--add {target}")
		l = []
		print("START_TORRENT_ON_ADD:", self.START_TORRENT_ON_ADD)

		if self.START_TORRENT_ON_ADD:
			ts2 = self.getTorrents()
			tids2 = [t for t in ts2]
			tid = [t for t in tids2 if t not in tids][0]
			print("Starting torrent...(start_on_add=True)")
			self.startTorrent(tid=tid)

	def startTorrent(self, tid):
		print("Starting torrent:", tid)
		return self._send(f"-t {tid} --start")

	def stopTorrent(self, tid):
		print("Stopping torrent:", tid)
		return self._send(f"-t {tid} --stop")

	def startAllTorrents(self):
		torrents = self.getTorrents()
		for tid in torrents:
			t = torrents[tid]
			self.startTorrent(t.ID)

	def stopAllTorrents(self):
		torrents = self.getTorrents()
		for tid in torrents:
			t = torrents[tid]
			self.stopTorrent(t.ID)

	def removeAndDeleteTorrent(self, tid):
		print(f"Purging torrent and all data ({tid})...")
		return self._send(f"-t {tid} --remove-and-delete")

	def removeTorrent(self, tid):
		print("Removing torrent...")
		return self._send(f"-t {tid} --remove")

	def is_running(self):
		off = 'Active: inactive (dead) since'
		on = 'Active: active (running) since'
		com = "sudo service transmission-daemon status"
		try:
			ret = subprocess.check_output(com, shell=True).decode().strip()
			if off in ret:
				self.SERVER_STARTED = False
				return False
			if on in ret:
				self.SERVER_STARTED = True
				return True
		except Exception as e:
			print(f"Error testing server state: {e}")
			return False

	def stopTransmission(self):
		com = "sudo service transmission-daemon stop"
		try:
			print("Transmission service stopping...")
			ret = subprocess.check_output(com, shell=True).decode().strip()
			self.SERVER_STARTED = False
			return True
		except:
			self.SERVER_STARTED = False
			return True

	def startTransmission(self):
		com = "sudo service transmission-daemon start"
		try:
			print("Transmission service starting...")
			ret = subprocess.check_output(com, shell=True).decode().strip()
			self.SERVER_STARTED = True
			return True
		except Exception as e:
			print(f"Failed to start service: {e}!")
			self.SERVER_STARTED = False
			return False

	def loop(self, wait=5):
		if not self.SERVER_STARTED:
			self.startTransmission()
		self.IS_LOOPING = True
		print(f"Loop starting. Updating every {wait} seconds..")
		while self.IS_LOOPING:
			time.sleep(wait)
			self.TORRENTS = self.getTorrents()
			if not self.IS_LOOPING:
				break
		print("Loop exiting...")

	def startLoop(self, daemon=True, wait=5):
		self.thread = threading.Thread(target=self.loop, args=(wait,))
		self.thread.daemon = daemon
		self.thread.start()
		print("Thread started!")
			
			

class Settings():
	def __init__(self, data_dir=None, seed_ratio=0, settings_file=None, init=False, logfile=None, loglevel='debug', **args):
		self.SEED_RATIO = seed_ratio
		if data_dir is None:
			self.DATA_DIR = os.path.join(os.path.expanduser("~"), '.pbdl')
		else:
			self.DATA_DIR = data_dir
		if settings_file is None:
			self.SETTINGS_FILE = os.path.join(self.DATA_DIR, 'settings.json')
		else:
			self.SETTINGS_FILE = settings_file
		self.SETTINGS = self.load_defaults()
		if logfile is None:
			logfile = os.path.join(self.DATA_DIR, 'transmission-daemon-log.txt')
		self.LOGFILE = logfile
		self.LOGLEVEL = loglevel
		if args != {}:
			print("Arguments provided! Using custom settings...")
			init = True
		if init:
			self._init_custom_settings(args=args)
	def load_defaults(self):
		d = {}
		d["alt_speed_down"] = 50
		d["alt_speed_time_begin"] = 540
		d["alt_speed_time_day"] = 127
		d["alt_speed_time_enabled"] = False
		d["alt_speed_time_end"] = 1020
		d["alt_speed_up"] = 50
		d["announce_ip"] = ""
		d["announce_ip_enabled"] = False
		d["anti_brute_force_enabled"] = False
		d["anti_brute_force_threshold"] = 100
		d["bind_address_ipv4"] = "0.0.0.0"
		d["bind_address_ipv6"] = "::"
		d["blocklist_enabled"] = False
		d["blocklist_url"] = "http://www.example.com/blocklist"
		d["cache_size_mb"] = 4
		d["default_trackers"] = ""
		d["dht_enabled"] = True
		d["download_dir"] = "/var/media/lib/transmission-daemon/downloads"
		d["download_limit"] = 100
		d["download_limit_enabled"] = 0
		d["download_queue_enabled"] = True
		d["download_queue_size"] = 5
		d["encryption"] = 1
		d["idle_seeding_limit"] = 2
		d["idle_seeding_limit_enabled"] = False
		d["incomplete_dir"] = ""
		d["incomplete_dir_enabled"] = False
		d["lpd_enabled"] = True
		d["max_peers_global"] = 200
		d["message_level"] = 5
		d["peer_congestion_algorithm"] = ""
		d["peer_limit_global"] = 200
		d["peer_limit_per_torrent"] = 50
		d["peer_port"] = 51413
		d["peer_port_random_high"] = 65535
		d["peer_port_random_low"] = 49152
		d["peer_port_random_on_start"] = False
		d["peer_socket_tos"] = "le"
		d["pex_enabled"] = True
		d["port_forwarding_enabled"] = False
		d["preallocation"] = 1
		d["prefetch_enabled"] = True
		d["queue_stalled_enabled"] = True
		d["queue_stalled_minutes"] = 30
		d["ratio_limit"] = 0
		d["ratio_limit_enabled"] = True
		d["rename_partial_files"] = False
		d["rpc_authentication_required"] = False
		d["rpc_bind_address"] = "0.0.0.0"
		d["rpc_enabled"] = True
		d["rpc_host_whitelist"] = ""
		d["rpc_host_whitelist_enabled"] = False
		d["rpc_password"] = ""
		d["rpc_port"] = 9091
		d["rpc_socket_mode"] = "0750"
		d["rpc_url"] = "/transmission/"
		d["rpc_username"] = "transmission"
		d["rpc_whitelist"] = "127.0.0.1"
		d["rpc_whitelist_enabled"] = False
		d["scrape_paused_torrents_enabled"] = True
		d["script_torrent_added_enabled"] = False
		d["script_torrent_added_filename"] = ""
		d["script_torrent_done_enabled"] = False
		d["script_torrent_done_filename"] = ""
		d["script_torrent_done_seeding_enabled"] = False
		d["script_torrent_done_seeding_filename"] = ""
		d["seed_queue_enabled"] = False
		d["seed_queue_size"] = 0
		d["speed_limit_down"] = 100
		d["speed_limit_down_enabled"] = False
		d["speed_limit_up"] = 1
		d["speed_limit_up_enabled"] = True
		d["start_added_torrents"] = True
		d["tcp_enabled"] = True
		d["torrent_added_verify_mode"] = "fast"
		d["trash_original_torrent_files"] = False
		d["umask"] = "022"
		d["upload_limit"] = 100
		d["upload_limit_enabled"] = 0
		d["upload_slots_per_torrent"] = 8
		d["utp_enabled"] = True
		return d

	def set(self, key, value, write_file=True):
		def get_dtype(var):
			return str(type(i)).split("'")[1]

		if key not in list(self.SETTINGS.keys()):
			raise Exception(f"Unknown key: {key}!")
		self.SETTINGS[key] = value

	def _prepare_settings_data(self, data):
		out = {}
		for k in data:
			v = data[k]
			key = k.replace('_', '-')
			out[key] = v
		return json.dumps(out, indent=2)

	def _write_settings_file(self, settings=None):
		print(f"TODO - put stop/start transmission-daemon function here and on exit before file write! (especially if it's in use)")
		print("Also need is_running function.")
		if settings is None:
			settings = self.SETTINGS
		outdata = self._prepare_settings_data(data=settings)
		try:
			with open(self.SETTINGS_FILE, 'w') as f:
				f.write(outdata)
				f.close()
			print(f"Settings file updated!")
			return True
		except Exception as e:
			print(f"Error saving settings file: {e}")
			return False
			

	def _init_custom_settings(self, args={}, path=None):
		if path is None:
			path = self.DATA_DIR
		if not os.path.exists(path):
			os.makedirs(path, exist_ok=True)
		for k in args:
			self.SETTINGS[k] = args[k]
			print(f"Updated setting: {k}={args[k]}!")
		ret = self._write_settings_file(self.SETTINGS)
		if not ret:
			print(f"Unable to create custom settings file! Defaulting to, well, defaults...;-)")
			self.SETTINGS = self.load_defaults()
			if not self._write_settings_file(self.SETTINGS):
				txt = f"Couldn't write settings file! Wtf? {self.SETTINGS_FILE} - {self.SETTINGS}"
				raise Exception(txt)
			
	def _get_svcfile_data(self, data_dir=None, seed_ratio=None, loglevel=None, logfile=None):
		if data_dir is None:
			data_dir = self.DATA_DIR
		if seed_ratio is None:
			seed_ratio = self.SEED_RATIO
		if loglevel is None:
			loglevel = self.LOGLEVEL
		if logfile is None:
			logfile = self.LOGFILE
		exec = f"ExecStart=/usr/bin/transmission-daemon -f --config-dir \"{data_dir}\" -gsr {seed_ratio} --log-level={loglevel} --logfile \"{logfile}\""
		txt = f"""[Unit]
Description=Transmission BitTorrent Daemon
Wants=network-online.target
After=network-online.target

[Service]
User={os.environ['USER']}
Type=simple
ExecStart={exec}
ExecReload=/bin/kill -s HUP $MAINPID
NoNewPrivileges=true
MemoryDenyWriteExecute=true
ProtectSystem=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target"""
		return txt

	def install_patch(self):
		"""
		this patches the transmission-daemon service file to work around 'failure to notify' errors in Ubuntu24.
		"""
		data = _get_svcfile_data()
		install_path = '/etc/systemd/system/transmission-daemon.service'
		temp = 'transmission-daemon.service'
		with open(temp, 'w') as f:
			f.write(data)
			f.close
		return subprocess.check_output(f"sudo mv '{temp}' '{install_path}'", shell=True).decode().strip()	
	
class MediaObject():
	def __init__(self, filepath=None, **args):
		self.FILEPATH = filepath
		for k in args:
			self.__dict__[k] = args[k]
		self.TAG = Tag(filepath=self.FILEPATH)

if __name__ == "__main__":
#	import sys
#	try:
#		query = sys.argv[1]
#	except:
#		query = input("Enter query:")
#		if query == '':
#			print("No query provided! Defaulting to 'Rick and Morty'...")
#			query = 'Rick and Morty'
#		#raise Exception("No query provided!")
#	try:
#		cat = sys.argv[2]
#	except:
#		print("No category provided! Using 'video (200)'...")
#		cat = 200
#	pbdl = PBDL(query=query, cat=cat)
#	ret = pbdl.RESULTS.ITEMS
#	print(ret)
#	remote = TransmissionRemote(host='192.168.1.151')
	p = PBDL(cat='video')
	results = p.search('Rick and Morty')
	#season = "08"
	#episode_number = "02"
	#filtered = p.filter_by(f"S{season}E{episode_number}")
	obj = results.ITEMS[0]
