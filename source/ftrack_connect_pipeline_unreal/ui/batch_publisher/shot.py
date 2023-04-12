# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import os
import clique

from functools import partial


import unreal

from Qt import QtCore, QtWidgets

from ftrack_connect_pipeline import constants as core_constants

from ftrack_connect_pipeline.definition.definition_object import (
    DefinitionObject,
)

from ftrack_connect_pipeline_qt.ui.utility.widget import (
    dialog,
    context_selector,
    line,
)

from ftrack_connect_pipeline_unreal.ui.batch_publisher.base import (
    UnrealBatchPublisherWidgetBase,
    UnrealItemWidgetBase,
    BatchPublisherListWidgetBase,
)
from ftrack_connect_pipeline_qt.utils import clear_layout, set_property

from ftrack_connect_pipeline_unreal import utils as unreal_utils


class UnrealShotPublisherWidget(UnrealBatchPublisherWidgetBase):
    def __init__(
        self,
        client,
        parent=None,
    ):
        super(UnrealShotPublisherWidget, self).__init__(client, parent=parent)

    @property
    def capture_folder(self):
        '''Return the capture folder'''
        return self._capture_folder_input.text()

    def build(self):
        '''(Override) Build the widget, add project context selector'''
        self.warn_missing_data = QtWidgets.QLabel()
        self.warn_missing_data.setObjectName('red')
        self.layout().addWidget(self.warn_missing_data)
        self.sequence_context_selector = None

        self.warn_missing_data.setText(
            '<html><i>Please select a master sequence containing shot tracks!</i></html>'
        )

        # Add sequence context selector
        self.root_context_label = QtWidgets.QLabel('Target sequence:')
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
        capture_folder_widget.layout().setContentsMargins(2, 2, 2, 2)
        capture_folder_widget.layout().setSpacing(2)

        capture_folder_widget.layout().addWidget(
            QtWidgets.QLabel('Capture folder:')
        )

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
            'shot output in its own folder. This will enable shot publisher to pick up media'
        )
        self.layout().addWidget(capture_folder_widget)

        self._file_selector = QtWidgets.QFileDialog()
        self._file_selector.setFileMode(QtWidgets.QFileDialog.Directory)

        self.layout().addWidget(capture_folder_widget)

        # Add publish options

        self._cb_update_shot_frame_ranges = QtWidgets.QCheckBox(
            'Update shot frame ranges'
        )
        self._cb_update_shot_frame_ranges.setChecked(True)
        self.layout().addWidget(self._cb_update_shot_frame_ranges)

        self.layout().addWidget(line.Line(style='solid'))

        super(UnrealShotPublisherWidget, self).build()

    def _update_info_label(self):
        '''(Override) Update info label'''
        if self.model.rowCount() == 0:
            self._label_info.setText('No shots(s)')
        else:
            self._label_info.setText(
                'Listing {} {}'.format(
                    self.model.rowCount(),
                    'shots' if self.model.rowCount() > 1 else 'shot',
                )
            )

    def post_build(self):
        '''(Override)'''
        super(UnrealShotPublisherWidget, self).post_build()
        if self.sequence_context_selector:
            self.sequence_context_selector.entityChanged.connect(
                self.on_sequence_context_changed
            )
        self._file_selector.fileSelected.connect(self._on_select_folder)
        self._browser_button.clicked.connect(self._show_file_dialog)

    def _show_file_dialog(self):
        '''Shows the file dialog'''
        if len(self.capture_folder) > 0:
            self._file_selector.setDirectory(self.capture_folder)
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
        '''Handle sequence change - store *context* with current Unreal project'''
        unreal_utils.set_sequence_context_id(context['id'])
        self.update_items(
            self.sequence_context_selector.context_id, self.capture_folder
        )

    def build_items(self, shot_tracks, definition):
        '''Build list of shots to publish based on *shot_tracks* and selected *definition*'''
        self.warn_missing_data.setVisible(False)
        result = []

        level_sequence = unreal_utils.get_selected_sequence()

        for shot_track in sorted(
            shot_tracks, key=lambda x: x.get_shot_display_name()
        ):
            # Build the publisher definition, clone the definition

            definition_fragment = DefinitionObject(definition.to_dict())

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
                plugin['options']['sequence_name'] = level_sequence.get_name()

            # Fill in collected media on update

            result.append((shot_track, definition_fragment, {}))

        # Store and present
        self.set_items(result, UnrealShotPublisherListWidgetBase)

    def update_items(self, sequence_context_id, capture_folder):
        '''(Override) Update list of items to publish based on *sequence_context_id* and *capture_folder*'''
        if self.item_list:
            for row, widget in enumerate(self.item_list.assets):
                index = self.model.createIndex(row, 0, self.model)
                widget.update_item(
                    self.model.data(index), sequence_context_id, capture_folder
                )

    def can_publish(self):
        '''(Override) Return true if there is anything to publish'''
        # Check that project context is set
        if self.sequence_context_selector.context_id is None:
            dialog.ModalDialog(
                self,
                message='Please set the sequence context!'.format(),
            )
            return False

        # Check if any shots are selected
        for widget in self.item_list.assets:
            if widget.checked:
                return True

        dialog.ModalDialog(
            self,
            message='No shot(s) selected!'.format(),
        )
        return False

    def prepare_run_definition(self, item):
        '''(Override) Called before *definition* is executed, injects asset and sequence data into definition'''

        # Raise batch publisher dialog as DCC might have come ontop of it
        self.client.activateWindow()

        # Make sure asset parent context exists and inject it into definition
        (shot_track, definition, metadata) = item

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
            if self._cb_update_shot_frame_ranges.isChecked():
                for key in ['start', 'end']:
                    if key in metadata:
                        plugin['options'][key] = metadata[key]

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


