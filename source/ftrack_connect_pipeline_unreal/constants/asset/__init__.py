# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack
import os
import unreal

# FTRACK_PLUGIN_ID = 0x190319
FTRACK_PLUGIN_TYPE = 'ftrackAssetNode'
LOCKED = 'locked'
ASSET_LINK = 'asset_link'
NODE_METADATA_TAG = "ftrack"
NODE_SNAPSHOT_METADATA_TAG = "ftrack_snapshot"
FTRACK_ROOT_PATH = os.path.realpath(
    os.path.join(unreal.SystemLibrary.get_project_saved_directory(), "ftrack")
)
ROOT_CONTEXT_STORE_FILE_NAME = "root_context.json"
SEQUENCE_CONTEXT_STORE_FILE_NAME = "sequence_context.json"

from ftrack_connect_pipeline.constants.asset import *
