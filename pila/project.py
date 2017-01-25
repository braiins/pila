"""project management

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
import os
import traceback

class ProjectToolLoadFailed(SCons.Warnings.Warning):
    pass


def get_project_path(env, kconfig_prefix):
    return getattr(env['CONFIG'], '%s_DIR' % kconfig_prefix)


def LoadProject(env, kconfig_prefix, tool_name=None,
                tool_rel_path=os.path.join('site_scons', 'site_tools')):
    """
    This method loads project specific tool.
    @param environment - environment that will have the tool loaded
    @kconfig_prefix - The unique prefix of the project used within the
    kconfig configuration system
    @param tool_name - optionally, user may override the name of the
    tool to be loaded - defaults to lower cased kconfig prefix
    @param tool_rel_path - relative path within the project where the
    tool resides
    """
    if not SCons.Util.is_List(kconfig_prefix):
        kconfig_prefix_list = [kconfig_prefix]
    else:
        kconfig_prefix_list = kconfig_prefix

    if tool_name is not None and len(kconfig_prefix_list) > 1:
        raise SCons.Errors.StopError(ProjectToolLoadFailed,
                                     'You can specify only ONE kconfig_prefix ' \
                                     'when a tool name is specified, kconfig ' \
                                     'prefix: {}, tool name: {}'.format
                                     (kconfig_prefix_list[0], tool_name))

    for prefix in kconfig_prefix_list:
        try:
            project_path = get_project_path(env, prefix)
            toolpath = os.path.join(project_path, tool_rel_path)
            real_tool_name = prefix.lower() if tool_name is None else tool_name

            env.Tool(real_tool_name, toolpath=[toolpath])
        except Exception as e:
            traceback.print_exc()
            raise SCons.Errors.StopError(ProjectToolLoadFailed,
                                         'Failed to load tool: %s for kconfig ' \
                                         'prefix: %s, tool relative path: %s, ' \
                                         'Error: %s' %
                                         (tool_name, prefix, tool_rel_path, e))
    env.Append(PILA_KCONFIG_PROJECT_PREFIX_LIST=kconfig_prefix_list)


def ProjectSConscript(env, kconfig_prefix, use_root_variant_dir=True,
                      *args, **kwargs):
    """
    This method reads SConscript for projects denoted by their unique
    kconfig prefices.

    @param kconfig_prefix_list - list of kconfig prefices of
    individual projects whose SConscript is to be read
    @param use_root_variant_dir - when true, we take the top level
    variant dir and use it for build output into a subdirectory named
    by each project. This is the case when this method is called from
    toplevel SConstruct file.
    """
    if not SCons.Util.is_List(kconfig_prefix):
        kconfig_prefix_list = [kconfig_prefix]
    else:
        kconfig_prefix_list = kconfig_prefix

    # root variant dir requested
    if use_root_variant_dir is True:
        variant_dir = env.subst('${VARIANT_DIR}')
    else:
        variant_dir = ''

    # Process all project prefices and read all their sconscripts. The
    # variant dir is the project name optionally prepended with global
    # root variant dir specified in the environment
    for prefix in kconfig_prefix_list:
        project_path = get_project_path(env, prefix)
        # extract project directory name from its normalized path
        project_name = os.path.basename(os.path.realpath(project_path))
        env.FeatureSConscript(dirs=[project_path],
                              variant_dir=os.path.join(variant_dir,
                                                       project_name),
                              duplicate=0,
                              *args,
                              **kwargs)
