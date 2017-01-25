#!/usr/bin/python

"""
Copyright (c) 2016 Braiins Systems s.r.o.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>

Purpose: this script converts a provided project configuration into
makefile include or C header includes or python configuration module as
requested by the corresponding command line options. Potential paths in the
configuration are detected and converted to absolute paths.

Run 'geconfig.py -h' for details
"""

import sys
import re
import os

from optparse import OptionParser


def set_config_generator(option, opt, value, parser, config_generator):
    """OptionParser callback method

    This callback method is used for registering individual command
    line options with regards to what tags are to be created

    @param option - is the Option instance that's calling the
    callback.

    @param opt - the option string seen on the command-line that's
    triggering the callback

    @param value - the argument to this option seen on the
    command-line - not used

    @param parser - the OptionParser instance driving the whole thing

    @param config_generator - configuration generator that has to be registered
    """
    setattr(parser.values, option.dest, config_generator)


class ConfigGenerator(object):
    def __init__(self, out_file=sys.stdout):
        self.out_file = out_file


    def output_header(self):
        pass


    def output_footer(self):
        pass


class CHeaderConfigGenerator(ConfigGenerator):
    """Provides methods for generating configuration in C header form.
    The header contains defines. Comments are output in a standard C
    format (/* ... */). The configuration values get translated as
    follows:

    Input config:
    # Comment feature 1
    CONFIG_FEAT1=y
    CONFIG_FEAT3=10
    CONFIG_FEAT4="somestring"

    Output config:
    /* Comment feature 1 */
    #define CONFIG_FEAT1 1
    /* Comment feature 2 */
    #undef CONFIG_FEAT2
    /* Comment feature 3 */
    #define CONFIG_FEAT3 10
    /* Comment feature 4 */
    #define CONFIG_FEAT4 somestring
    """

    def output_config(self, config, value):
        prefix = "#define"
        try:
            out_value = int(value)
        except ValueError, e:
            if (value == "y"):
                out_value = 1
            # no value for this config represented by absence of the
            # macro
            elif (value == "n"):
                out_value = ""
                prefix = "#undef"

            else:
                out_value = '"%s"' % value
        self.out_file.write('%s %s %s\n' % (prefix, config, out_value))

    def output_comment(self, comment):
        self.out_file.write('/* %s */\n' % comment)



class MakeConfigGenerator(ConfigGenerator):
    """Provides methods for generating configuration for inclusion into a Makefile
    The configuration values get
    translated as follows:

    Input config:
    # Comment feature 1
    CONFIG_FEAT1 anything

    Output config:
    # Comment feature 1
    CONFIG_FEAT1 = anything
    export CONFIG_FEAT1
    """

    def output_config(self, config, value):
        self.out_file.write('%s = %s' % (config, value))
        self.out_file.write('export %s' % config)


    def output_comment(self, comment):
        self.out_file.write('# %s' % comment)



class PythonConfigGenerator(ConfigGenerator):
    """Provides methods for generating configuration in Python module form.
    The header contains a top level class defines. Comments are output in a standard C
    format (/* ... */). The configuration values get translated as
    follows:

    Input config:
    # Comment feature 1
    CONFIG_FEAT1=y
    CONFIG_FEAT3=10
    CONFIG_FEAT4="somestring"

    Output config:
    class Config(object):
       def __init__(self):
          # Comment feature 1
          self.FEAT1 = True
          # Comment feature 2
    #undef CONFIG_FEAT2
    /* Comment feature 3 */
    #define CONFIG_FEAT3 10
    /* Comment feature 4 */
    #define CONFIG_FEAT4 somestring
    """

    def output_config(self, config, value):
        try:
            out_value = int(value)
        except ValueError, e:
            if (value == 'y'):
                out_value = 'True'
            # no value for this config represented by absence of the
            # macro
            elif (value == 'n'):
                out_value = 'False'

            else:
                out_value = "'%s'" % value
        # Each config option is stored as an attribute without the
        # 'CONFIG_' prefix
        self.out_file.write('        self.%s = %s\n' % (config[len('CONFIG_'):], out_value))


    def output_comment(self, comment):
        self.out_file.write('# %s\n' % comment)

    def output_footer(self):
        self.out_file.write('        pass\n')

    def output_header(self):
        self.out_file.write("""
class Config(object):

    def __getattr__(self, attr):
        \"\"\"
        Non-existing attributes are rendered as if the configuration
        option is not set.
        \"\"\"
        return False

    def __init__(self):
""")



class GenConfigOptionParser(OptionParser):
    """Extended option parser for selecting the correct
    method.

    The parser defines a special callback that allows registering a
    particular method to calculate a checksum
    """

    def __init__(self):
        """Initialization sets up supported options

        @param self
        """
        OptionParser.__init__(self)

        # each of the following option causes adding a specific type of a tag
        # into the 'tag_list' attribute
        self.add_option('-m', '--makefile', action='callback',
                        callback=set_config_generator,
                        callback_args=(MakeConfigGenerator(),),
                        dest='config_generator',
                        help='generate configuration for makefile inclusion')
        self.add_option('-c', '--cheader', action='callback',
                        callback=set_config_generator,
                        callback_args=(CHeaderConfigGenerator(),),
                        dest='config_generator',
                        help='generate configuration as C header')
        self.add_option('-p', '--py', action='callback',
                        callback=set_config_generator,
                        callback_args=(PythonConfigGenerator(),),
                        dest='config_generator',
                        help='generate configuration as Python module')

        # default operation
        self.set_default('config_generator', MakeConfigGenerator())



def process_dot_config(in_file, config_generator):
    """
    Processes a .config generated by kconfig-frontends
    @param generator - generator used for output of the configuration
    """
    comment_re_str = "\s*#\s*(?P<comment>.*)"
    comment_re = re.compile(comment_re_str)

    # filter out configuration and value, skip any trailing comment
    config_re_str = "\s*(?P<config>[\w]+)\s*=(?P<value>[^#]+).*"
    config_re = re.compile(config_re_str)

    # filter out unset configuration option comment
    unset_config_re_str = '#\s*(?P<config>[\w]+) is not set'
    unset_config_re = re.compile(unset_config_re_str)

    lines = in_file.readlines()
    config_generator.output_header()
    for line in lines:
        line = line.rstrip('\n')

        m = unset_config_re.match(line)
        if m:
            config_generator.output_config(m.group('config'), 'n')
            continue

        m = comment_re.match(line)
        if m:
            config_generator.output_comment(m.group('comment'))
            continue

        m = config_re.match(line)
        if m:
            config_value = m.group('value').strip().strip('"')
            # detect paths and convert them to absolute paths
            if os.path.isdir(config_value) or config_value.startswith('./') \
                    or config_value.startswith('../'):
                config_value = os.path.realpath(config_value)

            config_generator.output_config(m.group('config'),
                                           config_value)
        config_generator.output_footer()


if __name__ == "__main__":
    p = GenConfigOptionParser()
    (opts, args) = p.parse_args(sys.argv[1:])

    process_dot_config(sys.stdin, opts.config_generator)
