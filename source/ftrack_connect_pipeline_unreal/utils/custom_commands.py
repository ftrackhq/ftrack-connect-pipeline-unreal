# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack
import threading
from functools import wraps
import os
import logging
import sys
import subprocess
import json
import datetime

import unreal

from ftrack_connect_pipeline.utils import (
    get_save_path,
)
from ftrack_connect_pipeline_unreal.constants import asset as asset_const

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
        ftrack_value = unreal.EditorAssetLibrary.get_metadata_tag(
            asset, "ftrack"
        )
        if id_value == ftrack_value:
            objects.append(node_name)
    return objects


def get_asset_info(node_name):
    '''Return the asset info from dcc object linked to asset path identified by *node_name*'''
    asset = get_asset_by_path(node_name)
    if asset is None:
        logger.warning(
            '(get_asset_info) Cannot find asset by path: {}'.format(node_name)
        )
        return None, None
    ftrack_value = unreal.EditorAssetLibrary.get_metadata_tag(asset, "ftrack")
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


def get_all_sequences(as_names=True):
    '''
    Returns a list of all sequences names
    '''
    result = []
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    for actor in actors:
        if actor.static_class() == unreal.LevelSequenceActor.static_class():
            seq = actor.load_sequence()
            result.append(seq.get_name() if as_names else seq)
            break
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


def open_file(path, options=None):
    '''Native open file function'''
    # return cmds.file(path, o=True, f=True)
    pass


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


def save_file(save_path, context_id=None, session=None, temp=True, save=True):
    '''Save scene locally in temp or with the next version number based on latest version
    in ftrack.'''

    # # Max has no concept of renaming a scene, always save
    # save = True
    #
    # if save_path is None:
    #     if context_id is not None and session is not None:
    #         # Attempt to find out based on context
    #         save_path, message = get_save_path(
    #             context_id, session, extension='.max', temp=temp
    #         )
    #
    #         if save_path is None:
    #             return False, message
    #     else:
    #         return (
    #             False,
    #             'No context and/or session provided to generate save path',
    #         )
    #
    # if save:
    #     rt.savemaxFile(save_path, useNewFile=True)
    #     message = 'Saved Max scene @ "{}"'.format(save_path)
    # else:
    #     raise Exception('Max scene rename not supported')
    #
    # result = save_path
    #
    # return result, message
    pass


### REFERENCES ###
# Follow this link for more reference commands in max:
# https://help.autodesk.com/view/3DSMAX/2016/ENU/?guid=__files_GUID_090B28AB_5710_45BB_B324_8B6FD131A3C8_htm


def reference_file(path, options=None):
    '''Native reference file function'''
    # return cmds.file(path, o=True, f=True)
    pass


def get_reference_node(dcc_object_name):
    '''
    Return the scene reference_node associated to the given
    *dcc_object_name*
    '''
    # dcc_object_node = rt.getNodeByName(dcc_object_name, exact=True)
    # if not dcc_object_node:
    #     return
    # component_path = asset_const.COMPONENT_PATH
    # for idx in range(1, rt.xrefs.getXRefFileCount()):
    #     reference_node = rt.xrefs.getXrefFile(idx)
    #     if reference_node.filename == component_path:
    #         return reference_node
    pass


def remove_reference_node(reference_node):
    '''Remove reference'''
    # rt.delete(reference_node)
    pass


def unload_reference_node(reference_node):
    '''Disable reference'''
    # reference_node.disabled = True
    pass


def load_reference_node(reference_node):
    '''Disable reference'''
    # reference_node.disabled = False
    pass


def update_reference_path(reference_node, component_path):
    '''Update the path of the given *reference_node* with the given
    *component_path*'''
    # reference_node.filename = component_path
    pass


#### PROJECT LEVEL PUBLISH AND LOAD ####


