# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_unreal.plugin import (
    UnrealBasePlugin,
    UnrealBasePluginWidget,
)


class UnrealOpenerCollectorPlugin(plugin.OpenerCollectorPlugin, UnrealBasePlugin):
    '''Class representing a Collector Plugin

    .. note::

        _required_output a List
    '''


class UnrealOpenerCollectorPluginWidget(
    pluginWidget.OpenerCollectorPluginWidget, UnrealBasePluginWidget
):
    '''Class representing a Collector Widget

    .. note::

        _required_output a List
    '''
