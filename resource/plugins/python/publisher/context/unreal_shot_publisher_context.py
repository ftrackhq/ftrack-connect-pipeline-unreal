# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import ftrack_api

from ftrack_connect_pipeline import plugin

from ftrack_connect_pipeline_unreal import utils as unreal_utils


class UnrealShotPublisherContextPlugin(plugin.PublisherContextPlugin):
    '''Unreal shot publisher context plugin'''

    plugin_name = 'unreal_shot_publisher_context'

    def run(self, context_data=None, data=None, options=None):
        '''Find out the sequence context id and shot name and sync the shot to ftrack'''

        shot_name = options.get('shot_name')
        sequence_context_id = options.get('sequence_context_id')

        try:
            shot = unreal_utils.push_shot_to_server(
                sequence_context_id,
                shot_name,
                self.session,
                start=options.get('start'),
                end=options.get('end'),
            )
            options['asset_parent_context_id'] = shot['id']
            self.logger.info('Shot "{}" sync done'.format(shot['name']))
        except Exception as e:
            raise Exception(
                'Failed to create sequence shot for "{}", '
                'please check your ftrack permissions and for any existing '
                'entities in conflict.\n\nDetails: {}'.format(shot_name, e)
            )

        output = self.output
        output.update(options)
        return output


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = UnrealShotPublisherContextPlugin(api_object)
    plugin.register()
