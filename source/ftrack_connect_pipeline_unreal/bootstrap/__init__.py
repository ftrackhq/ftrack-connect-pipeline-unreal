# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack
import os
import logging
import functools

from Qt import QtCore, QtWidgets, QtGui

import unreal

import ftrack_api

from ftrack_connect_pipeline import constants as core_constants
from ftrack_connect_pipeline.configure_logging import configure_logging

# Create a qapplication, needs to be done before using ftrack_connect_pipeline_qt
qapp = QtWidgets.QApplication.instance()
if qapp is None:
    qapp = QtWidgets.QApplication([])
    qapp.setWindowIcon(
        QtGui.QIcon(os.path.dirname(__file__) + '/UEFtrack.ico')
    )

from ftrack_connect_pipeline_qt import event
from ftrack_connect_pipeline_qt import constants as qt_constants
from ftrack_connect_pipeline_qt.ui.asset_manager.model import AssetListModel

from ftrack_connect_pipeline_unreal import host as unreal_host
from ftrack_connect_pipeline_unreal.client import (
    load,
    asset_manager,
    publish,
    change_context,
    log_viewer,
)
from ftrack_connect_pipeline_qt.client import documentation

from ftrack_connect_pipeline_unreal.utils import (
    custom_commands as unreal_utils,
)

configure_logging(
    'ftrack_connect_pipeline_unreal',
    extra_modules=['ftrack_connect_pipeline', 'ftrack_connect_pipeline_qt'],
    propagate=False,
)


logger = logging.getLogger('ftrack_connect_pipeline_unreal')


created_widgets = dict()

host = None


def get_ftrack_menu(menu_name='ftrack', submenu_name=None):
    '''Get the current ftrack menu, create it if does not exists.'''
    menus = unreal.ToolMenus.get()

    main_menu = menus.find_menu('LevelEditor.MainMenu')

    return main_menu.add_sub_menu(
        'Ftrack.Menu', 'Python', 'ftrack Menu', 'ftrack'
    )


def _open_widget(event_manager, asset_list_model, widgets, event):
    '''Open Unreal widget based on widget name in *event*, and create if not already
    exists'''
    widget_name = None
    widget_class = None
    for (_widget_name, _widget_class, unused_label, unused_image) in widgets:
        if _widget_name == event['data']['pipeline']['name']:
            widget_name = _widget_name
            widget_class = _widget_class
            break
    if widget_name:
        ftrack_client = widget_class
        widget = None
        if widget_name in created_widgets:
            widget = created_widgets[widget_name]
            # Is it still visible?
            is_valid_and_visible = False
            try:
                if widget is not None and widget.isVisible():
                    is_valid_and_visible = True
            except:
                pass
            finally:
                if not is_valid_and_visible:
                    del created_widgets[widget_name]  # Not active any more
                    if widget:
                        try:
                            widget.deleteLater()  # Make sure it is deleted
                        except:
                            pass
                        widget = None
        if widget is None:
            # Need to create
            if widget_name in [
                qt_constants.ASSEMBLER_WIDGET,
                core_constants.ASSET_MANAGER,
            ]:
                # Create with asset model
                widget = ftrack_client(event_manager, asset_list_model)
            else:
                # Create without asset model
                widget = ftrack_client(event_manager)
            created_widgets[widget_name] = widget
        widget.show()
        widget.raise_()
        widget.activateWindow()
    else:
        raise Exception(
            'Unknown widget {}!'.format(event['data']['pipeline']['name'])
        )


class EventFilterWidget(QtWidgets.QWidget):
    def eventFilter(self, obj, event):
        return False


def initialise():
    global host

    # TODO : later we need to bring back here all the unreal initialisations
    #  from ftrack-connect-unreal
    # such as frame start / end etc....

    logger.debug('Setting up the host')
    session = ftrack_api.Session(auto_connect_event_hub=False)

    event_manager = event.QEventManager(
        session=session, mode=core_constants.LOCAL_EVENT_MODE
    )

    host = unreal_host.UnrealHost(event_manager)

    logger.debug('Setting up the menu')

    # Shared asset manager model
    asset_list_model = AssetListModel(event_manager)

    widgets = list()
    widgets.append(
        (
            qt_constants.ASSEMBLER_WIDGET,
            load.UnrealQtAssemblerClientWidget,
            'Assembler',
            'greasePencilImport',
        )
    )
    widgets.append(
        (
            core_constants.ASSET_MANAGER,
            asset_manager.UnrealQtAssetManagerClientWidget,
            'Asset Manager',
            'volumeCube',
        )
    )
    widgets.append(
        (
            core_constants.PUBLISHER,
            publish.UnrealQtPublisherClientWidget,
            'Publisher',
            'greasePencilExport',
        )
    )
    widgets.append(
        (
            qt_constants.CHANGE_CONTEXT_WIDGET,
            change_context.UnrealQtChangeContextClientWidget,
            'Change context',
            'refresh',
        )
    )
    widgets.append(
        (
            core_constants.LOG_VIEWER,
            log_viewer.UnrealQtLogViewerClientWidget,
            'Log Viewer',
            'zoom',
        )
    )
    widgets.append(
        (
            qt_constants.DOCUMENTATION_WIDGET,
            documentation.QtDocumentationClientWidget,
            'Documentation',
            'SP_FileIcon',
        )
    )

    ftrack_menu = get_ftrack_menu()
    # Register and hook the dialog in ftrack menu
    for item in widgets:
        if item == 'divider':
            continue

        widget_name, unused_widget_class, label, image = item

        menu_entry = unreal.ToolMenuEntry(
            widget_name, type=unreal.MultiBlockType.MENU_ENTRY
        )
        menu_entry.set_label(label)
        menu_entry.set_string_command(
            unreal.ToolMenuStringCommandType.PYTHON,
            widget_name,
            string=(
                "from ftrack_connect_pipeline_unreal.bootstrap import launch_dialog;launch_dialog('{}')".format(
                    widget_name
                )
            ),
        )
        ftrack_menu.add_menu_entry(label, menu_entry)

    # Listen to widget launch events
    session.event_hub.subscribe(
        'topic={} and data.pipeline.host_id={}'.format(
            core_constants.PIPELINE_CLIENT_LAUNCH, host.host_id
        ),
        functools.partial(
            _open_widget, event_manager, asset_list_model, widgets
        ),
    )

    # Install dummy event filter to prevent Houdini from crashing during widget
    # build.
    # QtCore.QCoreApplication.instance().installEventFilter(EventFilterWidget())

    unreal_utils.init_unreal()


def launch_dialog(widget_name):
    '''Send an event to open *widget_name* client.'''
    host.launch_client(widget_name)


initialise()
