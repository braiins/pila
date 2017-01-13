"""configuration generator

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
"""
import SCons.Warnings
import SCons.Script
import importlib
import pila.genconfig
import pila.verbosity
import os

class ToolPilaConfigWarning(SCons.Warnings.Warning):
    pass

class ConfigNotFound(ToolPilaConfigWarning):
    pass


SCons.Warnings.enableWarningClass(ToolPilaConfigWarning)


def create_config_header(env, target, source):
    with open(str(target[0]), 'w') as config_header:
        generator = pila.genconfig.CHeaderConfigGenerator(config_header)
        with open(str(source[0]), 'r') as dot_file:
            pila.genconfig.process_dot_config(dot_file, generator)


def create_config_py(env, target, source):
    with open(str(target[0]), 'w') as config_py:
        generator = pila.genconfig.PythonConfigGenerator(config_py)
        with open(str(source[0]), 'r') as dot_file:
            pila.genconfig.process_dot_config(dot_file, generator)


def import_config_module(env):
    """Imports configuration module if it exists.

    The configuration is made available through the environment. The
    CFLAGS are extended with macro definitions from generated
    configuration header.

    The configuration header will be generated during build phase.

    @return True when configuration has been successfully imported and
    appended to the specified build environment
    """
    config_imported = True
    try:
        config_module_name = env.subst('$CONFIG_MODULE_NAME')
        config = importlib.import_module(config_module_name)
        # export the loaded configuration via this environment
        env.Append(CONFIG = config.Config())
    except ImportError as e:
        config_imported = False
        print("Config python module %s doesn't exist" % config_module_name)
    else:
        env.Append(CCFLAGS = ['-imacros', '$CONFIG_HEADER', ])
        # Configuration header is generated into the top level build
        # directory. Therefore, we specify a search path for it.
        env.Append(CPPPATH = '#$VARIANT_DIR')

        env.Command(os.path.join('$VARIANT_DIR', '$CONFIG_HEADER'),
                    env.subst('$DOT_CONFIG'),
                    action=pila.verbosity.Action(create_config_header,
                                                 'Creating configuration ' \
                                                 'header: $TARGET'))

    return config_imported


def find_program(env, program, path):
    """Try to find a specific program.

    If the program is not found in the specified path a current system
    path is searched, too.

    @program - program to look for
    @path - optional path to search

    """
    # First search in the SCons path
    path = env.WhereIs(program, path)
    if path:
        return path
    # then the OS path:
    path = SCons.Util.WhereIs(program)
    if path:
        return path


def generate(env):
    default_kconfig_frontend = 'qconf'
    SCons.Script.AddOption('--kconfig-frontend',
                           dest='kconfig_frontend',
                           type='string',
                           nargs=1,
                           action='store',
                           metavar='NAME',
                           default=default_kconfig_frontend,
                           help='Configuration tool name (e.g. qconf, gconf, ' \
                           'mconf, nconf, conf) default: {}'.format(default_kconfig_frontend))

    SCons.Script.AddOption('--kconfig-frontend-bin-path',
                           dest='kconfig_frontend_bin_path',
                           type='string',
                           nargs=1,
                           action='store',
                           metavar='PATH',
                           default=None,
                           help="Search path for the binary, default is to " \
                           "search system path")

    kconfig_frontend_prog = find_program(env, 'kconfig-{}'.
                                         format(
                                             SCons.Script.GetOption('kconfig_frontend')),
                                         path=SCons.Script.GetOption('kconfig_frontend_bin_path'))
    if kconfig_frontend_prog is None:
        raise SCons.Errors.StopError(
            ToolPilaConfigWarning,
            'Kconfig frontend ({}) not found'.
            format(SCons.Script.GetOption('kconfig_frontend')))

    env.Append(PILA_KCONFIG_FRONTEND=kconfig_frontend_prog)


def create_dot_config_target(env):
    dot_config_action = pila.verbosity.Action('DISPLAY=%s KCONFIG_CONFIG=`pwd`/$TARGET $PILA_KCONFIG_FRONTEND $SOURCES' % (os.environ['DISPLAY']),
                                              'Running config')
    dot_config = env.Command('$DOT_CONFIG', '$TOPLEVEL_KCONFIG', action=dot_config_action)
    env.AlwaysBuild(dot_config)
    # Never clean $DOT_CONFIG that has been manually created by config
    env.NoClean(dot_config)
    # Also prevent scons from removing the target before rebuilding
    # it. This is needed, so that kconfig frontend is able to read the
    # existing configuration
    env.Precious(dot_config)


def LoadBuildEnv(env, setup_build_env):
    """Loads configuration python module and sets up build environment.

    If the python configuration module doesn't exist, the build is
    switched into special configuration mode where:
    - config.py is generated from .config (if one exists)
    - interactive configuration is launched if .config is not present
      yet
    """


    py_config_action = pila.verbosity.Action(create_config_py,
                                             'Creating configuration module: ' \
                                             '$TARGET')
    py_config = env.Command('${CONFIG_MODULE_NAME}.py',
                            '$DOT_CONFIG', action=py_config_action)
    env.Alias('conf', py_config)
    env.NoClean(py_config)

    # Explicit configuration request -> make sure that .config gets rebuilt
    if 'conf' in SCons.Script.COMMAND_LINE_TARGETS:
        create_dot_config_target(env)
    else:
        if os.path.exists(py_config[0].name) and \
           os.path.exists(env.subst('$DOT_CONFIG')) and \
           import_config_module(env):
            # Configuration may specify cross tool chain prefix unless user
            # has explicitely set it when loading the tool
            if env['CROSS_COMPILE'] == '' and \
               env['CONFIG'].CROSS_COMPILE is not False:
                env['CROSS_COMPILE'] = env['CONFIG'].CROSS_COMPILE

            setup_build_env(env)
        else:
            print('=' * 80)
            print('Configuration python module is not present')
            print('Switching to configuration build, please, rerun build')
            print('=' * 80)
            # If base configuration sources exists, set default rule
            # to only regenerate config python module
            if os.path.exists(env.subst('$DOT_CONFIG')):
                env.Default(py_config)
            else:
                # Otherwise ensure interactive config tool is launched via the default target
                create_dot_config_target(env)
                env.Default('conf')