class UnrealShotPublisherListWidgetBase(BatchPublisherListWidgetBase):
    def __init__(self, batch_publisher_widget, parent=None):
        super(UnrealShotPublisherListWidgetBase, self).__init__(
            batch_publisher_widget, parent=parent
        )

    def rebuild(self):
        '''Add all shots from model to list, removing existing contents.'''
        clear_layout(self.layout())
        for row in range(self.model.rowCount()):
            index = self.model.createIndex(row, 0, self.model)

            (
                shot_track,
                definition,
                metadata,
            ) = self.model.data(index)

            # Build item widget
            item_widget = UnrealShotWidgetUnreal(
                index,
                self._batch_publisher_widget,
                self.model.event_manager,
            )
            set_property(
                item_widget,
                'first',
                'true' if row == 0 else 'false',
            )

            item_widget.set_data(shot_track, definition, metadata)
            self.add_widget(item_widget)

        self.layout().addWidget(QtWidgets.QLabel(), 1000)
        self.refreshed.emit()


class UnrealShotWidgetUnreal(UnrealItemWidgetBase):
    '''Unreal single shot widget to be used in shot publisher list widget'''

    def __init__(
        self,
        index,
        batch_publisher_widget,
        event_manager,
        parent=None,
    ):
        self._name = None
        super(UnrealShotWidgetUnreal, self).__init__(
            index,
            batch_publisher_widget,
            event_manager,
            parent=parent,
        )

    def get_ident_widget(self):
        '''Return the widget the presents the asset ident'''
        ident_container = QtWidgets.QWidget()
        ident_container.setLayout(QtWidgets.QHBoxLayout())
        ident_container.layout().setContentsMargins(0, 0, 0, 0)
        ident_container.layout().setSpacing(0)

        self._ident_widget_title = QtWidgets.QLabel()
        self._ident_widget_title.setObjectName('h4')
        ident_container.layout().addWidget(self._ident_widget_title)

        ident_container.layout().addWidget(QtWidgets.QLabel(), 100)

        self._ident_widget_frames = QtWidgets.QLabel()
        self._ident_widget_frames.setObjectName('gray')
        ident_container.layout().addWidget(self._ident_widget_frames)

        return ident_container

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
        metadata,
    ):
        '''(Override) Set data to be displayed in widget based on *shot_track*, *definition* and *metadata*'''
        self._widget_factory.batch_id = self.item_id

        # Get the shot name from the shot track
        self._name = shot_track.get_shot_display_name()

        self._start = shot_track.get_start_frame()
        self._end = shot_track.get_end_frame()

        self._ident_widget_title.setText('{}'.format(self._name))
        self._ident_widget_frames.setText(
            '[{}-{}]'.format(self._start, self._end)
        )
        super(UnrealShotWidgetUnreal, self).set_data(
            shot_track, definition, metadata
        )

    def get_ident(self):
        '''Return the asset name as human readable item ident'''
        return self._name

    def update_item(self, item_data, sequence_context_id, capture_folder):
        '''A *sequence_context_id* and *capture_folder* has been set, evaluate given the *item_data*'''

        (
            shot_track,
            definition,
            metadata,
        ) = item_data

        # Determine if can be published, e.g. media found
        if sequence_context_id is None:
            self.setToolTip('No sequence context selected')
            self.checkable = False
            return

        self.checkable = True
        media_found = False

        result = unreal_utils.find_rendered_media(
            capture_folder, shot_track.get_shot_display_name()
        )

        if result and isinstance(result, tuple):
            movie_path, sequence_path = result
            media_found = True

            tooltip = ''
            # Provide the media
            for d_component in definition.get_all(
                type=core_constants.COMPONENT
            ):
                if d_component['name'] in ['sequence', 'reviewable']:
                    for plugin in d_component.get_all(
                        type=core_constants.COLLECTOR,
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
                            if d_component['name'] == 'sequence':
                                plugin['options'][
                                    'image_sequence_path'
                                ] = target_media
                                tooltip += (
                                    'Publishing image sequence: {}<br>'.format(
                                        sequence_path
                                    )
                                )
                            else:
                                plugin['options']['movie_path'] = target_media
                                tooltip += 'Publishing reviewable movie: {}<br>'.format(
                                    movie_path
                                )
            if sequence_path:
                # Store start and end frame so we can update shot
                collection = clique.parse(sequence_path)
                start = list(collection.indexes)[0]
                end = list(collection.indexes)[-1]
                metadata['start'] = start
                metadata['end'] = end
            self.setToolTip('<html>{}</html>'.format(tooltip))

        self.checked = media_found
        if not media_found:
            self.setToolTip(
                result or 'Could not find an rendered media for shot'
            )

    def _store_options(self):
        '''(Override) Store options in metadata'''
        super(UnrealShotWidgetUnreal, self)._store_options()
        tooltip = ''
        # Update tooltip based on user input
        for d_component in self.factory.definition.get_all(
            type=core_constants.COMPONENT
        ):
            if d_component['name'] in ['sequence', 'reviewable']:
                for plugin in d_component.get_all(
                    type=core_constants.COLLECTOR,
                    category=core_constants.PLUGIN,
                ):
                    if 'options' in plugin:
                        has_media = False
                        if (
                            d_component['name'] == 'sequence'
                            and len(
                                plugin['options'].get('image_sequence_path')
                                or ''
                            )
                            > 0
                        ):
                            tooltip += (
                                'Publishing image sequence: {}<br>'.format(
                                    plugin['options']['image_sequence_path']
                                )
                            )
                            has_media = True
                        elif (
                            d_component['name'] == 'reviewable'
                            and len(plugin['options'].get('movie_path') or '')
                            > 0
                        ):
                            tooltip += (
                                'Publishing reviewable movie: {}<br>'.format(
                                    plugin['options']['movie_path']
                                )
                            )
                            has_media = True
                        plugin['enabled'] = has_media
                        self.checked = has_media
        if tooltip == '':
            tooltip = 'Could not find an rendered media for shot'
        self.setToolTip('<html>{}</html>'.format(tooltip))

    def run_callback(self, item_widget, event):
        '''(Override) Executed after an item has been publisher through event from pipeline'''
        pass
