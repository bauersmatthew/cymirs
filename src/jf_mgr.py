import sys
import os
from cm_err import *
import util as ut
import logging
"""Manage job file IO."""

job_file_tags = dict(
    JFT_CIRC_FILE='CIRC_INFO_FILE',
    JFT_REGION_FILE='REGION_INFO_FILE',
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

# tag categories
jft_blank_ok = ut.get_tag_batch( # can be blank
    job_file_tags,
    ('JFT_CIRC_FILE', 'JFT_REGION_FILE',
        'JFT_FC_DOWNREG',
        'JFT_EMAIL_ADDR', 'JFT_EMAIL_WHEN', 'JFT_TEXT_ADDR', 'JFT_TEXT_WHEN'))
jft_xor_groups = tuple(ut.get_tag_batch(job_file_tags, grp) for grp in ( # one or other given but not both
    ('JFT_CIRC_FILE', 'JFT_REGION_FILE')))
jft_files = ut.get_tag_batch( # is a file
    job_file_tags,
    ('JFT_CIRC_FILE', 'JFT_REGION_FILE', 'JFT_MIR_FILE', 'JFT_GENOME_FILE'))
jft_dirs = ut.get_tag_batch(job_file_tags, ('JFT_OUT_DIR')) # is a directory
jft_exprs = ut.get_tag_batch(job_file_tags, ('JFT_SIG_PVAL', 'JFT_FC_UPREG', 'JFT_FC_DOWNREG')) # float expressions
jft_nums = ut.get_tag_batch(job_file_tags, ('JFT_TOP_N')) # flat ints only
jft_mch = ut.get_tag_bath( # answers are restricted (e.g. yes/no, high/medium/low)
    job_file_tags,
    ('JFT_KEEP_TMP', 'JFT_STT_OUT_FMT', 'JFT_KEEP_ALL_OUTPUT', 'JFT_VERBOSITY',
        'JFT_EMAIL_WHEN', 'JFT_TEXT_WHEN'))

def generate_template(dest = sys.stdout):
    """Write a template file to the given file."""
    contents = None
    with open('jf_template.txt') as fh:
        contents = fh.read().format(jft=job_file_tags)
    dest.write(contents)

def _check_mch_tags(parts):
    """(Internal) Check values for multiple choice tags."""
    tag = parts[0]

    # just go through and check each separately/specifically
    if tag in ut.get_tag_batch(job_file_tags, ('JFT_KEEP_TMP', 'JFT_KEEP_ALL_OUTPUT'))
        return (parts[1].lower() in ['yes', 'no'])
    elif tag == job_file_tags['JFT_STT_OUT_FMT']:
        vals = parts[1].split(',')
        for val in vals:
            if val.lower() not in ['tsv', 'csv', 'xlsx']:
                return False
        return True
    elif tag == job_file_tags['JFT_VERBOSITY']:
        return (parts[1].lower() in ['slient', 'normal', 'verbose'])
    elif tag in ut.get_tag_batch(job_file_tags, ('JFT_EMAIL_WHEN', 'JFT_TEXT_WHEN')):
        vals = parts[1].split(',')
        for val in vals:
            if val.lower() not in ['step-minor', 'step-major', 'warning', 'error', 'after', 'finish', 'rundown']:
                return False
        return True

    # should never get here
    return False

def _jf_verify_value(parts):
    # function to get groups of tags easily
    gtgs = lambda *x: [job_file_tags[a] for a in x]
    
    # handle blank values
    if not parts[1]:
        # ok only if tag allows blanks
        if parts[0] in jft_blank_ok:
            return True
        return False
        
    # handle files
    if parts[0] in jft_files:
        if not parts[1]:
            pass
        return os.path.isfile(parts[1])
    # directories
    if parts[0] in jft_dirs:
        if not parts[1]:
            pass
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
    if parts[0] in jft_exprs:
        if not parts[1]:
            pass
        parts[1] = ut.eval_expr(parts[1])
        if parts[1] is None:
            return False
        return True
    # non-expression allowing
    if parts[0] in jft_nums:
        if not parts[1]:
            pass
        try:
            parts[1] = int(parts[1])
        except:
            return False
        return True
        
    # multiple/restricted choice
    if parts[0] in jft_mch:
        return _check_mch_tags(parts)

    # should never get here
    return False
    
def _jf_fill_blank(blank, config):
    """Fill in ONE blank."""
    if blank == 'JFT_FC_DOWNREG':
        config[blank] = 1/config['JFT_FC_UPREG']
    if blank in ('JFT_REGION_FILE', 'JFT_CIRC_FILE'):
        config[blank] = ''

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

    config = {} # descibe configuration given by job file

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
        if not _jf_verify_value(parts):
            raise CMELoad('job file invalid (invalid value) @ line {}'.format(lnum+1), 5)

        # save tag/value
        config[parts[0]] = parts[1]

    # check that all required tags are given
    for jft in job_file_tags:
        if jft not in config and jft not in jft_blank_ok:
            raise CMELoad('job file invalid (required fields missing)', 6)

    # translate logger level to be python compatible
    config['JFT_VERBOSITY'] = \
        {'silent':logging.CRITICAL, 'normal':logging.INFO, 'verbose':logging.DEBUG}[config['JFT_VERBOSITY']]
    # set logger level
    ut.log.setLevel(config['JFT_VERBOSITY'])

    # handle blank-ok tags
    for jft in jft_blank_ok:
        if jft not in config:
            ut.log.warning("Tag '{}' not found; using default.".format(jft))
            _jf_fill_blank(jft, config)
        elif not config[jft]:
            _jf_fill_blank(jft, config)

    # handle xor groups
    # go through each group, making sure only one tag in the group is given
    for xgrp in jft_xor_groups:
        found_one = False
        for tag in xgrp:
            if config[tag]:
                if found_one:
                    raise CMELoad('job file invalid (conficting tags given)', 7)
                else:
                    found_one = True

    # finished; return
    return config