def save_project_state(package_paths, include_paths=None):
    '''
    Takes a snapshot of the given *package_paths* status recursively, with the
    purpose os later identify which packages have been modified - i.e. are dirty
    and needs to be published.

    If *include_paths* is given, only these assets will be updated, merging the result
    with the current project state for all other assets - keeping them dirty.

    package_paths: Root folder from where to take the snapshot
    '''

    asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
    registry_filter = unreal.ARFilter(
        package_paths=package_paths, recursive_paths=True
    )
    cb_assets_data = asset_registry.get_assets(registry_filter)

    os_content_folder = unreal.SystemLibrary.get_project_content_directory()
    state_dictionary = {
        "assets": [],
        "date": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "description": "Saved state of the Unreal project content folder",
    }
    for asset_data in cb_assets_data:
        if not asset_data.is_u_asset():
            continue
        full_path = None
        for ext in ['.uasset', '.umap']:
            # TODO: Remove /Game/ from the path the correct way
            p = os.path.join(
                os_content_folder,
                '{}{}'.format(str(asset_data.package_name)[6:], ext),
            )
            if os.path.exists(p):
                full_path = p
        if not full_path:
            continue
        disk_size = os.path.getsize(full_path)
        mod_date = os.path.getmtime(full_path)
        info = {
            'package_name': str(asset_data.package_name),
            'disk_size': disk_size,
            'modified_date': mod_date,
        }
        state_dictionary['assets'].append(info)

    if not os.path.exists(asset_const.FTRACK_ROOT_PATH):
        logger.info(
            'Creating FTRACK_ROOT_PATH: {}'.format(
                asset_const.FTRACK_ROOT_PATH
            )
        )
        os.makedirs(asset_const.FTRACK_ROOT_PATH)

    state_path = os.path.join(
        asset_const.FTRACK_ROOT_PATH, asset_const.PROJECT_STATE_FILE_NAME
    )
    with open(state_path, 'w') as f:
        json.dump(state_dictionary, f, indent=4)
        logger.debug(
            'Successfully saved Unreal project state to: {}'.format(state_path)
        )
    return state_dictionary


def get_project_state():
    state_path = os.path.join(
        asset_const.FTRACK_ROOT_PATH, asset_const.PROJECT_STATE_FILE_NAME
    )
    if not os.path.exists(state_path):
        return None
    return json.load(open(state_path, 'r'))['assets']


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
    '''Read and return the project context from the current Unreal project.'''
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


def ensure_asset_build(root_context_id, asset_path, session):
    '''Ensure that an asset build exists on the *asset_path* relative *root_context_id*

    Expect: /Game/FirstPerson/Maps/FirstPersonMap
    '''

    asset_path_sanitized = asset_path.replace('/Game', 'Content')
    parent_context = session.query(
        'Context where id is "{}"'.format(root_context_id)
    ).one()
    project = session.query(
        'Project where id="{}"'.format(parent_context['project_id'])
    ).one()

    parts = asset_path_sanitized.split('/')

    for index, part in enumerate(parts):
        # Check if the context already exists
        child_context = session.query(
            'select id,name from Context where parent.id is "{0}" and name="{1}"'.format(
                parent_context['id'], part
            )
        ).first()
        if not child_context:
            # Create it
            if index < len(parts) - 1:
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
                        'Could not find a asset build type to be used when creating the Unreal project level asset build!'
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
                        'Could not find a asset build status to be used when creating the Unreal project level asset build!'
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


def get_asset_dependencies(asset_path):
    '''Return a list of asset dependencies for the given *asset_path*.'''

    # https://docs.unrealengine.com/4.27/en-US/PythonAPI/class/AssetRegistry.html?highlight=assetregistry#unreal.AssetRegistry.get_dependencies
    # Setup dependency options
    dep_options = unreal.AssetRegistryDependencyOptions(
        include_soft_package_references=True,
        include_hard_package_references=True,
        include_searchable_names=False,
        include_soft_management_references=True,
        include_hard_management_references=True,
    )
    # Start asset registry
    asset_reg = unreal.AssetRegistryHelpers.get_asset_registry()
    # Get dependencies for the given asset
    dependencies = [
        str(dep)
        for dep in asset_reg.get_dependencies(
            asset_path.split('.')[0], dep_options
        )
    ]

    # Filter out only dependencies that are in Game
    game_dependencies = list(
        filter(lambda x: x.startswith("/Game"), dependencies)
    )

    return game_dependencies


def determine_extension(path):
    '''Probe the file extension of the given asset path.'''
    for ext in ['', '.uasset', '.umap']:
        result = '{}{}'.format(path, ext)
        if os.path.exists(result):
            return result
    raise Exception(
        'Could not determine asset "{}" files extension on disk!'.format(path)
    )


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


#### MISC ####


def prepare_load_task(session, context_data, data, options):
    '''Prepare loader import task'''

    paths_to_import = []
    for collector in data:
        paths_to_import.extend(collector['result'])

    component_path = paths_to_import[0]

    task = unreal.AssetImportTask()

    task.filename = component_path

    asset_version_entity = session.query(
        'AssetVersion where id={}'.format(context_data['version_id'])
    ).first()
    import_path = '/Game/{}{}'.format(
        get_context_relative_path(session, asset_version_entity['task']),
        context_data['asset_name'],
    )

    task.destination_path = import_path.replace(' ', '_')
    task.destination_name = os.path.splitext(os.path.basename(component_path))[
        0
    ]

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


def disk_log(s):
    with open('C:\\TEMP\\unreal_log.txt', 'a') as f:
        f.write('[{}] {}\n'.format(datetime.datetime.now(), s))
    print(s)
