# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import time

import unreal as ue

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.host.engine import AssetManagerEngine
from ftrack_connect_pipeline_unreal_engine.asset import FtrackAssetTab
from ftrack_connect_pipeline.asset.asset_info import FtrackAssetInfo
from ftrack_connect_pipeline_unreal_engine.utils import custom_commands as unreal_utils
from ftrack_connect_pipeline_unreal_engine.constants import asset as asset_const


class UnrealAssetManagerEngine(AssetManagerEngine):
    ftrack_asset_class = FtrackAssetTab
    engine_type = 'asset_manager'

    def __init__(self, event_manager, host_types, host_id, asset_type=None):
        '''Initialise AssetManagerEngine with *event_manager*, *host*, *hostid*
        and *asset_type*'''
        super(UnrealAssetManagerEngine, self).__init__(
            event_manager, host_types, host_id, asset_type=asset_type
        )

    def discover_assets(self, assets=None, options=None, plugin=None):
        '''
        Discover all the assets in the scene:
        Returns status and result
        '''
        try:
            start_time = time.time()
            status = constants.UNKNOWN_STATUS
            result = []
            message = None

            result_data = {
                'plugin_name': 'None',
                'plugin_type': constants.PLUGIN_AM_ACTION_TYPE,
                'method': 'discover_assets',
                'status': status,
                'result': result,
                'execution_time': 0,
                'message': message
            }

            ftrack_asset_assets = unreal_utils.get_ftrack_assets()
            ftrack_asset_info_list = []

            for ass in ftrack_asset_assets:
                param_dict = FtrackAssetTab.get_parameters_dictionary(
                    ass
                )
                # avoid objects containing the old ftrack tab without information
                if not param_dict:
                    continue
                node_asset_info = FtrackAssetInfo(param_dict)
                ftrack_asset_info_list.append(node_asset_info)

            if not ftrack_asset_info_list:
                status = constants.ERROR_STATUS
            else:
                status = constants.SUCCESS_STATUS
            result = ftrack_asset_info_list

            end_time = time.time()
            total_time = end_time - start_time

            result_data['status'] = status
            result_data['result'] = result
            result_data['execution_time'] = total_time

            self._notify_client(plugin, result_data)

        except:
            import traceback
            self.logger.warning(traceback.format_exc())
            raise

        return status, result

    def remove_asset(self, asset_info, options=None, plugin=None):
        '''
        Removes the given *asset_info* from the scene.
        Returns status and result
        '''
        try:
            start_time = time.time()
            status = constants.UNKNOWN_STATUS
            result = []
            message = None

            plugin_type = constants.PLUGIN_AM_ACTION_TYPE
            plugin_name = None
            if plugin:
                plugin_type = '{}.{}'.format('asset_manager', plugin['type'])
                plugin_name = plugin.get('name')

            result_data = {
                'plugin_name': plugin_name,
                'plugin_type': plugin_type,
                'method': 'remove_asset',
                'status': status,
                'result': result,
                'execution_time': 0,
                'message': message
            }

            try:
                ass = FtrackAssetTab.get_ftrack_object_from_scene_on_asset_info(asset_info)
                if not ass:
                    message = "There is no ftrack object in the current scene with asset info '{}'".format(asset_info)
                    self.logger.warning(message)
                    status = constants.UNKNOWN_STATUS
                else:
                    try:
                        ue.EditorAssetLibrary.delete_asset(ass.get_path_name())
                        status = constants.SUCCESS_STATUS
                    except Exception as error:
                        message = str(
                            'Could not delete the ftrack_object, error: {}'.format(error)
                        )
                        self.logger.error(message)
                        status = constants.ERROR_STATUS
                    else:
                        bool_status = constants.status_bool_mapping[status]
                        if not bool_status:
                            status = constants.UNKNOWN_STATUS
            finally:
                end_time = time.time()
                total_time = end_time - start_time

                result_data['status'] = status
                result_data['result'] = result
                result_data['execution_time'] = total_time

            self._notify_client(plugin, result_data)
        except:
            import traceback
            self.logger.warning(traceback.format_exc())
            raise
        return status, result

    def select_asset(self, asset_info, options=None, plugin=None):
        '''
        Selects the given *asset_info* from the scene.
        *options* can contain clear_selection to clear the selection before
        select the given *asset_info*.
        Returns status and result
        '''
        try:

            start_time = time.time()
            status = constants.UNKNOWN_STATUS
            result = []
            message = None
            plugin_type = constants.PLUGIN_AM_ACTION_TYPE
            plugin_name = None
            if plugin:
                plugin_type = '{}.{}'.format('asset_manager', plugin['type'])
                plugin_name = plugin.get('name')

            result_data = {
                'plugin_name': plugin_name,
                'plugin_type': plugin_type,
                'method': 'select_asset',
                'status': status,
                'result': result,
                'execution_time': 0,
                'message': message
            }

            try:
                ass = FtrackAssetTab.get_ftrack_object_from_scene_on_asset_info(asset_info)
                if not ass:
                    message = "There is no ftrack object in the current scene with asset info '{}'".format(asset_info)
                    self.logger.warning(message)
                    status = constants.UNKNOWN_STATUS
                else:
                    try:
                        selection_path_names = []
                        selection_path_names.append(str(ass.get_path_name()))
                        ue.EditorAssetLibrary.sync_browser_to_objects(selection_path_names)
                        status = constants.SUCCESS_STATUS
                    except Exception as error:
                        message = str(
                            'Could not select ftrack_object, error: {}'.format(error)
                        )
                        self.logger.error(message)
                        status = constants.ERROR_STATUS
                    else:
                        bool_status = constants.status_bool_mapping[status]
                        if not bool_status:
                            status = constants.UNKNOWN_STATUS
            finally:
                end_time = time.time()
                total_time = end_time - start_time

                result_data['status'] = status
                result_data['result'] = result
                result_data['execution_time'] = total_time

            self._notify_client(plugin, result_data)

        except:
            import traceback
            self.logger.warning(traceback.format_exc())
            raise

        return status, result


