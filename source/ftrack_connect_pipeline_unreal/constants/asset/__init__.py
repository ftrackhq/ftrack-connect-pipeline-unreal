# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack
import os
import unreal

#FTRACK_PLUGIN_ID = 0x190319
FTRACK_PLUGIN_TYPE = 'ftrackAssetNode' # or 'ftracktab'
LOCKED = 'locked'
ASSET_LINK = 'asset_link'
FTRACK_ROOT_PATH = os.path.join(unreal.Path.project_content_dir, "ftrack")

from ftrack_connect_pipeline.constants.asset import *
