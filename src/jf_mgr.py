import sys
import os
from cm_err import *
"""Manage job file IO."""

job_file_tags = dict(
    JFT_CIRC_FILE='CIRC_INFO_FILE',
    JFT_MIR_FILE='MIR_INFO_FILE',
    JFT_GENOME_FILE='GENOME_FILE',
    JFT_OUT_DIR='OUTPUT_DIR',
    JFT_SIG_PVAL='SIG_PVALUE',
    JFT_FC_UPREG='FOLDCHNG_UP',
    JFT_FC_DOWNREG='FOLDCHNG_DOWN',
    JFT_KEEP_TMP='KEEP_TEMP_FILES',
    JFT_STT_OUT_FMT='SSHEET_OUT_FORMAT',
    JFT_TOP_N='TOP_N_VAL',
    JFT_KEEP_ALL_OUTPUT='KEEP_ALL',
    JFT_VERBOSITY='VERBOSITY',
    JFT_EMAIL_ADDR='EMAIL',
    JFT_EMAIL_WHEN='EMAIL_ON',
    JFT_TEXT_ADDR='TEXT_NUM',
    JFT_TEXT_WHEN='TEXT_ON')

def generate_template(dest = sys.stdout):
    """Write a template file to the given file."""
    contents = (
        "# this is a comment line!\n'
        '# all paths are relative to THIS FILE.\n'
        '# all fields must be filled in unless stated otherwise.\n'
        '# all multiple-choice fields are case-insensitive.\n\n'
        
        '#     ----    FILES    ----\n\n'
        
        '# the file containing info about the circRNAs.\n'
        '# format:\n'
        '#     circ_id\tgene_id\tchrom\tstart\tend\tstrand\treg\tp-va\n'
        '# notes:\n'
        '#     start and end coords are 0-based, [start, end) like BED.\n'
        '#     if reg is undefined, write na, NA, inf, or INF.\n'
        '{jft[JFT_CIRC_FILE]}=\n\n'
        
        '# the file containing info about the miRNAs.\n'
        '# the format of this file is described by targetscan.\n'
        '{jft[JFT_MIR_FILE]}=\n\n'
        
        '# the genome file.\n'
        '# this file should be formatted as a FASTA (NOT FASTQ!).\n'
        '# usually, it can be obtained from UCSC.\n'
        '{jft[JFT_GENOME_FILE]}=\n\n'
        
        '# the output directory.\n'
        '# the directory to write all output files to.\n'
        '{jft[JFT_OUT_DIR]}=./cymirs_out\n\n'
        
        '#     ----    OTHER SETTINGS    ----\n\n'
        
        '# the largest p-value to accept as significant.\n'
        '{jft[JFT_SIG_PVAL]}=.05\n\n'
        
        '# the minimum fold change required to be upregulated.\n'
        '# this value must be greater than FOLDCHNG_DOWN.\n'
        '# expressions (e.g. 1/2) are accepted.\n'
        '{jft[JFT_FC_UPREG]}=1.5\n\n'
        
        '# the maximum fold change required to be downregulated.\n'
        '# this value must be less than FOLDCHNG_UP.\n'
        '# expressions (e.g. 1/2) are accepted.\n'
        '# if this value is left blank, 1/{jft[JFT_FC_UPREG]} is used.\n'
        '{jft[JFT_FC_DOWNREG]}=\n\n'
        
        '# whether or not to keep temp files.\n'
        '# Yes ==> keep | No ==> delete\n'
        '{jft[JFT_KEEP_TMP]}=No\n\n'
        
        '# what formats to output stats in.\n'
        '# this should be a comma-separated (no spaces) list of formats.\n'
        '# avaliable formats: tsv | csv | xlsx\n'
        '{jft[JFT_STT_OUT_FMT]}=xlsx\n\n'
        
        '# the value of N in the given top-N miRNA overview per circle.\n'
        '{jft[JFT_TOP_N]}=5\n\n'
        
        '# whether or not all miRNA info should be kept in the final output, or if only the top-N should be displayed.\n'
        '# note: information about all miRNAs will still be available.\n'
        '{jft[JFT_KEEP_ALL_OUTPUT]}=No\n\n'
        
        '# how verbose the stderr output should be.\n'
        '# options: silent (NOT RECOMMENDED) | normal | verbose\n'
        '{jft[JFT_VERBOSITY]}=verbose\n\n'
        
        '#     ----    STATUS UPDATES    ----\n\n'
        
        '# where to send email messages to\n'
        '# if left blank, emails will not be sent.\n'
        '{jft[JFT_EMAIL_ADDR]}=\n\n'
        
        '# when to send email messages\n'
        '# this should be a comma-separated (no spaces) list of events.\n'
        '# available events:\n'
        '#     step-minor | step-major\n'
        '#     warning | error\n'
        '#     after | finish\n'
        '#     rundown\n'
        '# notes:\n'
        "#     'after' takes the number of minutes a parameter: after(60)\n"
        "#     'rundown' gives a rundown of the result on completion.\n"
        '{jft[JFT_EMAIL_WHEN]}=error,finish,rundown\n\n'
        
        '# where to send text messages to\n'
        '# if left blank, texts will not be sent.\n'
        '{jft[JFT_TEXT_ADDR]}=\n\n'
        
        '# when to send text messages\n'
        '# this option follows the same format and parameters as {jft[JFT_EMAIL_WHEN]}.\n'
        '{jft[JFT_TEXT_WHEN]}=error,finish,rundown\n\n'.format(jft=job_file_tags)
        
    dest.write(contents)
    
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

def _jf_verify_value(parts):
    # function to get groups of tags easily
    gtgs = lambda *x: [job_file_tags[a] for a in x]
    
    # handle blank values
    if not parts[1]:
        # ok only if tag allows blanks
        if parts[0] in gtgs('JFT_FC_DOWNREG', 'JFT_EMAIL_ADDR', 'JFT_TEXT_ADDR'):
            return True
        return False
        
    # handle files
    if parts[0] in gtgs('JFT_CIRC_FILE', 'JFT_MIR_FILE', 'JFT_GENOME_FILE'):
        return os.path.isfile(parts[1])
    # directories
    if parts[0] in gtgs('JFT_OUT_DIR'):
        # try to create if doesn't exist
        if not os.path.isdir(parts[1]):
            try:
                os.makedirs(parts[1])
            except:
                return False
        # the directory exists now, if it didn't before
        return True
        
    # handle numbers
    # expression-allowing
    if parts[0] in gtgs('JFT_SIG_PVAL', 'JFT_FC_UPREG', 'JFT_FC_DOWNREG'):
        parts[1] = eval_expr(parts[1])
        if parts[1] is None:
            return False
        return True
    # non-expression allowing
    if parts[0] in gtgs('JFT_TOP_N'):
        try:
            parts[1] = int(parts[1])
        except:
            return False
        return True
        
    # more specific cases
    # TODO TODO TODO TODO TODO
    

def load_jf(path):
    """Load a job file."""
    
    # check that path validity
    if not os.path.isfile(path):
        raise CMELoad('invalid job file path', 1)
    
    # load file
    lines = None
    try:
        with open(path) as fh:
            lines = fh.readlines()
    except:
        raise CMELoad('could not open job file', 2)
        
    # set working directory so that future paths work relative to the job file
    os.chdir(os.path.dirname(path))

    # parse line by line
    for lnum, line in enumerate(lines):
        line = line.strip()
        
        # skip blank lines, comments
        if not line or line[0] == '#':
            continue
            
        # check assignment line (first pass)
        if '=' not in line:
            raise CMELoad("job file invalid (no '=') @ line {}".format(lnum+1), 3)
            
        parts = line.split('=')
        parts[0] = parts[0].upper() # case insensitive
        
        # verify tag (second pass)
        if parts[0] not in job_file_tags.values():
            raise CMELoad('job file invalid (unrecognized tag) @ line {}'.format(lnum+1), 4)
            
        # verify value (second pass)
        
