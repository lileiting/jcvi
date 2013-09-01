#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
Perform DNA-DNA alignment using BLAST, NUCMER and BLAT. Keep the interface the
same and does parallelization both in core and on grid.
"""

import sys

from jcvi.utils.cbook import depends
from jcvi.apps.base import OptionParser, ActionDispatcher, debug
debug()


@depends
def run_formatdb(infile=None, outfile=None, dbtype="nucl"):
    cmd = BLPATH("makeblastdb")
    cmd += " -dbtype {0} -in {1}".format(dbtype, infile)
    sh(cmd)


@depends
def run_blat(infile=None, outfile=None, db="UniVec_Core", pctid=95, hitlen=50):
    cmd = 'blat {0} {1} -out=blast8 {2}'.format(db, infile, outfile)
    sh(cmd)

    blatfile = outfile
    filtered_blatfile = outfile + ".P{0}L{1}".format(pctid, hitlen)
    run_blast_filter(infile=blatfile, outfile=filtered_blatfile,
            pctid=pctid, hitlen=hitlen)
    shutil.move(filtered_blatfile, blatfile)


@depends
def run_vecscreen(infile=None, outfile=None, db="UniVec_Core",
        pctid=None, hitlen=None):
    """
    BLASTN parameters reference:
    http://www.ncbi.nlm.nih.gov/VecScreen/VecScreen_docs.html
    """
    nin = db + ".nin"
    run_formatdb(infile=db, outfile=nin)

    cmd = BLPATH("blastn")
    cmd += " -task blastn"
    cmd += " -query {0} -db {1} -out {2}".format(infile, db, outfile)
    cmd += " -penalty -5 -gapopen 4 -gapextend 4 -dust yes -soft_masking true"
    cmd += " -searchsp 1750000000000 -evalue 0.01 -outfmt 6 -num_threads 8"
    sh(cmd)


@depends
def run_megablast(infile=None, outfile=None, db=None, wordsize=None, \
        pctid=98, hitlen=100, best=None, evalue=0.01, task="megablast", cpus=16):

    assert db, "Need to specify database fasta file."

    nin = db + ".nin"
    nin00 = db + ".00.nin"
    nin = nin00 if op.exists(nin00) else (db + ".nin")
    run_formatdb(infile=db, outfile=nin)

    cmd = BLPATH("blastn")
    cmd += " -query {0} -db {1} -out {2}".format(infile, db, outfile)
    cmd += " -evalue {0} -outfmt 6 -num_threads {1}".format(evalue, cpus)
    cmd += " -task {0}".format(task)
    if wordsize:
        cmd += " -word_size {0}".format(wordsize)
    if pctid:
        cmd += " -perc_identity {0}".format(pctid)
    if best:
        cmd += " -max_target_seqs {0}".format(best)
    sh(cmd)

    if pctid and hitlen:
        blastfile = outfile
        filtered_blastfile = outfile + ".P{0}L{1}".format(pctid, hitlen)
        run_blast_filter(infile=blastfile, outfile=filtered_blastfile,
                pctid=pctid, hitlen=hitlen)
        shutil.move(filtered_blastfile, blastfile)


def run_blast_filter(infile=None, outfile=None, pctid=95, hitlen=50):
    from jcvi.formats.blast import filter

    logging.debug("Filter BLAST result (pctid={0}, hitlen={1})".\
            format(pctid, hitlen))
    pctidopt = "--pctid={0}".format(pctid)
    hitlenopt = "--hitlen={0}".format(hitlen)
    filter([infile, pctidopt, hitlenopt])


def main():

    actions = (
        ('blast', 'run blastn using query against reference'),
            )
    p = ActionDispatcher(actions)
    p.dispatch(globals())


def blast(args):
    """
    %prog blast ref.fasta query.fasta

    Calls blast and then filter the BLAST hits. Default is megablast.
    """
    task_choices = ("blastn", "blastn-short", "dc-megablast", \
                    "megablast", "vecscreen")

    p = OptionParser(blast.__doc__)
    p.set_align(pctid=None, evalue=.01)
    p.add_option("--wordsize", type="int", help="Word size [default: %default]")
    p.add_option("--best", default=1, type="int",
            help="Only look for best N hits [default: %default]")
    p.add_option("--task", default="megablast", choices=task_choices,
            help="Task of the blastn, one of {0}".\
                 format("|".join(task_choices)) + " [default: %default]")
    p.set_cpus()
    opts, args = p.parse_args(args)

    if len(args) != 2:
        sys.exit(not p.print_help())

    reffasta, queryfasta = args
    q = op.basename(queryfasta).split(".")[0]
    r = op.basename(reffasta).split(".")[0]
    blastfile = "{0}.{1}.blast".format(q, r)

    run_megablast(infile=queryfasta, outfile=blastfile, db=reffasta,
                  wordsize=opts.wordsize, pctid=opts.pctid, evalue=opts.evalue,
                  hitlen=None, best=opts.best, task=opts.task, cpus=opts.cpus)

    return blastfile


if __name__ == '__main__':
    main()