# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import ftrack_api

import unreal

from ftrack_connect_pipeline_unreal import plugin
from ftrack_connect_pipeline_unreal.utils import (
    custom_commands as unreal_utils,
)


class UnrealLevelPublisherCollectorPlugin(
    plugin.UnrealPublisherCollectorPlugin
):
    '''Unreal level/assets publisher collector plugin'''

    plugin_name = 'unreal_dependencies_publisher_collector'

    def fetch(self, context_data=None, data=None, options=None):
        '''Fetch all dependencies from the level or the selected asset'''

        if options.get('asset') is True:
            # Get dependencies of the selected asset
            selected_asset_data = (
                unreal.EditorUtilityLibrary.get_selected_asset_data()
            )

            if len(selected_asset_data) == 0:
                return []

            asset_path = str(selected_asset_data[0].package_name)

            return unreal_utils.get_asset_dependencies(asset_path)

        else:
            # Fetch level dependencies
            return unreal_utils.get_level_dependencies(recursive=True)

    def add(self, context_data=None, data=None, options=None):
        '''Fetch the selected asset from content browser'''

        selected_asset_data = (
            unreal.EditorUtilityLibrary.get_selected_asset_data()
        )

        if len(selected_asset_data) == 0:
            return ''

        return [str(selected_asset_data[0].package_name)]

    def run(self, context_data=None, data=None, options=None):
        '''Return the list of collected object from *options*'''
        unreal_objects = options.get('collected_objects', [])
        return unreal_objects


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = UnrealLevelPublisherCollectorPlugin(api_object)
    plugin.register()
