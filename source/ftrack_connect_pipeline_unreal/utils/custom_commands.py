# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack
import glob
import traceback
from functools import wraps
import os
import logging
import sys
import subprocess
import json
import datetime
import shutil

import unreal

import ftrack_api

from ftrack_connect_pipeline.utils import str_version, str_context
from ftrack_connect_pipeline import constants as core_constants
from ftrack_connect_pipeline.asset.asset_info import FtrackAssetInfo

from ftrack_connect_pipeline_unreal.constants import asset as asset_const
from ftrack_connect_pipeline_unreal.asset import UnrealFtrackObjectManager
from ftrack_connect_pipeline_unreal.asset.dcc_object import UnrealDccObject

logger = logging.getLogger(__name__)


### COMMON UTILS ###


def run_in_main_thread(f):
    '''Make sure a function runs in the main Unreal thread.'''

    @wraps(f)
    def decorated(*args, **kwargs):
        # Multithreading is disabled for Unreal integration
        return f(*args, **kwargs)

    return decorated


def init_unreal(context_id=None, session=None):
    '''
    Initialise timeline in Unreal based on shot/asset build settings.

    :param session:
    :param context_id: If provided, the timeline data should be fetched this context instead of environment variables.
    :param session: The session required to query from *context_id*.
    :return:
    '''

    pass


def get_main_window():
    """Return the QMainWindow for the main Unreal window."""
    return None


### OBJECT OPERATIONS ###


def get_ftrack_nodes():
    ftrack_nodes = []
    if not os.path.exists(asset_const.FTRACK_ROOT_PATH):
        return ftrack_nodes
    content = os.listdir(asset_const.FTRACK_ROOT_PATH)
    for item_name in content:
        if not "ftrackdata" in item_name:
            continue
        if item_name.endswith(".json"):
            ftrack_nodes.append(os.path.splitext(item_name)[0])
    return ftrack_nodes  # str ["xxxx_ftrackdata_3642"] == list of node names


def get_current_scene_objects():
    '''Returns all the objects in the scene'''
    # Return the list of all the assets found in the DirectoryPath.
    # https://docs.unrealengine.com/5.1/en-US/PythonAPI/class/EditorAssetLibrary.html?highlight=editorassetlibrary#unreal.EditorAssetLibrary
    return set(unreal.EditorAssetLibrary.list_assets("/Game", recursive=True))


def collect_children_nodes(node):
    '''Return all the children of the given *node*'''
    # child_nodes = []
    # for child in node.Children:
    #     _collect_children_nodes(child, child_nodes)
    #
    # return child_nodes
    pass


def _collect_children_nodes(n, nodes):
    '''Private function to recursively return children of the given *nodes*'''
    # for child in n.Children:
    #     _collect_children_nodes(child, nodes)
    #
    # nodes.append(n)
    pass


def delete_all_children(node):
    '''Delete all children from the given *node*'''
    # all_children = collect_children_nodes(node)
    # for node in all_children:
    #     rt.delete(node)
    # return all_children
    pass


def node_exists(node_name):
    '''Check if node_name exist in the project'''
    for content in unreal.EditorAssetLibrary.list_assets(
        "/Game", recursive=True
    ):
        if node_name in content:
            return True
    return False


def ftrack_node_exists(dcc_object_name):
    '''Check if ftrack node identified by *node_name* exist in the project'''
    dcc_object_node = None
    ftrack_nodes = get_ftrack_nodes()
    for node in ftrack_nodes:
        if node == dcc_object_name:
            dcc_object_node = node
            break
    return dcc_object_node is not None


def get_asset_by_path(node_name):
    '''Get Unreal asset object by path'''
    if not node_name:
        return None
    assetRegistry = unreal.AssetRegistryHelpers.get_asset_registry()
    asset_data = assetRegistry.get_assets_by_package_name(
        os.path.splitext(node_name)[0]
    )
    if asset_data:
        return asset_data[0].get_asset()
    return None


def get_asset_by_class(class_name):
    return [
        asset
        for asset in unreal.AssetRegistryHelpers.get_asset_registry().get_all_assets()
        if asset.get_class().get_name() == class_name
    ]


def delete_node(node_name):
    '''Delete the given *node_name*'''
    return unreal.EditorAssetLibrary.delete_asset(node_name)


def delete_ftrack_node(dcc_object_name):
    dcc_object_node = None
    ftrack_nodes = get_ftrack_nodes()
    for node in ftrack_nodes:
        if node == dcc_object_name:
            dcc_object_node = node
            break
    if not dcc_object_node:
        return False
    path_dcc_object_node = '{}{}{}.json'.format(
        asset_const.FTRACK_ROOT_PATH, os.sep, dcc_object_node
    )
    if os.path.exists(path_dcc_object_node):
        return os.remove(path_dcc_object_node)
    return False


def get_connected_nodes_from_dcc_object(dcc_object_name):
    '''Return all objects connected to the given *dcc_object_name*'''
    objects = []
    dcc_object_node = None
    ftrack_nodes = get_ftrack_nodes()
    for node in ftrack_nodes:
        if node == dcc_object_name:
            dcc_object_node = node
            break
    if not dcc_object_node:
        return
    path_dcc_object_node = '{}{}{}.json'.format(
        asset_const.FTRACK_ROOT_PATH, os.sep, dcc_object_node
    )
    with open(
        path_dcc_object_node,
        'r',
    ) as openfile:
        param_dict = json.load(openfile)
    id_value = param_dict.get(asset_const.ASSET_INFO_ID)
    for node_name in get_current_scene_objects():
        asset = get_asset_by_path(node_name)
        for metadata_tag in [
            asset_const.NODE_METADATA_TAG,
            asset_const.NODE_SNAPSHOT_METADATA_TAG,
        ]:
            ftrack_value = unreal.EditorAssetLibrary.get_metadata_tag(
                asset, metadata_tag
            )
            if id_value == ftrack_value:
                objects.append(node_name)
    return objects


