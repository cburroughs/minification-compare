#!/usr/bin/env python

# need to re-think exactly what I want this to do ..
# - 2 programs --> bunch of files (most important)
# - bunch of programs --> one file (or bunch?)


# todo: ability to save output file(s) to directory

import glob
import gzip
import itertools
import json
import os
import pprint
import sys
import tempfile

import path
# external dep, would like to eventually remove
from paver.easy import sh


# todo: move to external file
CSS_CMDS = {
    'yui-compressor-2.4.2' :
        {'cmd': 'java -jar minify-programs/yuicompressor-2.4.2.jar --type css -o OUTFILE INFILE'},
#    'CssCompressor.jar':
#        {'cmd': 'java -jar minify-programs/CssCompressor.jar -o OUTFILE INFILE'},
    'csstidy' :
        {'cmd': './minify-programs/csstidy   INFILE --optimise_shorthands=2 OUTFILE'}

    }


JS_CMDS = {
    'yui-compressor-2.4.2' :
        {'cmd': 'java -jar minify-programs/yuicompressor-2.4.2.jar --type js -o OUTFILE INFILE'},
    }



# todo: decide on best way to compare
def percent_difference(x1, x2):
    """ http://en.wikipedia.org/wiki/Percent_difference """
    return abs(1.0 * x1 - x2) / (1.0 * (x1 + x2) / 2)


def percent_change(x_old, x_new):
    """ http://en.wikipedia.org/wiki/Percentage_change """
    return (1.0 * x_new - x_old) / x_old


def rel_size(old, new):
    return 1 - (1.0 * new) / old


class MiniStats(object):
    """ Stats for what happens on one run of a minification program"""
    #in_file_size, in_file_size_gz, out_file_size,
    #out_file_size_gz)
    def __init__(self, in_size=0, in_size_gz=0,
                 out_size=None, out_size_gz=None):
        self.in_size = in_size
        self.in_size_gz = in_size_gz
        self.out_size = in_size if out_size is None else out_size
        self.out_size_gz = in_size if out_size_gz is None else out_size_gz

    def change(self, cmp_func=percent_change, gz=False):
        vanilla_change = cmp_func(self.in_size, self.out_size)
        gz_change = cmp_func(self.in_size_gz, self.out_size_gz)
        if gz:
            return gz_change
        else:
            return vanilla_change


# os.stat(path) . st_size
def file_stsz(file_path):
    """ How many bytes is the file on the given path?"""
    return os.stat(file_path).st_size


def gzipped_file_size(file_name, level=6):
    """ How big is a file when it is gzipped?"""
    file_obj = open(file_name)
    gzipped_file = gzip.open(tempfile.NamedTemporaryFile().name, 'wb',
                            compresslevel=level)
    gzipped_file.writelines(file_obj.readlines())
    gzipped_file.flush()
    return file_stsz(gzipped_file.name)


# filename or file obj?
def minify_file(cmd_info, orig_file):
    """ Minify one file with the given command and return a bunch of stats. """
    in_file = orig_file
    #pin_file = path.path(os.getcwd() + in_file)
    pin_file = in_file
    out_file = path.path(pin_file)
    ref_cout_delete = [] # all will be deleted when function ends, but
                         # we need to hang on to them until then
    #out_file = tempfile.NamedTemporaryFile(delete=True)
    pin_file = path.path(out_file.name)
    out_file = tempfile.NamedTemporaryFile(delete=True)
    #debug:
    print in_file, pin_file, pin_file.abspath()
    # todo: replace with template?
    cmd = cmd_info['cmd'].replace('INFILE', in_file).replace('OUTFILE', out_file.name)
    #print cmd
    #o = check_output(cmd.split(' '))
    o = sh(cmd)
    ref_cout_delete.append(out_file)

    in_file_size = file_stsz(orig_file)
    #out_file_size = file_stsz(out_file.name)
    in_file_size_gz = gzipped_file_size(orig_file)
    out_file_size_gz = gzipped_file_size(out_file.name)
    out_file_size = os.path.getsize(out_file.name)
    res_stats = MiniStats(in_size=in_file_size, in_size_gz=in_file_size_gz,
                          out_size=out_file_size, out_size_gz=out_file_size_gz)

    return (cmd_info, res_stats)


def print_text(cmd_list, res_stats):
    if len(cmd_list) == 0:
        return
    pprint.pprint(cmd_list)

    print ("in size: %s | out_size: %s | percent-change: %s" %
           (res_stats.in_size, res_stats.out_size,
            res_stats.change()))
    print ("in size gz: %s | out_size gz: %s | percent-change gz: %s" %
           (res_stats.in_size_gz, res_stats.out_size_gz,
            res_stats.change(gz=True)))
    print '----------'


def parse_argv(argv):
    from optparse import OptionParser

    parser = OptionParser()

    parser.add_option('--in-file-glob', dest='in_file_glob', default=None,
                      help='file we are trying to minify')
    # todo: better as args?
    parser.add_option('--mini-a', dest='base_mini', default=None,
                  help='')
    parser.add_option('--mini-b', dest='challenge_mini', default=None,
                  help='')
    # todo: n way compare
    parser.add_option('--type', dest='file_type', default='js',
                  help='css or js?')

    #parser.add_option('--try-chain', dest='out_format', default=False,
    #                  action='store_true',
    #                  help='try in multiple order')
    (opts, args) = parser.parse_args()

    if opts.in_file_glob is None:
        print >> sys.stderr, 'ERROR: Must specify a file.'
        parser.print_help()
        sys.exit(1)

    # if opts.base_mini is None or opts.challenge_mini is None:
    #     print >> sys.stderr, 'ERROR: Must specify minify programs.'
    #     parser.print_help()
    #     sys.exit(1)


    return (opts, args)


def main(argv):
    (opts, args) = parse_argv(argv)
    in_file_glob = opts.in_file_glob

    cmds = CSS_CMDS if opts.file_type == 'css' else JS_CMDS

    # todo: don't pass raw directories
    for file_name in glob.glob(in_file_glob):
        print file_name
        (cmd_list, res_stats) = minify_file(cmds[opts.base_mini], file_name)
        print_text(cmd_list, res_stats)
        print '--------------------'
        (cmd_list, res_stats) = minify_file(cmds[opts.challenge_mini],
                                            file_name)
        print_text(cmd_list, res_stats)

    # todo: mean comparision, total comparison


if __name__ == '__main__':
    main(sys.argv[1:])
