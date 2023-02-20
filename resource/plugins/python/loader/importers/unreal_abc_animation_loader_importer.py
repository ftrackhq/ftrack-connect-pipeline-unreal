# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack
import os

import unreal

from ftrack_connect_pipeline_unreal import plugin
from ftrack_connect_pipeline_unreal.constants.asset import modes as load_const
from ftrack_connect_pipeline_unreal.utils import (
    custom_commands as unreal_utils,
)
import ftrack_api


class UnrealAbcAnimationLoaderImporterPlugin(
    plugin.UnrealLoaderImporterPlugin
):
    load_modes = load_const.LOAD_MODES

    plugin_name = 'unreal_abc_animation_loader_importer'

    def run(self, context_data=None, data=None, options=None):
        '''Load Alembic animation file pointed out by collected *data*, with *options*.'''

        # Build import task
        task, component_path = unreal_utils.prepare_load_task(
            self.session, context_data, data
        )

        # Alembic animation specific options
        task.options = unreal.AbcImportSettings()
        task.options.import_type = unreal.AlembicImportType.GEOMETRY_CACHE
        task.options.material_settings.set_editor_property(
            'find_materials', options.get('ImportMaterials', False)
        )

        if options.get('UseCustomRange'):
            task.options.sampling_settings.frame_start = options[
                'AnimRangeMin'
            ]
            task.options.sampling_settings.frame_end = options['AnimRangeMax']

        # Animation specific options
        skeletonName = options.get('Skeleton')
        if skeletonName:
            skeletons = unreal_utils.get_asset_by_class('Skeleton')
            skeletonAD = None
            for skeleton in skeletons:
                if skeleton.asset_name == skeletonName:
                    skeletonAD = skeleton

            if skeletonAD is not None:
                task.options.set_editor_property(
                    'skeleton', skeletonAD.get_asset()
                )

        import_result = unreal_utils.import_file(task)
        self.logger.info(
            'Imported Alembic animation: {}'.format(import_result)
        )
        results = {}

        if options.get('RenameAnim', False):
            results[component_path] = unreal_utils.rename_node_with_prefix(
                import_result, options.get('RenameAnimPrefix', 'A_')
            )
        else:
            results[component_path] = import_result

        return results


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return

    abc_geo_importer = UnrealAbcAnimationLoaderImporterPlugin(api_object)
    abc_geo_importer.register()
