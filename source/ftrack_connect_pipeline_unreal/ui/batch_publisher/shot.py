# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import copy
import os
from functools import partial


import unreal

from Qt import QtCore, QtWidgets

from ftrack_connect_pipeline import constants as core_constants

from ftrack_connect_pipeline.definition.definition_object import (
    DefinitionObject,
    DefinitionList,
)

from ftrack_connect_pipeline_qt.ui.utility.widget import (
    dialog,
    context_selector,
    line,
)

from ftrack_connect_pipeline_qt.ui.batch_publisher.base import (
    BatchPublisherBaseWidget,
    ItemBaseWidget,
    BatchPublisherListBaseWidget,
)
from ftrack_connect_pipeline_qt.utils import clear_layout, set_property

from ftrack_connect_pipeline_unreal.utils import (
    custom_commands as unreal_utils,
)


class UnrealShotBatchPublisherWidget(BatchPublisherBaseWidget):
    def __init__(
        self,
        client,
        shot_tracks,
        parent_asset_version_id=None,
        parent_asset=None,
        level=None,
        parent=None,
    ):
        self._parent_asset_version_id = parent_asset_version_id
        self._parent_asset = parent_asset
        super(UnrealShotBatchPublisherWidget, self).__init__(
            client, shot_tracks, level=level, parent=parent
        )

    @property
    def shot_tracks(self):
        '''Return the list of initial Unreal asset paths passed to batch publisher widget from client'''
        return self.initial_items

    @property
    def capture_folder(self):
        return self._capture_folder_input.text()

    def build(self):
        '''(Override) Build the widget, add project context selector'''
        self.warn_missing_definition_label = QtWidgets.QLabel()
        self.layout().addWidget(self.warn_missing_definition_label)
        self.sequence_context_selector = None
        if self.level == 0:
            self.warn_missing_definition_label.setText(
                '<html><i>Could not locate shot publisher definition, please check configuration!</i></html>'
            )

            # Add sequence context selector
            self.root_context_label = QtWidgets.QLabel('Sequence context:')
            self.root_context_label.setObjectName('gray')
            self.layout().addWidget(self.root_context_label)
            self.sequence_context_selector = context_selector.ContextSelector(
                self.session, enble_context_change=True, select_task=False
            )
            self.layout().addWidget(self.sequence_context_selector)
            self.layout().addWidget(line.Line(style='solid'))

            # Add capture folder input
            capture_folder_widget = QtWidgets.QWidget()
            capture_folder_widget.setLayout(QtWidgets.QHBoxLayout())
            capture_folder_widget.layout().setContentsMargins(0, 0, 0, 0)
            capture_folder_widget.layout().setSpacing(0)

            capture_folder_widget.layout().addWidget(
                QtWidgets.QLabel('Capture folder:')
            )

            # TODO: Store video capture output folder in Unreal project
            default_capture_folder = os.path.realpath(
                os.path.join(
                    unreal.SystemLibrary.get_project_saved_directory(),
                    "VideoCaptures",
                )
            )
            self._capture_folder_input = QtWidgets.QLineEdit(
                default_capture_folder
            )
            self._capture_folder_input.setReadOnly(True)

            capture_folder_widget.layout().addWidget(
                self._capture_folder_input, 20
            )

            self._browser_button = QtWidgets.QPushButton('BROWSE')
            self._browser_button.setObjectName('borderless')

            capture_folder_widget.layout().addWidget(self._browser_button)

            capture_folder_widget.setToolTip(
                'Render shots to this folder, using the {shot}\\ syntax at end of path to have each '
                'shot output in its own folder, to enable shot publisher to pick up media'
            )
            self.layout().addWidget(capture_folder_widget)

            self._file_selector = QtWidgets.QFileDialog()
            self._file_selector.setFileMode(QtWidgets.QFileDialog.Directory)

            self.layout().addWidget(capture_folder_widget)

        super(UnrealShotBatchPublisherWidget, self).build()

    def post_build(self):
        super(UnrealShotBatchPublisherWidget, self).post_build()
        if self.sequence_context_selector:
            self.sequence_context_selector.entityChanged.connect(
                self.on_sequence_context_changed
            )
        self._file_selector.fileSelected.connect(self._on_select_folder)
        self._browser_button.clicked.connect(self._show_file_dialog)

    def _show_file_dialog(self):
        '''Shows the file dialog'''
        self._file_selector.show()

    def _on_select_folder(self, path):
        '''Updates the text with provided *path* when
        fileSelected of file_selector event is triggered'''
        self._capture_folder_input.setText(path)
        self.update_items(
            self.sequence_context_selector.context_id, self.capture_folder
        )

    def on_context_changed(self, context_id):
        '''(Override)Handle context change, propose default project context and populate project context selector'''
        if not self.sequence_context_selector:
            return
        context = self.session.query(
            'Context where id is "{}"'.format(context_id)
        ).one()
        default_root_context_id = context.get('project_id')
        self.sequence_context_selector.browse_context_id = (
            default_root_context_id
        )
        sequence_context_id = unreal_utils.get_sequence_context_id()
        self.sequence_context_selector.context_id = sequence_context_id
        self.update_items(
            self.sequence_context_selector.context_id, self.capture_folder
        )

    def on_sequence_context_changed(self, context):
        '''Handle context change - store it with current Unreal project'''
        unreal_utils.set_sequence_context_id(context['id'])
        self.update_items(
            self.sequence_context_selector.context_id, self.capture_folder
        )

    def build_items(self, definition):
        '''Build list of items (assets) to publish based on selected *definition*'''
        self.warn_missing_definition_label.setVisible(False)
        result = []

        for shot_track in sorted(self.shot_tracks):

            # Build the publisher definition
            definition_fragment = None
            for d_component in definition.get_all(
                type=core_constants.COMPONENT
            ):
                # Pick the first component encountered
                component_name_effective = d_component['name']

                # Construct definition fragment
                definition_fragment = DefinitionObject({})
                for key in definition:
                    if key == core_constants.COMPONENTS:
                        definition_fragment[key] = DefinitionList(
                            [DefinitionObject(d_component.to_dict())]
                        )
                        definition_fragment.get_first(
                            type=core_constants.COMPONENT
                        )['name'] = component_name_effective
                    else:
                        # Copy the category
                        definition_fragment[key] = copy.deepcopy(
                            definition[key]
                        )
                break

            if not definition_fragment:
                dialog.ModalDialog(
                    self,
                    message='{} publisher does not contain any usable component!'.format(
                        definition['name']
                    ),
                )
                return

            level_sequence = unreal_utils.get_selected_sequence()

            # Collect and provide the selected sequence
            for plugin in definition_fragment.get_all(
                type=core_constants.COLLECTOR,
                category=core_constants.PLUGIN,
            ):
                if not 'options' in plugin:
                    plugin['options'] = {}

                plugin['options']['collected_objects'] = [
                    level_sequence.get_name()
                ]

            # Fill in collected media on update

            result.append(
                (
                    shot_track,
                    definition_fragment,
                )
            )

        # Store and present
        self.set_items(result, UnrealBatchPublisherShotListWidget)

    def update_items(self, sequence_context_id, capture_folder):
        '''(Override) Update list of items to publish'''
        if self.item_list:
            for row, widget in enumerate(self.item_list.assets):
                index = self.model.createIndex(row, 0, self.model)
                widget.update_item(
                    self.model.data(index), sequence_context_id, capture_folder
                )

    def prepare_run_definition(self, item):
        '''(Override) Called before *definition* is executed.'''

        # Raise batch publisher dialog as DCC might have come ontop of it
        self.client.activateWindow()

        # Make sure asset parent context exists and inject it into definition
        (
            shot_track,
            definition,
        ) = item

        sequence_context_id = unreal_utils.get_sequence_context_id()
        shot_name = shot_track.get_shot_display_name()

        asset_name = definition['asset_type']

        # Create the shot if it does not already exist
        shot = unreal_utils.push_shot_to_server(
            sequence_context_id, shot_name, self.session
        )

        # Determine status
        project = self.session.query(
            'Project where id="{}"'.format(shot['project_id'])
        ).one()
        schema = project['project_schema']
        preferred_status = any_status = None
        for status in schema.get_statuses('AssetVersion'):
            any_status = status
            if status['name'].lower() in ['approved', 'completed']:
                preferred_status = status
                break

        # Find existing asset
        asset = self.session.query(
            'Asset where parent.id is "{}" and name is "{}"'.format(
                shot['id'], asset_name
            )
        ).first()

        asset_id = None
        if asset:
            asset_id = asset['id']
        # Inject context ident
        for plugin in definition.get_all(
            type=core_constants.CONTEXT,
            category=core_constants.PLUGIN,
        ):
            if not 'options' in plugin:
                plugin['options'] = {}
            # Store context data
            plugin['options']['context_id'] = self.client.context_id
            plugin['options']['sequence_context_id'] = sequence_context_id
            plugin['options']['shot_name'] = shot_name
            if asset_id:
                plugin['options']['asset_id'] = asset_id
            plugin['options']['asset_name'] = asset_name
            if any_status:
                plugin['options']['status_id'] = (
                    preferred_status['id']
                    if preferred_status
                    else any_status['id']
                )
            plugin['options']['is_valid_name'] = True
            break
        return definition

    def _on_item_published(self, item_widget):
        '''(Override) Executed when an item has been published'''
        pass


