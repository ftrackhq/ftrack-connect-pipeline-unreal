# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_connect_pipeline_qt.client.publish import QtPublisherClientWidget
import ftrack_connect_pipeline.constants as constants
import ftrack_connect_pipeline_qt.constants as qt_constants
import ftrack_connect_pipeline_unreal.constants as unreal_constants


class UnrealQtPublisherClientWidget(QtPublisherClientWidget):
    ui_types = [
        constants.UI_TYPE,
        qt_constants.UI_TYPE,
        unreal_constants.UI_TYPE,
    ]

    '''Dockable Unreal publisher widget'''

    def __init__(self, event_manager, parent=None):
        super(UnrealQtPublisherClientWidget, self).__init__(
            event_manager, parent=parent
        )
        self.setWindowTitle('Unreal Pipeline Publisher')

    def get_theme_background_style(self):
        return 'unreal'
