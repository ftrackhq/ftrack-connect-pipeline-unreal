# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import sys
import re
import os
import glob
import traceback

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

def open_level(level_asset):
    pass

def import_level(level_asset):
    pass

def merge_level(level_asset):
    pass


