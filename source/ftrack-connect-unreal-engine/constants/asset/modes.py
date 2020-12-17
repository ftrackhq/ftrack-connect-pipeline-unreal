# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_unreal_engine.utils import custom_commands as unreal_utils

# Load Modes
IMPORT_MODE = 'Import'
MERGE_MODE = 'Merge'
OPEN_MODE = 'Open'

LOAD_MODES = {
    IMPORT_MODE: unreal_utils.import_scene,
    MERGE_MODE: unreal_utils.merge_scene,
    OPEN_MODE: unreal_utils.open_scene,
}
