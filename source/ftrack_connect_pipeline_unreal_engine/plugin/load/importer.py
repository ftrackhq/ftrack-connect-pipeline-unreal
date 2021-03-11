# :coding: utf-8
# :copyright: Copyright (c) 2020 ftrack

import json

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

        context = event['data']['settings']['context']
        self.logger.debug('Current context : {}'.format(context))

        data = event['data']['settings']['data']
        self.logger.debug('Current data : {}'.format(data))

        options = event['data']['settings']['options']

        super_result = super(LoaderImporterUnrealPlugin, self)._run(event)

        result = super_result.get('result')

        if isinstance(result, dict):
            run = result.get('run')
            if isinstance(run, dict):
                # Import was successful, store ftrack metadata
                ftrack_asset_class = self.get_asset_class(context, data, options)

                # Only one component expected
                for (path_component, asset_or_assets) in run.items():
                    # Can arrive as a single or multiple assets
                    ftrack_asset_class.connect_objects(asset_or_assets if isinstance(asset_or_assets, list) else [asset_or_assets])
                    #if isinstance(assets, list):
                        # Ignore imported skeleton and physics assets
                    #    result[path_component] = assets[0]

        return super_result

class LoaderImporterUnrealWidget(pluginWidget.LoaderImporterWidget, BaseUnrealPluginWidget):
    ''' Class representing a Collector Widget

    .. note::

        _required_output a List
    '''



