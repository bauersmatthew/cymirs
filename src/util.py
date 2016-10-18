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
    # replace ^ with **
    carrot_idx = expr.find('^')
    while carrot_idx >= 0:
        expr = expr[:carrot_idx] + '**' + expr[carrot_idx+1:]
        carrot_idx = expr.find('^')

    # evaluate, return
    try:
        return eval(expr)
    except:
        return None



# --------        LOGGING        --------

# define custom logger levels
# steps: above info, below warning
LL_STEP_MINOR = 21
LL_STEP_MAJOR = 22
# regster
logging.addLevelName(LL_STEP_MINOR, 'MAJOR STEP')
logging.addLevelName(LL_STEP_MAJOR, 'MINOR STEP')

# set up logger
log = logging.Logger('cymirs_logger_main')
# add handler
log_handler = logging.StreamHandler(stream=sys.stderr)
log_handler.setFormatter(logging.Formatter(fmt='[%(levelname)s] %(message)s'))
log.addHandler(log_handler)
# add filter
log_filter = TextEmailFilter()
log_filter.defconfig()
log.addFilter(log_filter)

def send_email(msg):
	"""Send an email with default subject and given message."""
	# TODO... maybe...
	pass

requests = None
def send_text(dest, msg):
	"""Send a text with given contents to given number.

	Uses the textbelt service."""
	if requests is None:
		requests = __import__('requests')
	# send POST request to textbelt
	post_req = requests.post('http://textbelt.com/text', data={'number':dest, 'message':msg})
	
	# look at status
	if post_req.status_code != requests.codes.ok or post_req.headers['success'] != 'true':
		raise 1 # alert caller of failure

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
		# send email, text if appropriate
		if self.addr_email and record.levelno in when_email:
			try:
				send_email(self.addr_email, record.message)
			except:
				log.warning('Failed to send email; will not try again.')
				self.addr_email = ''

		if self.addr_txt and record.leveno in self.when_text:
			try:
				send_txt(self.addr_txt, record.message)
			except:
				log.warning('Failed to send text; will not try again.')
				self.addr_txt = ''

		# accept everything, change nothing
		return True