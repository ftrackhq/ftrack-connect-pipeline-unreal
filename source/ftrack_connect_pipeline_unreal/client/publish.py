# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack
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

from ftrack_connect_pipeline_qt.client.publish import QtPublisherClientWidget
from ftrack_connect_pipeline_qt.client.publish.batch import (
    QtBatchPublisherClientWidget,
)
from ftrack_connect_pipeline_qt.ui.utility.widget import (
    dialog,
    context_selector,
    definition_selector,
    line,
)
import ftrack_connect_pipeline_qt.constants as qt_constants
from ftrack_connect_pipeline_qt.ui.batch_publisher.base import (
    BatchPublisherBaseWidget,
    ItemBaseWidget,
    BatchPublisherListBaseWidget,
)
from ftrack_connect_pipeline_qt.utils import clear_layout, set_property

import ftrack_connect_pipeline_unreal.constants as unreal_constants
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
        self.resize(350, 800)

    def get_theme_background_style(self):
        return 'unreal'


class UnrealQtBatchPublisherClientWidget(QtBatchPublisherClientWidget):
    '''Unreal multiple versions publisher widget'''

    def __init__(
        self,
        event_manager,
        assets,
        parent_asset_version_id=None,
        title=None,
        immediate_run=False,
        parent=None,
    ):
        self._assets = assets
        self._parent_asset_version_id = parent_asset_version_id
        super(UnrealQtBatchPublisherClientWidget, self).__init__(
            event_manager,
            title=title,
            immediate_run=immediate_run,
            parent=parent,
        )
        self.setWindowTitle(title or 'ftrack Unreal Asset Publisher')

    def _build_definition_selector(self):
        return definition_selector.BatchDefinitionSelector(
            definition_title_filter_expression='^Asset Publisher$'
        )

    def _build_batch_publisher_widget(self):
        return UnrealBatchPublisherWidget(self)

    def _get_list_widget_class(self):
        return UnrealAssetListWidget

    def _build_items(self, definition):
        '''Build list of items (assets) to publish, exclude assets that have not changed
        since last publish'''
        self.batch_publisher_widget.warn_missing_definition_label.setVisible(
            False
        )
        result = []
        unrecognizeable_assets = []

        root_content_dir = (
            unreal.SystemLibrary.get_project_content_directory().replace(
                '/', os.sep
            )
        )

        for asset_path in sorted(self._assets):
            # Locate the asset info
            do_publish = False
            param_dict = None
            dcc_object_name, param_dict = unreal_utils.get_asset_info(
                asset_path
            )

            # Check asset, if it exists on disk and is an uasset
            try:
                absolute_asset_path = unreal_utils.determine_extension(
                    os.path.join(
                        root_content_dir,
                        asset_path.replace('/Game/', '').replace('/', os.sep),
                    )
                )
            except Exception as e:
                self.logger.exception(e)
                import traceback

                print('@@@ exc: "{}"'.format(traceback.format_exc()))
                unrecognizeable_assets.append(asset_path)
                continue

            if not absolute_asset_path.endswith('.uasset'):
                print(
                    '@@@ absolute_asset_path: "{}"'.format(absolute_asset_path)
                )
                unrecognizeable_assets.append(absolute_asset_path)
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

            # Collect and store asset path
            for plugin in definition_fragment.get_all(
                type=core_constants.COLLECTOR,
                category=core_constants.PLUGIN,
            ):
                if not 'options' in plugin:
                    plugin['options'] = {}

                plugin['options']['collected_objects'] = [asset_path]
                # Append dependencies
                plugin['options']['collected_objects'].extend(
                    unreal_utils.get_asset_dependencies(asset_path)
                )

            # Make sure sub dependencies are published in non interactive mode
            for plugin in definition_fragment.get_all(
                type=core_constants.PLUGIN_PUBLISHER_POST_FINALIZER_TYPE,
                category=core_constants.PLUGIN,
            ):
                if not 'options' in plugin:
                    plugin['options'] = {}
                plugin['options']['interactive'] = False

            result.append(
                (asset_path, definition_fragment, dcc_object_name, param_dict)
            )
        if len(unrecognizeable_assets) > 0:
            dialog.ModalDialog(
                self,
                message='Can not publish the following asset as they are not compatible with the chosen definition:\n\n{}'.format(
                    '\n'.join(unrecognizeable_assets)
                ),
            )

        return result

    def prepare_run_definition(self, item):
        '''(Override) Called before *definition* is executed.'''
        # Make sure asset parent context exists and inject it into definition
        (asset_path, definition, dcc_object_name, param_dict) = item

        project_context_id = unreal_utils.get_project_level_context()

        asset_name = os.path.splitext(os.path.basename(asset_path))[0]

        # Create the asset build
        asset_build = unreal_utils.ensure_asset_build(
            project_context_id, asset_path
        )

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
            project_context_id = self.batch_publisher_widget.project_context_id
            plugin['options']['context_id'] = self.context_id
            plugin['options']['project_context_id'] = project_context_id
            plugin['options']['asset_parent_context_id'] = asset_build['id']
            if asset_id:
                plugin['options']['asset_id'] = asset_id
            else:
                plugin['options']['asset_name'] = asset_name
            plugin['options']['is_valid_name'] = True

        return definition


