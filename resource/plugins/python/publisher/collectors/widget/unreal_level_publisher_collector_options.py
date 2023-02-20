# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
from functools import partial

from Qt import QtWidgets, QtCore

from ftrack_connect_pipeline_unreal import plugin
from ftrack_connect_pipeline_qt.plugin.widget import BaseOptionsWidget

import ftrack_api


class UnrealAssetsPublisherCollectorOptionsWidget(BaseOptionsWidget):
    '''Unreal assets user selection template plugin widget'''

    # Run fetch function on widget initialization
    auto_fetch_on_init = True

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
        super(UnrealAssetsPublisherCollectorOptionsWidget, self).__init__(
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
        '''build function widgets.'''
        super(UnrealAssetsPublisherCollectorOptionsWidget, self).build()

        self._summary_widget = QtWidgets.QLabel()
        self.layout().addWidget(self._summary_widget)

        collected_objects = self.options.get('collected_objects') or []
        current_level = ''
        if len(collected_objects) > 0:
            current_level = collected_objects[0]

        self.line_edit = QtWidgets.QLineEdit(current_level)
        self.line_edit.setReadOnly(True)

        self.layout().addWidget(self.line_edit)
        self.report_input()

    def on_fetch_callback(self, level_path):
        '''This function is called by the _set_internal_run_result function of
        the BaseOptionsWidget'''
        self.set_option_result([level_path], key='collected_objects')
        self.line_edit.clear()
        self.line_edit.setText(level_path)

    def report_input(self):
        '''(Override) Amount of collected objects has changed, notify parent(s)'''
        message = ''
        status = False
        num_objects = (
            1 if len(self._options.get('collected_objects') or []) > 0 else 0
        )
        if num_objects > 0:
            message = '{} level{} selected'.format(
                num_objects, 's' if num_objects > 1 else ''
            )
            status = True
        self.inputChanged.emit(
            {
                'status': status,
                'message': message,
            }
        )


class UnrealAssetsPublisherCollectorPluginWidget(
    plugin.UnrealPublisherCollectorPluginWidget
):
    plugin_name = 'unreal_level_publisher_collector'
    widget = UnrealAssetsPublisherCollectorOptionsWidget


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = UnrealAssetsPublisherCollectorPluginWidget(api_object)
    plugin.register()
