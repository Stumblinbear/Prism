import re

open('/var/log/prism.log', 'w').close()

levels = 0
def up(string=None):
	if string is not None:
		output('>%s' % string, string_color='\033[93m')
	global levels
	levels += 1
def down():
	global levels
	levels -= 1

def output(string='', prefix_color='\033[90m', prefix_char=':', extend_char='|', string_color=''):
	prefix = prefix_char + prefix_char + '> \033[1m'
	for i in range(0, levels):
		prefix = prefix + extend_char
	print('\033[1m' + prefix_color + prefix + '\033[0m' + string_color + str(string) + '\033[0m')
	with open('/var/log/prism.log', 'a') as f:
		f.write(re.sub('\x1b[^m]*m', '', prefix + str(string)) + '\n')

def info(string):
	output(string, '\033[34m', 'i', '|', '\033[94m')

def good(string):
	output(string, '\033[32m', 'o', '|', '\033[92m')

def error(string):
	output(string, '\033[31m', ':', '!', '\033[91m')
