# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack
import copy

from Qt import QtCore, QtWidgets

from ftrack_connect_pipeline_unreal.ui.factory.base import (
    UnrealBatchPublisherWidgetBaseFactory,
)


class UnrealShotPublisherWidgetFactory(UnrealBatchPublisherWidgetBaseFactory):
    '''Augmented widget factory for publisher client running in batch mode'''

    @property
    def client(self):
        '''Return the client'''
        return self._client

    def __init__(self, client, parent=None):
        from ftrack_connect_pipeline_unreal.ui.batch_publisher.shot import (
            UnrealShotPublisherWidget,
        )

        self._client = client
        self.client.batch_publisher_widget = UnrealShotPublisherWidget(
            self.client
        )
        super(UnrealShotPublisherWidgetFactory, self).__init__(
            client.event_manager,
            client.ui_types,
            parent=parent,
        )

    def build(
        self, definition, component_names_filter, component_extensions_filter
    ):
        return self.client.batch_publisher_widget
