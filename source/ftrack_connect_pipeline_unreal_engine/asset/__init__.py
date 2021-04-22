# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import json
import ftrack_api
from ftrack_connect_pipeline.asset import FtrackAssetInfo, FtrackAssetBase
from ftrack_connect_pipeline_unreal_engine.constants import asset as asset_const
from ftrack_connect_pipeline import constants as core_const
from ftrack_connect_pipeline_unreal_engine.utils import custom_commands as unreal_utils
from ftrack_connect_pipeline_unreal_engine.constants.asset import modes as load_const

import unreal as ue

PREFIX='ftrack.' 

class FtrackAssetTab(FtrackAssetBase):
    '''
    Base FtrackAssetTab class.
    '''

    def __init__(self, event_manager):
        '''
        Initialize FtrackAssetTab with *event_manager*.

        *event_manager* instance of
        :class:`ftrack_connect_pipeline.event.EventManager`
        '''
        super(FtrackAssetTab, self).__init__(event_manager)

    def is_sync(self, ass):
        '''Returns bool if the current ftrack_object is sync'''
        return self._check_ftrack_object_sync(ass)

    @staticmethod
    def get_parameters_dictionary(ass):
        '''
        Returns a diccionary with the keys and values of the given *ass*
        parameters
        '''
        param_dict = {}
        for key in list(asset_const.KEYS):
            value = ue.EditorAssetLibrary.get_metadata_tag(
                ass, "{}{}".format(PREFIX, key)
            )
            if value:
                param_dict[key] = value
        return param_dict

    @staticmethod
    def get_ftrack_object_from_scene_on_asset_info(asset_info):
        ftrack_asset_assets = unreal_utils.get_ftrack_assets()
        for ass in ftrack_asset_assets:
            param_dict = FtrackAssetTab.get_parameters_dictionary(ass)
            # avoid read and write nodes containing the old ftrack tab
            # without information
            if not param_dict or len(param_dict) == 0:
                continue
            node_asset_info = FtrackAssetInfo(param_dict)
            if node_asset_info.is_deprecated:
                raise DeprecationWarning(
                    "Can not read v1 ftrack asset plugin")
            if (
                    node_asset_info[asset_const.REFERENCE_OBJECT] ==
                    asset_info[asset_const.REFERENCE_OBJECT]
            ):
                return ass
        return None

    def get_ftrack_object_from_scene(self):
        '''
        Return the ftrack object names from the current asset_version if it exists in
        the scene.
        '''
        result_asset = None
        ftrack_asset_assets = unreal_utils.get_ftrack_assets()
        for ass in ftrack_asset_assets:
            param_dict = self.get_parameters_dictionary(ass)
            node_asset_info = FtrackAssetInfo(param_dict)
            if node_asset_info.is_deprecated:
                raise DeprecationWarning("Can not read v1 ftrack asset plugin")
            if (
                    node_asset_info[asset_const.REFERENCE_OBJECT] ==
                    self.asset_info[asset_const.REFERENCE_OBJECT]
            ):
                result_asset = ftrack_object
                break

        return result_asset

    def _check_ftrack_object_sync(self, ass):
        '''
        Check if the current parameters of the ftrack_object match the
        values of the asset_info.
        '''
        if not ass:
            self.logger.warning("Ftrack tab doesn't exists")
            return False

        param_dict = self.get_parameters_dictionary(ass)
        node_asset_info = FtrackAssetInfo(param_dict)

        if node_asset_info == self.asset_info:
            self.logger.debug("{} is synced".format(ass))
            synced = True

        return synced

    def _set_ftab(self, ass):
        '''
        Add ftrack asset parameters to object.
        '''

        if ass:
            for k, v in self.asset_info.items():
                ue.EditorAssetLibrary.set_metadata_tag(
                    ass, "{}{}".format(PREFIX, k), str(v)
                )
            ue.EditorAssetLibrary.save_loaded_asset(ass)

    def connect_objects(self, asset_paths):
        '''
        Add asset info to Unreal assets
        '''
        assetRegistry = ue.AssetRegistryHelpers.get_asset_registry()

        for ass_path in asset_paths:
            ass = assetRegistry.get_asset_by_object_path(ass_path)
            self._set_ftab(ass)

    def _update_ftrack_object(self, ass):
        '''
        Update the parameters of the unreal ftrack asset. And Return the
        ftrack_object updated
        '''

        for k, v in list(self.asset_info.items()):
            ue.EditorAssetLibrary.set_metadata_tag(
                ass, "{}{}".format(PREFIX, k), str(v)
            )
            ue.EditorAssetLibrary.save_loaded_asset(ass)