def get_asset_info(node_name, snapshot=False):
    '''Return the asset info from dcc object linked to asset path identified by *node_name*'''

    asset = get_asset_by_path(node_name)
    if asset is None:
        logger.warning(
            '(get_asset_info) Cannot find asset by path: {}'.format(node_name)
        )
        return None, None
    ftrack_value = unreal.EditorAssetLibrary.get_metadata_tag(
        asset,
        asset_const.NODE_METADATA_TAG
        if not snapshot
        else asset_const.NODE_SNAPSHOT_METADATA_TAG,
    )

    for dcc_object_node in get_ftrack_nodes():
        path_dcc_object_node = '{}{}{}.json'.format(
            asset_const.FTRACK_ROOT_PATH, os.sep, dcc_object_node
        )
        with open(
            path_dcc_object_node,
            'r',
        ) as openfile:
            param_dict = json.load(openfile)
        id_value = param_dict.get(asset_const.ASSET_INFO_ID)
        if id_value == ftrack_value:
            return dcc_object_node, param_dict
    return None, None


def conditional_remove_metadata_tag(node_name, metadata_tag):
    '''Remove *metadata_tag* from the given *node_name*, returns True if found'''
    asset = get_asset_by_path(node_name)
    ftrack_value = unreal.EditorAssetLibrary.get_metadata_tag(
        asset, metadata_tag
    )
    if ftrack_value:
        unreal.EditorAssetLibrary.remove_metadata_tag(asset, metadata_tag)
        # Have Unreal save the asset as it has been modified
        unreal.EditorAssetLibrary.save_asset(node_name)
        return True
    else:
        return False


### SEQUENCER ###


def get_all_sequences(as_names=True):
    '''
    Returns a list of all sequence assets used in level. If *as_names* is True, the asset name will be used instead of the asset itself.
    '''
    result = []
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    for actor in actors:
        if actor.static_class() == unreal.LevelSequenceActor.static_class():
            level_sequence = actor.load_sequence()
            value = level_sequence.get_name() if as_names else level_sequence
            if not value in result:
                result.append(value)
            break
    return result


def get_selected_sequence():
    '''Return the selected level sequence asset or None if no sequence is selected.'''
    for (
        sequence_actor
    ) in unreal.EditorLevelLibrary.get_selected_level_actors():
        if (
            sequence_actor.static_class()
            == unreal.LevelSequenceActor.static_class()
        ):
            return sequence_actor.load_sequence()
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


### SELECTION ###


def select_all():
    '''Select all objects from the scene'''
    # return rt.select(rt.objects)
    pass


def deselect_all():
    '''Clear the selection'''
    # rt.clearSelection()
    pass


def add_node_to_selection(node):
    '''Add the given *node* to the current selection'''
    # rt.selectMore(node)
    pass


def create_selection_set(set_name):
    '''Create a new selection set containing the current selection.'''
    # rt.selectionSets[set_name] = rt.selection
    pass


def selection_empty():
    '''Empty the current selection'''
    # return rt.selection.count == 0
    pass


def select_only_type(obj_type):
    '''Select all *obj_type* from the scene'''
    # selected_cameras = []
    # for obj in rt.selection:
    #     if rt.SuperClassOf(obj) == obj_type:
    #         selected_cameras.append(obj)
    # return selected_cameras
    pass


### FILE OPERATIONS ###

# TODO: Find a better name for this function. This is not a relative path.
def get_context_relative_path(session, ftrack_task):
    # location.
    links_for_task = session.query(
        'select link from Task where id is "{}"'.format(ftrack_task['id'])
    ).first()['link']
    relative_path = ""
    # remove the project
    links_for_task.pop(0)
    for link in links_for_task:
        relative_path += link['name'].replace(' ', '_')
        relative_path += '/'
    return relative_path


def open_file(path, options, session):
    '''Open an Unreal level or asset file pointed out by *path* - copy to local project content browser based on context passed
    with *options* using *session* object'''

    filename, extension = os.path.splitext(os.path.basename(path))

    version_id = options['version_id']

    asset_version = session.query(
        'AssetVersion where id={}'.format(version_id)
    ).one()

    asset = session.query(
        'select name from Asset where id is "{}"'.format(
            asset_version['asset_id']
        )
    ).first()

    root_context_id = get_root_context_id()

    if root_context_id is None:
        logger.warning(
            'Need project root context ID set to be able to evaluate Unreal asset content browser path'
        )

    found_root_context = False
    link = []
    parent_context = asset
    while parent_context:
        if parent_context['id'] == root_context_id:
            found_root_context = True
            break
        link.insert(0, parent_context['name'])
        if (
            parent_context.entity_type == 'Project'
            or not 'parent' in parent_context
        ):
            # Stop here
            break
        parent_context = session.query(
            'select name from Context where id is "{}"'.format(
                parent_context['parent']['id']
            )
        ).first()

    root_content_dir = (
        unreal.SystemLibrary.get_project_content_directory().replace(
            '/', os.sep
        )
    )
    if found_root_context:
        # Import relative to project root context, remove Content start folder and cut off asset build part
        filename = '{}{}'.format(asset['name'], extension)
        import_path = os.path.join(root_content_dir, os.sep.join(link[1:-2]))
    else:
        # Import relative to project root
        import_path = os.path.join(root_content_dir, os.sep.join(link))
    import_path = os.path.join(import_path, filename)

    parent = os.path.dirname(import_path)
    if not os.path.exists(parent):
        os.makedirs(parent)
    shutil.copy(path, import_path)
    return import_path


