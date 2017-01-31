"""All pila builders

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
import pila.verbosity
import pila.events

def FeatureObject(env, target=None, source=None, is_enabled=True, *args, **kw):
    """
    Wrapper for the standard static object build that provides the
    object only if requested. This Pseudo builder is useful when
    preparing conditionally compiled components based on external
    configuration.
    """
    feature_object = None

    if not source:
        source = target[:]

    if is_enabled:
        feature_object = env.Object(target, source, *args, **kw)
        # Every object depends on the configuration header that is
        # being injected via imacro (See configuration.LoadConfig)
        env.Depends(feature_object, env.subst('#$VARIANT_DIR/$CONFIG_HEADER'))
        env.Append(PILA_OBJECTS=feature_object)
        pila.events.dispatcher.register_feature_object(env, target, source,
                                                       *args, **kw)

    return feature_object


def FeatureSConscript(env, is_enabled=True, *args, **kw):
    """
    Wrapper for the standard SConscript method that executes a
    sconscripts if the associated feature is enabled

    @param is_enabled - when true the sub-sconscript is read and
    executed
    """
    result = None

    if is_enabled:
        result = env.SConscript(*args, **kw)

    return result


def BuiltInObject(env, target_env):
    """
    @param target_env - target environment where the resulting
    built-in object is to be registered
    """
    ld_action = pila.verbosity.Action('$LINK -r -o $TARGET $SOURCES',
                                      '[LD-builtin] $TARGET')
    cmd = env.Command('built-in.o', env['PILA_OBJECTS'], action=ld_action)
    target_env.Append(PILA_BUILTINS=cmd)
    pila.events.dispatcher.register_built_in_object(env, target_env)


def ComponentProgram(env, target, *args, **kw):
    """
    Provides a program linked from all built-ins in the specified
    environment. A side effect is a map file
    @param target - where the resulting program is to be stored
    """
    map_file = env.File('%s.map' % target)

    # Create the program and register the map file as a side effect,
    # so that the build system is able to track it
    prog = env.Program(target, env['PILA_BUILTINS'],
                       LINKFLAGS=['$LINKFLAGS', '-Map=%s' % map_file.path],
                       *args, **kw)

    env.SideEffect(map_file, prog)
    pila.events.dispatcher.register_component_program(env, target, *args, **kw)

    return prog
