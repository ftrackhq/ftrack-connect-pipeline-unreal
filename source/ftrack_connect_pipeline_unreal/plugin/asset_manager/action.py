# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_unreal.plugin import UnrealBasePlugin


class UnrealAssetManagerActionPlugin(
    plugin.AssetManagerActionPlugin, UnrealBasePlugin
):
    '''
    Class representing a Asset Manager Action Unreal Plugin
    '''