class UnrealBatchPublisherWidget(BatchPublisherBaseWidget):
    @property
    def project_context_id(self):
        return self._project_context_selector.context_id

    def __init__(self, client, parent=None):
        super(UnrealBatchPublisherWidget, self).__init__(client, parent=parent)

    def build(self):
        '''(Override) Build the widget, add project context selector'''
        self.warn_missing_definition_label = QtWidgets.QLabel(
            '<html><i>Could not locate asset publisher definition, please check configuration!</i></html>'
        )
        self.layout().addWidget(self.warn_missing_definition_label)
        self.project_context_label = QtWidgets.QLabel('Project Context:')
        self.project_context_label.setObjectName('gray')
        self.layout().addWidget(self.project_context_label)
        self._project_context_selector = context_selector.ContextSelector(
            self.session, enble_context_change=True, select_task=False
        )
        self.layout().addWidget(self._project_context_selector)
        self.layout().addWidget(line.Line(style='solid'))
        super(UnrealBatchPublisherWidget, self).build()

    def post_build(self):
        super(UnrealBatchPublisherWidget, self).post_build()
        self._project_context_selector.entityChanged.connect(
            self.on_project_context_changed
        )

    def on_context_changed(self, context_id):
        '''(Override)Handle context change, propose default project context and populate project context selector'''
        context = self.session.query(
            'Context where id is "{}"'.format(context_id)
        ).one()
        default_project_context_id = context.get('project_id')
        self._project_context_selector.browse_context_id = (
            default_project_context_id
        )
        project_context_id = unreal_utils.get_project_context_id()
        print(
            '@@@ on_context_changed; project_context_id: {}'.format(
                project_context_id
            )
        )
        self._project_context_selector.context_id = project_context_id

    def on_project_context_changed(self, context):
        '''Handle context change - store it with current Unreal project'''
        unreal_utils.set_project_context(context['id'])


class UnrealAssetWidget(ItemBaseWidget):
    '''Unreal asset widget to be used in batch publisher list widget'''

    def get_ident_widget(self):
        self._ident_widget = QtWidgets.QLabel()
        return self._ident_widget

    def get_context_widget(self):
        self._context_widget = QtWidgets.QWidget()
        return self._context_widget

    def set_data(self, asset_path, definition, dcc_object_name, param_dict):
        '''(Override) Set data to be displayed in widget'''
        self._ident_widget.setText(str(asset_path))
        super(UnrealAssetWidget, self).set_data(definition)
        # Determine if needs publish
        do_publish = False
        if dcc_object_name is None:
            # Not tracked yet, that's fine
            do_publish = True
        else:
            # TODO: Check if the asset has changed since last publish
            do_publish = True
        self.set_selected(do_publish)
        if not do_publish:
            self.info_message = (
                "Asset is up to date and has not changed since last publish"
            )

    def get_progress_label(self, item):
        asset_path = item[0]
        # Return asset name
        return asset_path.split('/')[-1]


class UnrealAssetListWidget(BatchPublisherListBaseWidget):
    def rebuild(self):
        '''Add all assets(components) again from model.'''
        # TODO: Save selection state
        clear_layout(self.layout())
        for row in range(self.model.rowCount()):
            index = self.model.createIndex(row, 0, self.model)

            (
                asset_path,
                definition,
                dcc_object_name,
                param_dict,
            ) = self.model.data(index)

            # Build item widget
            item_widget = UnrealAssetWidget(
                index, self._batch_publisher_widget, self.model.event_manager
            )
            set_property(
                item_widget,
                'first',
                'true' if row == 0 else 'false',
            )

            item_widget.set_data(
                asset_path, definition, dcc_object_name, param_dict
            )
            self.layout().addWidget(item_widget)
            item_widget.clicked.connect(
                partial(self.item_clicked, item_widget)
            )

        self.layout().addWidget(QtWidgets.QLabel(), 1000)
        self.refreshed.emit()

    def item_clicked(self, item_widget):
        pass
