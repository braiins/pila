"""cmake generator module


Copyright (c) 2017 Braiins Systems s.r.o.

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
import os
import pila.verbosity

class CMakeGen(object):
    """CMake generator

    """
    cmake_src_var = 'SOURCES'
    def __init__(self):
        self.cmake_snippet_action = \
            pila.verbosity.Action(self.create_cmake_snippet,
                                  '[CMake snippet] $TARGET')
        self.cmake_action = \
            pila.verbosity.Action(self.compose_cmake,
                                  '[CMake compose] $TARGET')

    def create_cmake_snippet(self, env, target, source):
        """
        Creates cmake snippet that appends specified sources to CMake variable.

        :param env:
        :param target:
        :param source:
        :return:
        """
        with open(str(target[0]), 'w') as snippet:
            self.add_cmake_defs(snippet, env)
            self.render_statement(snippet,
                                  'list(APPEND {}'.format(self.cmake_src_var),
                                  source)

    @classmethod
    def render_statement(clz, output, statement, lines=[], quoted=False):
        """Helper method that renders a statement optionally with quoting

        :param output:
        :param statement:
        :param lines:
        :param quoted:
        :return:
        """
        output.write('{}\n'.format(statement))
        if quoted is True:
            # Quoting a set of strings requires explicit line continuations
            # just like GNU make
            separator = ' \\'
            output.write('"{}\n'.format(separator))
        else:
            separator = ''
        for l in lines:
            output.write('{0}{1}\n'.format(l, separator))
        if quoted is True:
            output.write('"\n')
        output.write(')\n')

    @classmethod
    def add_cmake_defs(clz, output, env):
        clz.render_statement(output, 'add_definitions(',
                             env.subst(env['_CPPDEFFLAGS']).split())

    def compose_cmake(self, env, target, source):
        """Compose cmake file from all source snippets

        The header of the generated CMake contains build environment settings.


        :param env: build environment that is to be converted into something
        that CMake understands
        :param target: output file where the resulting CMake is to bo stored
        :param source: list of cmake snippets to be merged
        """
        with open(str(target[0]), 'w') as cmake:
            self.render_statement(cmake, 'cmake_minimum_required(VERSION',
                                  ['3.5'])
            self.render_statement(cmake, 'set(CMAKE_C_COMPILER',
                                  [env.subst('$CC')])
            self.render_statement(cmake, 'enable_language(ASM')
            self.render_statement(cmake, 'set(CMAKE_EXE_LINKER_FLAGS',
                                  map(env.subst, ['$CCLINKFLAGS',
                                                  '$_LINKFLAGS', '$__RPATH',
                                                  '$_LIBDIRFLAGS']),
                                  quoted=True
                                  )
            self.render_statement(cmake, 'include_directories(',
                                  map(env.Dir, env['CPPPATH']))
            self.render_statement(cmake, 'set(CMAKE_C_FLAGS',
                                  map(env.subst, env.Flatten(env['CCFLAGS'])),
                                  quoted=True)
            self.add_cmake_defs(cmake, env)
            for s in source[1:]:
                with open(str(s)) as snippet:
                    cmake.write(snippet.read())

            # finally append the executable that consists of all the
            # previously defined sources. Use basename of the executable to
            # prevent warning reported by CMake
            executable = os.path.basename(str(source[0]))
            self.render_statement(cmake, 'add_executable(',
                                  [
                                      executable,
                                      '${%s}' % self.cmake_src_var,
                                  ])
            self.render_statement(cmake, 'target_link_libraries(',
                                  [executable] + env.subst('$LIBS').split())

    def register_feature_object(self, env, target, source, *args, **kw):
        """Appends all sources of the feature object to list for CMake snippet

        :param env:
        :param target: object target that is to be built (unused)
        :param source: list of sources for building the target
        :param args: unused
        :param kw: unused
        """
        # We have to wrap all sources into an explicit 'File' object since we
        # don't create a CMake snippet until a built-in object is declared.
        # If we didn't wrap it here, the path would not be correct.
        sources = map(env.File, env.Flatten(source))
        env.Append(PILA_CMAKE_SRC=sources)

    def register_built_in_object(self, env, target_env, built_in_name, *args,
                                 **kw):
        """Generates a CMake snippet for the set of sources.

        This callback is triggered when a built-in object is declared in
        SConscript.

        The method will instantiate a command to create a CMake snippet that
        covers all sources that have been used to compose the built-in object.

        :param env: environment where the feature object is to be built
        :param target_env: target environment where the resulting cmake snippet
        needs to be registered
        :param built_in_name: see BuiltInObject
        :param args: unused
        :param kw:
        """
        if 'PILA_CMAKE_SRC' in env:
            snippet_name = '{}.CMakeLists.snippet'.format(built_in_name)
            cmake_snippet = env.Command(snippet_name,
                                        env['PILA_CMAKE_SRC'],
                                        action=self.cmake_snippet_action)
            target_env.Append(PILA_CMAKE_SNIPPET=cmake_snippet)

    def register_component_program(self, env, target, *args, **kw):
        """
        Generates final CMake.

        :param env: environment where resulting cmake is to be built
        :param target: component program's target will become the first
        source as it is needed for various entries inside of the generated
        CMakeLists file
        :param args: unused
        :param kw: unused
        """
        print('CMakeGen component program %s' % target)
        # target is passed as the first source
        cmake = env.Command('%s.CMakeLists.txt' % target,
                            [target] + env['PILA_CMAKE_SNIPPET'],
                            action=self.cmake_action)



