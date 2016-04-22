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


def create_config_module(env):
    # TODO: temporary hack that creates the configuration module
    if env.Execute(env.subst('mkdir -p $VARIANT_DIR')):
        raise SCons.Errors.StopError(
            ToolPilaConfigWarning,
            "Creation of directory variant dir: %s failed" %
            env.subst('$VARIANT_DIR'))
        # The mkdir failed, don't try to build.
        env.Exit(1)
    with open(env.subst('$VARIANT_DIR/${CONFIG_MODULE_NAME}.py'), 'w') as py_file:
        generator = pila.genconfig.PythonConfigGenerator(py_file)
        with open(env.subst('$DOT_CONFIG'), 'r') as dot_file:
            pila.genconfig.process_dot_config(dot_file, generator)
    init_py = open(env.subst('$VARIANT_DIR/__init__.py'), 'w')
    init_py.close()


def LoadConfig(env):
    """
    Loads configuration (.config) file. The configuration is made
    available through the environment. The CFLAGS are extended with
    macro definitions from the generated configuration header.
    """
    config_module_name = env.subst('$CONFIG_MODULE_NAME')
    create_config_module(env)
    try:
        config = importlib.import_module(env.subst('${VARIANT_DIR}.${CONFIG_MODULE_NAME}'))
        env.Append(CONFIG = config.Config())
    except ImportError:
        raise SCons.Errors.StopError(
            ConfigNotFound,
            "Could not import configuration module: %s" %
            config_module_name)

    env.Append(CCFLAGS = ['-imacros', env.subst('$CONFIG_HEADER'), ])
    # Configuration header is generated into the top level build
    # directory. Therefore, we specify a search path for it.
    env.Append(CPPPATH = env.subst('#$VARIANT_DIR'))
    env.Command(env.subst('$VARIANT_DIR/$CONFIG_HEADER'),
                env.subst('$DOT_CONFIG'),
                action=pila.verbosity.Action(create_config_header, 'Creating configuration header: $TARGET'))

    # Configuration may specify cross tool chain prefix unless user
    # has explicitely set it when loading the tool
    if env['CROSS_COMPILE'] == '' and env['CONFIG'].CROSS_COMPILE is not False:
        env['CROSS_COMPILE'] = env['CONFIG'].CROSS_COMPILE
