# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack
import os
import re
import clique

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_unreal_engine.plugin import (
    BaseUnrealPlugin, BaseUnrealPluginWidget
)
from ftrack_connect_pipeline_unreal_engine.constants import asset as asset_const
from ftrack_connect_pipeline_unreal_engine.utils import custom_commands as unreal_utils
from ftrack_connect_pipeline_unreal_engine.asset import FtrackAssetTab

class PublisherFinalizerUnrealPlugin(plugin.PublisherFinalizerPlugin, BaseUnrealPlugin):
    ''' Class representing a Finalizer Plugin

        .. note::

            _required_output is a dictionary containing the 'context_id',
            'asset_name', 'asset_type', 'comment' and 'status_id' of the
            current asset
    '''

    def _run(self, event):
        ''' Run the current plugin with the settings form the *event*.

            .. note::

               We are not committing the changes here to ftrack, as they should be
               committed in the finalizer plugin itself. This way we avoid
               publishing the dependencies if the plugin fails.
        '''
        self.version_dependencies = []
        for data in event['data']['settings']['data']:
            for output in data.get('result') or []:
                if output.get('name') == 'output':
                    for plugin_output in output.get('result') or []:
                        if plugin_output.get('name') == 'package_output':
                            dependency_version_ids = plugin_output.get('user_data',{}).get('data',{}).\
                            get('version_dependency_ids')
                            if 0<len(dependency_version_ids):
                                self.logger.info('Got version dependencies: {}'.format(dependency_version_ids))
                                for dependency_version_id in dependency_version_ids:
                                    dependency_version = self.session.query(
                                        'select version from AssetVersion where id is "{}"'.format(
                                            dependency_version_id
                                        )
                                    ).one()
                                    if dependency_version not in self.version_dependencies:
                                        self.version_dependencies.append(dependency_version)

        super_result = super(PublisherFinalizerUnrealPlugin, self)._run(event)

        return super_result


class PublisherFinalizerUnrealWidget(
    pluginWidget.PublisherFinalizerWidget, BaseUnrealPluginWidget
):
    ''' Class representing a Finalizer Widget

        .. note::

            _required_output is a dictionary containing the 'context_id',
            'asset_name', 'asset_type', 'comment' and 'status_id' of the
            current asset
    '''


