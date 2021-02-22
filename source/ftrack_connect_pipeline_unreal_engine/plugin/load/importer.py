# :coding: utf-8
# :copyright: Copyright (c) 2020 ftrack

import json

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_unreal_engine.plugin import (
    BaseUnrealPlugin, BaseUnrealPluginWidget
)

from ftrack_connect_unreal_engine.asset import FtrackAssetTab
from ftrack_connect_unreal_engine.constants import asset as asset_const
from ftrack_connect_unreal_engine.constants.asset import modes as load_const
from ftrack_connect_unreal_engine.utils import custom_commands as unreal_utils


class LoaderImporterUnrealPlugin(plugin.LoaderImporterPlugin, BaseUnrealPlugin):
    ''' Class representing a Collector Plugin

    .. note::

        _required_output a List
    '''
    ftrack_asset_class = FtrackAssetTab

    def _run(self, event):
        '''

        If we import a unreal scene, we don't add any FtrackTab for now.

        '''

        try:
            self.old_data = unreal_utils.get_current_scene_objects()
            self.logger.info('Scene objects : {}'.format(len(self.old_data)))

            context = event['data']['settings']['context']
            self.logger.debug('Current context : {}'.format(context))

            data = event['data']['settings']['data']
            self.logger.debug('Current data : {}'.format(data))

            options = event['data']['settings']['options']


            super_result = super(LoaderImporterUnrealPlugin, self)._run(event)

            options[asset_const.ASSET_INFO_OPTIONS] = json.dumps(
                event['data']
            ).encode('base64')

            asset_load_mode = options.get(asset_const.LOAD_MODE)

            if asset_load_mode != load_const.OPEN_MODE:

                self.new_data = unreal_utils.get_current_scene_objects()

                diff = self.new_data.difference(self.old_data)

                if diff:

                    self.logger.debug(
                        'Checked differences between ftrack_objects before and after'
                        ' inport : {}'.format(diff)
                    )

                    ftrack_asset_class = self.get_asset_class(context, data, options)

                    ftrack_asset_class.connect_objects(diff)
                else:
                    self.logger.debug('No differences found in the scene')

            return super_result

        except:
            import traceback
            print(traceback.format_exc())
            raise


class LoaderImporterUnrealWidget(pluginWidget.LoaderImporterWidget, BaseUnrealPluginWidget):
    ''' Class representing a Collector Widget

    .. note::

        _required_output a List
    '''



