from time import time

class memorize(object):
   '''
   Modified from django.utils.functional.memoize to add cache expiry.

   Wrap a function so that results for any argument tuple are stored in
   'cache'. Note that the args to the function must be usable as dictionary
   keys. Only cache results younger than expiry_time (seconds) will be returned.

   Only the first num_args are considered when creating the key.
   '''
   def __init__(self, expiry_time=0, num_args=None):
	   self.cache = { }
	   self.expiry_time = expiry_time
	   self.num_args = num_args

   def __call__(self, func):
	   def wrapped(*args):
		   # The *args list will act as the cache key (at least the first part of it)
		   # [:None] is equivalent to [:]
		   mem_args = args[:self.num_args]
		   # Check the cache
		   if mem_args in self.cache:
			   result, timestamp = self.cache[mem_args]
			   # Check the age.
			   age = time() - timestamp
			   if not self.expiry_time or age < self.expiry_time:
				   return result
		   # Get a new result
		   result = func(*args)
		   # Cache it
		   self.cache[mem_args] = (result, time())
		   # and return it.
		   return result
	   return wrapped
