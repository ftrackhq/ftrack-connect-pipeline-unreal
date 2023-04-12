# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import copy

from Qt import QtCore, QtWidgets

from ftrack_connect_pipeline_unreal.ui.factory.base import (
    UnrealBatchPublisherWidgetFactoryBase,
)


class UnrealShotPublisherWidgetFactoryBase(
    UnrealBatchPublisherWidgetFactoryBase
):
    '''Augmented widget factory for shot publisher client running in batch mode'''

    @property
    def client(self):
        '''Return the client'''
        return self._client

    def __init__(self, client, parent=None):
        self._client = client
        super(UnrealShotPublisherWidgetFactoryBase, self).__init__(
            client.event_manager,
            client.ui_types,
            parent=parent,
        )

        # Create shot publisher widget

        from ftrack_connect_pipeline_unreal.ui.batch_publisher.shot import (
            UnrealShotPublisherWidgetUnreal,
        )  # Prevent circular import

        self.client.batch_publisher_widget = UnrealShotPublisherWidgetUnreal(
            self.client
        )

    def pre_build(self):
        super(UnrealShotPublisherWidgetFactoryBase, self).pre_build()

    def build(
        self, definition, component_names_filter, component_extensions_filter
    ):
        return self.client.batch_publisher_widget
