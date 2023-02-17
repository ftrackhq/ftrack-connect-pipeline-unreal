# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from Qt import QtWidgets, QtCore, QtGui

import unreal

import ftrack_api

from ftrack_connect_pipeline_qt import plugin

from ftrack_connect_pipeline_qt.plugin.widget import BaseOptionsWidget
from ftrack_connect_pipeline_qt.plugin.widget.context import StatusSelector
from ftrack_connect_pipeline_qt.ui.utility.widget.context_selector import (
    ContextSelector,
)
from ftrack_connect_pipeline_qt.ui.utility.widget import line
from ftrack_connect_pipeline_qt.ui.utility.widget.asset_selector import (
    AssetSelector,
)
from ftrack_connect_pipeline_qt.utils import BaseThread
from ftrack_connect_pipeline_qt.ui.utility.widget import dialog
from ftrack_connect_pipeline_qt.ui.utility.widget.entity_info import EntityInfo

from ftrack_connect_pipeline_unreal.utils import (
    custom_commands as unreal_utils,
)


class UnrealRootPublisherContextOptionsWidget(BaseOptionsWidget):
    '''Unreal project publisher context plugin widget'''

    statusesFetched = QtCore.Signal(object)

    @property
    def root_context_id(self):
        return self._root_context_selector.context_id

    @root_context_id.setter
    def root_context_id(self, context_id):
        if context_id:
            self.set_asset_parent_context(context_id)
        # Passing project context id to options
        self.set_option_result(context_id, key='root_context_id')

    @property
    def asset_parent_context_id(self):
        return self._asset_parent_context_selector.context_id

    @asset_parent_context_id.setter
    def asset_parent_context_id(self, context_id):
        if not self.is_temp_asset:
            self._asset_parent_context_selector.context_id = context_id
        # Passing parent context id to options
        self.set_option_result(context_id, key='asset_parent_context_id')
        self.on_asset_parent_selected()

    def __init__(
        self,
        parent=None,
        session=None,
        data=None,
        name=None,
        description=None,
        options=None,
        context_id=None,
        asset_type_name=None,
    ):
        super(UnrealRootPublisherContextOptionsWidget, self).__init__(
            parent=parent,
            session=session,
            data=data,
            name=name,
            description=description,
            options=options,
            context_id=context_id,
            asset_type_name=asset_type_name,
        )

        self.is_temp_asset = False

    def build(self):
        '''Prevent widget name from being displayed with header style.'''
        self.layout().setContentsMargins(10, 0, 0, 0)

        self.name_label = QtWidgets.QLabel(self.name.title())
        self.name_label.setToolTip(self.description)
        self.layout().addWidget(self.name_label)

        project_context_id = None
        if self.context_id:
            context = self.session.query(
                'Context where id is "{}"'.format(self.context_id)
            ).one()
            project_context_id = context.get('project_id')

            # Pass task context id to options
            self.set_option_result(self.context_id, key='task_context_id')
            self.set_option_result(self.context_id, key='context_id')

        self._root_context_selector = ContextSelector(
            self.session,
            enble_context_change=True,
            select_task=False,
            browse_context_id=project_context_id,
        )
        self.layout().addWidget(self._root_context_selector)

        self.layout().addWidget(line.Line())

        self.layout().addWidget(
            QtWidgets.QLabel('Unreal snapshot (asset build) context')
        )
        self._asset_parent_context_selector = ContextSelector(self.session)
        self.layout().addWidget(self._asset_parent_context_selector)

        self.layout().addWidget(line.Line())

        self.layout().addLayout(self._build_asset_selector())

        # Connect the status signal
        self.statusesFetched.connect(self.set_statuses)

        self.layout().addWidget(line.Line())
        version_and_comment = QtWidgets.QWidget()
        version_and_comment.setLayout(QtWidgets.QVBoxLayout())
        version_and_comment.layout().addWidget(
            QtWidgets.QLabel('Version information')
        )
        version_and_comment.layout().addLayout(self._build_status_selector())
        version_and_comment.layout().addLayout(self._build_comments_input())
        self.layout().addWidget(version_and_comment)

        # Fetch the Unreal project context id
        self.root_context_id = unreal_utils.get_root_context_id()

    def post_build(self):
        '''Post build hook.'''
        super(UnrealRootPublisherContextOptionsWidget, self).post_build()

        self._root_context_selector.entityChanged.connect(
            self.on_root_context_changed
        )
        self._asset_parent_context_selector.changeContextClicked.connect(
            self.on_change_asset_parent_context_clicked
        )
        self.asset_selector.assetChanged.connect(self._on_asset_changed)
        self.comments_input.textChanged.connect(self._on_comment_updated)
        self.status_selector.currentIndexChanged.connect(
            self._on_status_changed
        )

    def on_root_context_changed(self, context):
        '''Handle user context change - store it with Unreal project'''
        unreal_utils.set_root_context_id(context['id'])
        self.root_context_id = context['id']

    def on_change_asset_parent_context_clicked(self):
        dialog.ModalDialog(
            self.parent(),
            message='The unreal asset parent context is not editable.',
        )

    def on_asset_parent_selected(self):
        '''
        Enable asset name, status and description only if the
        asset_parent_context_id is set
        '''
        if not self.asset_parent_context_id:
            return
        if not self.status_layout.isEnabled():
            self.status_layout.setEnabled(True)
            if self.is_temp_asset:
                self.emit_statuses(self.statuses)
            else:
                thread = BaseThread(
                    name='get_status_thread',
                    target=self._get_statuses,
                    callback=self.emit_statuses,
                    target_args=(),
                )
                thread.start()
        if not self.coments_layout.isEnabled():
            self.coments_layout.setEnabled(True)
        if not self.asset_layout.isEnabled():
            self.asset_layout.setEnabled(True)

    def set_asset_parent_context(self, root_context_id):
        '''Set the project context for the widget to *context_id*. Make sure the corresponding project
        asset build is created and use it as the context.'''
        asset_path = None
        if self.options.get('selection') is True:
            # Fetch the selected asset in content browser
            selected_asset_data = (
                unreal.EditorUtilityLibrary.get_selected_asset_data()
            )
            if len(selected_asset_data) > 0:
                asset_path = str(selected_asset_data[0].package_name)
        else:
            # Fetch the current level
            asset_path = str(
                unreal.EditorLevelLibrary.get_editor_world().get_path_name()
            ).split('.')[0]

        if not asset_path:
            return

        full_ftrack_asset_path = None
        try:
            # Get the full ftrack asset path
            full_ftrack_asset_path = unreal_utils.get_full_ftrack_asset_path(
                root_context_id, asset_path, session=self.session
            )
        except Exception as e:
            dialog.ModalDialog(
                self.parent(),
                message='Failed to get the asset_path from ftrack. '
                'Please make sure the root is created.\n\nDetails: {}'.format(
                    asset_path, e
                ),
            )
            raise
        asset_build = unreal_utils.get_asset_build_form_path(
            root_context_id, full_ftrack_asset_path, self.session
        )

        temp_asset_build = None
        self.is_temp_asset = False
        if not asset_build:
            # {id:'0000'}
            temp_asset_build, statuses = unreal_utils.get_temp_asset_build(
                root_context_id, asset_path, self.session
            )
            asset_build = temp_asset_build
            self._asset_parent_context_selector.disable_thumbnail = True

            self.is_temp_asset = True
            self.statuses = statuses

        self._asset_parent_context_selector.entity = asset_build
        if self.is_temp_asset:
            self._asset_parent_context_selector.set_entity_info_path(
                full_ftrack_asset_path
            )
        self.asset_parent_context_id = asset_build['id']
        self.asset_selector.set_context(
            self.asset_parent_context_id, self.asset_type_name
        )
        self.asset_selector.set_asset_name(asset_build['name'])
        self.set_option_result(full_ftrack_asset_path, key='ftrack_asset_path')

        if temp_asset_build:
            # Remove temp asset_build from the session
            self.session.delete(temp_asset_build)
            self.session.reset()
            self.logger.info("Rolling back temp asset build creation")

            # No need to session commit because we didn't commit the temp asset

    def _on_status_changed(self, status):
        '''Updates the options dictionary with provided *status* when
        currentIndexChanged of status_selector event is triggered'''
        status_id = self.status_selector.itemData(status)
        self.set_option_result(status_id, key='status_id')
        self.status_selector.on_status_changed(status_id)

    def _on_comment_updated(self):
        '''Updates the option dictionary with current text when
        textChanged of comments_input event is triggered'''
        current_text = self.comments_input.toPlainText()
        self.set_option_result(current_text, key='comment')

    def _on_asset_changed(self, asset_name, asset_entity, is_valid):
        '''Updates the option dictionary with provided *asset_name* when
        asset_changed of asset_selector event is triggered'''
        self.set_option_result(asset_name, key='asset_name')
        self.set_option_result(is_valid, key='is_valid_name')
        if asset_entity:
            self.set_option_result(asset_entity['id'], key='asset_id')
            self.assetChanged.emit(asset_name, asset_entity['id'], is_valid)
        else:
            self.assetChanged.emit(asset_name, None, is_valid)

    def _build_asset_selector(self):
        '''Builds the asset_selector widget'''
        self.asset_layout = QtWidgets.QVBoxLayout()
        # self.asset_layout.setContentsMargins(0, 0, 0, 0)
        self.asset_layout.setAlignment(QtCore.Qt.AlignTop)

        self.asset_selector = AssetSelector(self.session)
        self.asset_layout.addWidget(self.asset_selector)
        if not self.asset_parent_context_id:
            self.asset_layout.setEnabled(False)
        return self.asset_layout

    def _build_status_selector(self):
        '''Builds the status_selector widget'''
        self.status_layout = QtWidgets.QHBoxLayout()
        # self.status_layout.setContentsMargins(0, 0, 0, 0)
        self.status_layout.setAlignment(QtCore.Qt.AlignTop)

        self.asset_status_label = QtWidgets.QLabel("Status")
        self.asset_status_label.setObjectName('gray')

        self.status_selector = StatusSelector()

        self.status_layout.addWidget(self.asset_status_label)
        self.status_layout.addWidget(self.status_selector, 10)

        self.status_layout.addStretch()

        thread = BaseThread(
            name='get_status_thread',
            target=self._get_statuses,
            callback=self.emit_statuses,
            target_args=(),
        )
        thread.start()

        if not self.asset_parent_context_id:
            self.status_layout.setEnabled(False)

        return self.status_layout

    def _build_comments_input(self):
        '''Builds the comments_container widget'''
        self.coments_layout = QtWidgets.QHBoxLayout()
        self.coments_layout.setContentsMargins(0, 0, 0, 0)

        comment_label = QtWidgets.QLabel('Description')
        comment_label.setObjectName('gray')
        comment_label.setAlignment(QtCore.Qt.AlignTop)
        self.comments_input = QtWidgets.QTextEdit()
        self.comments_input.setMaximumHeight(40)
        self.comments_input.setPlaceholderText("Type a description...")
        self.coments_layout.addWidget(comment_label)
        self.coments_layout.addWidget(self.comments_input)

        self.set_option_result(
            self.comments_input.toPlainText(), key='comment'
        )
        if not self.asset_parent_context_id:
            self.coments_layout.setEnabled(False)
        return self.coments_layout

    def emit_statuses(self, statuses):
        '''Emit signal to set statuses on the combobox'''
        # Emit signal to add the sttuses to the combobox
        # because here we could have problems with the threads
        if statuses:
            self.statusesFetched.emit(statuses)

    def set_statuses(self, statuses):
        '''Set statuses on the combo box'''
        self.status_selector.clear()
        self.status_selector.set_statuses(statuses)
        if statuses:
            self.set_option_result(statuses[0]['id'], key='status_id')
            self.status_selector.on_status_changed(statuses[0]['id'])

    def _get_statuses(self):
        '''Returns the status of the selected assetVersion'''
        if not self.asset_parent_context_id:
            return None

        context_entity = self.session.query(
            'select link, name, parent, parent.name from Context where id '
            'is "{}"'.format(self.asset_parent_context_id)
        ).one()

        project = self.session.query(
            'select name, parent, parent.name from Context where id is "{}"'.format(
                context_entity['link'][0]['id']
            )
        ).one()

        schema = project['project_schema']
        statuses = schema.get_statuses('AssetVersion')
        return statuses


class UnrealRootPublisherContextOptionsPluginWidget(
    plugin.PublisherContextPluginWidget
):
    '''Project publisher context widget enabling user selection'''

    plugin_name = 'unreal_root_publisher_context'
    widget = UnrealRootPublisherContextOptionsWidget


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = UnrealRootPublisherContextOptionsPluginWidget(api_object)
    plugin.register()
