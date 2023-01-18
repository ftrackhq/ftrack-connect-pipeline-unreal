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
from ftrack_connect_pipeline_qt.ui.asset_manager.asset_manager import (
    AssetWidget,
)

import ftrack_connect_pipeline_unreal.constants as unreal_constants


class UnrealQtAssetManagerClientWidget(QtAssetManagerClientWidget):
    '''Dockable unreal asset manager widget'''

    ui_types = [
        constants.UI_TYPE,
        qt_constants.UI_TYPE,
        unreal_constants.UI_TYPE,
    ]

    snapshot_assets = True

    def __init__(
        self,
        event_manager,
        asset_list_model,
        snapshot_list_model,
        is_assembler=False,
        multithreading_enabled=False,
        parent=None,
    ):
        self._snapshot_list_model = snapshot_list_model
        super(UnrealQtAssetManagerClientWidget, self).__init__(
            event_manager,
            asset_list_model,
            is_assembler=is_assembler,
            multithreading_enabled=multithreading_enabled,
            parent=parent,
        )
        self.setWindowTitle('Unreal Pipeline Asset Manager')
        self.resize(350, 800)

    def get_theme_background_style(self):
        return 'unreal' if not self.is_assembler else 'transparent'

    def get_snapshot_asset_widget_class(self):
        '''Return snapshot asset widget class'''
        return UnrealSnapshotAssetWidget

    def get_snapshot_list_model(self):
        '''Return snapshot list model'''
        return self._snapshot_list_model


class UnrealSnapshotAssetWidget(AssetWidget):
    '''Unreal snapshot asset widget, adjust rendering with indentation'''
