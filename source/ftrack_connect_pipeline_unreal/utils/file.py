# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import os
import glob

from ftrack_connect_pipeline import utils as core_utils

import unreal


def import_file(asset_import_task):
    '''Native import file function using the object unreal.AssetImportTask() given as *asset_import_task*'''
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(
        [asset_import_task]
    )
    return (
        asset_import_task.imported_object_paths[0]
        if len(asset_import_task.imported_object_paths or []) > 0
        else None
    )


def find_movie(render_folder):
    if not render_folder or not os.path.exists(render_folder):
        return None

    avi_files = glob.glob(os.path.join(render_folder, '*.avi'))

    if avi_files:
        return avi_files[0]

    return None


def find_rendered_media(render_folder, shot_name):
    '''Find rendered media in the given *render_folder*, will return a tuple with image sequence and video file if found.
    Otherwise it will return an error message'''

    error_message = 'Render folder does not exist: "{}"'.format(render_folder)

    if render_folder and os.path.exists(render_folder):
        shot_render_folder = os.path.join(render_folder, shot_name)

        error_message = 'Shot folder does not exist: "{}"'.format(
            shot_render_folder
        )

        if shot_render_folder and os.path.exists(shot_render_folder):
            error_message = 'No media found in shot folder: "{}"'.format(
                shot_render_folder
            )

            # Locate AVI media and possible image sequence on disk
            movie_path = find_movie(shot_render_folder)
            sequence_path = core_utils.find_image_sequence(shot_render_folder)

            if movie_path or sequence_path:
                return movie_path, sequence_path

    return error_message
