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
        current_asset = ''
        if len(collected_objects) > 0:
            current_asset = collected_objects[0]

        widget_layout = QtWidgets.QHBoxLayout()
        widget_layout.setContentsMargins(0, 0, 0, 0)
        widget_layout.setAlignment(QtCore.Qt.AlignTop)

        label = QtWidgets.QLabel('Asset:')
        self.line_edit = QtWidgets.QLineEdit(current_asset)
        self.line_edit.setReadOnly(True)

        widget_layout.addWidget(label)
        widget_layout.addWidget(self.line_edit)
        self.layout().addLayout(widget_layout)

        self._empty_label = QtWidgets.QLabel(
            'Hint: Select an asset in the Unreal content browser and refresh the publisher to use it.'
        )
        self.layout().addWidget(self._empty_label)
        self._empty_label.setVisible(len(current_asset) == 0)
        self.report_input()

    def post_build(self):
        super(UnrealAssetsPublisherCollectorOptionsWidget, self).post_build()
        self.line_edit.textChanged.connect(self._on_asset_changed)

    def _on_asset_changed(self, asset_path):
        self.set_option_result([asset_path], key='collected_objects')
        self._empty_label.setVisible(len(asset_path) == 0)
        self.report_input()

    def on_fetch_callback(self, result):
        '''This function is called by the _set_internal_run_result function of
        the BaseOptionsWidget'''
        self.line_edit.clear()
        self.line_edit.setText(result)

    def on_add_callback(self, result):
        '''This function is called by the _set_internal_run_result function of
        the BaseOptionsWidget'''
        self.line_edit.clear()
        self.line_edit.setText(result)

    def report_input(self):
        '''(Override) Amount of collected objects has changed, notify parent(s)'''
        message = ''
        status = False
        num_objects = (
            1 if len(self._options.get('collected_objects') or []) > 0 else 0
        )
        if num_objects > 0:
            message = '{} asset{} selected'.format(
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
    plugin_name = 'unreal_assets_publisher_collector'
    widget = UnrealAssetsPublisherCollectorOptionsWidget


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = UnrealAssetsPublisherCollectorPluginWidget(api_object)
    plugin.register()
