# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import copy

from Qt import QtCore, QtWidgets

from ftrack_connect_pipeline import constants as core_constants

from ftrack_connect_pipeline_qt import constants as qt_constants
from ftrack_connect_pipeline_qt.ui.factory.ui_overrides import (
    UI_OVERRIDES,
)

from ftrack_connect_pipeline_qt.ui.factory import WidgetFactoryBase


class UnrealBatchPublisherWidgetBaseFactory(WidgetFactoryBase):
    '''Augmented widget factory for publisher client running in batch mode'''

    def __init__(self, event_manager, ui_types, parent=None):
        super(UnrealBatchPublisherWidgetBaseFactory, self).__init__(
            event_manager,
            ui_types,
            parent=parent,
        )

        # Use the same batch progress widget as the loader for now
        self.progress_widget = self.create_progress_widget(
            core_constants.LOADER
        )

    @staticmethod
    def client_type():
        '''Return the type of client'''
        return core_constants.PUBLISHER

    def set_definition(self, definition):
        self.definition = definition

    def build(
        self, definition, component_names_filter, component_extensions_filter
    ):
        '''(Override) Build batch publisher widget, must be implemented by child'''
        raise NotImplementedError()


class UnrealBatchPublisherItemWidgetBaseFactory(WidgetFactoryBase):
    '''Augmented widget factory for a publishable item'''

    def __init__(self, event_manager, ui_types, parent=None):
        super(UnrealBatchPublisherItemWidgetBaseFactory, self).__init__(
            event_manager,
            ui_types,
            parent=parent,
        )

    @staticmethod
    def client_type():
        '''Return the type of client'''
        return core_constants.PUBLISHER

    def set_definition(self, definition):
        self.definition = definition

    def build(self, main_widget):
        '''(Redefine) Add'''

        # Create the components widget based on the definition
        (
            self.components_obj,
            unused_has_visible_plugins,
        ) = self.create_step_container_widget(
            self.definition, core_constants.COMPONENTS
        )

        main_widget.layout().addWidget(self.components_obj.widget)

        # Create the finalizers widget based on the definition
        finalizers_label = QtWidgets.QLabel('Finalizers')
        main_widget.layout().addWidget(finalizers_label)
        finalizers_label.setObjectName('h4')

        (
            self.finalizers_obj,
            has_visible_finalizers,
        ) = self.create_step_container_widget(
            self.definition, core_constants.FINALIZERS
        )

        main_widget.layout().addWidget(self.finalizers_obj.widget)

        if (
            not UI_OVERRIDES.get(core_constants.FINALIZERS).get('show', True)
            or not has_visible_finalizers
        ):
            self.finalizers_obj.widget.hide()

        main_widget.layout().addStretch()

        # Check all components status of the current UI
        self.post_build()

        return main_widget

    def build_progress_ui(self, item_id, ident):
        '''Build only progress widget components, prepare to run.'''
        if not self.progress_widget:
            return
        for step in self.definition.get_all(category=core_constants.STEP):
            step_type = step['type']
            step_name = step.get('name')
            if step_type != core_constants.FINALIZER:
                if step.get('visible', True) is True:
                    self.progress_widget.add_step(
                        step_type, step_name, batch_id=item_id
                    )
            else:
                for stage in step.get_all(category=core_constants.STAGE):
                    stage_name = stage.get('name')
                    if stage.get('visible', True) is True:
                        self.progress_widget.add_step(
                            step_type, stage_name, batch_id=item_id
                        )
