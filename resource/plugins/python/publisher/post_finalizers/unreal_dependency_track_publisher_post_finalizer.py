# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import copy
import os
import ftrack_api

from ftrack_connect_pipeline import constants as core_constants
from ftrack_connect_pipeline.constants import asset as asset_const
from ftrack_connect_pipeline.asset.asset_info import FtrackAssetInfo

from ftrack_connect_pipeline_unreal import plugin
from ftrack_connect_pipeline_unreal.constants.asset import modes as load_const

from ftrack_connect_pipeline_unreal.utils import (
    custom_commands as unreal_utils,
)


class UnrealDependencyTrackPublisherFinalizerPlugin(
    plugin.UnrealPublisherPostFinalizerPlugin
):
    '''Plugin for start tracking an asset as a dependency with a snapshot asset info in Unreal.'''

    plugin_name = 'unreal_dependency_track_publisher_post_finalizer'

    def extract_loader_options(self, options):
        if options is None:
            options = {}
        return {
            'definition': options.get('definition') or 'Asset Loader',
            'plugin_name': options.get('plugin_name')
            or 'unreal_asset_loader_importer',
            'method': options.get('method') or 'init_and_load',
        }

    def generate_snapshot_asset_info_options(
        self,
        context_data,
        loader_options,
        component_id,
        component_name,
        component_path,
    ):
        '''
        Returns a dictionary of options for creating a snapshot asset_info.
        '''
        return {
            "pipeline": {
                "plugin_name": loader_options['plugin_name'],
                "plugin_type": "loader.importer",
                "method": "init_and_load",
                "category": "plugin",
                "host_type": "unreal",
                "definition": loader_options['definition'],
                "load_mode": load_const.OPEN_MODE,
            },
            "settings": {
                "context_data": context_data,
                "data": [
                    {
                        "name": "common_context_loader_collector",
                        "options": {},
                        "result": {
                            asset_const.COMPONENT_ID: component_id,
                            asset_const.COMPONENT_NAME: component_name,
                            asset_const.COMPONENT_PATH: component_path,
                        },
                        "status": True,
                        "category": "plugin",
                        "type": "collector",
                        "plugin_type": "loader.collector",
                        "method": "run",
                        "user_data": {},
                        "widget_ref": None,
                        "host_id": None,
                        "plugin_id": None,
                    }
                ],
                "options": {},
            },
        }

    def run(self, context_data=None, data=None, options=None):
        '''Create/update local snapshot asset info based on *context_data* and *data*, with snapshot
        loader defined in *options*.'''

        # Extract version ID from the run data
        asset_version_id = None
        component_name = None
        asset_filesystem_path = None
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
                        for component_name in plugin_result['result'][
                            'component_names'
                        ]:
                            if not component_name in [
                                'thumbnail',
                                'reviewable',
                            ]:
                                break
                        break

        if not asset_filesystem_path:
            return {'message': 'No asset could be extracted from publish!'}

        # Convert to game path
        asset_path = unreal_utils.filesystem_asset_path_to_asset_path(
            asset_filesystem_path
        )

        # Check if already has snapshot asset info
        dcc_object_name, param_dict = unreal_utils.get_asset_info(
            asset_path, snapshot=True
        )

        if param_dict:
            # Remove the existing snapshot asset info on disk, otherwise creating
            # and storing it will fail below
            self.logger.warning(
                'Removing existing snapshot asset info @ "{}"!'.format(
                    param_dict
                )
            )
            unreal_utils.delete_ftrack_node(dcc_object_name)

        asset_version = self.session.query(
            'AssetVersion where id is "{}"'.format(asset_version_id)
        ).one()

        # Create new snapshot asset info
        component = self.session.query(
            'Component where version.id is {} and name is "{}"'.format(
                asset_version_id, component_name
            )
        ).one()
        # Find out were the asset got stored
        location = self.session.pick_location()
        component_path = location.get_filesystem_path(component)
        ftrack_object_manager = self.FtrackObjectManager(self.event_manager)

        # Generate asset info options with publish context augmented with version and component data
        context_data_merged = copy.deepcopy(context_data)
        context_data_merged[asset_const.VERSION_ID] = asset_version_id
        context_data_merged[asset_const.COMPONENT_ID] = component['id']

        asset_info_options = self.generate_snapshot_asset_info_options(
            context_data_merged,
            self.extract_loader_options(options),
            component['id'],
            component['name'],
            component_path,
        )
        ftrack_object_manager.asset_info = FtrackAssetInfo.create(
            asset_version,
            component_name,
            component_path=component_path,
            component_id=component['id'],
            load_mode=load_const.OPEN_MODE,
            objects_loaded=True,
            is_snapshot=True,
        )
        ftrack_object_manager.asset_info[
            asset_const.ASSET_INFO_OPTIONS
        ] = asset_info_options

        # Store asset info with Unreal project
        dcc_object = self.DccObject(
            name=ftrack_object_manager.generate_dcc_object_name()
        )
        ftrack_object_manager.dcc_object = dcc_object

        # Connect to existing dependency, needs to be done before aligning modification date
        ftrack_object_manager.connect_objects([asset_path])

        # Align modification date with component source
        stat = os.stat(asset_filesystem_path)
        os.utime(
            asset_filesystem_path,
            times=(
                stat.st_atime,
                ftrack_object_manager.asset_info[asset_const.MOD_DATE],
            ),
        )
        self.logger.debug(
            'Restored file modification time: {} on asset: {} (size: {})'.format(
                ftrack_object_manager.asset_info[asset_const.MOD_DATE],
                asset_filesystem_path,
                ftrack_object_manager.asset_info[asset_const.FILE_SIZE],
            )
        )

        message = (
            'Stored snapshot asset info {} for dependency asset "{}"'.format(
                ftrack_object_manager.asset_info, asset_path
            )
        )
        self.logger.debug(message)
        return {'message': message}


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = UnrealDependencyTrackPublisherFinalizerPlugin(api_object)
    plugin.register()
