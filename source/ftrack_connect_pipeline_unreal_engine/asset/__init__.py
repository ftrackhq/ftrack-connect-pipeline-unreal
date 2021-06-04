# :coding: utf-8
# :copyright: Copyright (c) 2014-2021 ftrack

import os
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

    def init_ftrack_object(self):
        '''
        Return the ftrack ftrack_object for this class. It checks if there is
        already a matching ftrack asset in the scene and stores its path.
        '''
        asset_path = self.get_ftrack_object_from_scene()
        if not asset_path:
            self.logger.warning('My ftrack object has disappeared! (asset info:'
                                ' {})'.format(self.asset_info))
        else:
            if not self.is_sync(asset_path):
                self._update_ftrack_object(asset_path)

        self.ftrack_object = asset_path

        return self.ftrack_object

    def is_sync(self, asset_path):
        '''Returns bool if the current ftrack_object is sync'''
        return self._check_ftrack_object_sync(asset_path)

    @staticmethod
    def get_parameters_dictionary(asset):
        '''
        Returns a diccionary with the keys and values of the given *asset*
        parameters
        '''
        param_dict = {}
        for key in list(asset_const.KEYS):
            value = ue.EditorAssetLibrary.get_metadata_tag(
                asset, '{}{}'.format(PREFIX, key)
            )
            if value:
                param_dict[key] = value
        return param_dict

    def get_ftrack_object_from_scene(self):
        ''' Find asset matching *asset_info* '''
        ftrack_asset_assets = unreal_utils.get_ftrack_assets()
        result_path = None
        for asset in ftrack_asset_assets:
            param_dict = FtrackAssetTab.get_parameters_dictionary(asset)
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
                    self.asset_info[asset_const.REFERENCE_OBJECT]
            ):
                result_path = asset.get_path_name()
                break
        self.logger.debug('Found {} existing node'.format(result_path))
        return result_path

    def _check_ftrack_object_sync(self, asset_path):
        '''
        Check if the current parameters of the ftrack asset pointed
         out by *asset_path* match the values of the asset_info.
        '''
        asset = unreal_utils.get_asset_by_path(asset_path)

        if not asset:
            self.logger.error("ftrack asset doesn't exists")
            return False

        param_dict = self.get_parameters_dictionary(asset)
        node_asset_info = FtrackAssetInfo(param_dict)

        synced = False

        if node_asset_info == self.asset_info:
            self.logger.debug('{} is synced'.format(asset))
            synced = True

        return synced

    def _set_ftab(self, asset_path):
        '''
        Add ftrack asset parameters to an asset pointed out by *asset_path*.
        '''
        asset = unreal_utils.get_asset_by_path(asset_path)
        if asset:
            for k, v in self.asset_info.items():
                ue.EditorAssetLibrary.set_metadata_tag(
                    asset, '{}{}'.format(PREFIX, k), str(v)
                )
            ue.EditorAssetLibrary.save_loaded_asset(asset)

    def connect_objects(self, asset_paths):
        '''
        Add asset info to Unreal assets defined in *asset_paths*
        '''

        for asset_path in asset_paths:
            self._set_ftab(asset_path)


    def _update_ftrack_object(self, asset_path):
        '''
        Update the parameters of the unreal ftrack asset at *asset_path*.
        '''

        asset = unreal_utils.get_asset_by_path(asset_path)

        if asset:
            for k, v in list(self.asset_info.items()):
                ue.EditorAssetLibrary.set_metadata_tag(
                    asset, '{}{}'.format(PREFIX, k), str(v)
                )
                ue.EditorAssetLibrary.save_loaded_asset(asset)


