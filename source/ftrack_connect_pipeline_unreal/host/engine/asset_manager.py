# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import copy

import time
import random
import string
import os

import unreal

import ftrack_api

from ftrack_connect_pipeline import constants as core_constants
from ftrack_connect_pipeline.host.engine import AssetManagerEngine
from ftrack_connect_pipeline.asset.asset_info import FtrackAssetInfo

from ftrack_connect_pipeline_unreal import utils as unreal_utils
from ftrack_connect_pipeline_unreal.constants import asset as asset_const
from ftrack_connect_pipeline_unreal.asset import UnrealFtrackObjectManager
from ftrack_connect_pipeline_unreal.asset.dcc_object import UnrealDccObject


class UnrealAssetManagerEngine(AssetManagerEngine):
    engine_type = 'asset_manager'

    FtrackObjectManager = UnrealFtrackObjectManager
    '''FtrackObjectManager class to use'''
    DccObject = UnrealDccObject
    '''DccObject class to use'''

    def __init__(
        self, event_manager, host_types, host_id, asset_type_name=None
    ):
        '''Initialise AssetManagerEngine with *event_manager*, *host*, *hostid*
        and *asset_type_name*'''
        super(UnrealAssetManagerEngine, self).__init__(
            event_manager, host_types, host_id, asset_type_name=asset_type_name
        )

    @unreal_utils.run_in_main_thread
    def discover_assets(self, assets=None, options=None, plugin=None):
        '''
        Discover all the assets in the scene:
        Returns status and result
        '''
        start_time = time.time()
        status = core_constants.UNKNOWN_STATUS
        result = []
        message = None

        result_data = {
            'plugin_name': None,
            'plugin_type': core_constants.PLUGIN_AM_ACTION_TYPE,
            'method': 'discover_assets',
            'status': status,
            'result': result,
            'execution_time': 0,
            'message': message,
        }

        ftrack_asset_nodes = unreal_utils.get_ftrack_nodes()
        ftrack_asset_info_list = []

        if ftrack_asset_nodes:
            for node_name in ftrack_asset_nodes:
                param_dict = self.DccObject.dictionary_from_object(node_name)
                node_asset_info = FtrackAssetInfo(param_dict)
                ftrack_asset_info_list.append(node_asset_info)

            if not ftrack_asset_info_list:
                status = core_constants.ERROR_STATUS
            else:
                status = core_constants.SUCCESS_STATUS
        else:
            self.logger.debug("No assets in the project")
            status = core_constants.SUCCESS_STATUS

        result = ftrack_asset_info_list

        end_time = time.time()
        total_time = end_time - start_time

        result_data['status'] = status
        result_data['result'] = result
        result_data['execution_time'] = total_time

        self._notify_client(plugin, result_data)

        return status, result

    @unreal_utils.run_in_main_thread
    def select_asset(self, asset_info, options=None, plugin=None):
        '''
        Selects the given *asset_info* from the scene.
        *options* can contain clear_selection to clear the selection before
        select the given *asset_info*.
        Returns status and result
        '''
        start_time = time.time()
        status = core_constants.UNKNOWN_STATUS
        result = []
        message = None

        plugin_type = core_constants.PLUGIN_AM_ACTION_TYPE
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
            'message': message,
        }

        self.asset_info = asset_info
        dcc_object = self.DccObject(
            from_id=asset_info[asset_const.ASSET_INFO_ID]
        )
        self.dcc_object = dcc_object

        asset_paths = []
        try:
            asset_paths = unreal_utils.get_connected_nodes_from_dcc_object(
                dcc_object.name
            )
            if not asset_paths:
                raise Exception(
                    'No Unreal asset found for {}'.format(dcc_object.name)
                )
            unreal.EditorAssetLibrary.sync_browser_to_objects(asset_paths)
            status = core_constants.SUCCESS_STATUS
        except Exception as error:
            message = str(
                'Could not select the assets {}, error: {}'.format(
                    str(asset_paths), error
                )
            )
            self.logger.error(message)
            status = core_constants.ERROR_STATUS

        bool_status = core_constants.status_bool_mapping[status]
        if not bool_status:
            end_time = time.time()
            total_time = end_time - start_time

            result_data['status'] = status
            result_data['result'] = result
            result_data['execution_time'] = total_time
            result_data['message'] = message

            self._notify_client(plugin, result_data)
            return status, result

        end_time = time.time()
        total_time = end_time - start_time

        result_data['status'] = status
        result_data['result'] = result
        result_data['execution_time'] = total_time

        self._notify_client(plugin, result_data)

        return status, result

    @unreal_utils.run_in_main_thread
    def select_assets(self, assets, options=None, plugin=None):
        '''
        Returns status dictionary and results dictionary keyed by the id for
        executing the :meth:`select_asset` for all the
        :class:`~ftrack_connect_pipeline.asset.FtrackAssetInfo` in the given
        *assets* list.

        *assets*: List of :class:`~ftrack_connect_pipeline.asset.FtrackAssetInfo`
        '''
        return super(UnrealAssetManagerEngine, self).select_assets(
            assets=assets, options=options, plugin=plugin
        )

    @unreal_utils.run_in_main_thread
    def load_asset(self, asset_info, options=None, plugin=None):
        '''
        Override load_asset method to deal with unloaded assets.
        '''

        # It's an import, so load asset with the main method
        return super(UnrealAssetManagerEngine, self).load_asset(
            asset_info=asset_info, options=options, plugin=plugin
        )

    @unreal_utils.run_in_main_thread
    def change_version(self, asset_info, options, plugin=None):
        '''
        (Override) Support Unreal asset version change preserving in memory references.
        '''
        start_time = time.time()
        status = core_constants.UNKNOWN_STATUS
        result = {}
        message = None

        plugin_type = core_constants.PLUGIN_AM_ACTION_TYPE
        plugin_name = None
        if plugin:
            plugin_type = '{}.{}'.format('asset_manager', plugin['type'])
            plugin_name = plugin.get('name')

        result_data = {
            'plugin_name': plugin_name,
            'plugin_type': plugin_type,
            'method': 'change_version',
            'status': status,
            'result': result,
            'execution_time': 0,
            'message': message,
        }

        new_version_id = options['new_version_id']

        self.asset_info = asset_info
        dcc_object = self.DccObject(
            from_id=asset_info[asset_const.ASSET_INFO_ID]
        )
        self.dcc_object = dcc_object

        # Get Component name from the original asset info
        component_name = self.asset_info.get(asset_const.COMPONENT_NAME)
        # Get the asset info options from the original asset info
        asset_info_options = self.asset_info[asset_const.ASSET_INFO_OPTIONS]
        # Make sure assets are not deleted, just renamed to a temporary name
        remove_options = {'rename_to_temporary': True}
        remove_result = None
        remove_status = None
        # first run remove
        try:
            remove_status, remove_result = self.remove_asset(
                asset_info=asset_info, options=remove_options, plugin=None
            )
        except Exception as e:
            remove_status = core_constants.ERROR_STATUS
            self.logger.exception(e)
            message = str(
                "Error removing asset with version id {} \n error: {} "
                "\n asset_info: {}".format(
                    asset_info[asset_const.VERSION_ID], e, asset_info
                )
            )
            self.logger.error(message)

        bool_status = core_constants.status_bool_mapping[remove_status]
        if not bool_status:
            end_time = time.time()
            total_time = end_time - start_time

            result_data['status'] = status
            result_data['result'] = result
            result_data['execution_time'] = total_time
            result_data['message'] = message

            self._notify_client(plugin, result_data)

            return remove_status, remove_result

        try:
            # Get asset version entity of the ne_ version_id
            asset_version_entity = self.session.query(
                'select version from AssetVersion where id is "{}"'.format(
                    new_version_id
                )
            ).one()

            # Collect data of the new version
            asset_entity = asset_version_entity['asset']
            asset_id = asset_entity['id']
            version_number = int(asset_version_entity['version'])
            asset_name = asset_entity['name']
            asset_type_name = asset_entity['type']['name']
            version_id = asset_version_entity['id']
            location = asset_version_entity.session.pick_location()
            component_path = None
            component_id = None
            for component in asset_version_entity['components']:
                if component['name'] == component_name:
                    component_id = component['id']
                    if location.get_component_availability(component) == 100.0:
                        component_path = location.get_filesystem_path(
                            component
                        )
            if component_path is None:
                raise Exception(
                    'Component {}({}) @ version {}({}) is not available in your current location {}({})'.format(
                        component_name,
                        component_id,
                        version_number,
                        version_id,
                        location['name'],
                        location['id'],
                    )
                )
            # Use the original asset_info options to reload the new version
            # Collect asset_context_data and asset data
            asset_context_data = asset_info_options['settings']['context_data']
            asset_context_data[asset_const.ASSET_ID] = asset_id
            asset_context_data[asset_const.VERSION_NUMBER] = version_number
            asset_context_data[asset_const.ASSET_NAME] = asset_name
            asset_context_data[asset_const.ASSET_TYPE_NAME] = asset_type_name
            asset_context_data[asset_const.VERSION_ID] = version_id

            # Update asset_info_options
            asset_info_options['settings']['data'][0]['result'] = {
                asset_const.COMPONENT_NAME: component_name,
                asset_const.COMPONENT_ID: component_id,
                asset_const.COMPONENT_PATH: component_path,
            }
            asset_info_options['settings']['context_data'].update(
                asset_context_data
            )

            # make a copy to new asset_info_options to avoid having encoded
            # options after running the plugin.
            new_asset_info_options = copy.deepcopy(asset_info_options)

            # Run the plugin with the asset info options
            run_event = ftrack_api.event.base.Event(
                topic=core_constants.PIPELINE_RUN_PLUGIN_TOPIC,
                data=asset_info_options,
            )

            plugin_result_data = self.session.event_hub.publish(
                run_event, synchronous=True
            )

            # Get the result
            result_data = plugin_result_data[0]

            if not result_data:
                self.logger.error("Error re-loading asset")

            # Get the new asset_info and dcc from the result
            new_asset_info = result_data['result'][
                new_asset_info_options['pipeline']['method']
            ]['asset_info']
            new_dcc_object = result_data['result'][
                new_asset_info_options['pipeline']['method']
            ]['dcc_object']
            new_asset_info[asset_const.REFERENCE_OBJECT] = new_dcc_object.name

            if result_data:
                temporary_assets = []
                for d in remove_result:
                    if isinstance(d, tuple):
                        temporary_assets.append(d)
                if temporary_assets:
                    load_result = result_data['result'][
                        new_asset_info_options['pipeline']['method']
                    ]['result']
                    for node in load_result.values():
                        asset = unreal.EditorAssetLibrary.load_asset(node)
                        asset_class_name = asset.__class__.__name__
                        self.logger.info(
                            'Identifying previous loaded asset for: {}'.format(
                                node
                            )
                        )
                        corresponding_node = None
                        # Attempt to find corresponding old node
                        for (
                            previous_node,
                            previous_asset_class_name,
                        ) in temporary_assets:
                            if previous_asset_class_name == asset_class_name:
                                corresponding_node = previous_node
                                break
                        if corresponding_node:
                            corresponding_asset = (
                                unreal.EditorAssetLibrary.load_asset(
                                    corresponding_node
                                )
                            )
                            self.logger.info(
                                'Consolidating from previous asset: {}'.format(
                                    corresponding_node
                                )
                            )
                            unreal.EditorAssetLibrary.consolidate_assets(
                                asset, [corresponding_asset]
                            )
                        else:
                            self.logger.warning(
                                'Could not find previous corresponding asset'
                            )
                    # Remove leftovers
                    for (
                        previous_node,
                        previous_asset_class_name,
                    ) in temporary_assets:
                        if unreal_utils.node_exists(previous_node):
                            self.logger.warning(
                                'Result of removing previous unrelated asset: {} (class: {})'.format(
                                    unreal_utils.delete_node(previous_node),
                                    previous_asset_class_name,
                                )
                            )
                else:
                    self.logger.error(
                        'Not able to consolidate asset(s), no remove result is available'
                    )

            self.asset_info = new_asset_info
            self.dcc_object = new_dcc_object

        except UserWarning as e:
            self.logger.debug(e)
            pass

        except Exception as e:
            status = core_constants.ERROR_STATUS
            message = str(
                'Error changing version of asset with version id {} \n '
                'error: {} \n asset_info: {}'.format(
                    asset_info[asset_const.VERSION_ID], e, asset_info
                )
            )
            self.logger.error(message)

            end_time = time.time()
            total_time = end_time - start_time

            result_data['status'] = status
            result_data['result'] = result
            result_data['execution_time'] = total_time
            result_data['message'] = message

            self._notify_client(plugin, result_data)
            return status, result

        if not new_asset_info:
            status = core_constants.ERROR_STATUS
        else:
            status = core_constants.SUCCESS_STATUS

        result[asset_info[asset_const.ASSET_INFO_ID]] = new_asset_info

        end_time = time.time()
        total_time = end_time - start_time

        result_data['status'] = status
        result_data['result'] = result
        result_data['execution_time'] = total_time

        self._notify_client(plugin, result_data)

        return status, result

    @unreal_utils.run_in_main_thread
    def unload_asset(self, asset_info, options=None, plugin=None):
        '''
        Removes the given *asset_info* from the scene.
        Returns status and result
        '''
        start_time = time.time()
        status = core_constants.UNKNOWN_STATUS
        result = []
        message = None

        plugin_type = core_constants.PLUGIN_AM_ACTION_TYPE
        plugin_name = None
        if plugin:
            plugin_type = '{}.{}'.format('asset_manager', plugin['type'])
            plugin_name = plugin.get('name')

        result_data = {
            'plugin_name': plugin_name,
            'plugin_type': plugin_type,
            'method': 'unload_asset',
            'status': status,
            'result': result,
            'execution_time': 0,
            'message': message,
        }

        self.asset_info = asset_info
        dcc_object = self.DccObject(
            from_id=asset_info[asset_const.ASSET_INFO_ID]
        )
        self.dcc_object = dcc_object

        nodes = (
            unreal_utils.get_connected_nodes_from_dcc_object(
                self.dcc_object.name
            )
            or []
        )

        for node in nodes:
            self.logger.debug('Removing object: {}'.format(node))
            try:
                if unreal_utils.node_exists(node):
                    if not unreal_utils.delete_node(node):
                        raise Exception(
                            'Unreal asset could not be deleted from library.'
                        )
                    result.append(str(node))
                    status = core_constants.SUCCESS_STATUS
            except Exception as error:
                message = str(
                    'Node: {0} could not be deleted, error: {1}'.format(
                        node, error
                    )
                )
                self.logger.error(message)
                status = core_constants.ERROR_STATUS

            bool_status = core_constants.status_bool_mapping[status]
            if not bool_status:
                end_time = time.time()
                total_time = end_time - start_time

                result_data['status'] = status
                result_data['result'] = result
                result_data['execution_time'] = total_time
                result_data['message'] = message

                self._notify_client(plugin, result_data)
                return status, result

        self.ftrack_object_manager.objects_loaded = False

        end_time = time.time()
        total_time = end_time - start_time

        result_data['status'] = status
        result_data['result'] = result
        result_data['execution_time'] = total_time

        self._notify_client(plugin, result_data)

        return status, result

    @unreal_utils.run_in_main_thread
    def remove_asset(self, asset_info, options=None, plugin=None):
        '''
        Removes the given *asset_info* from the scene.
        Returns status and result
        '''
        start_time = time.time()
        status = core_constants.UNKNOWN_STATUS
        result = []
        message = None
        rename_to_temporary = (
            options.get('rename_to_temporary', False) if options else False
        )

        plugin_type = core_constants.PLUGIN_AM_ACTION_TYPE
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
            'message': message,
        }

        self.asset_info = asset_info
        dcc_object = self.DccObject(
            from_id=asset_info[asset_const.ASSET_INFO_ID]
        )
        self.dcc_object = dcc_object

        nodes = (
            unreal_utils.get_connected_nodes_from_dcc_object(
                self.dcc_object.name
            )
            or []
        )

        for node in nodes:
            if not rename_to_temporary:
                self.logger.debug('Removing object: {}'.format(node))
                try:
                    if unreal_utils.node_exists(node):
                        if not unreal_utils.delete_node(node):
                            raise Exception(
                                'Unreal asset could not be deleted from library.'
                            )
                        result.append(str(node))
                        status = core_constants.SUCCESS_STATUS
                    else:
                        self.logger.debug(
                            'Could not renaming none existing object: {}'.format(
                                node
                            )
                        )
                except Exception as error:
                    message = str(
                        'Node: {0} could not be deleted, error: {1}'.format(
                            node, error
                        )
                    )
                    self.logger.error(message)
                    status = core_constants.ERROR_STATUS

                bool_status = core_constants.status_bool_mapping[status]
                if not bool_status:
                    end_time = time.time()
                    total_time = end_time - start_time

                    result_data['status'] = status
                    result_data['result'] = result
                    result_data['execution_time'] = total_time
                    result_data['message'] = message

                    self._notify_client(plugin, result_data)
                    return status, result
            else:
                # Generate temp name and map it to class
                try:
                    if unreal_utils.node_exists(node):
                        asset = unreal.EditorAssetLibrary.load_asset(node)
                        asset_class_name = asset.__class__.__name__
                        suffix = '_{}'.format(
                            ''.join(
                                random.choice(
                                    string.ascii_uppercase + string.digits
                                )
                                for _ in range(16)
                            )
                        )
                        asset_name = os.path.splitext(node)[0]
                        new_name = '{}{}'.format(asset_name, suffix)
                        self.logger.debug(
                            'Renaming object: {} > temp: {}'.format(
                                asset_name, new_name
                            )
                        )
                        if not unreal_utils.rename_node_with_suffix(
                            asset_name, suffix
                        ):
                            raise Exception(
                                'Unreal asset could not be renamed.'
                            )
                        # Supply the new name to the result together with Unreal class name so newly loaded assets can be mapped
                        # during consolidate
                        result.append((str(new_name), asset_class_name))
                        status = core_constants.SUCCESS_STATUS
                    else:
                        self.logger.debug(
                            'Could not renaming none existing object: {}'.format(
                                node
                            )
                        )
                except Exception as error:
                    message = str(
                        'Node: {0} could not be renamed, error: {1}'.format(
                            node, error
                        )
                    )
                    self.logger.error(message)
                    status = core_constants.ERROR_STATUS

                bool_status = core_constants.status_bool_mapping[status]
                if not bool_status:
                    end_time = time.time()
                    total_time = end_time - start_time

                    result_data['status'] = status
                    result_data['result'] = result
                    result_data['execution_time'] = total_time
                    result_data['message'] = message

                    self._notify_client(plugin, result_data)
                    return status, result
        if unreal_utils.ftrack_node_exists(self.dcc_object.name):
            try:
                unreal_utils.delete_ftrack_node(self.dcc_object.name)
                result.append(str(self.dcc_object.name))
                status = core_constants.SUCCESS_STATUS
            except Exception as error:
                message = str(
                    'Could not delete the dcc_object, error: {}'.format(error)
                )
                self.logger.error(message)
                status = core_constants.ERROR_STATUS

            bool_status = core_constants.status_bool_mapping[status]
            if not bool_status:
                end_time = time.time()
                total_time = end_time - start_time

                result_data['status'] = status
                result_data['result'] = result
                result_data['execution_time'] = total_time
                result_data['message'] = message

                self._notify_client(plugin, result_data)

                return status, result

        end_time = time.time()
        total_time = end_time - start_time

        result_data['status'] = status
        result_data['result'] = result
        result_data['execution_time'] = total_time

        self._notify_client(plugin, result_data)

        return status, result
