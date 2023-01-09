# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from Qt import QtWidgets, QtCore

from ftrack_connect_pipeline_qt.client import open
import ftrack_connect_pipeline.constants as constants
import ftrack_connect_pipeline_unreal.constants as unreal_constants
from ftrack_connect_pipeline_unreal.utils.custom_commands import (
    get_main_window,
)
from ftrack_connect_pipeline_qt import constants as qt_constants


class UnrealQtOpenerClientWidget(open.QtOpenerClientWidget):
    '''Open dialog and client'''

    ui_types = [
        constants.UI_TYPE,
        qt_constants.UI_TYPE,
        unreal_constants.UI_TYPE,
    ]
    definition_extensions_filter = ['.umap', '.uasset']

    def __init__(self, event_manager, parent=None):
        super(UnrealQtOpenerClientWidget, self).__init__(event_manager)
