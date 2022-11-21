# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import unreal

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_unreal.plugin import (
    UnrealBasePlugin,
    UnrealBasePluginWidget,
)

from ftrack_connect_pipeline_unreal.utils import custom_commands as unreal_utils
from ftrack_connect_pipeline_unreal.constants.asset import modes as load_const
from ftrack_connect_pipeline_unreal.constants import asset as asset_const


class UnrealLoaderImporterPlugin(plugin.LoaderImporterPlugin, UnrealBasePlugin):
    '''Class representing a Collector Plugin

    .. note::

        _required_output a List
    '''

    load_modes = load_const.LOAD_MODES

    dependency_load_mode = load_const.REFERENCE_MODE

    @unreal_utils.run_in_main_thread
    def get_current_objects(self):
        return unreal_utils.get_current_scene_objects()


class UnrealLoaderImporterPluginWidget(
    pluginWidget.LoaderImporterPluginWidget, UnrealBasePluginWidget
):
    '''Class representing a Collector Widget

    .. note::

        _required_output a List
    '''
