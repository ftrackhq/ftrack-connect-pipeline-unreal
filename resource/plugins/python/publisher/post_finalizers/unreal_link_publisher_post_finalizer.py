# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import json
import os

import ftrack_api

from ftrack_connect_pipeline import constants as core_constants
from ftrack_connect_pipeline_unreal import plugin

from ftrack_connect_pipeline_unreal.utils import (
    custom_commands as unreal_utils,
)
from ftrack_connect_pipeline_unreal.constants import asset as asset_const


class UnrealLinkPublisherFinalizerPlugin(
    plugin.UnrealPublisherPostFinalizerPlugin
):
    '''Plugin for finalizing the Unreal asset publish process by linking the task to the asset build'''

    plugin_name = 'unreal_link_publisher_post_finalizer'

    def run(self, context_data=None, data=None, options=None):
        '''Link task provided in *context_data* to snapshot asset build provided in *context_data*.'''

        # Locate the task
        task = self.session.query(
            'Task where id is "{}"'.format(context_data['context_id'])
        ).one()

        if not 'asset_parent_context_id' in context_data:
            raise Exception(
                'No asset parent context id found in context data!'
            )

        # Locate the task
        asset_build = self.session.query(
            'AssetBuild where id is "{}"'.format(
                context_data['asset_parent_context_id']
            )
        ).one()

        # Create task incoming link if not exits
        tcl = self.session.query(
            'TypedContextLink where from_id is "{}" and to_id is "{}"'.format(
                asset_build['id'], task['id']
            )
        ).first()
        if not tcl:
            self.session.create(
                'TypedContextLink', {'from': asset_build, 'to': task}
            )
            self.session.commit()
            return {
                'message': 'Linked asset build {} to task context {}.'.format(
                    asset_build['id'], task['id']
                )
            }
        else:
            return {
                'message': 'Alread a link from asset build {} to task context {}.'.format(
                    asset_build['id'], task['id']
                )
            }


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = UnrealLinkPublisherFinalizerPlugin(api_object)
    plugin.register()
