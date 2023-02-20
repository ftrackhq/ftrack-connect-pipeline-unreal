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


class UnrealAssetOpenerImporterPlugin(plugin.UnrealOpenerImporterPlugin):
    '''Unreal native importer plugin.'''

    plugin_name = 'unreal_asset_opener_importer'

    def run(self, context_data=None, data=None, options=None):
        '''Open an Unreal asset from path stored in collected object provided with *data*'''

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

        is_dependency = options.get('is_dependency') is True
        asset_info = copy.deepcopy(
            self.asset_info
        )  # Store a local reference to asset info as it seems to me a singleton
        for component_path in paths_to_import:

            self.logger.debug(
                'Copy path to content folder: "{}"'.format(component_path)
            )
            asset_filesystem_path = load_mode_fn(
                component_path, unreal_options, self.session
            )

            # Restore any ftrack dependency asset info
            unreal_utils.import_ftrack_dependency_asset_info(
                context_data['version_id'],
                asset_filesystem_path,
                self.event_manager,
            )

            asset_path = unreal_utils.filesystem_asset_path_to_asset_path(
                asset_filesystem_path
            )

            # Load dependencies if not already being loaded as a dependency
            if not is_dependency:

                if options.get('dependencies') is True:
                    # Set asset_info as loaded, cannot be done after dependencies has been imported
                    # as object manager is a singleton and will be used for all imports
                    self.ftrack_object_manager.objects_loaded = True

                    self.logger.debug('Loading dependencies')
                    objects_to_connect = unreal_utils.import_dependencies(
                        context_data['version_id'],
                        self.event_manager,
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

                # Connect my self, cannot be done in plugin run as it will also detect
                # and connect dependencies
                unreal_utils.connect_object(
                    asset_path, asset_info, self.logger
                )

            # Have Unreal discover the asset
            assetRegistry = unreal.AssetRegistryHelpers.get_asset_registry()
            assetRegistry.scan_paths_synchronous(
                [os.path.dirname(asset_filesystem_path)], force_rescan=True
            )

            # Load the asset in Unreal
            self.logger.debug(
                'Result of loading asset "{}" in Unreal editor: {}'.format(
                    asset_path,
                    unreal.EditorAssetLibrary.load_asset(asset_path),
                )
            )

            self.logger.debug(
                'Imported Unreal asset to: "{}"'.format(asset_filesystem_path)
            )

            results[component_path] = asset_filesystem_path

        return results


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = UnrealAssetOpenerImporterPlugin(api_object)
    plugin.register()
