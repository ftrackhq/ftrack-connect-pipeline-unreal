# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_connect_pipeline_qt.client.save import QtSaveClientWidget
from ftrack_connect_pipeline_unreal.utils import custom_commands as unreal_utils


class UnrealQtSaveClientWidget(QtSaveClientWidget):
    '''Client for doing an incremental save of Unreal scene locally

    This is sample code that exists here for reference and not used by the current
    version of the framework.
    '''

    dcc_utils = unreal_utils
