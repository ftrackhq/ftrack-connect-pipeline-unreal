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


class UnrealAbcRigLoaderImporterPlugin(plugin.UnrealLoaderImporterPlugin):
    load_modes = load_const.LOAD_MODES

    plugin_name = 'unreal_abc_rig_loader_importer'

    def run(self, context_data=None, data=None, options=None):
        '''Load Alembic rig file pointed out by collected *data*, with *options*.'''

        # Build import task
        task, component_path = unreal_utils.prepare_load_task(
            self.session, context_data, data, options
        )

        # Alembic rig specific options
        task.options = unreal.AbcImportSettings()
        task.options.import_type = unreal.AlembicImportType.SKELETAL
        task.options.material_settings.set_editor_property(
            'find_materials', options.get('ImportMaterials', False)
        )

        # Rig specific options
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
        self.logger.info('Imported Alembic rig: {}'.format(import_result))
        loaded_skeletal_mesh = unreal.EditorAssetLibrary.load_asset(
            import_result
        )

        results = {component_path: []}

        if options.get('RenameSkelMesh', False):
            results[component_path].append(
                unreal_utils.rename_node_with_prefix(
                    import_result, options.get('RenameSkelMeshPrefix', 'SK_')
                )
            )
        else:
            results[component_path].append(
                loaded_skeletal_mesh.get_path_name()
            )

        mesh_skeleton = loaded_skeletal_mesh.skeleton
        if mesh_skeleton:
            if options.get('RenameSkeleton', False):
                results[component_path].append(
                    unreal_utils.rename_node_with_prefix(
                        mesh_skeleton.get_path_name(),
                        options.get('RenameSkeletonPrefix', 'SKEL_'),
                    )
                )
            else:
                results[component_path].append(mesh_skeleton.get_path_name())

        mesh_physics_asset = loaded_skeletal_mesh.physics_asset
        if mesh_physics_asset:
            if options.get('RenamePhysAsset', False):
                results[component_path].append(
                    unreal_utils.rename_node_with_prefix(
                        mesh_physics_asset.get_path_name(),
                        options.get('RenamePhysAssetPrefix', 'PHAT_'),
                    )
                )
            else:
                results[component_path].append(
                    mesh_physics_asset.get_path_name()
                )

        return results


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return

    abc_geo_importer = UnrealAbcRigLoaderImporterPlugin(api_object)
    abc_geo_importer.register()
