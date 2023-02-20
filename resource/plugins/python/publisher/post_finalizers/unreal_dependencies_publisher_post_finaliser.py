# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack
import os.path

import ftrack_api

from ftrack_connect_pipeline import constants as core_constants
from ftrack_connect_pipeline_unreal import plugin
from ftrack_connect_pipeline_qt import constants as qt_constants

from ftrack_connect_pipeline_unreal.utils import (
    custom_commands as unreal_utils,
)


class UnrealDependenciesPublisherFinalizerPlugin(
    plugin.UnrealPublisherPostFinalizerPlugin
):
    '''Plugin for finalizing the Unreal asset/level dependencies publish process'''

    plugin_name = 'unreal_dependencies_publisher_post_finalizer'

    def run(self, context_data=None, data=None, options=None):
        '''Publisher unreal asset dependencies to ftrack'''

        # Get the dependencies and the host ID from data
        dependencies = (
            host_id
        ) = asset_version_id = asset_filesystem_path = None
        for comp in data:
            if comp['type'] == 'component':
                for result in comp['result']:
                    if result['name'] == 'exporter':
                        plugin_result = result['result'][0]
                        dependencies = plugin_result['user_data']['data']
                        host_id = plugin_result['host_id']
                        asset_filesystem_path = plugin_result['result'][0]
                        break
            elif comp['type'] == 'finalizer':
                for result in comp['result']:
                    if result['name'] == 'finalizer':
                        plugin_result = result['result'][0]
                        asset_version_id = plugin_result['result'][
                            'asset_version_id'
                        ]
                        break

        if not dependencies:
            return {'message': 'No dependencies supplied for publish!'}

        asset_path = unreal_utils.filesystem_asset_path_to_asset_path(
            asset_filesystem_path
        )

        pipeline_data = {
            'host_id': host_id,
            'name': qt_constants.BATCH_PUBLISHER_WIDGET,
            'title': 'Publish {} dependencies - {}'.format(
                'level'
                if asset_filesystem_path.lower().endswith('.umap')
                else 'asset',
                os.path.basename(asset_filesystem_path),
            ),
            'source': str(self),
            'assets': dependencies,
            'parent_asset': asset_path,
            'parent_asset_version_id': asset_version_id,
        }
        if not options.get('interactive') is False:
            # Build and send batch publisher spawn event
            event = ftrack_api.event.base.Event(
                topic=core_constants.PIPELINE_CLIENT_LAUNCH,
                data={'pipeline': pipeline_data},
            )
            self._event_manager.publish(
                event,
            )

            return {
                'message': 'Launched publish of dependencies with batch publisher client'
            }
        else:
            # Publish of dependencies are handled by the batch publisher, store data for pickup
            return {
                'message': 'Stored dependency data for pickup by batch publisher'
            }, {'data': pipeline_data}


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = UnrealDependenciesPublisherFinalizerPlugin(api_object)
    plugin.register()
