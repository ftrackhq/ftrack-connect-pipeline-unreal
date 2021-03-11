# # :coding: utf-8
# # :copyright: Copyright (c) 2020 ftrack

from ftrack_connect_pipeline_qt.client.load import QtLoaderClient
import ftrack_connect_pipeline.constants as constants
import ftrack_connect_pipeline_qt.constants as qt_constants
import ftrack_connect_pipeline_unreal_engine.constants as unreal_constants


class UnrealLoaderClient(QtLoaderClient):
    ui_types = [constants.UI_TYPE, qt_constants.UI_TYPE, unreal_constants.UI_TYPE]

    '''Dockable unreal load widget'''
    def __init__(self, event_manager, parent=None):
        super(UnrealLoaderClient, self).__init__(
            event_manager=event_manager, parent=parent
        )
        self.setWindowTitle('Unreal Pipeline Loader')
        self.resize(300, 600)


