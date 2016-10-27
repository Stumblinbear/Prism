from setuptools import setup, find_packages
import sys

setup(
	name='prism',
	version='1.0.0',
	description='',
	author='Stumblinbear',
	author_email='stumblinbear@gmail.com',
	url='https://github.com/CodingForCookies/Prism',
	license='MIT License',

	install_requires=list(filter(None, open('requirements.txt').read().splitlines())),
	packages=find_packages(exclude=['prism/tmp']),
	data_files=[('/etc/init.d', ['etc/init.d/prism-panel'])]
)
