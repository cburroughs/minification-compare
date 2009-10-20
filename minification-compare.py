#!/usr/bin/env python

# need to re-think exactly what I want this to do ..
# - bunch of programs --> one file (or bunch?)
# - 2 programs --> bunch of files


import glob
import gzip
import itertools
import json
import os
import pprint
import sys
import tempfile

import path
# external dep, would like to eventuall remove
from paver.easy import sh


CSS_CMDS = {
    'yui-compressor-2.4.2' :
    {'cmd': 'java -jar minify-programs/yuicompressor-2.4.2.jar --type css -o OUTFILE INFILE'},
    'CssCompressor.jar':
        {'cmd': 'java -jar minify-programs/CssCompressor.jar -o OUTFILE INFILE'}
    }


JS_CMDS = {
    'yui-compressor':
        {'cmd': 'java -jar minify-programs/yuicompressor-2.4.2.jar --type js -o OUTFILE INFILE'}
    }


def percent_difference(x1, x2):
    return abs(1.0 * x1 - x2) / (1.0 * (x1 + x2) / 2)


def percent_change(x_old, x_new):
    return (1.0 * x_new - x_old) / x_old


# os.stat(path) . st_size
def file_stsz(file_path):
    return os.stat(file_path).st_size


def rel_size(old, new):
    return 1 - (1.0 * new) / old


def gzipped_file_size(file_name, level=6):
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
    ref_cout_delete = [] # all will be deleted when function ends
    #out_file = tempfile.NamedTemporaryFile(delete=True)
    # just css for now
    pin_file = path.path(out_file.name)
    out_file = tempfile.NamedTemporaryFile(delete=True)
    print in_file, pin_file, pin_file.abspath()
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
    #print out_file_size
    #in_file_size_gz = None
    #out_file_size_gz = None
    # todo: define classes or at least dicts for passing all this around
    return (cmd_info, in_file_size, in_file_size_gz, out_file_size,
            out_file_size_gz)


def print_text(cmd_list, in_file_size, in_file_size_gz, out_file_size,
                out_file_size_gz):
    if len(cmd_list) == 0:
        return
    pprint.pprint(cmd_list)
    print ("in size: %s | out_size: %s | percent-change: %s" %
           (in_file_size, out_file_size,
            percent_change(in_file_size, out_file_size)))
    print ("in size gz: %s | out_size gz: %s | percent-change gz: %s" %
           (in_file_size_gz, out_file_size_gz,
            percent_change(in_file_size_gz, out_file_size_gz)))

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
    parser.add_option('--type', dest='file_type', default=None,
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
        (cmd_list, in_file_size, in_file_size_gz, out_file_size,
         out_file_size_gz) = minify_file(cmds[opts.base_mini], file_name)
        print_text(cmd_list, in_file_size, in_file_size_gz, out_file_size,
                   out_file_size_gz)
    # todo: mean comparision, total comparison


if __name__ == '__main__':
    main(sys.argv[1:])
