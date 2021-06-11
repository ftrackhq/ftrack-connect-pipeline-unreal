# :coding: utf-8
# :copyright: Copyright (c) 2014-2021 ftrack

import json
import base64

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_unreal_engine.plugin import (
    BaseUnrealPlugin, BaseUnrealPluginWidget
)

from ftrack_connect_pipeline_unreal_engine.asset import FtrackAssetTab
from ftrack_connect_pipeline_unreal_engine.constants import asset as asset_const
from ftrack_connect_pipeline_unreal_engine.constants.asset import modes as load_const
from ftrack_connect_pipeline_unreal_engine.utils import custom_commands as unreal_utils


class LoaderImporterUnrealPlugin(plugin.LoaderImporterPlugin, BaseUnrealPlugin):
    ''' Class representing a Collector Plugin

    .. note::

        _required_output a List
    '''

    ftrack_asset_class = FtrackAssetTab

    def _run(self, event):
        ''' Apply ftrack info to loaded asset. '''

        super_result = super(LoaderImporterUnrealPlugin, self)._run(event)

        context_data = self.plugin_settings.get('context_data')
        self.logger.debug('Current context : {}'.format(context_data))

        data = self.plugin_settings.get('data')
        self.logger.debug('Current data : {}'.format(data))

        options = self.plugin_settings.get('options')
        self.logger.debug('Current options: {}'.format(options))

        result = super_result.get('result')

        options[asset_const.ASSET_INFO_OPTIONS] = base64.encodebytes(
            json.dumps(event['data']).encode('utf-8')
        ).decode('utf-8')

        if isinstance(result, dict):
            run = result.get('run')
            if isinstance(run, dict):
                # Import was successful, store ftrack metadata
                ftrack_asset_class = self.get_asset_class(
                    context_data, data, options)

                for (path_component, asset_paths) in run.items():
                    ftrack_asset_class.connect_objects(asset_paths)

        return super_result

class LoaderImporterUnrealWidget(pluginWidget.LoaderImporterWidget,
                                 BaseUnrealPluginWidget):
    ''' Class representing a Collector Widget

    .. note::

        _required_output a List
    '''



