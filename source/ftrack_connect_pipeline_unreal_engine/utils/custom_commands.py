# :coding: utf-8
# :copyright: Copyright (c) 2014-2021 ftrack

import os

import logging

import unreal as ue

from ftrack_connect_pipeline_unreal_engine.constants import asset as asset_const

logger = logging.getLogger(__name__)
    
def get_ftrack_assets():
    result = []

    assets = (
        ue.AssetRegistryHelpers()
        .get_asset_registry()
        .get_assets_by_path('/Game', True)
    )
    for asset_data in assets:
        # unfortunately to access the tag values objects needs to
        # be in memory....
        asset = asset_data.get_asset()
        asset_component_id = asset_data.get_tag_value(
            'ftrack.{}'.format(asset_const.COMPONENT_ID)
        )
        if asset and asset_component_id:
            result.append(asset)

    return set(result)

def get_asset_by_path(asset_path):
    if not asset_path:
        return None
    assetRegistry = ue.AssetRegistryHelpers.get_asset_registry()
    asset_data = assetRegistry.get_assets_by_package_name(
        os.path.splitext(asset_path)[0])
    if 0 < len(asset_data):
       return asset_data[0].get_asset()
    return None

def open_level(level_asset):
    pass

def import_level(level_asset):
    pass

def merge_level(level_asset):
    pass

def get_all_sequences(as_names=True):
    '''
        Returns a list of of all sequences names
    '''
    result = []
    actors = ue.EditorLevelLibrary.get_all_level_actors()
    for actor in actors:
        if actor.static_class() == ue.LevelSequenceActor.static_class():
            seq = actor.load_sequence()
            result.append(seq.get_name() if as_names else seq)
            break
    return result


