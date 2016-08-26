from setuptools import setup, find_packages
from codecs import open
from os import path

print(list(filter(None, open('requirements.txt').read().splitlines())))

setup(
	name='prism',
	version='1.0.0',
	description='',
	author='Stumblinbear',
	author_email='stumblinbear@gmail.com',
	url='https://github.com/pypa/sampleproject',
	license='MIT License',
	
	install_requires=list(filter(None, open('requirements.txt').read().splitlines())),
	packages=find_packages(exclude=[ 'libs', 'tmp' ]),
	#scripts=[ 'prism-panel' ],
	data_files=[
        #('/etc/prism', [ 'packaging/files/config.json' ]),
        ('/etc/init.d', [ 'prism-panel' ])
	]
)