def get_dependencies_from_metadata(asset_version):
    dependencies = None
    if core_constants.PIPELINE_METADATA_KEY in list(
        asset_version['metadata'].keys()
    ):
        metadata = json.loads(
            asset_version['metadata'][core_constants.PIPELINE_METADATA_KEY]
        )
        if 'dependencies' in metadata:
            dependencies = metadata.get('dependencies', [])
    return dependencies


def import_dependencies(version_id, event_manager, provided_logger=None):
    '''Recursive import all dependencies of the given *version_id* using *session* object logging woth *provided_logger*. Returns a list
    of messages about the import process.'''

    result = []

    logger_effective = provided_logger or logger

    def add_message(message):
        print(message)
        logger_effective.info(message)
        result.append(message)

    asset_version = event_manager.session.query(
        'AssetVersion where id="{}"'.format(version_id)
    ).one()
    ident = str_version(asset_version, by_task=False)

    location = event_manager.session.pick_location()

    dependencies = get_dependencies_from_metadata(asset_version)
    if not dependencies:
        add_message('No dependencies found for {}'.format(ident))
        return result

    if not os.path.exists(asset_const.FTRACK_ROOT_PATH):
        os.makedirs(asset_const.FTRACK_ROOT_PATH)

    for asset_info in [
        FtrackAssetInfo(asset_info_raw) for asset_info_raw in dependencies
    ]:
        dependency_ident = str(asset_info)
        try:
            # Fetch the version
            dependency_asset_version = event_manager.session.query(
                'AssetVersion where id="{}"'.format(
                    asset_info[asset_const.VERSION_ID]
                )
            ).one()
            dependency_ident = str_version(
                dependency_asset_version, by_task=False
            )

            # Is it available in this location?
            component = event_manager.session.query(
                'Component where id="{}"'.format(
                    asset_info[asset_const.COMPONENT_ID]
                )
            ).one()
            if location.get_component_availability(component) != 100.0:
                add_message(
                    'Asset "{}" is not available in current location ({})'.format(
                        dependency_ident, location['name']
                    )
                )
                continue

            # Check if asset is already tracked in Unreal
            ftrack_object_manager = UnrealFtrackObjectManager(event_manager)
            ftrack_object_manager.asset_info = asset_info
            dcc_object = UnrealDccObject()
            dcc_object.name = ftrack_object_manager.generate_dcc_object_name()
            if dcc_object.exists():
                add_message(
                    'Asset "{}" already tracked in Unreal, removing!'.format(
                        dependency_ident
                    )
                )
                delete_ftrack_node(dcc_object.name)

            # Bring it in
            run_event = ftrack_api.event.base.Event(
                topic=core_constants.PIPELINE_RUN_PLUGIN_TOPIC,
                data=asset_info[asset_const.ASSET_INFO_OPTIONS],
            )

            logger_effective.debug(
                'Loading dependency, event: {}'.format(run_event)
            )

            plugin_result_dataset = event_manager.session.event_hub.publish(
                run_event, synchronous=True
            )
            # Did import go well?
            if not plugin_result_dataset:
                add_message(
                    'Failed to import asset {} - no result'.format(
                        dependency_ident
                    )
                )
                continue
            plugin_result_data = plugin_result_dataset[0]
            if (
                plugin_result_data.get('status')
                != core_constants.SUCCESS_STATUS
            ):
                add_message(
                    'Failed to import asset {}. Details: {}'.format(
                        dependency_ident, plugin_result_data
                    )
                )
                continue

            logger_effective.debug(
                'Dependency load result: {}'.format(plugin_result_data)
            )

            asset_filesystem_path = list(
                list(plugin_result_data['result'].values())[0][
                    'result'
                ].values()
            )[0]
            imported_asset_info = list(plugin_result_data['result'].values())[
                0
            ]['asset_info']

            add_message(
                'Imported asset {} to: "{}"'.format(
                    dependency_ident, asset_filesystem_path
                )
            )

            # Import dependencies of this asset
            result.extend(
                import_dependencies(
                    dependency_asset_version['id'],
                    event_manager,
                    logger_effective,
                )
            )
        except:
            add_message(traceback.format_exc())
            add_message(
                'An exception occurred when attempting to import dependency {}'.format(
                    dependency_ident
                )
            )
    return result


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


#### PROJECT LEVEL ASSET PUBLISH AND LOAD ####


def get_root_context_id():
    '''Read and return the project context from the current Unreal project.'''
    context_path = os.path.join(
        asset_const.FTRACK_ROOT_PATH,
        asset_const.ROOT_CONTEXT_STORE_FILE_NAME,
    )
    if not os.path.exists(context_path):
        return None
    return json.load(open(context_path, 'r'))['context_id']


def set_root_context_id(context_id):
    '''Write the project context to the current Unreal project.'''
    context_path = os.path.join(
        asset_const.FTRACK_ROOT_PATH,
        asset_const.ROOT_CONTEXT_STORE_FILE_NAME,
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
        "description": "The ftrack project level context id, bound to the Unreal project.",
    }
    with open(context_path, 'w') as f:
        json.dump(context_dictionary, f)
        logger.debug(
            'Successfully saved Unreal project context to: {}'.format(
                context_path
            )
        )


