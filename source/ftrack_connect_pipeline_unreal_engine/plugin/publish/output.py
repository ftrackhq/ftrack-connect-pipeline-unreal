# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_unreal_engine.plugin import (
    BaseUnrealPlugin, BaseUnrealPluginWidget
)


class PublisherOutputUnrealPlugin(plugin.PublisherOutputPlugin, BaseUnrealPlugin):
    ''' Class representing an Output Plugin
    .. note::

        _required_output a Dictionary
    '''


class PublisherOutputUnrealWidget(
    pluginWidget.PublisherOutputWidget, BaseUnrealPluginWidget
):
    ''' Class representing an Output Widget
        .. note::

            _required_output a Dictionary
    '''


