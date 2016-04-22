"""pila top level module - configures basic construction environment

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

import pila.builders
import pila.configuration
import pila.project
import os


def generate(env):
    """Add Builders and construction variables to the Environment.
    """
    env.SetDefault(
        CROSS_COMPILE = '',
        VARIANT_DIR = 'build',
        DOT_CONFIG = '.config',
        CONFIG_MODULE_NAME = 'config',
        CONFIG_HEADER = 'config.pila.h',
        PILA_BUILTINS=[],
        CCFLAGS_OPT='-O1',
        )
    env['AR'] = '${CROSS_COMPILE}ar'
    env['AS'] = '${CROSS_COMPILE}as'
    env['CC'] = '${CROSS_COMPILE}gcc'
    env['CPP'] = '${CROSS_COMPILE}cpp'
    env['CXX'] = '${CROSS_COMPILE}g++'
    # We will use gcc for linking as it selects the proper library
    # search path based on exact machine type
    env['LINK'] = '${CROSS_COMPILE}ld'
    env['RANLIB'] = '${CROSS_COMPILE}ranlib'

    env.AddMethod(pila.builders.FeatureObject, 'FeatureObject')
    env.AddMethod(pila.builders.ComponentProgram, 'ComponentProgram')
    env.AddMethod(pila.builders.FeatureSConscript, 'FeatureSConscript')
    env.AddMethod(pila.builders.BuiltInObject, 'BuiltInObject')
    env.AddMethod(pila.configuration.LoadConfig, 'LoadConfig')
    env.AddMethod(pila.project.LoadProject, 'LoadProject')
    env.AddMethod(pila.project.ProjectSConscript, 'ProjectSConscript')
    env.Append(CCFLAGS='$CCFLAGS_OPT')
    env.VariantDir(env.subst('$VARIANT_DIR'), '.', duplicate=0)

    # Short message for GCC when verbosity is not desired
    pila.verbosity.load_short_messages_gcc(env)


def exists(env):
    return 1