#### ASSET PATHS  ####


def sanitize_asset_path(asset_path):
    '''Convert given *asset_path* to a content-browser like path'''
    # TODO: should ask epic at some point to get the full path as its shown in
    #  the content browser so we don't have to "magically" change it here
    asset_path_sanitized = asset_path.replace('/Game', 'Content')
    return asset_path_sanitized


def ftrack_asset_path_exist(root_context_id, asset_path, session):
    '''Check if the given *full_ftrack_path* exist in the ftrack platform'''
    parent_context = session.query(
        'Context where id is "{}"'.format(root_context_id)
    ).one()
    if not parent_context:
        return False
    full_ftrack_path = sanitize_asset_path(asset_path)
    # Split asset path in array parts
    asset_path_parts = full_ftrack_path.split('/')
    # Get index of the root to support full path and asset path
    if parent_context['name'] not in asset_path_parts:
        start_idx = None
    else:
        start_idx = asset_path_parts.index(parent_context['name'])
    if start_idx or start_idx == 0:
        asset_path_parts = asset_path_parts[start_idx + 1 :]

    # Check from the root forward
    for index, part in enumerate(asset_path_parts):
        # Check if current part already exists
        child_context = session.query(
            'select id,name from Context where parent.id is "{0}" and name="{1}"'.format(
                parent_context['id'], part
            )
        ).first()
        if not child_context:
            return False
        parent_context = child_context
    return True


def get_ftrack_ancestors_names(ftrack_object):
    '''Returns ancestor names of the given ftrack_object'''
    return list(x['name'] for x in list(ftrack_object['ancestors']))


def get_full_ftrack_asset_path(root_context_id, asset_path, session):
    '''Given the *root_context_id* and the *asset_path*,
    returns the full path for the ftrack platform'''
    # Sanitize asset_path
    asset_path_sanitized = sanitize_asset_path(asset_path)
    # Get context(AB,Asset,Folder) ftrack object of the root_context_id
    parent_context = session.query(
        'Context where id is "{}"'.format(root_context_id)
    ).one()
    if not parent_context:
        raise Exception(
            'Could not find the root context object in ftrack, '
            'Please make sure the Root is created in your project.'
        )
    # Get project ftrack object from where our root_context_id is pointing.
    project = session.query(
        'Project where id="{}"'.format(parent_context['project_id'])
    ).one()

    # Get ancestors from root to project
    ancestor_names = get_ftrack_ancestors_names(parent_context)

    # Generate full path
    full_path = os.path.join(
        project['name'],
        *ancestor_names,
        parent_context['name'],
        *asset_path_sanitized.split('/')
    )
    return full_path.replace("\\", "/")


def filesystem_asset_path_to_asset_path(full_asset_path):
    '''Converts a full asset filesystem path to an asset path'''
    root_content_dir = (
        unreal.SystemLibrary.get_project_content_directory().replace(
            '/', os.sep
        )
    )
    if len(full_asset_path) > len(root_content_dir):
        result = '{}Game{}{}'.format(
            os.sep, os.sep, full_asset_path[len(root_content_dir) :]
        )
    else:
        result = full_asset_path  # Already an asset path
    return os.path.join(
        os.path.dirname(result), os.path.splitext(os.path.basename(result))[0]
    ).replace(
        '\\', '/'
    )  # Remove extension


def asset_path_to_filesystem_path(asset_path, root_content_dir=None):
    '''Converts *asset_path* to a full absolute asset filesystem path. Use the provided *root_content_dir*.'''
    if root_content_dir is None:
        root_content_dir = (
            unreal.SystemLibrary.get_project_content_directory().replace(
                '/', os.sep
            )
        )
    if asset_path.lower().startswith('/game/'):
        asset_path = asset_path[6:]  # Remove /Game/ prefix
    path = os.path.join(root_content_dir, asset_path.replace('/', os.sep))
    # Probe our way to finding out the extension as we can't tell from the asset path
    for ext in ['', '.uasset', '.umap']:
        result = '{}{}'.format(path, ext)
        if os.path.exists(result):
            return result
    raise Exception(
        'Could not determine asset "{}" files extension on disk!'.format(path)
    )


#### ASSET <> ASSET BUILD SYNCHRONISATION  ####


def get_asset_build_form_path(root_context_id, asset_path, session):
    '''Check if the given *full_ftrack_path* exist in the ftrack platform'''
    parent_context = session.query(
        'Context where id is "{}"'.format(root_context_id)
    ).one()
    if not parent_context:
        return
    full_ftrack_path = sanitize_asset_path(asset_path)
    # Split asset path in array parts
    asset_path_parts = full_ftrack_path.split('/')
    # Get index of the root to support full path and asset path
    if parent_context['name'] not in asset_path_parts:
        start_idx = None
    else:
        start_idx = asset_path_parts.index(parent_context['name'])
    if start_idx or start_idx == 0:
        asset_path_parts = asset_path_parts[start_idx + 1 :]

    child_context = None
    # Check from the root forward
    for index, part in enumerate(asset_path_parts):
        # Check if current part already exists
        child_context = session.query(
            'select id,name from Context where parent.id is "{0}" and name="{1}"'.format(
                parent_context['id'], part
            )
        ).first()

        if not child_context:
            return

        parent_context = child_context
    return child_context


