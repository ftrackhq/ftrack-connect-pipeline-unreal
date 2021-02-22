# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack
import os
import re
import clique

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_unreal_engine.plugin import (
    BaseUnrealPlugin, BaseUnrealPluginWidget
)
from ftrack_connect_unreal_engine.constants import asset as asset_const
from ftrack_connect_unreal_engine.utils import custom_commands as unreal_utils


class PublisherFinalizerUnrealPlugin(plugin.PublisherFinalizerPlugin, BaseUnrealPlugin):
    ''' Class representing a Finalizer Plugin

        .. note::

            _required_output is a dictionary containing the 'context_id',
            'asset_name', 'asset_type', 'comment' and 'status_id' of the
            current asset
    '''


class PublisherFinalizerUnrealWidget(
    pluginWidget.PublisherFinalizerWidget, BaseUnrealPluginWidget
):
    ''' Class representing a Finalizer Widget

        .. note::

            _required_output is a dictionary containing the 'context_id',
            'asset_name', 'asset_type', 'comment' and 'status_id' of the
            current asset
    '''


