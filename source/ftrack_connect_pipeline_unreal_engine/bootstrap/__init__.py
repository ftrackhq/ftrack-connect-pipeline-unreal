# :coding: utf-8
# :copyright: Copyright (c) 2014-2021 ftrack

import os
import sys
import traceback
import logging


import unreal as ue

from ftrack_connect_pipeline_qt import event
from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline_unreal_engine import host as unreal_host

import ftrack_api

from ftrack_connect_pipeline.configure_logging import configure_logging

configure_logging(
    'ftrack_connect_pipeline_unreal_engine',
    extra_modules=['ftrack_connect_pipeline', 'ftrack_connect_pipeline_qt'],
    propagate=False
)

logger = logging.getLogger('ftrack_connect_pipeline_unreal_engine')

def get_dialog(name):

    from ftrack_connect_pipeline_unreal_engine.client import load
    from ftrack_connect_pipeline_unreal_engine.client import publish
    from ftrack_connect_pipeline_unreal_engine.client import asset_manager
    from ftrack_connect_pipeline_unreal_engine.client import log_viewer

    if 'Publish' in name:
        return publish.UnrealPublisherClient
    elif 'Loader' in name:
        return load.UnrealLoaderClient
    elif 'Asset' in name:
        return asset_manager.UnrealAssetManagerClient
    elif 'LogViewer' in name:
        return log_viewer.UnrealLogViewerClient


class Command(object):
    '''
        Command object allowing binding between UI and actions
    '''

    def __init__(
        self,
        name,
        display_name,
        description,
        command_type='dialog',
        user_data=None,
    ):
        self.name = name
        self.display_name = display_name
        self.description = description
        self.command_type = command_type
        self.user_data = user_data


class FTrackContext(object):
    '''
        Generic context ftrack object allowing caching of python specific data.
    '''

    def __init__(self):
        self.connector = None
        self.dialogs = dict()
        self.tickHandle = None
        self.app = None
        self._init_commands()
        self._init_tags()
        self._init_capture_arguments()

    def _init_commands(self):

        self.commands = []
        # main menu commands
        self.commands.append(
            Command(
                'ftrackLoader',
                'Loader',
                'ftrack load asset',
                'dialog'
            )
        )
        self.commands.append(Command('', '', '', 'separator'))
        self.commands.append(
            Command(
                'ftrackPublish',
                'Publish',
                'ftrack publish',
                'dialog'
            )
        )
        self.commands.append(Command('', '', '', 'separator'))
        self.commands.append(
            Command(
                'ftrackAssetManager',
                'Asset manager',
                'ftrack browser',
                'dialog',
            )
        )
        self.commands.append(Command('', '', '', 'separator'))
        self.commands.append(
            Command(
                'ftrackLogViewer',
                'Log Viewer',
                'ftrack log viewer',
                'dialog'
            )
        )
        # TODO: Bring back info and task widgets

    def _init_tags(self):

        from ftrack_connect_pipeline_unreal_engine.constants import asset as \
            asset_const

        self.tags = []
        PREFIX = 'ftrack.'
        for comp in asset_const.KEYS:
            self.tags.append(PREFIX + comp)

    def _init_capture_arguments(self):
        self.capture_args = []
        self.capture_args.append('-ResX=1280')
        self.capture_args.append('-ResY=720')
        self.capture_args.append('-MovieQuality=75')

    def external_init(self):
        pass

    def setTimeLine(self):
        '''
            Set time line to FS , FE environment values
        '''

        from ftrack_connect_pipeline_unreal_engine.utils import custom_commands\
            as unreal_utils

        # This is for the current frame range
        start = os.getenv('FS')
        end = os.getenv('FE')
        fps = os.getenv('FPS')

        sequences = unreal_utils.get_all_sequences(as_names=False)
        if 0<len(sequences):
            master_sequence = sequences[0]
            if master_sequence:
                master_sequence.set_playback_start(int(float(start)))
                master_sequence.set_playback_end(int(float(end)))
                master_sequence.set_display_rate(ue.FrameRate(int(float(fps))))
                ue.EditorAssetLibrary.save_loaded_asset(master_sequence)
                logger.info('Set master sequence timeline to: {}-{}, {} fps'
                            .format(start, end, fps))
            else:
                logger.info(
                    'No LevelSequence were found in the current map'
                    + ' therefore time range cannot be set.'
                )

