# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import json
import os

import ftrack_api

from ftrack_connect_pipeline import constants as core_constants
from ftrack_connect_pipeline_unreal import plugin

from ftrack_connect_pipeline_unreal.utils import (
    custom_commands as unreal_utils,
)
from ftrack_connect_pipeline_unreal.constants import asset as asset_const


class UnrealAssetInfoPublisherFinalizerPlugin(
    plugin.UnrealPublisherPostFinalizerPlugin
):
    '''Plugin for finalizing the Unreal asset info publish process'''

    plugin_name = 'unreal_assetinfo_publisher_post_finalizer'

    def run(self, context_data=None, data=None, options=None):
        '''Publish the non snapshot asset info to ftrack if exists'''

        # Extract version ID from the run data
        asset_version_id = asset_filesystem_path = param_dict = None
        for comp in data:
            if comp['type'] == core_constants.COMPONENT:
                for result in comp['result']:
                    if result['name'] == core_constants.EXPORTER:
                        plugin_result = result['result'][0]
                        asset_filesystem_path = plugin_result['result'][0]
                        break
            elif comp['type'] == core_constants.FINALIZER:
                for result in comp['result']:
                    if result['name'] == core_constants.FINALIZER:
                        plugin_result = result['result'][0]
                        asset_version_id = plugin_result['result'][
                            'asset_version_id'
                        ]
                        break

        # Get asset info, must be run in main thread
        if not asset_filesystem_path:
            return {'message': 'No asset could be extracted from publish!'}

        # Convert to game path
        asset_path = unreal_utils.filesystem_asset_path_to_asset_path(
            asset_filesystem_path
        )

        unused_dcc_object_name, param_dict = unreal_utils.get_asset_info(
            asset_path
        )

        # Read current metadata
        asset_version = self.session.query(
            'AssetVersion where id is "{0}"'.format(asset_version_id)
        ).one()
        metadata = {}
        if core_constants.PIPELINE_METADATA_KEY in asset_version.get(
            'metadata'
        ):
            metadata = json.loads(
                asset_version['metadata'][core_constants.PIPELINE_METADATA_KEY]
            )

        if param_dict:
            # Store the asset info as metadata in ftrack

            metadata[
                core_constants.PIPELINE_ASSET_INFO_METADATA_KEY
            ] = param_dict

            self.logger.debug('Asset info to store @ "{}"!'.format(metadata))

            message = 'Stored ftrack dependency asset info on asset version'
        else:
            message = (
                'No ftrack dependency asset info to store on asset version'
            )

        if asset_filesystem_path and os.path.exists(asset_filesystem_path):
            # Store file size and modification time for sync purposes
            metadata[asset_const.MOD_DATE] = os.path.getmtime(
                asset_filesystem_path
            )
            metadata[asset_const.FILE_SIZE] = os.path.getsize(
                asset_filesystem_path
            )
            message += "; Stored asset local file size({}) and modification time({}) on asset version".format(
                metadata[asset_const.FILE_SIZE], metadata[asset_const.MOD_DATE]
            )
        else:
            message += "; No local file size and modification time to store on asset version"

        asset_version['metadata'][
            core_constants.PIPELINE_METADATA_KEY
        ] = json.dumps(metadata)
        self.session.commit()

        self.logger.debug(message)
        return {'message': message}


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = UnrealAssetInfoPublisherFinalizerPlugin(api_object)
    plugin.register()
