# :coding: utf-8
# :copyright: Copyright (c) 2020 ftrack

import json

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_unreal_engine.plugin import (
    BaseUnrealPlugin, BaseUnrealPluginWidget
)

from ftrack_connect_pipeline_unreal_engine.asset import FtrackAssetTab
from ftrack_connect_pipeline_unreal_engine.constants import asset as asset_const
from ftrack_connect_pipeline_unreal_engine.constants.asset import modes as load_const
from ftrack_connect_pipeline_unreal_engine.utils import custom_commands as unreal_utils


class LoaderImporterUnrealPlugin(plugin.LoaderImporterPlugin, BaseUnrealPlugin):
    ''' Class representing a Collector Plugin

    .. note::

        _required_output a List
    '''

    ftrack_asset_class = FtrackAssetTab

    def _run(self, event):
        ''' Apply ftrack info to loaded asset. '''

        super_result = super(LoaderImporterUnrealPlugin, self)._run(event)

        ftrack_asset_class = self.get_asset_class(context, data, options)
        result = super_result.get('result')

        ftrack_asset_class.connect_objects(result.values())

        return super_result

class LoaderImporterUnrealWidget(pluginWidget.LoaderImporterWidget, BaseUnrealPluginWidget):
    ''' Class representing a Collector Widget

    .. note::

        _required_output a List
    '''



