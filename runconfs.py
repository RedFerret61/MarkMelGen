#!/usr/bin/env python
# -*- coding: utf-8 -*-
# runconfs.py which runs MarkMelGen with the configuration files in the directory and passes on parameters and searches output for errors
# free and open-source software, Paul Wardley Davies, see MarkMelGen/license.txt

# usage: runconfs.py [-h] [-c CONFIG] [-g] [-s]
#
# optional arguments:
#   -h, --help            show this help message and exit
#   -c CONFIG, --config CONFIG
#                         config file path, relative to current working directory e.g. conf
#   -g                    No graphs i.e. override DISPLAY_GRAPHS = False
#   -s                    No score. i.e. override DISPLAY_SCORE = False

# usage examples:
# 1. run top level
# cd <installation directory>
# python runconfs.py
#
# 2. run conf
# python runconfs.py -c conf
#
# 3. run conf/test without graphs or scores
# python runconfs.py -c conf/test -g -s


# standard libraries
import argparse
import glob
import os
import platform
import subprocess
from time import strftime
# from datetime import datetime


def main():

    # get platform
    os_name = os.name
    platform_system = platform.system()
    platform_release = platform.release()
    # print('os_name', os_name,'platform_system',platform_system,'platform_release',platform_release)
    # e.g. nt Windows 10
    # e.g. Linux platform_release 5.4.0-26-generic
    
    # Get the current working directory
    cwd = os.getcwd()
    # Print the current working directory
    # print("Current working directory: {0}".format(cwd))

    parser = argparse.ArgumentParser()

    # Specify command line arguments.
    parser.add_argument('-c', '--config',
                        help='config file path, relative to current working directory e.g. conf',
                        default='',
                        type=str)
    parser.add_argument(
        "-g",
        help="No graphs i.e. override DISPLAY_GRAPHS = False",
        action="store_true"
    )
    parser.add_argument(
        "-s",
        help="No score. i.e. override DISPLAY_SCORE = False",
        action="store_true"
    )

    # Parse command line arguments.
    args = parser.parse_args()

    # Bind reference to specified options.
    args_config = os.path.basename(args.config)
    # print("args.config, args_config", args.config, args_config)
    args_g = args.g
    args_s = args.s

    program_arguments = ' '

    # Bind reference to final parameter values.
    # print('args_g',args_g, 'args_s', args_s)
    if args_g is not None:
        if args_g:
            # print('-g found so no graphs i.e. override DISPLAY_GRAPHS = False')
            program_arguments = program_arguments + '-g '

    if args_s is not None:
        if args_s:
            # print('-s found so no score. i.e. override DISPLAY_SCORE = False')
            program_arguments = program_arguments + '-s '

    program_fully_qualified = "python3 MarkMelGen.py" + program_arguments
    if "Windows" in platform.system():        
        program_fully_qualified = "python MarkMelGen.py" + program_arguments
        
    # print('program_fully_qualified', program_fully_qualified)

    # os.curdir is a string representing the current directory (always '.')   -
    # os.pardir is a string representing the parent directory (always '..')   -
    # os.sep is the (or a most common) pathname separator ('/' or '\\')

    rel_config_path = os.curdir + os.sep + args.config
    # print('rel_config_path', rel_config_path)

    # os.chdir(os.curdir + os.sep + args_config)
    os.chdir(rel_config_path)

    conf_files = glob.glob(f'*.conf')
    print('\nConfiguration files found:', conf_files, '\n')

    # Change to original current working directory
    os.chdir(cwd)
    # print("Current working directory: {0}".format(cwd))

    # cases for graphs and score flags:
    # None  Pre close*2 pktc
    # -g        Pre close s pktc
    # -g -s   None
    # -s.       Post close g pktc

    redirection_base_str = ' > '
    redirection_end_str = ' 2>&1'

    for conf_file in conf_files:

        conf_file_no_extension = os.path.splitext(conf_file)[0]
        # print('conf_file', conf_file, 'conf_file_no_extension',conf_file_no_extension)
        dt_string = strftime("%Y%m%d-%H_%M_%S")
        # print("date and time =", dt_string)
        log_path_file = 'output' + os.sep + conf_file_no_extension + '-' + dt_string + '.log'
        redirection_str = redirection_base_str + log_path_file + redirection_end_str
        # print('redirection_str', redirection_str)

        call_str = program_fully_qualified + '-c' + rel_config_path + os.sep + conf_file + redirection_str
        # print('Next Command line to run: ', call_str)
        # input('Press Enter to continue...')

        if (not args_s) and (not args_g):
            print('\nAfter MarkMelGen has run. 1. Close all graph windows. 2. Close score window to continue. (Discard as score already saved)')
            # input('Press Enter to continue...')

        if (not args_s) and (args_g):
            print('\nAfter MarkMelGen has run. Close score window to continue. (Discard as score already saved)')
            # input('Press Enter to continue...')

        # run MarkMelGen
        print(dt_string,'Running: ', call_str,'...')
        subprocess.call(call_str, shell=True)

        # look for failures in log
        logfile_list = open(log_path_file)
        search_words = ['Traceback', 'MarkMelGen.py', 'Error', 'Warning']
        print('Search log for', search_words, '...blank if nothing found...')
        for line in logfile_list:
            if any(word in line for word in search_words):
                print(line)

        # if no_score_with_graphs:
        if (args_s) and (not args_g):
            input('\nClose all graph windows, then ... Press Enter to continue...')

if __name__ == '__main__':

    main()
