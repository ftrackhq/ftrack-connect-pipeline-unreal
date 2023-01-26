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
from ftrack_connect_pipeline_unreal.ui.batch_publisher import (
    UnrealBatchPublisherWidget,
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

    def __init__(
        self,
        event_manager,
        asset_paths,
        parent_asset_version_id=None,
        parent_asset=None,
        title=None,
        parent=None,
    ):
        self._parent_asset_version_id = parent_asset_version_id
        self._parent_asset = parent_asset
        if not asset_paths:
            # Choose selected assets in Unreal Content browser
            asset_paths = [
                str(selected_asset.package_name)
                for selected_asset in unreal.EditorUtilityLibrary.get_selected_asset_data()
            ]
        # More than one asset selected?
        if len(asset_paths) == 0:
            dialog.ModalDialog(
                None,
                title='Batch publisher',
                message='No assets selected in Unreal content browser!',
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
        )

    def _build_batch_publisher_widget(self):
        '''Build Unreal batch publisher widget'''
        return UnrealBatchPublisherWidget(
            self,
            self.initial_items,
            parent_asset_version_id=self._parent_asset_version_id,
            parent_asset=self._parent_asset,
        )

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
