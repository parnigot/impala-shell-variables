#!/usr/bin/env python

from optparse import OptionParser
import logging
import sys
import codecs
import os.path
import subprocess


# Initialize module level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)
stderr_handler = logging.StreamHandler()
stderr_formatter = logging.Formatter(u"%(levelname)s: %(message)s")
stderr_handler.setFormatter(stderr_formatter)
logger.addHandler(stderr_handler)

# Some constants
CONFIG_FILE_SEPARATOR = "="
VERSION = '0.1'
CLI_USAGE_MESSAGE = u"""\
%prog [options] <path-to-sql-file> <path-to-configuration-file>

Script that runs a query against impala, using impala-shell, performing variable
substitution from a configuration file.
"""


def parse_cli_arguments():
    """Parse cli arguments. I'm using OptParse for python2.6 compatibility
    (RHEL 6)

    :return the output of OptionParser.parse(), a tuple with (options, args)
    """
    parser = OptionParser(usage=CLI_USAGE_MESSAGE, version=VERSION)
    # Add additional-options option
    parser.add_option(
        '-a', '--additional-options',
        help=u'Additional options for impala-shell, double quoted '
             u'(es: "-k -d DBNAME")',
        default=None
    )
    parser.add_option(
        '-v', '--verbose',
        action="store_true",
        help=u"Turn on verbose output",
        default=False
    )
    parser.add_option(
        '-d', '--dry-run',
        action="store_true",
        help=u"Just print the formatted sql query without executing it"
    )
    # Parse args
    opts, args = parser.parse_args()
    # Check if the user provided the two mandatory paths
    if len(args) < 2:
        logger.error(u"Please provide both the path to the sql query and the "
                     u"configuration file.")
        sys.exit(1)
    return opts, args


def get_query_as_string(sql_query_path):
    """
    Read the sql query and return it as a single string

    :param sql_query_path: absolute path to the sql file
    :return: the content of the sql file as unicode string
    """
    with codecs.open(sql_query_path, encoding='utf-8') as query:
        return query.read()


def get_variables(configuration_file_path):
    """Return a dictionary with the variables from the configuration file
    with the format:

    { "variable_name": "variable_value" }

    :param configuration_file_path: Absolute path to the configuration_file_path
    :return: the dictionary with the variables
    """
    returned_dict = {}
    with codecs.open(configuration_file_path, encoding='utf-8') as cf:
        for line in cf:
            # Skip empty lines
            trimmed_line = line.strip()
            if not trimmed_line:
                continue
            # Populate the dict splitting the line on the =
            try:
                var_name, var_value = line.split(CONFIG_FILE_SEPARATOR)
                returned_dict[var_name.strip()] = var_value.strip()
            # Exit on parsing error
            except ValueError:
                logger.error(
                    u'Invalid line in configuration file: "{}"'.format(line)
                )
                sys.exit(1)
    logger.debug(u"Variables from config file: \n" + str(returned_dict))
    return returned_dict


def substitute_variables(sql_string, variables):
    """
    Substitute the variables in sql_string with value from variables

    :param sql_string: an unicode with the "raw" sql query
    :param variables: the dictionary with the variable
    :return: the query formatted
    """
    try:
        formatted = sql_string.format(**variables)
        logger.debug(u"Formatted query: \n" + formatted)
        return formatted
    except KeyError as e:
        logger.error(u'The query requires a variable missing from the '
                     u'configuration file: "{}"'.format(e.args[0]))
        sys.exit(1)


def run_query(sql_string, impala_options, dry_run):
    """
    Run the query with impala-shell

    :param sql_string: the sql query with variables already substituted
    :param impala_options: impala additional options
    :param dry_run: pass true to print the query without executing
    :return impala-shell return code
    """
    impala_args = ['impala-shell']
    if impala_options is not None:
        impala_args.extend(impala_options.split(" "))
    impala_args.append("-q")
    impala_args.append(sql_string)
    # Call impala-shell
    if dry_run:
        logger.debug(u"Performing a dry run")
        sys.stdout.write(sql_string)
        return 0
    else:
        logger.debug(
            u"Calling impala-shell with arguments: " + u" ".join(impala_args)
        )
        return subprocess.call(impala_args)

if __name__ == '__main__':
    # Parse cli arguments
    opts, args = parse_cli_arguments()
    # Activate verbose mode if requested
    if opts.verbose:
        logger.setLevel(logging.DEBUG)
    # Convert provided paths to absolute paths
    sql_path = os.path.abspath(os.path.expanduser(args[0]))
    logger.debug(u'Provided sql path is: {}'.format(sql_path))
    config_path = os.path.abspath(os.path.expanduser(args[1]))
    logger.debug(u'Provided config. file path is: {}'.format(config_path))
    # Check if the two files exists
    if not os.path.isfile(sql_path):
        logger.error(u"sql file not found: {}".format(sql_path))
        sys.exit(1)
    if not os.path.isfile(config_path):
        logger.error(u"configuration file not found: {}".format(config_path))
        sys.exit(1)
    # Perform the variable substitution
    raw_sql = get_query_as_string(sql_path)
    config_variables = get_variables(config_path)
    formatted_sql = substitute_variables(raw_sql, config_variables)
    # Run the query
    ret_code = run_query(formatted_sql, opts.additional_options, opts.dry_run)
    if ret_code == 0:
        logger.info(u"Everything ok, goodbye!")
    else:
        logger.error(u"Error executing the query")
        sys.exit(1)
