# :coding: utf-8
# :copyright: Copyright (c) 2020 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_unreal_engine.plugin import (
    BaseUnrealPlugin, BaseUnrealPluginWidget
)


class LoaderPostImportUnrealPlugin(plugin.LoaderPostImportPlugin, BaseUnrealPlugin):
    ''' Class representing a Collector Plugin

    .. note::

        _required_output a List
    '''


class LoaderPostImportUnrealWidget(
    pluginWidget.LoaderPostImportWidget, BaseUnrealPluginWidget
):
    ''' Class representing a Collector Widget

    .. note::

        _required_output a List
    '''