def get_temp_asset_build(root_context_id, asset_path, session):
    '''Returns the temp asset build under the given *root_context_id*, basing the name on *asset_path* using *session*'''

    asset_path = sanitize_asset_path(asset_path)
    parent_context = session.query(
        'Context where id is "{}"'.format(root_context_id)
    ).one()
    if not parent_context:
        raise Exception(
            'Could not find the root context object in ftrack, '
            'Please make sure the Root is created in your project.'
        )
    # Get project ftrack object from where our root_context_id is pointing.
    project = session.query(
        'Project where id="{}"'.format(parent_context['project_id'])
    ).one()

    # Split asset path in array parts
    asset_path_parts = asset_path.split('/')

    # Get Object type
    objecttype_assetbuild = session.query(
        'ObjectType where name="{}"'.format('Asset Build')
    ).one()
    schema = session.query(
        'Schema where project_schema_id="{0}" and object_type_id="{1}"'.format(
            project['project_schema_id'],
            objecttype_assetbuild['id'],
        )
    ).one()
    statuses = project['project_schema'].get_statuses('AssetVersion')
    preferred_assetbuild_type = assetbuild_type = None
    for typ in session.query(
        'SchemaType where schema_id="{0}"'.format(schema['id'])
    ).all():
        assetbuild_type = session.query(
            'Type where id="{0}"'.format(typ['type_id'])
        ).first()
        if assetbuild_type['name'] == 'Prop':
            preferred_assetbuild_type = assetbuild_type
            break
    if not assetbuild_type:
        raise Exception(
            'Could not find a asset build type to be used when '
            'creating the Unreal project level asset build!'
        )
    # Get status
    preferred_assetbuild_status = assetbuild_status = None
    for st in session.query(
        'SchemaStatus where schema_id="{0}"'.format(schema['id'])
    ).all():
        assetbuild_status = session.query(
            'Status where id="{0}"'.format(st['status_id'])
        ).first()
        if assetbuild_status['name'] == 'Completed':
            preferred_assetbuild_status = assetbuild_status
            break
    if not assetbuild_status:
        raise Exception(
            'Could not find a asset build status to be used when '
            'creating the Unreal project level asset build!'
        )

    # Create an asset build
    child_context = session.create(
        'AssetBuild',
        {
            'name': asset_path_parts[-1],
            'parent': parent_context,
            'type': preferred_assetbuild_type or assetbuild_type,
            'status': preferred_assetbuild_status or assetbuild_status,
        },
    )
    return child_context, statuses


def push_asset_build_to_server(root_context_id, asset_path, session):
    '''
    Ensure that an asset build structure exists on the *asset_path* relative
    *root_context_id*
    '''
    asset_path = sanitize_asset_path(asset_path)
    parent_context = session.query(
        'Context where id is "{}"'.format(root_context_id)
    ).one()
    if not parent_context:
        raise Exception(
            'Could not find the root context object in ftrack, '
            'Please make sure the Root is created in your project.'
        )
    project = session.query(
        'Project where id="{}"'.format(parent_context['project_id'])
    ).one()

    # Split asset path in array parts
    asset_path_parts = asset_path.split('/')
    # Get index of the root to support full path and asset path
    if parent_context['name'] not in asset_path_parts:
        start_idx = None
    else:
        start_idx = asset_path_parts.index(parent_context['name'])
    if start_idx or start_idx == 0:
        asset_path_parts = asset_path_parts[start_idx + 1 :]

    for index, part in enumerate(asset_path_parts):
        # Check if current part already exists
        child_context = session.query(
            'select id,name from Context where parent.id is "{0}" and name="{1}"'.format(
                parent_context['id'], part
            )
        ).first()
        if not child_context:
            # Create it
            if index < len(asset_path_parts) - 1:
                # Create a folder
                child_context = session.create(
                    'Folder',
                    {
                        'name': part,
                        'parent': parent_context,
                    },
                )
                session.commit()
                logger.info(
                    'Created Unreal project level folder: {}'.format(
                        child_context['name']
                    )
                )
            else:
                # Find out possible asset build types
                objecttype_assetbuild = session.query(
                    'ObjectType where name="{}"'.format('Asset Build')
                ).one()
                schema = session.query(
                    'Schema where project_schema_id="{0}" and object_type_id="{1}"'.format(
                        project['project_schema_id'],
                        objecttype_assetbuild['id'],
                    )
                ).one()
                preferred_assetbuild_type = assetbuild_type = None
                for typ in session.query(
                    'SchemaType where schema_id="{0}"'.format(schema['id'])
                ).all():
                    assetbuild_type = session.query(
                        'Type where id="{0}"'.format(typ['type_id'])
                    ).first()
                    if assetbuild_type['name'] == 'Prop':
                        preferred_assetbuild_type = assetbuild_type
                        break
                if not assetbuild_type:
                    raise Exception(
                        'Could not find a asset build type to be used when '
                        'creating the Unreal project level asset build!'
                    )
                preferred_assetbuild_status = assetbuild_status = None
                for st in session.query(
                    'SchemaStatus where schema_id="{0}"'.format(schema['id'])
                ).all():
                    assetbuild_status = session.query(
                        'Status where id="{0}"'.format(st['status_id'])
                    ).first()
                    if assetbuild_status['name'] == 'Completed':
                        preferred_assetbuild_status = assetbuild_status
                        break
                if not assetbuild_status:
                    raise Exception(
                        'Could not find a asset build status to be used when '
                        'creating the Unreal project level asset build!'
                    )
                # Create an asset build
                child_context = session.create(
                    'AssetBuild',
                    {
                        'name': part,
                        'parent': parent_context,
                        'type': preferred_assetbuild_type or assetbuild_type,
                        'status': preferred_assetbuild_status
                        or assetbuild_status,
                    },
                )
                session.commit()
                logger.info(
                    'Created Unreal project level asset build: {}'.format(
                        child_context['name']
                    )
                )

        parent_context = child_context
    return parent_context


