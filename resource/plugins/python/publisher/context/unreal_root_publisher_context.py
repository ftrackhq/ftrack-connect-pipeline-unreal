# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_connect_pipeline import plugin
import ftrack_api

from ftrack_connect_pipeline_unreal.utils import (
    custom_commands as unreal_utils,
)


class UnrealRootPublisherContextPlugin(plugin.PublisherContextPlugin):
    '''Unreal project publisher context plugin'''

    plugin_name = 'unreal_root_publisher_context'

    def run(self, context_data=None, data=None, options=None):
        '''Find out the project context'''

        asset_path = options.get('ftrack_asset_path')
        root_context_id = options.get('root_context_id')

        try:
            asset_build = unreal_utils.push_asset_build_to_server(
                root_context_id, asset_path, self.session
            )
            options['asset_parent_context_id'] = asset_build['id']
            self.logger.info(
                'asset_build {} structure checks done'.format(
                    asset_build['name']
                )
            )
        except Exception as e:
            raise Exception(
                'Failed to create project level asset build for asset "{}", '
                'please check your ftrack permissions and for any existing '
                'entities in conflict.\n\nDetails: {}'.format(asset_path, e)
            )

        output = self.output
        output.update(options)
        return output


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = UnrealRootPublisherContextPlugin(api_object)
    plugin.register()
