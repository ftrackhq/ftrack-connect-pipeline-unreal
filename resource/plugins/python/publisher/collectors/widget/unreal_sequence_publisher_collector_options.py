# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import os

import unreal

from Qt import QtWidgets

import ftrack_api

from ftrack_connect_pipeline_qt.plugin.widget import BaseOptionsWidget
from ftrack_connect_pipeline_qt.ui.utility.widget import dialog
from ftrack_connect_pipeline_unreal import plugin
from ftrack_connect_pipeline_unreal import utils as unreal_utils


class UnrealSequencePublisherCollectorOptionsWidget(BaseOptionsWidget):
    '''Unreal sequence collector widget plugin'''

    # Run fetch function on widget initialization
    auto_fetch_on_init = False

    @property
    def media_path(self):
        '''Return the media path from options'''
        result = self.options.get('media_path')
        if result:
            result = result.strip()
            if len(result) == 0:
                result = None
        return result

    @media_path.setter
    def media_path(self, media_path):
        '''Store *media_path* in options and update widgets'''
        if media_path is not None and len(media_path) > 0:
            self.set_option_result(media_path, 'media_path')
            # Remember last used path
            unreal_utils.update_project_settings({'media_path': media_path})
        else:
            media_path = '<please choose am image sequence>'
            self.set_option_result(None, 'media_path')

        # Update UI
        self._media_path_le.setText(media_path)
        self._media_path_le.setToolTip(media_path)

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
        self.unreal_sequences = []
        super(UnrealSequencePublisherCollectorOptionsWidget, self).__init__(
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
        '''Build the options widget'''
        super(UnrealSequencePublisherCollectorOptionsWidget, self).build()

        self._pickup_label = QtWidgets.QLabel(
            'Pick up rendered image sequence: '
        )

        self._browse_media_path_widget = QtWidgets.QWidget()
        self._browse_media_path_widget.setLayout(QtWidgets.QHBoxLayout())
        self._browse_media_path_widget.layout().setContentsMargins(0, 0, 0, 0)
        self._browse_media_path_widget.layout().setSpacing(0)

        self._media_path_le = QtWidgets.QLineEdit()
        self._media_path_le.setReadOnly(True)

        self._browse_media_path_widget.layout().addWidget(
            self._media_path_le, 20
        )

        self._browse_media_path_btn = QtWidgets.QPushButton('BROWSE')
        self._browse_media_path_btn.setObjectName('borderless')

        self._browse_media_path_widget.layout().addWidget(
            self._browse_media_path_btn
        )
        self.layout().addWidget(self._browse_media_path_widget)

        # Use previous value if available
        path = self.media_path
        if not path or len(path) == 0:
            path = unreal_utils.get_project_settings().get('media_path')
        self.media_path = path

        self.report_input()

    def post_build(self):
        super(UnrealSequencePublisherCollectorOptionsWidget, self).post_build()

        self._browse_media_path_btn.clicked.connect(
            self._show_image_sequence_dialog
        )

    def _show_image_sequence_dialog(self):
        '''Shows the file dialog for image sequences'''
        if not self.media_path:
            start_dir = os.path.realpath(
                os.path.join(
                    unreal.SystemLibrary.get_project_saved_directory(),
                    "VideoCaptures",
                )
            )
        else:
            start_dir = os.path.dirname(self._media_path_le.text())

        # TODO: add all supported file formats
        # supported_file_formats = [".bmp","float",".pcx",".png",".psd",".tga",".jpg",".exr",".dds", ".hdr"]
        media_path = QtWidgets.QFileDialog.getExistingDirectory(
            caption='Choose directory containing rendered image sequence',
            dir=start_dir,
            options=QtWidgets.QFileDialog.setNameFilter(("Images (*.png *.xpm *.jpg)"))
        )

        if not media_path:
            return

        media_path = os.path.normpath(media_path)

        image_sequence_path = unreal_utils.find_image_sequence(media_path)

        if not image_sequence_path:
            dialog.ModalDialog(
                None,
                title='Locate rendered image sequence',
                message='An image sequence on the form "prefix.NNNN.ext" were not found in: {}!'.format(
                    media_path
                ),
            )

        self.media_path = image_sequence_path

        self.report_input()

    def report_input(self):
        '''(Override) Amount of collected objects has changed, notify parent(s)'''
        status = False
        num_objects = (
            1
            if self.media_path and len(self.media_path) > 0
            else 0
        )
        if num_objects > 0:
            message = '1 {} selected'.format(
                'image sequence' if self.image_sequence else 'movie'
            )
            status = True
        else:
            message = 'No media selected!'
        self.inputChanged.emit(
            {
                'status': status,
                'message': message,
            }
        )


class UnrealSequencePublisherCollectorPluginWidget(
    plugin.UnrealPublisherCollectorPluginWidget
):
    plugin_name = 'unreal_sequence_publisher_collector'
    widget = UnrealSequencePublisherCollectorOptionsWidget


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = UnrealSequencePublisherCollectorPluginWidget(api_object)
    plugin.register()
