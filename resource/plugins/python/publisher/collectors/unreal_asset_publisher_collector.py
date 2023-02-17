# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import ftrack_api

import unreal

from ftrack_connect_pipeline_unreal import plugin
from ftrack_connect_pipeline_unreal.utils import (
    custom_commands as unreal_utils,
)


class UnrealAssetPublisherCollectorPlugin(
    plugin.UnrealPublisherCollectorPlugin
):
    '''Unreal asset publisher collector plugin'''

    plugin_name = 'unreal_asset_publisher_collector'

    def fetch(self, context_data=None, data=None, options=None):
        '''Fetch the selected asset from content browser'''

        selected_asset_data = (
            unreal.EditorUtilityLibrary.get_selected_asset_data()
        )

        if len(selected_asset_data) == 0:
            return ''

        return str(selected_asset_data[0].package_name)

    def run(self, context_data=None, data=None, options=None):
        '''Pass on collected Unreal assets to publish'''
        collected_objects = options.get('collected_objects') or []
        return collected_objects


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = UnrealAssetPublisherCollectorPlugin(api_object)
    plugin.register()
