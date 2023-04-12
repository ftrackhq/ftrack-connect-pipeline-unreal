# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import os
import json
import datetime
import logging

import unreal

import ftrack_connect_pipeline_unreal.constants as unreal_constants
from ftrack_connect_pipeline_unreal.constants import asset as asset_const

logger = logging.getLogger(__name__)


def get_all_sequences(as_names=True):
    '''
    Returns a list of all sequence assets in the project If *as_names* is True,
    the asset name will be returned instead of the asset itself.
    '''
    result = []
    top_level_asset_path = {
        "package_name": "/Script/LevelSequence",
        "asset_name": "LevelSequence",
    }
    all_seq_asset_data = (
        unreal.AssetRegistryHelpers.get_asset_registry().get_assets_by_class(
            top_level_asset_path
        )
    )
    for _seq in all_seq_asset_data:
        if str(_seq.package_path).startswith(unreal_constants.GAME_ROOT_PATH):
            if as_names:
                result.append(str(_seq.asset_name))
                continue
            result.append(_seq.get_asset())

    return result


def get_selected_sequence():
    '''Return the selected level sequence asset or sequence selected in the content browser.
    Returns None if no sequence is selected.'''
    for (
        sequence_actor
    ) in unreal.EditorLevelLibrary.get_selected_level_actors():
        if (
            sequence_actor.static_class()
            == unreal.LevelSequenceActor.static_class()
        ):
            return sequence_actor.load_sequence()
    # Check if any sequence is selected in the content browser
    selected_assets = unreal.EditorUtilityLibrary.get_selected_assets()
    if selected_assets:
        for asset in selected_assets:
            if asset.static_class() == unreal.LevelSequence.static_class():
                return asset
    return None


def get_sequence_shots(level_sequence):
    '''
    Returns a list of all shot tracks in the given *level_sequence*.
    '''
    result = []
    master_tracks = level_sequence.get_master_tracks()
    if master_tracks:
        for track in master_tracks:
            if (
                track.static_class()
                == unreal.MovieSceneCinematicShotTrack.static_class()
            ):
                for shot_track in track.get_sections():
                    if (
                        shot_track.static_class()
                        == unreal.MovieSceneCinematicShotSection.static_class()
                    ):
                        result.append(shot_track)

    return result


def get_sequence_context_id():
    '''Read and return the sequence context from the current Unreal project.'''
    context_path = os.path.join(
        asset_const.FTRACK_ROOT_PATH,
        asset_const.SEQUENCE_CONTEXT_STORE_FILE_NAME,
    )
    if not os.path.exists(context_path):
        return None
    return json.load(open(context_path, 'r'))['context_id']


def set_sequence_context_id(context_id):
    '''Write the sequence *context_id* to the current Unreal project.'''
    context_path = os.path.join(
        asset_const.FTRACK_ROOT_PATH,
        asset_const.SEQUENCE_CONTEXT_STORE_FILE_NAME,
    )
    if not os.path.exists(asset_const.FTRACK_ROOT_PATH):
        logger.info(
            'Creating FTRACK_ROOT_PATH: {}'.format(
                asset_const.FTRACK_ROOT_PATH
            )
        )
        os.makedirs(asset_const.FTRACK_ROOT_PATH)
    context_dictionary = {
        "context_id": context_id,
        "date": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "description": "The ftrack sequence context, used with Master sequence shot publisher.",
    }
    with open(context_path, 'w') as f:
        json.dump(context_dictionary, f)
        logger.info(
            'Successfully saved Unreal sequence context to: {}'.format(
                context_path
            )
        )
