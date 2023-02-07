# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack
import unreal

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
        return 'unreal'


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
            for actor in unreal.EditorLevelLibrary.get_selected_level_actors():
                if (
                    actor.static_class()
                    == unreal.LevelSequenceActor.static_class()
                ):
                    # Get shot tracks
                    level_sequence = actor.load_sequence()
                    shot_tracks = unreal_utils.get_sequence_shots()
                    if shot_tracks:
                        # A master sequence with shots are selected, enter that mode
                        self.batch_publish_mode = (
                            unreal_constants.BATCH_PUBLISH_SHOTS
                        )
                        break
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
            self.setWindowTitle(title or 'ftrack Unreal Shot Publisher')
        else:
            # More than one asset selected?
            if len(asset_paths) == 0:
                dialog.ModalDialog(
                    None,
                    title='Batch publisher',
                    message='No assets selected in Unreal content browser, or Master sequence in level!',
                )
                return
            elif len(asset_paths) == 1:
                dialog.ModalDialog(
                    None,
                    title='Batch publisher',
                    message='Please use the standard publisher for single asset selections.',
                )
                return
            # TODO: Check if there are levels in selection, abort if so
            super(UnrealQtBatchPublisherClientWidget, self).__init__(
                event_manager,
                asset_paths,
                title=title,
                parent=parent,
            )
            self.setWindowTitle(title or 'ftrack Unreal Asset Batch Publisher')

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

    def check_add_processed_items(self, asset_path):
        '''(Override) Check so asset is not the parent asset'''
        if asset_path == self._parent_asset:
            return False
        return super(
            UnrealQtBatchPublisherClientWidget, self
        ).check_add_processed_items(asset_path)

    def run(self):
        '''(Override) Run the publisher.'''
        # Check that project context is set
        if (
            self.batch_publisher_widget.root_context_selector.context_id
            is None
        ):
            dialog.ModalDialog(
                self,
                message='Please set the Unreal root context!'.format(),
            )
            return
        super(UnrealQtBatchPublisherClientWidget, self).run()
