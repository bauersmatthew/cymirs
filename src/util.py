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


class PathGenerator:
	"""To assist with generating appropriate paths."""
	def __init__(self):
		self.prefix = ''
		self.keeptmp = False

	def set_outdir(self, path):
		"""Set output directory."""
		self.prefix = path + '/'

	def set_keeptmp(self, keep):
		"""Set whether or not to keep temp files."""
		self.keeptmp = keep

	def gen_outf(self, name):
		"""Generate an output file path."""
		return self.prefix + name

	def gen_tmpf(self, name):
		"""Generate a temp file path."""
		if self.keeptmp:
			return self.prefix + 'tmp/tmp-' + name
		else:
			return 

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
		self.addr_txt = ''
		self.when_txt = []

	def set_addr_txt(self, jf_val):
		"""Set txt address according to job file value."""
		self.addr_txt = jf_val

	def _parse_jfv_when(self, jf_val):
		"""Parse on when values for text/email.

		Intented for internal use only."""
		if not jf_val:
			return []

		parsed = []

		events = jf_val.split(',')
		for ev in events:
			parsed.append(
				{
				"step-minor":LL_STEP_MINOR,
				"step-major":LL_STEP_MAJOR,
				"warning":logging.WARNING,
				"error":logging.ERROR
				# others (after/finish/rundown) not handled here
				}[ev])
		return parsed

	def set_when_txt(self, jf_val):
		"""Set txt triggers according to job file value."""
		self.when_txt = self._parse_jfv_when(jf_val)

	def filter(self, record):
		# send email, text if appropriate
		if self.addr_email and record.levelno in when_email:
			try:
				send_email(self.addr_email, record.message)
			except:
				log.warning('Failed to send email; will not try again.')
				self.addr_email = ''

		if self.addr_txt and record.leveno in self.when_txt:
			try:
				send_txt(self.addr_txt, record.message)
			except:
				log.warning('Failed to send text; will not try again.')
				self.addr_txt = ''

		# accept everything, change nothing
		return True