# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import time
import queue
import threading

from Qt import QtCore, QtWidgets

from ftrack_connect_pipeline import constants as core_constants

import ftrack_connect_pipeline_qt.constants as qt_constants
from ftrack_connect_pipeline_qt.client.publish import QtPublisherClientWidget
from ftrack_connect_pipeline_qt.ui.factory.publisher import (
    PublisherWidgetFactory,
)
from ftrack_connect_pipeline_qt.ui.utility.widget import (
    dialog,
)
import ftrack_connect_pipeline_unreal.constants as unreal_constants
from ftrack_connect_pipeline_unreal.ui.factory.batch_publisher import (
    UnrealShotPublisherWidgetFactory,
)
from ftrack_connect_pipeline_unreal import utils as unreal_utils


class UnrealQtPublisherClientBaseWidget(QtPublisherClientWidget):
    '''Unreal publisher client widget base class contining batch publish logic,
    candidate to be merged to QT publisher client widget'''

    prepareNextItem = QtCore.Signal()
    queueNextItem = QtCore.Signal(object, object)
    runNextItem = QtCore.Signal(object, object)
    runPost = QtCore.Signal()

    batch = False
    item_name = '?'

    def __init__(self, event_manager, parent=None):
        self.reset_processed_items()
        self.batch_publisher_widget = None
        super(UnrealQtPublisherClientBaseWidget, self).__init__(
            event_manager, parent=parent
        )

    # Batch publish logic

    def set_run_callback_function(self, fn):
        self._run_callback_fn = fn

    def _run_callback(self, event):
        '''Callback of the :meth:`~ftrack_connect_pipeline.client.run_plugin'''
        super(UnrealQtPublisherClientBaseWidget, self)._run_callback(event)
        if self._run_callback_fn:
            self._run_callback_fn(event)

    def post_build(self):
        super(UnrealQtPublisherClientBaseWidget, self).post_build()
        self.prepareNextItem.connect(self.prepare_next_item)
        self.queueNextItem.connect(self.queue_next_item)
        self.runNextItem.connect(self.run_next_item)
        self.runPost.connect(self.run_post)

    def on_context_changed_sync(self, context_id):
        '''Override context changed to avoid context change'''
        super(UnrealQtPublisherClientBaseWidget, self).on_context_changed_sync(
            context_id
        )
        if self.batch_publisher_widget:
            self.batch_publisher_widget.on_context_changed(context_id)

    def reset_processed_items(self):
        '''Keep track of processed items to prevent duplicates and cycles. If *include_initial_items* is true,
        the initial items will be included in the processed items list.'''
        self._processed_items = []

    def setup_widget_factory(self, widget_factory, definition):
        widget_factory.set_definition(definition)
        widget_factory.host_connection = self._host_connection
        widget_factory.set_definition_type(definition['type'])

    def _on_run_plugin(self, plugin_data, method):
        '''Function called to run one single plugin *plugin_data* with the
        plugin information and the *method* to be run has to be passed'''
        self.run_plugin(plugin_data, method, self.engine_type)

    def _on_log_item_added(self, log_item):
        ''' 'Called when widget fetch plugin is run'''
        if self.batch_publisher_widget:
            self.batch_publisher_widget.on_log_item_added(log_item)

    def run(self):
        '''(Override) Function called when the run button is clicked.'''

        if not self.batch:
            super(UnrealQtPublisherClientBaseWidget, self).run()
            return
        elif not self.batch_publisher_widget.can_publish():
            return

        # Check if anything to publish
        if self.batch_publisher_widget.count() == 0:
            dialog.ModalDialog(
                self,
                message='Please select at least one item to publish!'.format(),
            )
            return

        # Setup queue if items to prepare and publish
        self.prepare_queue = queue.Queue()
        # Queued up (item_widget, definition) tuples to run, processed by background worker
        self._run_queue_async = queue.Queue()

        self._stop_run = False

        # Spawn background thread
        thread = threading.Thread(target=self._relay_run_signals_async)
        thread.start()

        self.progress_widget.prepare_add_steps()
        self.progress_widget.set_status(
            core_constants.RUNNING_STATUS, 'Initializing...'
        )

        self.batch_publisher_widget.run()

    def prepare_next_item(self):
        '''Pull one item from the queue and prepare it to be run'''
        if self.prepare_queue.empty():
            self.runPost.emit()
            return
        if self._stop_run:
            return

        item_widget = self.prepare_queue.get()

        item_widget.batch_publisher_widget.prepare_item(item_widget)

    def queue_next_item(self, item_widget, definition):
        '''Queue the publish run of *item_widget* and *definition*'''
        if self._stop_run:
            return
        # Have Qt process events / paint widgets, relay over background thread
        self._run_queue_async.put((item_widget, definition))

    def _relay_run_signals_async(self):
        '''Background thread running a loop polling for items and their definition to run, emitting run event'''

        while not self._stop_run:
            # Get item to run
            if self._run_queue_async.empty():
                time.sleep(0.2)
                continue

            item_widget, definition = self._run_queue_async.get()

            self.runNextItem.emit(item_widget, definition)

    def run_next_item(self, item_widget, definition):
        '''Run the publish of the *item_widget* using *definition*'''
        if self._stop_run:
            return
        item_widget.batch_publisher_widget.run_item(item_widget, definition)

    def run_abort(self):
        '''Abort batch publisher - empty queue'''
        if not self._stop_run:
            if self.prepare_queue is not None:
                self.prepare_queue.queue.clear()
            if self._run_queue_async is not None:
                self._run_queue_async.queue.clear()
            self.logger.warning('Aborted batch publish')

    def run_post(self):
        '''All items has been published, post process'''

        self._stop_run = True

        total, succeeded, failed = self.batch_publisher_widget.run_post()

        if succeeded > 0:
            if failed == 0:
                self.progress_widget.set_status(
                    core_constants.SUCCESS_STATUS,
                    'Successfully published {}/{} {}{}!'.format(
                        succeeded,
                        total,
                        self.item_name,
                        's' if total > 1 else '',
                    ),
                )
            else:
                self.progress_widget.set_status(
                    core_constants.WARNING_STATUS,
                    'Successfully published {}/{} {}{}, {} failed - check logs for more information!'.format(
                        succeeded,
                        total,
                        self.item_name,
                        's' if total > 1 else '',
                        failed,
                    ),
                )
        else:
            self.progress_widget.set_status(
                core_constants.ERROR_STATUS,
                'Could not publish any {}{} - check logs for more information!'.format(
                    self.item_name,
                    's' if total > 1 else '',
                ),
            )

    def refresh(self, checked_items):
        '''(Override)'''
        self.run_button.setText(
            'PUBLISH{}'.format(
                '({})'.format(len(checked_items))
                if len(checked_items) > 0
                else ''
            )
        )
        self.run_button.setEnabled(0 < len(checked_items))
        super(UnrealQtPublisherClientBaseWidget, self).refresh()