class UnrealBatchPublisherShotListWidget(BatchPublisherListBaseWidget):
    def __init__(self, batch_publisher_widget, parent=None):
        super(UnrealBatchPublisherShotListWidget, self).__init__(
            batch_publisher_widget, UnrealShotWidget, parent=parent
        )

    def rebuild(self):
        '''Add all shot tracks again from model.'''
        clear_layout(self.layout())
        for row in range(self.model.rowCount()):
            index = self.model.createIndex(row, 0, self.model)

            (
                shot_track,
                definition,
            ) = self.model.data(index)

            # Build item widget
            item_widget = self.item_widget_class(
                index,
                self._batch_publisher_widget,
                self.model.event_manager,
            )
            set_property(
                item_widget,
                'first',
                'true' if row == 0 else 'false',
            )

            item_widget.set_data(shot_track, definition)
            self.layout().addWidget(item_widget)
            item_widget.clicked.connect(
                partial(self.item_clicked, item_widget)
            )

        self.layout().addWidget(QtWidgets.QLabel(), 1000)
        self.refreshed.emit()

    def item_clicked(self, event, item_widget):
        pass


class UnrealShotWidget(ItemBaseWidget):
    '''Unreal asset widget to be used in batch publisher list widget'''

    def __init__(
        self,
        index,
        batch_publisher_widget,
        event_manager,
        parent=None,
    ):
        self._dependencies_batch_publisher_widget = None
        self._asset_path = None
        super(UnrealShotWidget, self).__init__(
            index,
            batch_publisher_widget,
            event_manager,
            collapsable=False,
            parent=parent,
        )

    def get_ident_widget(self):
        '''Return the widget the presents the asset ident'''
        self._ident_widget = QtWidgets.QLabel()
        return self._ident_widget

    def get_context_widget(self):
        '''Return the widget the presents the context selection'''
        self._context_widget = QtWidgets.QWidget()
        return self._context_widget

    def init_content(self, content_layout):
        '''(Override) Build the widget content'''
        pass

    def set_data(
        self,
        shot_track,
        definition,
    ):
        '''(Override) Set data to be displayed in widget'''

        # Get the shot name from the shot track
        self._name = shot_track.get_shot_display_name()

        self._start = shot_track.get_start_frame()
        self._end = shot_track.get_end_frame()

        self._ident_widget.setText(
            '{} [{}-{}]'.format(self._name, self._start, self._end)
        )
        super(UnrealShotWidget, self).set_data(definition)

    def get_ident(self):
        '''Return the asset name as human readable item ident'''
        return self._asset_path.split('/')[-1] if self._asset_path else '?'

    def update_item(self, item_data, sequence_context_id, capture_folder):
        '''A *sequence_context_id* and *capture_folder* has been set, evaluate'''

        (
            shot_track,
            definition,
        ) = item_data

        # Determine if can be published, e.g. media found
        media_found = False

        result = unreal_utils.find_rendered_media(
            capture_folder, shot_track.get_shot_display_name()
        )

        if result and isinstance(result, tuple):
            sequence_path, movie_path = result
            media_found = True

            tooltip = ''
            # Provide the media
            for d_component in definition.get_all(
                type=core_constants.COMPONENT
            ):
                if d_component['name'] in ['sequence', 'reviewable']:
                    for plugin in d_component.get_all(
                        type=core_constants.EXPORTER,
                        category=core_constants.PLUGIN,
                    ):
                        target_media = (
                            sequence_path
                            if d_component['name'] == 'sequence'
                            else movie_path
                        )
                        plugin['enabled'] = target_media is not None
                        if target_media:
                            if not 'options' in plugin:
                                plugin['options'] = {}
                            plugin['options']['mode'] = 'pickup'
                            plugin['options']['file_path'] = target_media
                            if sequence_path:
                                tooltip += 'Using image sequence: {}'.format(
                                    sequence_path
                                )
                            else:
                                tooltip += 'Using reviewable movie: {}'.format(
                                    movie_path
                                )

        self.set_checked(media_found)
        if not media_found:
            self.setToolTip(
                result or 'Could not find an rendered media for shot'
            )

    def run_callback(self, item_widget, event):
        '''(Override) Executed after an item has been publisher through event from pipeline'''
        pass
