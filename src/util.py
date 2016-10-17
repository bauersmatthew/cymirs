"""Provides some basic utility functions."""
import logging
import sys

def get_tag_batch(src, tags):
	"""Get a tuple of the values in the given dict corresponding to
		the given tags."""
	return tuple(src[tag] for tag in tags)

def eval_expr(expr):
    """Evaluate a simple (pythonic) mathematical expression.
    
    Does some basic input sanitization and then calls eval."""
    expr = expr.strip()
    
    # sanitize badly; only allow eE.^()-+*/0123456789
    # i dont figure anyone will try to hack this anyway, and all they could do is
    #     call a function called like eee() or something
    for ch in expr:
        if ch not in 'eE.^()-+*/0123456789':
            return None
            
    # evaluate, return
    try:
        return eval(expr)
    except:
        return None

# set up logger
log = logging.Logger('cymirs_logger_main')
log_handler = logging.StreamHandler(stream=sys.stderr)
log_handler.setFormatter(fmt='[%(levelname)s] %(message)s')
log.addHandler(log_handler)

def send_email(msg):
	"""Send an email with default subject and given message."""
	# TODO
	pass

class TextEmailFilter(logging.Filter):
	"""Custom filter for sending emails or texts."""
	def defconfig(self):
		"""Set defaults for text/email values.

		MUST BE CALLED BEFORE ANYTHING ELSE."""
		self.addr_email = ''
		self.addr_txt = ''
		self.when_email = []
		self.when_txt = []

	def filter(self, record):
		if record.levelno in when_email:
