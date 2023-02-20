# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack
import copy
import os

import unreal

import ftrack_api

from ftrack_connect_pipeline.constants import asset as asset_const

from ftrack_connect_pipeline_unreal import plugin
from ftrack_connect_pipeline_unreal.constants.asset import modes as load_const
from ftrack_connect_pipeline_unreal.utils import (
    custom_commands as unreal_utils,
)


class UnrealLevelOpenerImporterPlugin(plugin.UnrealOpenerImporterPlugin):
    '''Unreal level importer plugin.'''

    plugin_name = 'unreal_level_opener_importer'

    def run(self, context_data=None, data=None, options=None):
        '''Open an Unreal level from path stored in collected object provided with *data*'''

        load_mode = load_const.OPEN_MODE
        load_mode_fn = self.load_modes.get(
            load_mode, list(self.load_modes.keys())[0]
        )

        # Pass version ID to enable evaluation of content browser path
        unreal_options = copy.deepcopy(options)
        unreal_options.update(
            {'version_id': context_data['version_id']}.items()
        )

        results = {}

        paths_to_import = []
        for collector in data:
            paths_to_import.append(
                collector['result'].get(asset_const.COMPONENT_PATH)
            )

        for component_path in paths_to_import:

            self.logger.debug(
                'Copy path to content folder: "{}"'.format(component_path)
            )
            level_filesystem_path = load_mode_fn(
                component_path, unreal_options, self.session
            )

            if options.get('dependencies') is True:

                self.logger.debug('Loading dependencies')
                objects_to_connect = unreal_utils.import_dependencies(
                    context_data['version_id'],
                    self.event_manager,
                    recursive=False,  # All dependencies are tracked in level
                    provided_logger=self.logger,
                )

                self.logger.debug(
                    'Connecting {} dependencies'.format(
                        len(objects_to_connect)
                    )
                )
                for dep_asset_path, dep_asset_info in objects_to_connect:
                    unreal_utils.connect_object(
                        dep_asset_path, dep_asset_info, self.logger
                    )

            # Have Unreal discover the level
            assetRegistry = unreal.AssetRegistryHelpers.get_asset_registry()
            assetRegistry.scan_paths_synchronous(
                [os.path.dirname(level_filesystem_path)], force_rescan=True
            )

            self.logger.debug(
                'Imported Unreal level to: "{}"'.format(level_filesystem_path)
            )

            results[component_path] = level_filesystem_path

        return results


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = UnrealLevelOpenerImporterPlugin(api_object)
    plugin.register()
