# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from Qt import QtWidgets, QtCore, QtGui

import ftrack_api

from ftrack_connect_pipeline_qt import plugin
from ftrack_connect_pipeline_qt.plugin.widget import BaseOptionsWidget
from ftrack_connect_pipeline_qt.ui.utility.widget.context_selector import (
    ContextSelector,
)

from ftrack_connect_pipeline_unreal.utils import (
    custom_commands as unreal_utils,
)


class UnrealRootLoaderContextOptionsWidget(BaseOptionsWidget):
    '''Unreal loader root context plugin widget'''

    @property
    def root_context_id(self):
        return self._root_context_selector.context_id

    @root_context_id.setter
    def root_context_id(self, context_id):
        self._root_context_selector.context_id = context_id
        # Pass root context id to options
        self.set_option_result(context_id, key='root_context_id')

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
        super(UnrealRootLoaderContextOptionsWidget, self).__init__(
            parent=parent,
            session=session,
            data=data,
            name=name,
            description=description,
            options=options,
            context_id=context_id,
            asset_type_name=asset_type_name,
        )

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

        self._root_context_selector = ContextSelector(
            self.session,
            enble_context_change=True,
            select_task=False,
            browse_context_id=project_context_id,
        )
        self.layout().addWidget(self._root_context_selector)

        self.root_context_id = unreal_utils.get_root_context_id()

    def post_build(self):
        '''Post build hook.'''
        super(UnrealRootLoaderContextOptionsWidget, self).post_build()

        self._root_context_selector.entityChanged.connect(
            self.on_root_context_changed
        )

    def on_root_context_changed(self, context):
        '''Handle context change - store it with Unreal project'''
        unreal_utils.set_root_context_id(context['id'])
        self.root_context_id = context['id']


class UnrealRootLoaderContextOptionsPluginWidget(
    plugin.LoaderContextPluginWidget
):
    '''Loader context widget enabling selection of root ftrack context'''

    plugin_name = 'unreal_root_loader_context'
    widget = UnrealRootLoaderContextOptionsWidget


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = UnrealRootLoaderContextOptionsPluginWidget(api_object)
    plugin.register()