#### SEQUENCE LEVEL SHOT PUBLIS ####


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
    '''Write the sequence context to the current Unreal project.'''
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
        logger.debug(
            'Successfully saved Unreal sequence context to: {}'.format(
                context_path
            )
        )


#### SEQUENCER SHOT <> SHOT SYNCHRONISATION  ####


def push_shot_to_server(
    sequence_context_id, shot_name, session, start=None, end=None
):
    '''Created a shot named *shot_name* in the sequence with the given *sequence_context_id*, using the supplied *session*.
    If shot exists, return the existing shot.'''

    parent_context = session.query(
        'Context where id is "{}"'.format(sequence_context_id)
    ).one()
    if not parent_context:
        raise Exception(
            'Could not find the sequence context object in ftrack, '
            'Please make sure the Root is created in your project.'
        )

    sequence_ident = str_context(parent_context)

    # Do not check if it is an actual sequence context, shots are allowed many types context

    # Find shot
    shot_entity = session.query(
        'Shot where name is "{}" and parent_id is "{}"'.format(
            shot_name, parent_context['id']
        )
    ).first()

    if not shot_entity:
        logger.info(
            'Creating shot "{}" beneath {}'.format(shot_name, sequence_ident)
        )
        shot_entity = session.create(
            'Shot',
            {
                'name': shot_name,
                'parent': parent_context,
            },
        )
        session.commit()

    shot_ident = str_context(shot_entity)

    if 'fstart' in shot_entity['custom_attributes'] and start is not None:
        prev_start = shot_entity['custom_attributes']['fstart']
        if prev_start is None:
            prev_start = -1
        if start > -1 and prev_start != start:
            logger.info(
                'Updating shot {} start frame {} > {}'.format(
                    shot_ident, prev_start, start
                )
            )
            shot_entity['custom_attributes']['fstart'] = start
    if 'fend' in shot_entity['custom_attributes'] and end is not None:
        prev_end = shot_entity['custom_attributes']['fend']
        if prev_end is None:
            prev_end = -1
        if end > -1 and prev_end != end:
            logger.info(
                'Updating shot {} end frame {} > {}'.format(
                    shot_ident, prev_end, end
                )
            )
            shot_entity['custom_attributes']['fend'] = end
    return shot_entity


#### UNREAL DEPENDENCY RESOLVE  ####


def get_asset_dependencies(
    parent_asset_path,
    recursive=False,
    include_hard_management_references=True,
    include_hard_package_references=True,
    include_searchable_names=False,
    include_soft_management_references=False,
    include_soft_package_references=False,
):
    '''Return a list of asset dependencies for the given *asset_path*. If *recursive* is True, return all dependencies
    recursively, otherwise only return direct dependencies.

    Populate the Unreal dependencys options with *include_hard_management_references*,
    *include_hard_package_references*, *include_searchable_names*, *include_soft_management_references* and
    *include_soft_package_references*.
    '''

    # https://docs.unrealengine.com/4.27/en-US/PythonAPI/class/AssetRegistry.html?highlight=assetregistry#unreal.AssetRegistry.get_dependencies
    # Setup dependency options
    dep_options = unreal.AssetRegistryDependencyOptions(
        include_hard_management_references=include_hard_management_references,
        include_hard_package_references=include_hard_package_references,
        include_searchable_names=include_searchable_names,
        include_soft_management_references=include_soft_management_references,
        include_soft_package_references=include_soft_package_references,
    )
    # Start asset registry
    asset_reg = unreal.AssetRegistryHelpers.get_asset_registry()

    result = []

    def conditional_add_asset_path(asset_path):
        '''Add the given *asset_path* to the result list if it is in Game and not already in the result list.'''
        asset_path = os.path.splitext(asset_path)[0]
        if asset_path.lower().startswith('/game/') and not (
            asset_path == parent_asset_path or asset_path in result
        ):
            result.append(asset_path)

    def _get_asset_dependencies(asset_path):
        '''Get asset dependencies for the given *asset_path* and them to result.'''

        if asset_path in result:
            return []

        # Get dependencies for the given asset
        dependencies = [
            str(dep)
            for dep in (
                asset_reg.get_dependencies(
                    asset_path.split('.')[0], dep_options
                )
                or []
            )
        ]

        # Filter out only dependencies that are in Game
        game_dependencies = []

        for dep in dependencies:
            conditional_add_asset_path(dep)

        result.extend(game_dependencies)

        if recursive:
            # Get dependencies for all dependencies
            for dep in game_dependencies:
                _get_asset_dependencies(dep)

    _get_asset_dependencies(parent_asset_path)

    return result


