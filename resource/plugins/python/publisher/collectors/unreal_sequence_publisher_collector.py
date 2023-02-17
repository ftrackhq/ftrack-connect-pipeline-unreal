# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import unreal

import ftrack_api

from ftrack_connect_pipeline_unreal import plugin
from ftrack_connect_pipeline_unreal.utils import (
    custom_commands as unreal_utils,
)


class UnrealSequencePublisherCollectorPlugin(
    plugin.UnrealPublisherCollectorPlugin
):
    '''Unreal sequence publisher collector plugin'''

    plugin_name = 'unreal_sequence_publisher_collector'

    def select(self, context_data=None, data=None, options=None):
        '''Select all the sequences in the given plugin *options*'''
        selected_items = options.get('selected_items', [])
        return selected_items

    def fetch(self, context_data=None, data=None, options=None):
        '''Fetch all sequences from the level/map'''
        result = []
        collected_objects = unreal_utils.get_all_sequences()

        # Find the selected sequence
        seq_name_sel = None
        for actor in unreal.EditorLevelLibrary.get_selected_level_actors():
            if (
                actor.static_class()
                == unreal.LevelSequenceActor.static_class()
            ):
                seq_name_sel = actor.get_name()
                break

        for object in collected_objects:
            data = {'value': object}
            if object == seq_name_sel:
                data['default'] = True
            result.append(data)

        return result

    def run(self, context_data=None, data=None, options=None):
        '''Return the name of sequence from plugin *options*'''
        sequence_name = options.get('sequence_name')
        if not sequence_name:
            return False, {'message': 'No sequence chosen.'}
        return [sequence_name]


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = UnrealSequencePublisherCollectorPlugin(api_object)
    plugin.register()
