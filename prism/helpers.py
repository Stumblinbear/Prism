import math

def convert_bytes(size, format=False):
	if(size == 0):
		if format:
			return '0b'
		return (0, "b")
	size_name = ("b", "kb", "mb", "gb", "tb", "pb", "eb", "zb", "yb")
	i = int(math.floor(math.log(size, 1024)))
	p = math.pow(1024, i)
	s = round(size / p, 2)
	if format:
		return '%s%s' % (int(s), size_name[i])
	return (int(s), size_name[i])

def next_color(i):
	colors = [ '#337AB7', '#00A65A', '#F39C12', '#DD4B39', '#4682B4', '#20B2AA', '#FFD700', '#00FA9A', '#7B68EE', '#FF00FF', '#20B2AA', '#BC8F8F', '#8B008B', '#008000', '#000080' ]
	return colors[i % len(colors)]

from threading import Thread
try:
	from Queue import Queue, Empty 
except:
	from queue import Queue, Empty 

class NonBlockingStreamReader:
	def __init__(self, stream):
		self._s = stream
		self._q = Queue()

		def _populateQueue(stream, queue):
			while True:
				stream.flush()
				line = stream.readline()
				if line:
					queue.put(line)

		self._t = Thread(target = _populateQueue, args = (self._s, self._q))
		self._t.daemon = True
		self._t.start()

	def readline(self, timeout = None):
		try:
			return self._q.get(block = timeout is not None, timeout = timeout)
		except Empty:
			return None

class UnexpectedEndOfStream(Exception): pass
