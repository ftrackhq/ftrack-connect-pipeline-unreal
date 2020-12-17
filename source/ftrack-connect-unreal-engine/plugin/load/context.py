# :coding: utf-8
# :copyright: Copyright (c) 2020 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_unreal_engine.plugin import (
    BaseUnrealPlugin, BaseUnrealPluginWidget
)


class LoaderContextUnrealPlugin(plugin.LoaderContextPlugin, BaseUnrealPlugin):
    ''' Class representing a Context Plugin
    .. note::

        _required_output is a dictionary containing the 'context_id',
        'asset_name', 'comment' and 'status_id' of the current asset
    '''


class LoaderContextUnrealWidget(
    pluginWidget.LoaderContextWidget, BaseUnrealPluginWidget
):
    ''' Class representing a Context Widget
    .. note::

        _required_output is a dictionary containing the 'context_id',
        'asset_name', 'comment' and 'status_id' of the current asset
    '''




