# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_connect_pipeline_unreal import plugin
from ftrack_connect_pipeline_qt.plugin.widget.base_collector_widget import (
    BaseCollectorWidget,
)

import ftrack_api


class UnrealDependenciesPublisherCollectorOptionsWidget(BaseCollectorWidget):
    '''Unreal dependencies user selection template plugin widget'''

    # Run fetch function on widget initialization
    auto_fetch_on_init = True

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
        super(
            UnrealDependenciesPublisherCollectorOptionsWidget, self
        ).__init__(
            parent=parent,
            session=session,
            data=data,
            name=name,
            description=description,
            options=options,
            context_id=context_id,
            asset_type_name=asset_type_name,
        )

    def report_input(self):
        '''(Override) Do not report back for dependencies, they are published separately'''
        pass


class UnrealDependenciesPublisherCollectorPluginWidget(
    plugin.UnrealPublisherCollectorPluginWidget
):
    plugin_name = 'unreal_dependencies_publisher_collector'
    widget = UnrealDependenciesPublisherCollectorOptionsWidget


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = UnrealDependenciesPublisherCollectorPluginWidget(api_object)
    plugin.register()