ftrackContext = FTrackContext()

@ue.uclass()
class FTrackPipelineWrapper(ue.FTrackConnect):
    '''
        Main class for binding and interacting between python and ftrack
        C++ plugin.
    '''

    def _post_init(self):
        '''
            Equivalent to __init__ but will also be called from C++
        '''
        from Qt import QtWidgets, QtCore, QtGui

        ftrackContext.app = QtWidgets.QApplication.instance()
        if ftrackContext.app is None:
            ftrackContext.app = QtWidgets.QApplication([])
            ftrackContext.app.setWindowIcon(
                QtGui.QIcon(os.path.dirname(__file__) + '/UE4Ftrack.ico')
            )

        logger.info('Initializing ftrack Connect framework.')

        session = ftrack_api.Session(auto_connect_event_hub=False)

        self.currentEntity = session.query('Task where id={}'.format(
            os.getenv('FTRACK_CONTEXTID') or os.getenv('FTRACK_TASKID')))

        ftrackContext.event_manager = event.QEventManager(
            session=session, mode=constants.LOCAL_EVENT_MODE # REMOTE_EVENT_MODE
        )

        ftrackContext.host = unreal_host.UnrealHost(ftrackContext.event_manager)

        ftrackContext.external_init()
        #ftrackContext.connector.registerAssets()
        ftrackContext.setTimeLine()

        for tag in ftrackContext.tags:
            self.add_global_tag_in_asset_registry(tag)

        self.on_connect_initialized()

    @ue.ufunction(override=True)
    def shutdown(self):
        from Qt import QtWidgets, QtCore, QtGui

        try:
            # TODO: shutdown event manager
            #ftrackContext.event_manager.disconnect()

            app = QtWidgets.QApplication.instance()
            if app:
                app.quit()
                for w in app.topLevelWidgets():
                    try:
                        w.close()
                    except:
                        logger.warning(traceback.format_exc())
                QtWidgets.QApplication.processEvents()
                QtWidgets.QApplication.quit()
        finally:
            # Tear down background threads/event listeners
            os._exit(0)
            sys.exit(0)

    @ue.ufunction(override=True)
    def get_ftrack_menu_items(self):
        menu_items = []
        for command in ftrackContext.commands:
            menu_item = ue.FTrackMenuItem()
            menu_item.display_name = command.display_name
            menu_item.name = command.name
            menu_item.type = command.command_type
            menu_item.description = command.description
            menu_items.append(menu_item)
        return menu_items

    @ue.ufunction(override=True)
    def execute_command(self, command_name):
        for command in ftrackContext.commands:
            if command.name == command_name:
                if command.command_type == 'dialog':
                    logging.info('Executing command' + command.name)
                    self._open_dialog(command.name, command.display_name)
                    break

    def _open_dialog(self, dialog_ident, title):
        '''
            Open *dialog_class* and create if not already existing.
        '''
        dialog_class = get_dialog(dialog_ident)
        dialog_name = dialog_ident

        if dialog_name not in ftrackContext.dialogs:
            ftrack_dialog = dialog_class(ftrackContext.event_manager)
            ftrack_dialog.setWindowTitle(title)
            ftrackContext.dialogs[dialog_name] = ftrack_dialog
            # this does not seem to work but is the logical way of operating.
            ue.parent_external_window_to_slate(
                ftrack_dialog.effectiveWinId()
            )

        if ftrackContext.dialogs[dialog_name] is not None:
            ftrackContext.dialogs[dialog_name].show()

    @ue.ufunction(override=True)
    def get_capture_arguments(self):
        str_capture_args = ''
        for capture_arg in ftrackContext.capture_args:
            str_capture_args += capture_arg
            str_capture_args += ' '
        return str_capture_args