def get_level_dependencies(recursive=False):
    '''Return a list of asset dependencies for the current level. If *recursive* is True, return asset dependencies.'''

    level_path = str(
        unreal.EditorLevelLibrary.get_editor_world().get_path_name()
    )

    result = []

    def conditional_add_asset_path(asset_path):
        '''Add the given *asset_path* to the result list if it is a game asset and not already resolved or is the level itself.'''
        asset_path = os.path.splitext(asset_path)[0]
        # Make sure it is a game asset and not already resolved
        if asset_path.lower().startswith('/game/') and not (
            asset_path == level_path or asset_path in result
        ):
            result.append(asset_path)
            if recursive:
                for dep in get_asset_dependencies(asset_path):
                    conditional_add_asset_path(dep)

    for actor in unreal.EditorLevelLibrary.get_all_level_actors():

        try:  # Do not stumble on exceptions here
            if actor.static_class() == unreal.SkeletalMeshActor.static_class():
                skeletal_mesh_component = actor.skeletal_mesh_component
                if skeletal_mesh_component:
                    skeletal_mesh_asset = (
                        skeletal_mesh_component.skeletal_mesh_asset
                    )
                    if skeletal_mesh_asset:
                        conditional_add_asset_path(
                            skeletal_mesh_asset.get_path_name()
                        )
                    skinned_asset_asset = skeletal_mesh_component.skinned_asset
                    if skinned_asset_asset:
                        conditional_add_asset_path(
                            skinned_asset_asset.get_path_name()
                        )
            elif (
                actor.static_class()
                == unreal.LevelSequenceActor.static_class()
            ):
                sequence_asset = actor.load_sequence()
                if sequence_asset:
                    conditional_add_asset_path(sequence_asset.get_path_name())
            elif actor.static_class() == unreal.Actor.static_class():
                # Probably a blueprint
                cls = actor.get_class()
                conditional_add_asset_path(cls.get_path_name())

            # TODO: Make sure we cover all actor types and are able to extract asset dependencies accordingly

        except Exception as e:
            logger.error(e)
            print(traceback.format_exc())

    return result


### TIME OPERATIONS ###


def get_time_range():
    '''Return the start and end frame of the current scene'''
    # start = rt.animationRange.start
    # end = rt.animationRange.end
    # return (start, end)
    pass


### RENDERING ###


def compile_capture_args(options):
    capture_args = []
    if 'resolution' in options:
        resolution = options['resolution']  # On the form 320x240(4:3)
        parts = resolution.split('(')[0].split('x')
        capture_args.append('-ResX={}'.format(parts[0]))
        capture_args.append('-ResY={}'.format(parts[1]))
    if 'movie_quality' in options:
        quality = int(options['movie_quality'])
        capture_args.append(
            '-MovieQuality={}'.format(max(0, min(quality, 100)))
        )
    return capture_args


def render(
    sequence_path,
    unreal_map_path,
    content_name,
    destination_path,
    fps,
    capture_args,
    logger,
    image_format=None,
    frame=None,
):
    '''
    Render a video or image sequence from the given sequence actor.

    :param sequence_path: The path of the sequence within the level.
    :param unreal_map_path: The level to render.
    :param content_name: The name of the render.
    :param destination_path: The path to render to.
    :param fps: The framerate.
    :param capture_args: White space separate list of additional capture arguments.
    :param logger: A logger to log to.
    :param image_format: (Optional) The image sequence file format, if None a video (.avi) will be rendered.
    :param frame: (Optional) The target frame to render within sequence.
    :return:
    '''

    def __generate_target_file_path(
        destination_path, content_name, image_format, frame
    ):
        '''Generate the output file path based on *destination_path* and *content_name*'''
        # Sequencer can only render to avi file format
        if image_format is None:
            output_filename = '{}.avi'.format(content_name)
        else:
            if frame is None:
                output_filename = (
                    '{}'.format(content_name)
                    + '.{frame}.'
                    + '{}'.format(image_format)
                )
            else:
                output_filename = '{}.{}.{}'.format(
                    content_name, '%04d' % frame, image_format
                )
        output_filepath = os.path.join(destination_path, output_filename)
        return output_filepath

    def __build_process_args(
        sequence_path,
        unreal_map_path,
        content_name,
        destination_path,
        fps,
        image_format,
        capture_args,
        frame,
    ):
        '''Build unreal command line arguments based on the arguments given.'''
        # Render the sequence to a movie file using the following
        # command-line arguments
        cmdline_args = []

        # Note that any command-line arguments (usually paths) that could
        # contain spaces must be enclosed between quotes
        unreal_exec_path = '"{}"'.format(sys.executable)

        # Get the Unreal project to load
        unreal_project_filename = '{}.uproject'.format(
            unreal.SystemLibrary.get_game_name()
        )
        unreal_project_path = os.path.join(
            unreal.SystemLibrary.get_project_directory(),
            unreal_project_filename,
        )
        unreal_project_path = '"{}"'.format(unreal_project_path)

        # Important to keep the order for these arguments
        cmdline_args.append(unreal_exec_path)  # Unreal executable path
        cmdline_args.append(unreal_project_path)  # Unreal project
        cmdline_args.append(
            unreal_map_path
        )  # Level to load for rendering the sequence

        # Command-line arguments for Sequencer Render to Movie
        # See: https://docs.unrealengine.com/en-us/Engine/Sequencer/
        #           Workflow/RenderingCmdLine
        sequence_path = '-LevelSequence={}'.format(sequence_path)
        cmdline_args.append(sequence_path)  # The sequence to render

        output_path = '-MovieFolder="{}"'.format(destination_path)
        cmdline_args.append(
            output_path
        )  # exporters folder, must match the work template

        movie_name_arg = '-MovieName={}'.format(content_name)
        cmdline_args.append(movie_name_arg)  # exporters filename

        cmdline_args.append("-game")
        cmdline_args.append(
            '-MovieSceneCaptureType=/Script/MovieSceneCapture.'
            'AutomatedLevelSequenceCapture'
        )
        cmdline_args.append("-ForceRes")
        cmdline_args.append("-Windowed")
        cmdline_args.append("-MovieCinematicMode=yes")
        if image_format is not None:
            cmdline_args.append("-MovieFormat={}".format(image_format.upper()))
        else:
            cmdline_args.append("-MovieFormat=Video")
        cmdline_args.append("-MovieFrameRate=" + str(fps))
        if frame is not None:
            cmdline_args.append("-MovieStartFrame={}".format(frame))
            cmdline_args.append("-MovieEndFrame={}".format(frame))
        cmdline_args.extend(capture_args)
        cmdline_args.append("-NoTextureStreaming")
        cmdline_args.append("-NoLoadingScreen")
        cmdline_args.append("-NoScreenMessages")
        return cmdline_args

    try:
        # Check if any existing files
        if os.path.exists(destination_path) and os.path.isfile(
            destination_path
        ):
            logger.warning(
                'Removing existing destination file: "{}"'.format(
                    destination_path
                )
            )
            os.remove(destination_path)
        if os.path.exists(destination_path):
            for fn in os.listdir(destination_path):
                # Remove files having the same prefix as destination file
                if fn.split('.')[0] == content_name:
                    file_path = os.path.join(destination_path, fn)
                    logger.warning(
                        'Removing existing file: "{}"'.format(file_path)
                    )
                    os.remove(file_path)
        else:
            # Create it
            logger.info(
                'Creating output folder: "{}"'.format(destination_path)
            )
            os.makedirs(destination_path)
    except Exception as e:
        logger.exception(e)
        msg = (
            'Could not delete {} contents. The Sequencer will not be able to'
            ' exporters the media to that location.'.format(destination_path)
        )
        logger.error(msg)
        return False, {'message': msg}

    output_filepath = __generate_target_file_path(
        destination_path, content_name, image_format, frame
    )

    # Unreal will be started in game mode to render the video
    cmdline_args = __build_process_args(
        sequence_path,
        unreal_map_path,
        content_name,
        destination_path,
        fps,
        image_format,
        capture_args,
        frame,
    )

    logger.debug('Sequencer command-line arguments: {}'.format(cmdline_args))

    # Send the arguments as a single string because some arguments could
    # contain spaces and we don't want those to be quoted
    envs = os.environ.copy()
    envs.update({'FTRACK_CONNECT_DISABLE_INTEGRATION_LOAD': '1'})
    subprocess.call(' '.join(cmdline_args), env=envs)

    return output_filepath


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
            sequence_path, start, end = find_image_sequence(shot_render_folder)

            if movie_path or sequence_path:
                return movie_path, sequence_path, start, end

    return error_message


