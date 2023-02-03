# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import os
import unreal

from Qt import QtWidgets, QtCore

from ftrack_connect_pipeline_qt.utils import clear_layout, set_property
from ftrack_connect_pipeline_qt.ui.asset_manager.asset_manager import (
    AssetManagerWidget,
    AssetManagerListWidget,
    AssetWidget,
)
from ftrack_connect_pipeline_qt.ui.asset_manager.base import (
    AssetListContainerWidget,
)
from ftrack_connect_pipeline_unreal.utils import (
    custom_commands as unreal_utils,
)


class UnrealAssetManagerWidget(AssetManagerWidget):
    '''Override selected functionality within the Unreal asset manager'''

    def build_asset_list_container(self, scroll_widget, snapshot=False):
        '''Override'''
        if snapshot:
            return UnrealSnapshotAssetListContainerWidget(scroll_widget)
        else:
            return UnrealAssetListContainerWidget(scroll_widget)

    def build_asset_manager_list_widget(self, snapshot=False):
        '''Provide custom Unreal snapshot asset list widget if *snapshot* is true'''
        if snapshot:
            return UnrealAssetManagerSnapshotListWidget(
                self,
                self.client.get_snapshot_list_model(),
                self.client.get_snapshot_asset_widget_class(),
                docked=self.client.is_docked(),
            )
        else:
            return super(
                UnrealAssetManagerWidget, self
            ).build_asset_manager_list_widget()

    def post_build(self):
        super(UnrealAssetManagerWidget, self).post_build()
        # Make sure a change in show all triggers a rebuild
        self.snapshot_asset_list_container.cb_show_all.clicked.connect(
            self._on_rebuild
        )


class UnrealSnapshotAssetListContainerWidget(AssetListContainerWidget):
    '''Custom Unreal snapshot asset list container widget containing label & show all checkbox'''

    @property
    def show_all(self):
        return self.cb_show_all is not None and self.cb_show_all.isChecked()

    def __init__(self, scroll_widget, parent=None):
        self.cb_show_all = None
        super(UnrealSnapshotAssetListContainerWidget, self).__init__(
            scroll_widget, parent=parent
        )

    def pre_build(self):
        super(UnrealSnapshotAssetListContainerWidget, self).pre_build()
        self._header_widget = QtWidgets.QWidget()
        self._header_widget.setLayout(QtWidgets.QVBoxLayout())
        self._header_widget.layout().setContentsMargins(5, 0, 5, 0)
        self._header_widget.layout().setSpacing(0)

        label_widget = QtWidgets.QLabel('Unreal assets:')
        self._header_widget.layout().addWidget(label_widget)

        self.cb_show_all = QtWidgets.QCheckBox('Show all')
        self.cb_show_all.setToolTip(
            'Show all tracked and un-tracked dependencies, not only the level dependencies.'
        )
        self._header_widget.layout().addWidget(self.cb_show_all)

    def post_build(self):
        super(UnrealSnapshotAssetListContainerWidget, self).post_build()
        self.cb_show_all.clicked.connect(self._on_show_all_clicked)

    def _on_show_all_clicked(self):
        pass


class UnrealAssetListContainerWidget(AssetListContainerWidget):
    '''Custom Unreal asset list container widget with label'''

    @property
    def show_all(self):
        return self.cb_show_all is not None and self.cb_show_all.isChecked()

    def __init__(self, scroll_widget, parent=None):
        self.cb_show_all = None
        super(UnrealAssetListContainerWidget, self).__init__(
            scroll_widget, parent=parent
        )

    def pre_build(self):
        super(UnrealAssetListContainerWidget, self).pre_build()
        self._header_widget = QtWidgets.QWidget()
        self._header_widget.setLayout(QtWidgets.QVBoxLayout())
        self._header_widget.layout().setContentsMargins(5, 0, 5, 0)
        self._header_widget.layout().setSpacing(0)

        label_widget = QtWidgets.QLabel('ftrack assets:')
        self._header_widget.layout().addWidget(label_widget)

        # Add filler to align
        self._header_widget.layout().addWidget(QtWidgets.QLabel(''))


