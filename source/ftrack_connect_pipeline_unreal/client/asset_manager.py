# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_connect_pipeline_qt.client.asset_manager import (
    QtAssetManagerClientWidget,
)
import ftrack_connect_pipeline.constants as constants
import ftrack_connect_pipeline_qt.constants as qt_constants
from ftrack_connect_pipeline_qt.ui.asset_manager.base import (
    AssetManagerBaseWidget,
)
import ftrack_connect_pipeline_unreal.constants as unreal_constants


class UnrealQtAssetManagerClientWidget(QtAssetManagerClientWidget):
    ui_types = [
        constants.UI_TYPE,
        qt_constants.UI_TYPE,
        unreal_constants.UI_TYPE,
    ]
    '''Dockable unreal asset manager widget'''

    def __init__(self, event_manager, asset_list_model, parent=None):
        super(UnrealQtAssetManagerClientWidget, self).__init__(
            event_manager,
            asset_list_model,
            multithreading_enabled=False,
            parent=parent,
        )
        self.setWindowTitle('Unreal Pipeline Asset Manager')
        self.resize(350, 800)

    def get_theme_background_style(self):
        return 'unreal'


class UnrealSnapshotAssetManagerWidget(AssetManagerBaseWidget):
    def get_tab_name(self):
        '''Return the name of the tab, if multiple tabs are used. Can be overridden by child'''
        return 'Unreal Assets'
