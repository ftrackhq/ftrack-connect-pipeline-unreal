# :coding: utf-8
# :copyright: Copyright (c) 2014-2021 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_unreal_engine.plugin import (
    BaseUnrealPlugin, BaseUnrealPluginWidget
)


class PublisherCollectorUnrealPlugin(
    plugin.PublisherCollectorPlugin, BaseUnrealPlugin
):
    ''' Class representing a Collector Plugin

    .. note::

        _required_output a List
    '''


class PublisherCollectorUnrealWidget(
    pluginWidget.PublisherCollectorWidget, BaseUnrealPluginWidget
):
    ''' Class representing a Collector Widget

    .. note::

        _required_output a List
    '''



