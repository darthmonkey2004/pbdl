from distutils.core import setup

setup(name='pbdl',
	packages=['pbdl'],
	version='0.2',
	description='PBDL - Pirate Bay DownLoader/Transmission Torrent Controller',
	author='Matt McClellan',
	author_email='darthmonkey2004@gmail.com',
	url='http://www.simiantech.biz/',
	scripts=['pbdl_setup.sh'],
	data_files=('README', 'requirements.txt'),
)
