# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_unreal_engine.plugin import (
    BaseUnrealPlugin, BaseUnrealPluginWidget
)


class PublisherValidatorUnrealPlugin(
    plugin.PublisherValidatorPlugin, BaseUnrealPlugin
):
    ''' Class representing a Validator Plugin

    .. note::

        _required_output a Boolean
    '''


class PublisherValidatorUnrealWidget(
    pluginWidget.PublisherValidatorWidget, BaseUnrealPluginWidget
):
    ''' Class representing a Validator widget

    .. note::

        _required_output a Boolean
    '''


