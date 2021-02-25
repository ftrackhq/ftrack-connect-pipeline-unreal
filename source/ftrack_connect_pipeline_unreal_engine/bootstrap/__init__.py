# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

#import unreal_ftrack_connect_pipeline

# :coding: utf-8
# :copyright: Copyright (c) 2021 ftrack

import os
import traceback
import logging

def log(s):
    #with open("C:\\TEMP\\unreal_ftrack_connect_pipeline.log", "a") as f:
    with open("/tmp/unreal_ftrack_connect_pipeline.log", "a") as f:
        f.write("{}\n".format(s))
    print(s)

def warning(s):
    log("[WARNING] {}".format(s))# :coding: utf-8


try:

    import unreal

    import ftrack_api

    logger = logging.getLogger('ftrack_connect_pipeline_unreal.bootstrap')
    logger.setLevel(logging.DEBUG)

    def get_dialog(name):

        from ftrack_connect_pipeline_unreal_engine.client import load
        from ftrack_connect_pipeline_unreal_engine.client import publish
        #from ftrack_connect_pipeline_unreal_engine.client import asset_manager
        #from ftrack_connect_pipeline_unreal_engine.client import log_viewer

        if "Publish" in name:
            return publish.UnrealPublisherClient
        elif "Loader" in name:
            return load.UnrealLoaderClient

    class Command(object):
        """
            Command object allowing binding between UI and actions
        """

        def __init__(
            self,
            name,
            display_name,
            description,
            command_type="dialog",
            user_data=None,
        ):
            self.name = name
            self.display_name = display_name
            self.description = description
            self.command_type = command_type
            self.user_data = user_data


    class FTrackContext(object):
        """
            Generic context ftrack object allowing caching of python specific data.
        """

        def __init__(self):
            self.connector = None
            self.dialogs = dict()
            self.tickHandle = None
            self._init_commands()
            self._init_tags()
            self._init_capture_arguments()

        def _init_commands(self):

            self.commands = []
            # main menu commands
            self.commands.append(
                Command(
                    "ftrackLoader",
                    "Loader",
                    "ftrack load asset",
                    "dialog"
                )
            )
            # self.commands.append(Command("", "", "", "separator"))
            # self.commands.append(
            #     Command(
            #         "ftrackAssetManager",
            #         "Asset manager",
            #         "ftrack browser",
            #         "dialog",
            #         FtrackUnrealAssetManagerDialog,
            #     )
            # )
            # self.commands.append(Command("", "", "", "separator"))
            self.commands.append(
                Command(
                    "ftrackPublish",
                    "Publish",
                    "ftrack publish",
                    "dialog"
                )
            )
            # self.commands.append(Command("", "", "", "separator"))
            # self.commands.append(
            #     Command(
            #         "ftrackInfo",
            #         "Info",
            #         "ftrack info",
            #         "dialog",
            #         FtrackUnrealInfoDialog,
            #     )
            # )
            # self.commands.append(
            #     Command(
            #         "ftrackTasks",
            #         "Tasks",
            #         "ftrack tasks",
            #         "dialog",
            #         FtrackTasksDialog,
            #     )
            # )

        def _init_tags(self):
            self.tags = []
            tagPrefix = "ftrack."
            self.tags.append(tagPrefix + "IntegrationVersion")
            self.tags.append(tagPrefix + "AssetComponentId")
            self.tags.append(tagPrefix + "AssetVersionId")
            self.tags.append(tagPrefix + "ComponentName")
            self.tags.append(tagPrefix + "AssetId")
            self.tags.append(tagPrefix + "AssetType")
            self.tags.append(tagPrefix + "AssetVersion")

        def _init_capture_arguments(self):
            self.capture_args = []
            self.capture_args.append("-ResX=1280")
            self.capture_args.append("-ResY=720")
            self.capture_args.append("-MovieQuality=75")

        def external_init(self):
            pass
            #self.connector = Connector()


    ftrackContext = FTrackContext()


    @unreal.uclass()
    class FTrackConnectWrapper(unreal.FTrackConnect):
        """
            Main class for binding and interacting between python and ftrack C++ plugin.
        """

        def _post_init(self):
            """
            Equivalent to __init__ but will also be called from C++
            """
            #ftrack.setup()

            from Qt import QtWidgets, QtCore, QtGui

            app = QtWidgets.QApplication.instance()
            if app is None:
                app = QtWidgets.QApplication([])
                app.setWindowIcon(
                    QtGui.QIcon(os.path.dirname(__file__) + '/UE4Ftrack.ico')
                )
            print('@@@ app: {}'.format(app))

            session = ftrack_api.Session(auto_connect_event_hub=False)

            self.currentEntity = session.query('Task where id={}'.format(os.getenv('FTRACK_CONTEXTID') or os.getenv('FTRACK_TASKID')))

            from ftrack_connect_pipeline_unreal_engine import host as unreal_host
            from ftrack_connect_pipeline_qt import event
            from ftrack_connect_pipeline import constants

            ftrackContext.event_manager = event.QEventManager(
                session=session, mode=constants.LOCAL_EVENT_MODE # REMOTE_EVENT_MODE
            )

            FTrackContext._host = unreal_host.UnrealHost(ftrackContext.event_manager)


            #ftrackContext.external_init()
            #ftrackContext.connector.registerAssets()
            #ftrackContext.connector.setTimeLine()

            for tag in ftrackContext.tags:
                self.add_global_tag_in_asset_registry(tag)

            # Install the ftrack logging handlers
            #ftrack_connect.config.configure_logging(
            #    'ftrack_connect_pipeline_unreal_engine', level='INFO'
            #)

            self.on_connect_initialized()

        @unreal.ufunction(override=True)
        def shutdown(self):
            from Qt import QtWidgets, QtCore, QtGui

            # TODO: shutdown host

            QtWidgets.QApplication.instance().quit()
            QtWidgets.QApplication.processEvents()

        @unreal.ufunction(override=True)
        def get_ftrack_menu_items(self):
            menu_items = []
            for command in ftrackContext.commands:
                menu_item = unreal.FTrackMenuItem()
                menu_item.display_name = command.display_name
                menu_item.name = command.name
                menu_item.type = command.command_type
                menu_item.description = command.description
                menu_items.append(menu_item)
            return menu_items

        @unreal.ufunction(override=True)
        def execute_command(self, command_name):
            for command in ftrackContext.commands:
                if command.name == command_name:
                    if command.command_type == "dialog":
                        logging.info('Executing command' + command.name)
                        self._open_dialog(command.name, command.display_name)
                        break

        def _open_dialog(self, dialog_ident, title):
            '''Open *dialog_class* and create if not already existing.'''
            dialog_class = get_dialog(dialog_ident)
            dialog_name = dialog_ident

            #if (
            #    dialog_name == FtrackImportAssetDialog
            #    or dialog_name == FtrackPublishDialog
            #) and dialog_name in ftrackContext.dialogs:
            #    ftrackContext.dialogs[dialog_name].deleteLater()
            #    ftrackContext.dialogs[dialog_name] = None
            #    del ftrackContext.dialogs[dialog_name]

            if dialog_name not in ftrackContext.dialogs:
                ftrack_dialog = dialog_class(ftrackContext.event_manager)
                ftrack_dialog.setWindowTitle(title)
                ftrackContext.dialogs[dialog_name] = ftrack_dialog
                # this does not seem to work but is the logical way of operating.
                unreal.parent_external_window_to_slate(
                    ftrack_dialog.effectiveWinId()
                )

            if ftrackContext.dialogs[dialog_name] is not None:
                ftrackContext.dialogs[dialog_name].show()

        @unreal.ufunction(override=True)
        def get_capture_arguments(self):
            str_capture_args = ''
            for capture_arg in ftrackContext.capture_args:
                str_capture_args += capture_arg
                str_capture_args += ' '
            return str_capture_args

except:
    import traceback
    warning(traceback.format_exc())