class UnrealAssetManagerSnapshotListWidget(AssetManagerListWidget):
    '''Custom asset manager list view widget'''

    @property
    def show_all(self):
        return (
            self._asset_manager_widget.snapshot_asset_list_container.show_all
        )

    def __init__(
        self,
        asset_manager_widget,
        model,
        asset_widget_class,
        docked=False,
        parent=None,
    ):
        self._asset_manager_widget = asset_manager_widget
        super(UnrealAssetManagerSnapshotListWidget, self).__init__(
            model, asset_widget_class, docked=docked, parent=parent
        )

    def rebuild(
        self,
    ):
        '''Clear widget and add all assets again from model plus untracked dependencies'''
        asset_widgets = super(
            UnrealAssetManagerSnapshotListWidget, self
        ).rebuild(add=False)

        # Query level or all dependencies
        if self.show_all:
            # Fetch all assets in Unreal project
            assets = [
                os.path.splitext(ass)[0]
                for ass in unreal_utils.get_current_scene_objects()
            ]

        else:
            # Fetch from level
            level_path = str(
                unreal.EditorLevelLibrary.get_editor_world().get_path_name()
            )
            assets = unreal_utils.get_asset_dependencies(level_path)
            # Hide the tracked assets that are not part of level
            asset_widgets_remove = []
            for asset_widget in asset_widgets:
                found = False
                for asset_path in assets:
                    if asset_widget.asset_path.lower() == asset_path.lower():
                        found = True
                if not found:
                    asset_widgets_remove.append(asset_widget)
            for asset_widget in asset_widgets_remove:
                asset_widgets.remove(asset_widget)

        if len(assets) > 0:
            # Create and append to widgets
            for asset_path in assets:
                # Make sure it is not already an tracked asset
                tracked = False
                for asset_widget in asset_widgets:
                    if asset_widget.asset_path.lower() == asset_path.lower():
                        tracked = True
                        break
                if not tracked:
                    asset_widgets.append(
                        UntrackedUnrealAssetWidget(
                            asset_path, not self.show_all
                        )
                    )
        # Sort
        for asset_widget in sorted(
            asset_widgets, key=lambda aw: aw.asset_path
        ):
            self.add_widget(asset_widget)
        self.refresh()
        self.refreshed.emit()


class UnrealAssetWidget(AssetWidget):
    '''Widget representation of an Unreal asset(asset_info)'''

    @property
    def asset_path(self):
        return self._asset_path

    def set_asset_info(self, asset_info):
        '''(Override)'''
        version = super(UnrealAssetWidget, self).set_asset_info(asset_info)
        # Calculate Unreal path from its context
        parts = []
        for ab_name in reversed(
            [link['name'] for link in version['asset']['parent']['link']]
        ):
            if ab_name.lower() == 'content':
                break
            parts.insert(0, ab_name)
        self._asset_path = '/Game/{}'.format('/'.join(parts))


class UnrealSnapshotAssetWidget(UnrealAssetWidget):
    '''Unreal snapshot asset widget, adjust rendering with indentation'''

    # TODO: Color the widget blue if updated and needs to be published


class UntrackedUnrealAssetWidget(QtWidgets.QFrame):
    '''Widget representation of an Unreal asset(asset_info)'''

    @property
    def asset_path(self):
        return self._asset_path

    def __init__(self, asset_path, is_level_dependency, parent=None):
        super(UntrackedUnrealAssetWidget, self).__init__(parent=parent)
        self._asset_path = asset_path
        self._is_level_dependency = is_level_dependency
        self.pre_build()
        self.build()

    def pre_build(self):
        '''Prepare general layout.'''
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setContentsMargins(10, 1, 1, 1)
        self.layout().setSpacing(0)
        self.setToolTip(
            'Untracked {} asset: {}'.format(
                'level dependency'
                if self._is_level_dependency
                else 'unreal asset',
                self.asset_path,
            )
        )

    def build(self):
        content_directory = self.asset_path[: self.asset_path.rfind('/')]
        label_content_directory = QtWidgets.QLabel(content_directory)
        label_content_directory.setStyleSheet('font-size: 9px;')
        label_content_directory.setObjectName("gray-dark")
        self.layout().addWidget(label_content_directory)

        asset_name = self.asset_path[self.asset_path.rfind('/') + 1 :]
        label_content_name = QtWidgets.QLabel(asset_name)
        label_content_name.setObjectName('h4')
        self.layout().addWidget(label_content_name)
