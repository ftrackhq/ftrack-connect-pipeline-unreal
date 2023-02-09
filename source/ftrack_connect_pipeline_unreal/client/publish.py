# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack
import unreal

from Qt import QtWidgets, QtCore, QtGui

from ftrack_connect_pipeline import constants as core_constants

from ftrack_connect_pipeline_qt.client.publish import QtPublisherClientWidget
from ftrack_connect_pipeline_qt.client.publish.batch import (
    QtBatchPublisherClientWidget,
)
from ftrack_connect_pipeline_qt.ui.utility.widget import (
    dialog,
    definition_selector,
)
import ftrack_connect_pipeline_qt.constants as qt_constants


import ftrack_connect_pipeline_unreal.constants as unreal_constants
from ftrack_connect_pipeline_unreal.ui.batch_publisher.asset import (
    UnrealAssetBatchPublisherWidget,
)
from ftrack_connect_pipeline_unreal.ui.batch_publisher.shot import (
    UnrealShotBatchPublisherWidget,
)
from ftrack_connect_pipeline_unreal.utils import (
    custom_commands as unreal_utils,
)


class UnrealQtPublisherClientWidget(QtPublisherClientWidget):
    ui_types = [
        core_constants.UI_TYPE,
        qt_constants.UI_TYPE,
        unreal_constants.UI_TYPE,
    ]
    '''Unreal single version publisher widget'''

    def __init__(self, event_manager, parent=None):
        super(UnrealQtPublisherClientWidget, self).__init__(
            event_manager, parent=parent
        )
        self.setWindowTitle('Unreal Pipeline Publisher')
        self.resize(600, 800)

    def get_theme_background_style(self):
        return 'ftrack'

    def is_docked(self):
        False


class UnrealQtBatchPublisherClientWidget(QtBatchPublisherClientWidget):
    '''Unreal multiple versions publisher widget'''

    ui_types = [
        core_constants.UI_TYPE,
        qt_constants.UI_TYPE,
        unreal_constants.UI_TYPE,
    ]

    batch_publish_mode = unreal_constants.BATCH_PUBLISH_ASSETS

    def __init__(
        self,
        event_manager,
        asset_paths=None,
        parent_asset_version_id=None,
        parent_asset=None,
        title=None,
        parent=None,
    ):
        self._parent_asset_version_id = parent_asset_version_id
        self._parent_asset = parent_asset
        shot_tracks = None
        if not asset_paths:
            # Any level sequence selected?
            level_sequence = unreal_utils.get_selected_sequence()
            if level_sequence:
                # Get shot tracks
                shot_tracks = unreal_utils.get_sequence_shots(level_sequence)
                if shot_tracks:
                    # A master sequence with shots are selected, enter that mode
                    self.batch_publish_mode = (
                        unreal_constants.BATCH_PUBLISH_SHOTS
                    )
            # Choose selected assets in Unreal Content browser
            asset_paths = [
                str(selected_asset.package_name)
                for selected_asset in unreal.EditorUtilityLibrary.get_selected_asset_data()
            ]
        if shot_tracks:
            super(UnrealQtBatchPublisherClientWidget, self).__init__(
                event_manager,
                shot_tracks,
                title=title,
                parent=parent,
            )
            self.setWindowTitle(title or 'ftrack Unreal Batch Publisher')
            self.resize(1000, 700)
        else:
            # More than one asset selected?
            if len(asset_paths) == 0:
                message = 'No assets selected in Unreal content browser, or Master sequence in level!'
                dialog.ModalDialog(
                    None,
                    title='Batch publisher',
                    message=message,
                )
                raise Exception(message)
            elif len(asset_paths) == 1:
                message = 'Please use the standard publisher for single asset selections.'
                dialog.ModalDialog(
                    None,
                    title='Batch publisher',
                    message=message,
                )
                raise Exception(message)
            # TODO: Check if there are levels in selection, abort if so
            super(UnrealQtBatchPublisherClientWidget, self).__init__(
                event_manager,
                asset_paths,
                title=title,
                parent=parent,
            )
            self.setWindowTitle(title or 'ftrack Unreal Batch Publisher')

    def _build_definition_selector(self):
        '''Build Unreal definition selector widget'''
        return definition_selector.BatchDefinitionSelector(
            definition_title_filter_expression='^Asset Publisher$'
            if self.batch_publish_mode == unreal_constants.BATCH_PUBLISH_ASSETS
            else '^Shot Publisher$',
        )

    def _build_batch_publisher_widget(self):
        '''Build Unreal batch publisher widget'''
        if self.batch_publish_mode == unreal_constants.BATCH_PUBLISH_ASSETS:
            return UnrealAssetBatchPublisherWidget(
                self,
                self.initial_items,
                parent_asset_version_id=self._parent_asset_version_id,
                parent_asset=self._parent_asset,
            )
        else:
            return UnrealShotBatchPublisherWidget(self, self.initial_items)

    def build(self):
        super(UnrealQtBatchPublisherClientWidget, self).build()
        # Add dependency track button
        if self._parent_asset_version_id is not None:
            self.track_button = TrackButton('TRACK DEPENDENCIES')
            self.track_button.setFocus()
            self.track_button.setToolTip(
                'Track dependencies for the published asset and close'
            )
            self.button_widget.layout().addWidget(self.track_button)

    def post_build(self):
        super(UnrealQtBatchPublisherClientWidget, self).post_build()
        if self._parent_asset_version_id is not None:
            self.track_button.clicked.connect(self._on_track_dependencies)

    def _on_track_dependencies(self):
        if self.batch_publisher_widget.dependencies_published:
            # Already done
            dialog.ModalDialog(
                None,
                title='Batch publisher',
                message='The dependencies has already been tracked with ftrack.',
            )
            return
        self.batch_publisher_widget.publish_dependencies()
        dialog.ModalDialog(
            None,
            title='Batch publisher',
            message='Successfully tracked existing dependencies without publishing any new.',
        )
        self.hide()
        self.deleteLater()

    def check_add_processed_items(self, asset_path):
        '''(Override) Check so asset is not the parent asset'''
        if asset_path == self._parent_asset:
            return False
        return super(
            UnrealQtBatchPublisherClientWidget, self
        ).check_add_processed_items(asset_path)

    def run(self):
        '''(Override) Run the publisher.'''
        if self.batch_publisher_widget.can_publish():
            super(UnrealQtBatchPublisherClientWidget, self).run()


class TrackButton(QtWidgets.QPushButton):
    def __init__(self, label, parent=None):
        super(TrackButton, self).__init__(label, parent=parent)
        self.setMaximumHeight(32)
        self.setMinimumHeight(32)
