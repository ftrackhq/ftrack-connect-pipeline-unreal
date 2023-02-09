# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import copy
import os
from functools import partial
import json

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

from ftrack_connect_pipeline_unreal.constants import asset as asset_const
from ftrack_connect_pipeline_unreal.utils import (
    custom_commands as unreal_utils,
)
import tempfile


class UnrealAssetBatchPublisherWidget(BatchPublisherBaseWidget):
    @property
    def parent_asset_version_id(self):
        '''Return parent asset version id'''
        return self._parent_asset_version_id

    @parent_asset_version_id.setter
    def parent_asset_version_id(self, value):
        '''Set the parent asset version id'''
        self._parent_asset_version_id = value

    @property
    def parent_asset(self):
        '''Return parent asset'''
        return self._parent_asset

    @parent_asset.setter
    def parent_asset(self, value):
        '''Set the parent asset'''
        self._parent_asset = value

    def __init__(
        self,
        client,
        initial_items,
        parent_asset_version_id=None,
        parent_asset=None,
        level=None,
        parent=None,
    ):
        self._parent_asset_version_id = parent_asset_version_id
        self._parent_asset = parent_asset
        self.dependencies_published = False
        super(UnrealAssetBatchPublisherWidget, self).__init__(
            client, initial_items, level=level, parent=parent
        )

    @property
    def initial_asset_paths(self):
        '''Return the list of initial Unreal asset paths passed to batch publisher widget from client'''
        return self.initial_items

    def build(self):
        '''(Override) Build the widget, add project context selector'''
        self.warn_missing_definition_label = QtWidgets.QLabel()
        self.layout().addWidget(self.warn_missing_definition_label)
        self.root_context_selector = None
        if self.level == 0:
            self.warn_missing_definition_label.setText(
                '<html><i>Could not locate asset publisher definition, please check configuration!</i></html>'
            )
            self.root_context_label = QtWidgets.QLabel('Root context:')
            self.root_context_label.setObjectName('gray')
            self.layout().addWidget(self.root_context_label)
            self.root_context_selector = context_selector.ContextSelector(
                self.session, enble_context_change=True, select_task=False
            )
            self.layout().addWidget(self.root_context_selector)
            self.layout().addWidget(line.Line(style='solid'))
        super(UnrealAssetBatchPublisherWidget, self).build()

    def _update_info_label(self):
        '''(Override) Update info label'''
        if self.model.rowCount() == 0:
            self._label_info.setText('No asset(s)')
        elif self.level == 0:
            self._label_info.setText(
                'Listing {} {}'.format(
                    self.model.rowCount(),
                    'assets' if self.model.rowCount() > 1 else 'asset',
                )
            )
        else:
            self._label_info.setText(
                '{} {}'.format(
                    self.model.rowCount(),
                    'dependency'
                    if self.model.rowCount() == 1
                    else 'dependencies',
                )
            )

    def post_build(self):
        super(UnrealAssetBatchPublisherWidget, self).post_build()
        if self.root_context_selector:
            self.root_context_selector.entityChanged.connect(
                self.on_root_context_changed
            )

    def on_context_changed(self, context_id):
        '''(Override)Handle context change, propose default project context and populate project context selector'''
        if not self.root_context_selector:
            return
        context = self.session.query(
            'Context where id is "{}"'.format(context_id)
        ).one()
        default_root_context_id = context.get('project_id')
        self.root_context_selector.browse_context_id = default_root_context_id
        root_context_id = unreal_utils.get_root_context_id()
        self.root_context_selector.context_id = root_context_id
        self.update_items(self.root_context_selector.context_id)

    def on_root_context_changed(self, context):
        '''Handle context change - store it with current Unreal project'''
        unreal_utils.set_root_context_id(context['id'])
        self.update_items(self.root_context_selector.context_id)

    def build_items(self, definition):
        '''Build list of items (assets) to publish based on selected *definition*'''
        self.warn_missing_definition_label.setVisible(False)
        result = []
        unrecognizeable_assets = []

        root_content_dir = (
            unreal.SystemLibrary.get_project_content_directory().replace(
                '/', os.sep
            )
        )

        for asset_path in sorted(self.initial_asset_paths):
            # Already processed?
            if not self.client.check_add_processed_items(asset_path):
                # Prevent duplicates and infinite loops
                continue
            # Locate the asset info file and data
            dcc_object_name, param_dict = unreal_utils.get_asset_info(
                asset_path, snapshot=True
            )

            # Check asset, if it exists on disk and is an uasset
            try:
                filesystem_asset_path = (
                    unreal_utils.asset_path_to_filesystem_path(
                        asset_path, root_content_dir=root_content_dir
                    )
                )
            except Exception as e:
                self.logger.exception(e)

                unrecognizeable_assets.append(asset_path)
                continue

            if not filesystem_asset_path.endswith('.uasset'):
                unrecognizeable_assets.append(filesystem_asset_path)
                continue

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

            dependencies = []

            # Collect and store asset path
            for plugin in definition_fragment.get_all(
                type=core_constants.COLLECTOR,
                category=core_constants.PLUGIN,
            ):
                if not 'options' in plugin:
                    plugin['options'] = {}

                if not 'dependencies' in plugin['name']:
                    plugin['options']['collected_objects'] = [asset_path]
                else:
                    # Resolve dependencies
                    dependencies = unreal_utils.get_asset_dependencies(
                        asset_path
                    )
                    plugin['options']['collected_objects'] = dependencies

            # Make sure sub dependencies are published in non interactive mode
            for plugin in definition_fragment.get_all(
                plugin='unreal_dependencies_publisher_post_finalizer',
            ):
                if not 'options' in plugin:
                    plugin['options'] = {}
                plugin['options']['interactive'] = False

            # Make sure dependencies are tracked in local unreal project
            for plugin in definition_fragment.get_all(
                plugin='unreal_dependency_track_publisher_post_finalizer',
            ):
                plugin['enabled'] = True

            result.append(
                (
                    asset_path,
                    filesystem_asset_path,
                    definition_fragment,
                    dependencies,
                    dcc_object_name,
                    param_dict,
                )
            )

        if len(unrecognizeable_assets) > 0:
            dialog.ModalDialog(
                self,
                message='Can not publish the following asset as they are not found on disk or is compatible with the chosen definition:\n\n{}'.format(
                    '\n'.join(unrecognizeable_assets)
                ),
            )

        # Store and present
        self.set_items(result, UnrealBatchPublisherAssetListWidget)

    def update_items(self, root_context_id):
        '''(Override) Update list of items to publish'''
        if self.item_list:
            for widget in self.item_list.assets:
                widget.update_item(root_context_id)

    def can_publish(self):
        '''(Override) Check if we can publish'''
        # Check that project context is set
        if self.root_context_selector.context_id is None:
            dialog.ModalDialog(
                self,
                message='Please set the Unreal root context!'.format(),
            )
            return False
        # Check if any assets are selected
        for widget in self.item_list.assets:
            if widget.checked:
                return True

        dialog.ModalDialog(
            self,
            message='No asset(s) selected!'.format(),
        )
        return False

    def prepare_run_definition(self, item):
        '''(Override) Called before *definition* is executed.'''

        # Raise batch publisher dialog as DCC might have come ontop of it
        self.client.activateWindow()

        # Make sure asset parent context exists and inject it into definition
        (
            asset_path,
            filesystem_asset_path,
            definition,
            dependencies,
            dcc_object_name,
            param_dict,
        ) = item

        root_context_id = unreal_utils.get_root_context_id()

        asset_name = os.path.splitext(os.path.basename(asset_path))[0]

        # Get the full ftrack asset path
        full_ftrack_asset_path = unreal_utils.get_full_ftrack_asset_path(
            root_context_id, asset_path, session=self.session
        )

        # Create the asset build, so we can find and supply the asset
        asset_build = unreal_utils.push_asset_build_to_server(
            root_context_id, full_ftrack_asset_path, self.session
        )

        # Determine status
        project = self.session.query(
            'Project where id="{}"'.format(asset_build['project_id'])
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
                asset_build['id'], asset_name
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
            plugin['options']['root_context_id'] = root_context_id
            plugin['options']['asset_parent_context_id'] = asset_build['id']
            plugin['options']['ftrack_asset_path'] = full_ftrack_asset_path
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
        if self.parent_asset_version_id:
            # Check if all items have been published
            all_published = True
            for item_widget in self.item_list.checked(as_widgets=True):
                if not item_widget.has_run:
                    # Still has more to go
                    all_published = False
                    break
            if all_published:
                self.logger.info('All assets have been published')
                self.publish_dependencies()
        else:
            self.logger.debug(
                'Not able to track dependencies, no published version id stored for "{}"'.format(
                    self.parent_asset
                )
            )

    def publish_dependencies(self):
        '''Publish dependencies for all items'''
        all_items = self.item_list.items()
        self.logger.info(
            'Tracking {} dependencies as list of asset infos on "{}"'.format(
                len(all_items), self.parent_asset
            )
        )
        asset_infos = []
        # Collect asset infos from all items
        for item, item_widget in all_items:
            # Expand
            (
                asset_path,
                filesystem_asset_path,
                definition,
                dependencies,
                dcc_object_name,
                param_dict,
            ) = item
            if item_widget.checked:
                # This asset has been published, fetch its asset info
                (
                    unused_dcc_object_name,
                    asset_info,
                ) = unreal_utils.get_asset_info(asset_path, snapshot=True)
            else:
                # Use the previously stored asset info, if any
                asset_info = param_dict
            if asset_info is not None:
                asset_infos.append(asset_info)
        if len(asset_infos) > 0:
            asset_version = self.session.query(
                'AssetVersion where id is "{0}"'.format(
                    self.parent_asset_version_id
                )
            ).one()
            component_path = tempfile.NamedTemporaryFile(suffix='.json').name

            metadata = {'dependencies': asset_infos}
            with open(component_path, 'w') as f:
                json.dump(metadata, f)

            self.logger.debug('Metadata to store @ "{}"!'.format(metadata))
            location = self.session.pick_location()
            asset_version.create_component(
                component_path,
                data={'name': 'dependencies'},
                location=location,
            )
            self.session.commit()
        else:
            self.logger.debug(
                'No dependency asset infos to track for "{}"'.format(
                    self.parent_asset
                )
            )
        self.dependencies_published = True


class UnrealBatchPublisherAssetListWidget(BatchPublisherListBaseWidget):
    def __init__(self, batch_publisher_widget, parent=None):
        super(UnrealBatchPublisherAssetListWidget, self).__init__(
            batch_publisher_widget, UnrealAssetWidget, parent=parent
        )

    def rebuild(self):
        '''Add all assets(components) again from model.'''
        clear_layout(self.layout())
        for row in range(self.model.rowCount()):
            index = self.model.createIndex(row, 0, self.model)

            (
                asset_path,
                filesystem_asset_path,
                definition,
                dependencies,
                dcc_object_name,
                param_dict,
            ) = self.model.data(index)

            # Build item widget
            item_widget = self.item_widget_class(
                index,
                self._batch_publisher_widget,
                dependencies,
                self.model.event_manager,
            )
            set_property(
                item_widget,
                'first',
                'true' if row == 0 else 'false',
            )

            item_widget.set_data(
                asset_path,
                filesystem_asset_path,
                definition,
                dependencies,
                dcc_object_name,
                param_dict,
            )
            self.layout().addWidget(item_widget)
            item_widget.clicked.connect(
                partial(self.item_clicked, item_widget)
            )

        self.layout().addWidget(QtWidgets.QLabel(), 1000)
        self.refreshed.emit()

    def item_clicked(self, event, item_widget):
        pass


class UnrealAssetWidget(ItemBaseWidget):
    '''Unreal asset widget to be used in batch publisher list widget'''

    @property
    def dependencies(self):
        '''Return list of dependency asset paths'''
        return self._dependencies

    @property
    def dependencies_batch_publisher_widget(self):
        '''Returns the batch publisher widget that manages the depenedencies'''
        return self._dependencies_batch_publisher_widget

    def __init__(
        self,
        index,
        batch_publisher_widget,
        dependencies,
        event_manager,
        parent=None,
    ):
        self._dependencies = dependencies or []
        self._dependencies_batch_publisher_widget = None
        self._asset_path = None
        super(UnrealAssetWidget, self).__init__(
            index,
            batch_publisher_widget,
            event_manager,
            collapsable=len(dependencies) > 0,
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
        if len(self.dependencies) > 0:
            # Create a batch publisher widget for content and populate it
            level = self.level + 1
            self._dependencies_batch_publisher_widget = (
                UnrealAssetBatchPublisherWidget(
                    self.batch_publisher_widget.client,
                    self.dependencies,
                    level=level,
                )
            )
            self.content.layout().setContentsMargins(2 + (10 * level), 2, 2, 2)
            self.add_widget(self._dependencies_batch_publisher_widget)
            self.content.layout().addStretch()

    def set_data(
        self,
        asset_path,
        asset_filesystem_path,
        definition,
        dependencies,
        dcc_object_name,
        param_dict,
    ):
        '''(Override) Set data to be displayed in widget'''
        self._asset_path = asset_path
        self._ident_widget.setText(str(asset_path))
        super(UnrealAssetWidget, self).set_data(definition)
        if self._dependencies_batch_publisher_widget:
            self._dependencies_batch_publisher_widget.parent_asset = asset_path
            self._dependencies_batch_publisher_widget.build_items(definition)
        self._widget_factory.batch_id = self.item_id
        # Determine if needs publish
        do_publish = True
        if dcc_object_name is not None:
            do_publish = False
            # Check if the asset has changed since last publish
            if os.path.exists(asset_filesystem_path):
                mod_date = os.path.getmtime(asset_filesystem_path)
                if mod_date != param_dict.get(asset_const.MOD_DATE):
                    do_publish = True

        self.checked = do_publish
        if not do_publish:
            self.setToolTip(
                'Asset is up to date and has not changed since last publish'
            )
        elif dcc_object_name is not None:
            self.info_message = '<html><i>Asset has been modified since last publish</i></html>'

    def get_ident(self):
        '''Return the asset name as human readable item ident'''
        return self._asset_path.split('/')[-1] if self._asset_path else '?'

    def update_item(self, root_context_id):
        '''A project context has been set, store with dependencies'''
        if len(self.dependencies) > 0:
            self._dependencies_batch_publisher_widget.update_items(
                root_context_id
            )

    def run(self):
        '''(Override)'''
        # Recursively add dependencies to progress widget and queue up
        if self.dependencies_batch_publisher_widget is not None:
            self.dependencies_batch_publisher_widget.run()

    def summarise(self):
        '''(Override)'''
        total = 0
        succeeded = 0
        failed = 0
        if self.dependencies_batch_publisher_widget:
            (
                _total,
                _succeeded,
                _failed,
            ) = self.dependencies_batch_publisher_widget.run_post()
            total += _total
            succeeded += _succeeded
            failed += _failed
        return total, succeeded, failed

    def run_callback(self, item_widget, event):
        '''(Override) Executed after an item has been publisher through event from pipeline,
        enable dependency asset info storage.'''
        # Check for post finalizer data in event

        # TODO: Extract asset info and store with item

        user_data = asset_version_id = None
        for step in event.get('data', []):
            for stage in step.get('result', []):
                if stage.get('name') == 'finalizer':
                    for plugin in stage.get('result', []):
                        if 'asset_version_id' in plugin['result']:
                            asset_version_id = plugin['result'][
                                'asset_version_id'
                            ]
                            break
                elif stage.get('name') == 'post_finalizer':
                    for plugin in stage.get('result', []):
                        if (
                            plugin.get('name')
                            == 'unreal_dependencies_publisher_post_finalizer'
                        ):
                            if 'data' in plugin.get('user_data', {}):
                                user_data = plugin['user_data']['data']
                                break
        if user_data:
            # Store in widget for later use
            self.finalizer_user_data = user_data
        else:
            self.logger.info('No dependency data found in event payload!')

        if asset_version_id:
            if self.dependencies_batch_publisher_widget:
                self.dependencies_batch_publisher_widget.parent_asset_version_id = (
                    asset_version_id
                )
        else:
            self.logger.warning(
                'No asset version data found in event payload!'
            )
        self.logger.debug(
            'Stored post finalized data for "{}": user data: {}, asset version id: {}'.format(
                self.get_ident(), user_data, asset_version_id
            )
        )