class UnrealQtPublisherClientWidget(UnrealQtPublisherClientBaseWidget):
    ui_types = [
        core_constants.UI_TYPE,
        qt_constants.UI_TYPE,
        unreal_constants.UI_TYPE,
    ]
    '''Unreal publisher widget'''

    def __init__(self, event_manager, parent=None):
        super(UnrealQtPublisherClientWidget, self).__init__(
            event_manager, parent=parent
        )
        self.setWindowTitle('Unreal Pipeline Publisher')
        self.resize(600, 800)

    def get_theme_background_style(self):
        return 'ftrack'

    def is_docked(self):
        return False

    def change_definition(self, definition, schema, component_names_filter):
        '''(Override)'''
        # Need to switch factory and progress widget based on new definition chosen?
        items = None
        if definition:
            if definition['name'].lower().find('shot') > -1:
                target_factory_class = UnrealShotPublisherWidgetFactory
                self.batch = True
                self.item_name = 'shot'
            # TODO: add support for batch publish of assets
            else:
                target_factory_class = PublisherWidgetFactory
                self.batch = False
            if self.widget_factory.__class__ != target_factory_class:
                if target_factory_class != PublisherWidgetFactory:
                    # Switch factory, will initialise batch_publisher_widget as needed
                    self.widget_factory = target_factory_class(self)
                    if (
                        target_factory_class
                        == UnrealShotPublisherWidgetFactory
                    ):
                        # Locate shot tracks
                        selected_sequence = (
                            unreal_utils.get_selected_sequence()
                        )
                        if selected_sequence:
                            # Get shot tracks
                            items = unreal_utils.get_sequence_shots(
                                selected_sequence
                            )
                else:
                    self.batch_publisher_widget = None
                    self.widget_factory = target_factory_class(
                        self.event_manager, self.ui_types
                    )
        super(UnrealQtPublisherClientWidget, self).change_definition(
            definition, schema, component_names_filter
        )
        if definition and self.batch_publisher_widget:
            self.batch_publisher_widget.on_context_changed(self.context_id)
            if items:
                self.batch_publisher_widget.build_items(items, definition)
                self.run_button.setEnabled(True)
