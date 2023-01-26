# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from Qt import QtWidgets, QtCore


from ftrack_connect_pipeline import constants as core_constants


from ftrack_connect_pipeline_qt.client import load
import ftrack_connect_pipeline_qt.constants as qt_constants

from ftrack_connect_pipeline_unreal.constants.asset import modes as load_const
import ftrack_connect_pipeline_unreal.constants as unreal_constants
from ftrack_connect_pipeline_unreal.client.asset_manager import (
    UnrealQtAssetManagerClientWidget,
)


class UnrealQtAssemblerClientWidget(load.QtAssemblerClientWidget):
    '''Unreal assembler dialog'''

    ui_types = [
        core_constants.UI_TYPE,
        qt_constants.UI_TYPE,
        unreal_constants.UI_TYPE,
    ]

    def __init__(
        self,
        event_manager,
        asset_list_model,
        snapshot_asset_list_model,
        parent=None,
    ):
        self._snapshot_asset_list_model = snapshot_asset_list_model
        super(UnrealQtAssemblerClientWidget, self).__init__(
            event_manager,
            load_const.LOAD_MODES,
            asset_list_model,
            multithreading_enabled=False,
        )

        # Make sure we stays on top of Unreal
        self.setWindowFlags(QtCore.Qt.Window)

    def get_asset_manager_client(self):
        '''(Override) Return the class of the asset manager client'''
        return UnrealQtAssetManagerClientWidget(
            self.event_manager,
            self._asset_list_model,
            self._snapshot_asset_list_model,
            is_assembler=True,
            multithreading_enabled=self.multithreading_enabled,
        )

    def accept_component(self, component):
        '''(Override) Allow snapshot components on published Unreal assets.'''
        if component['name'].startswith(
            core_constants.FTRACKREVIEW_COMPONENT_NAME
        ):
            return False
        if component['name'] == core_constants.SNAPSHOT_COMPONENT_NAME:
            asset = component['version']['asset']
            if (
                asset['type']['name'].lower()
                != unreal_constants.UASSET_ASSET_TYPE
            ):
                return False
        return True
