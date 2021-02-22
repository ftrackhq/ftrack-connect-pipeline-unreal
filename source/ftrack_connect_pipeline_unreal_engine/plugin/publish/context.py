# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_unreal_engine.plugin import (
    BaseUnrealPlugin, BaseUnrealPluginWidget
)


class PublisherContextUnrealPlugin(plugin.PublisherContextPlugin, BaseUnrealPlugin):
    ''' Class representing a Context Plugin
    .. note::

        _required_output is a dictionary containing the 'context_id',
        'asset_name', 'comment' and 'status_id' of the current asset
    '''


class PublisherContextUnrealWidget(
    pluginWidget.PublisherContextWidget, BaseUnrealPluginWidget
):
    ''' Class representing a Context Widget
    .. note::

        _required_output is a dictionary containing the 'context_id',
        'asset_name', 'comment' and 'status_id' of the current asset
    '''




