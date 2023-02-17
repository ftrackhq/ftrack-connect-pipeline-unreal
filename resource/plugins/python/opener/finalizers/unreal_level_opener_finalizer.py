# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack
import unreal

import ftrack_api

from ftrack_connect_pipeline import constants as core_constants

from ftrack_connect_pipeline_unreal import plugin
from ftrack_connect_pipeline_unreal.utils import (
    custom_commands as unreal_utils,
)


class UnrealLevelOpenerFinalizerPlugin(plugin.UnrealOpenerFinalizerPlugin):
    '''Unreal level open finalizer plugin.'''

    plugin_name = 'unreal_level_opener_finalizer'

    def run(self, context_data=None, data=None, options=None):
        '''Open the level in Unreal Editor.'''

        result = {}

        # Find the path to level
        level_filesystem_path = None
        for comp in data:
            if comp['type'] == core_constants.COMPONENT:
                for result in comp['result']:
                    if result['type'] == core_constants.IMPORTER:
                        plugin_result = result['result'][0]
                        level_filesystem_path = list(
                            plugin_result['result'].values()
                        )[0]
                        break
        # Expect: "C:\\Users\\<user name>\\Documents\\Unreal Projects\\MyEmptyProject\\Content\\Levels\\NewWorld.umap"
        # Transform to asset path
        level_path = unreal_utils.filesystem_asset_path_to_asset_path(
            level_filesystem_path
        )

        self.logger.debug(
            'Opening level {} in Unreal editor'.format(level_path)
        )
        unreal.EditorLevelLibrary.load_level(level_path)

        return result


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = UnrealLevelOpenerFinalizerPlugin(api_object)
    plugin.register()
