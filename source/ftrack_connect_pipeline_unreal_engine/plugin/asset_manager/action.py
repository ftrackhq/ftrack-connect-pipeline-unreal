# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_unreal_engine.plugin import BaseUnrealPlugin
from ftrack_connect_pipeline_unreal_engine.asset import FtrackAssetTab


class AssetManagerActionUnrealPlugin(
    plugin.AssetManagerActionPlugin, BaseUnrealPlugin
):
    '''
    Class representing a Asset Manager Action Unreal Plugin
    '''
    ftrack_asset_class = FtrackAssetTab

