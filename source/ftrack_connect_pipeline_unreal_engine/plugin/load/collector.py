# :coding: utf-8
# :copyright: Copyright (c) 2020 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_unreal_engine.plugin import (
    BaseUnrealPlugin, BaseUnrealPluginWidget
)


class LoaderCollectorUnrealPlugin(plugin.LoaderCollectorPlugin, BaseUnrealPlugin):
    ''' Class representing a Collector Plugin

    .. note::

        _required_output a List
    '''



class LoaderCollectorUnrealWidget(
    pluginWidget.LoaderCollectorWidget, BaseUnrealPluginWidget
):
    ''' Class representing a Collector Widget

    .. note::

        _required_output a List
    '''



