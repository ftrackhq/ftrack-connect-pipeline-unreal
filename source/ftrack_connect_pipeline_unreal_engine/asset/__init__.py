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


class FtrackAssetTab(FtrackAssetBase):
    '''
    Base FtrackAssetTab class.
    '''

    def is_sync(self, obj_path):
        '''Returns bool if the current ftrack_object is sync'''
        return self._check_ftrack_object_sync(obj_path)

    def __init__(self, event_manager):
        '''
        Initialize FtrackAssetTab with *event_manager*.

        *event_manager* instance of
        :class:`ftrack_connect_pipeline.event.EventManager`
        '''
        super(FtrackAssetTab, self).__init__(event_manager)

    # def init_ftrack_object(self):
    #     '''
    #     Return the ftrack ftrack_object for this class. It checks if there is
    #     already a matching ftrack ftrack_object in the scene, in this case it
    #     updates the ftrack_object if it's not. In case there is no ftrack_object
    #     in the scene this function creates a new one.
    #     '''
    #     ftrack_object = self.get_ftrack_object_from_scene() or self.create_new_ftrack_object()
    #
    #     if not self.is_sync(ftrack_object):
    #         ftrack_object = self._update_ftrack_object(ftrack_object)
    #
    #     self.ftrack_object = ftrack_object
    #
    #     return self.ftrack_object

    @staticmethod
    def get_parameters_dictionary(obj):
        '''
        Returns a diccionary with the keys and values of the given *obj*
        parameters
        '''
        param_dict = {}
        if obj.parmTemplateGroup().findFolder('ftrack'):
            for parm in obj.parms():
                if parm.name() in asset_const.KEYS:
                    param_dict[parm.name()] = parm.eval()
        return param_dict

    @staticmethod
    def get_ftrack_object_from_scene_on_asset_info(asset_info):
        ftrack_asset_nodes = unreal_utils.get_ftrack_objects()
        for obj in ftrack_asset_nodes:
            param_dict = FtrackAssetTab.get_parameters_dictionary(obj)
            # avoid read and write nodes containing the old ftrack tab
            # without information
            if not param_dict:
                continue
            node_asset_info = FtrackAssetInfo(param_dict)
            if node_asset_info.is_deprecated:
                raise DeprecationWarning(
                    "Can not read v1 ftrack asset plugin")
            if (
                    node_asset_info[asset_const.REFERENCE_OBJECT] ==
                    asset_info[asset_const.REFERENCE_OBJECT]
            ):
                return obj.path()
        return None

    def get_ftrack_object_from_scene(self):
        '''
        Return the ftrack object path from the current asset_version if it exists in
        the scene.
        '''
        return self.get_ftrack_object_from_scene_on_asset_info(self.asset_info)

    def _check_ftrack_object_sync(self, obj_path):
        '''
        Check if the current parameters of the ftrack_object match the
        values of the asset_info.
        '''
        if not obj_path:
            self.logger.warning("Ftrack tab doesn't exists")
            return False

        synced = False
        obj = hou.node(obj_path)
        param_dict = self.get_parameters_dictionary(obj)
        node_asset_info = FtrackAssetInfo(param_dict)

        if node_asset_info == self.asset_info:
            self.logger.debug("{} is synced".format(ftrack_object))
            synced = True

        return synced
    #
    # def add_ftab(self, obj):
    #     '''
    #     Add ftrack asset parameters to object.
    #     '''
    #
    #     PREFIX='ftrack.'
    #     if obj:
    #         ue.EditorAssetLibrary.set_metadata_tag(
    #             linked_obj, "{}{}".format(PREFIX, asset_const.VERSION_ID), context['version_id']
    #         )
    #         ue.EditorAssetLibrary.set_metadata_tag(
    #             linked_obj, "{}{}".format(PREFIX, asset_const.COMPONENT_PATH), path_imported
    #         )
    #         ue.EditorAssetLibrary.set_metadata_tag(
    #             linked_obj, "{}{}".format(PREFIX, asset_const.ASSET_NAME), context['asset_name']
    #         )
    #         ue.EditorAssetLibrary.set_metadata_tag(
    #             linked_obj, "{}{}".format(PREFIX, asset_const.COMPONENT_NAME), context['component_name']
    #         )
    #         ue.EditorAssetLibrary.set_metadata_tag(
    #             linked_obj, "{}{}".format(PREFIX, asset_const.ASSET_TYPE), context['asset_type']
    #         )
    #         ue.EditorAssetLibrary.set_metadata_tag(
    #             linked_obj, "{}{}".format(PREFIX, asset_const.ASSET_ID), context['asset_id']
    #         )
    #         ue.EditorAssetLibrary.set_metadata_tag(
    #             linked_obj, "{}{}".format(PREFIX, asset_const.COMPONENT_ID), context['component_id']
    #         )
    #         ue.EditorAssetLibrary.set_metadata_tag(
    #             linked_obj, "{}{}".format(PREFIX, asset_const.VERSION_ID), context['version_id']
    #         )
    #         ue.EditorAssetLibrary.set_metadata_tag(
    #             linked_obj, "ftrack.IntegrationVersion", __version__
    #         )  # to be changed at cleanup
    #         ue.EditorAssetLibrary.save_loaded_asset(linked_obj)


    def _set_ftab(self, obj):
        '''
        Add ftrack asset parameters to object.
        '''

        if obj:
            for k, v in self.asset_info.items():
                ue.EditorAssetLibrary.set_metadata_tag(
                    obj, "{}{}".format(PREFIX, k), v
                )
            ue.EditorAssetLibrary.save_loaded_asset(obj)

    def connect_objects(self, objects):
        '''
        Add asset info to Unreal objects
        '''
        for obj in objects:
            self._set_ftab(obj)

    def _update_ftrack_object(self, obj_path):
        '''
        Update the parameters of the ftrack_object. And Return the
        ftrack_object updated
        '''

        pass


