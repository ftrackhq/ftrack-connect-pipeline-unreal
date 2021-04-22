# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_unreal_engine import constants as unreal_constants

class BaseUnrealPlugin(plugin.BasePlugin):
    host_type = unreal_constants.HOST_TYPE
    ''' '''
    # def _run(self, event):
    #     super_fn = super(BaseUnrealPlugin, self)._run
    #
    #     result = hdefereval.executeInMainThreadWithResult(super_fn)
    #
    #     return result


from ftrack_connect_pipeline_qt import plugin as pluginWidget

class BaseUnrealPluginWidget(BaseUnrealPlugin, pluginWidget.BasePluginWidget):
    category = 'plugin.widget'
    ui_type = unreal_constants.UI_TYPE

    #def _run(self, event):
    #    super_fn = super(BaseUnrealPluginWidget, self)._run
    #
    #    result = hdefereval.executeInMainThreadWithResult(super_fn)
    #
    #   return result


from ftrack_connect_pipeline_unreal_engine.plugin.load import *
from ftrack_connect_pipeline_unreal_engine.plugin.publish import *
from ftrack_connect_pipeline_unreal_engine.plugin.asset_manager import *