def find_image_sequence(render_folder):
    '''Try to find a continous image sequence in the *render_folder*, Unreal always names frames "Image.0001.png".
    Will return the clique parsable expression together with first and last frame number.'''

    if not render_folder or not os.path.exists(render_folder):
        return None, -1, -1

    # Search folder for images sequence, extract minimum and maximum frame number
    prefix = None
    ext = None
    start = sys.maxsize
    end = -sys.maxsize
    for filename in os.listdir(render_folder):
        parts = filename.split('.')
        if len(parts) == 3:
            if prefix is None:
                prefix = parts[0]
            elif prefix != parts[0]:
                continue  # Ignore files with different prefix
            if ext is None:
                ext = parts[2]
            elif ext != parts[2]:
                continue  # Ignore files with different extension
            try:
                frame = int(parts[1])
                if frame < start:
                    start = frame
                if frame > end:
                    end = frame
            except:
                continue
    return (
        '{}.%04d.{} [{}-{}]'.format(
            os.path.join(render_folder, prefix),
            ext,
            start,
            end,
        ),
        start,
        end,
    )


def find_movie(render_folder):
    if not render_folder or not os.path.exists(render_folder):
        return None

    avi_files = glob.glob(os.path.join(render_folder, '*.avi'))

    if avi_files:
        return avi_files[0]

    return None


#### MISC ####


def prepare_load_task(session, context_data, data, options):
    '''Prepare loader import task based on *data* and *context_data* supplied, based on *options*.'''

    paths_to_import = []
    for collector in data:
        paths_to_import.append(
            collector['result'].get(asset_const.COMPONENT_PATH)
        )

    component_path = paths_to_import[0]

    # Check if it exists
    if not os.path.exists(component_path):
        raise Exception(
            'The asset file does not exist: "{}"'.format(component_path)
        )

    task = unreal.AssetImportTask()

    task.filename = component_path

    # Determine the folder to import to
    selected_context_browser_path = (
        unreal.EditorUtilityLibrary.get_current_content_browser_path()
    )
    if selected_context_browser_path is not None:
        import_path = selected_context_browser_path
    else:
        import_path = '/Game'

    task.destination_path = import_path.replace(' ', '_')
    task.destination_name = context_data['asset_name'].replace(' ', '_')

    task.replace_existing = options.get('ReplaceExisting', True)
    task.automated = options.get('Automated', True)
    task.save = options.get('Save', True)

    return task, component_path


def rename_node_with_prefix(node_name, prefix):
    '''This method allow renaming a UObject to put a prefix to work along
    with UE4 naming convention.
      https://github.com/Allar/ue4-style-guide'''
    assert node_name is not None, 'No node name/asset path provided'
    object_ad = unreal.EditorAssetLibrary.find_asset_data(node_name)
    new_name_with_prefix = '{}/{}{}'.format(
        str(object_ad.package_path),
        prefix,
        str(object_ad.asset_name),
    )

    if unreal.EditorAssetLibrary.rename_asset(node_name, new_name_with_prefix):
        return new_name_with_prefix
    else:
        return node_name


def assets_to_paths(assets):
    result = []
    for asset in assets:
        result.append(asset.get_path_name())
    return result
