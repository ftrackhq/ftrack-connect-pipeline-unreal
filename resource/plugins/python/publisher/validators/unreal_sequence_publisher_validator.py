# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_connect_pipeline_unreal import plugin

import ftrack_api


class UnrealSequencePublisherValidatorPlugin(
    plugin.UnrealPublisherValidatorPlugin
):
    plugin_name = 'unreal_sequence_publisher_validator'

    def run(self, context_data=None, data=None, options=None):
        '''Return true if all the collected Unreal node supplied with *data* are sequences'''
        if not data:
            return False
        collected_objects = []
        for collector in data:
            collected_objects.extend(collector['result'])
        if not collected_objects or len(collected_objects) == 0:
            return False, {'message': 'No level sequence added!'}
        if len(collected_objects) != 1:
            return (
                False,
                {'message': 'More than one(1) level sequence added!'},
            )
        # No need to validate selection, only sequences can be added
        return True


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = UnrealSequencePublisherValidatorPlugin(api_object)
    plugin.register()
