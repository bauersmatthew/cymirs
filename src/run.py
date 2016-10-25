from cm_err import *
import util as ut
import jf_mgr as jfm
from collections import namedtuple

Interval = namedtuple('Interval', ['chrom', 'start', 'end', 'strand'])

def load_circ_file(path):
    """Loads the circle info file at the given path.

    Returns in two parts:
        -    The intervals
        -    The other info

    Other info entry contents:
        (circ_id, gene_id, reg, pval)"""
    intervals = []
    circ_info = {}
    try:
        with open(path) as fin:
            for line in fin:
                line = line.rstrip()
                # skip blank lines
                if not line:
                    continue
                
                fields = line.split('\t')
                curr_intvl = Interval(fields[2], int(fields[3]), int(fields[4]), fields[5])
                intervals.append(curr_intvl)
                circ_info[curr_intvl] = (fields[0], fields[1], float(fields[6]), float(fields[7]))
    except:
        raise CMERun('Failed to load circ file!', 2)

    return intervals, circ_info

def load_region_file(path):
    """Loads the BED region file at the given path."""
    intervals = []
    try:
        with open(path) as fin:
            for line in fin:
                line = line.rstrip()
                if not line:
                    continue
                fields = line.split('\t')
                curr_intvl = Interval(fields[0], int(fields[1]), int(fields[2]), fields[5])
                intervals.append(curr_intvl)
    except:
        raise CMERun('Failed to load (non-circle) region file!', 3)

    return intervals


def run_job(jf_path):
    """Run job, given job config file."""
    # load job file
    config = None
    try:
        config = jfm.load_jf(jf_path)
    except CMErr:
        raise
    except:
        raise CMERun('Job file loading failed unexpectedly!', 1)

    # respond to global/immediate log settings
    # logging
    ut.log_filter.set_addr_txt(config['JFT_TEXT_ADDR'])
    ut.log_filter.set_when_txt(config['JFT_TEXT_WHEN'])
    # log verbosity/level is set in load_jft!

    # load circ/region file
    do_circ = True if config['JFT_CIRC_FILE'] else False
    intervals = None
    circ_info = None
    if do_circ:
        intervals, circ_info = load_circ_file(config['JFT_CIRC_FILE'])
    else:
        intervals = load_region_file(config['JFT_REGION_FILE'])

    # run bedtools 