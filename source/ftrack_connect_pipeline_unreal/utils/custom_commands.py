# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack
import threading
from functools import wraps
import os
import logging
import sys
import subprocess
import json

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
        if threading.currentThread().name != 'MainThread':
            return f(*args, **kwargs)
        else:
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
        if item_name not in "ftrackdata":
            continue
        if item_name.endswith(".json"):
            ftrack_nodes.append(os.path.splitext(item_name)[0])
    return ftrack_nodes


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


def get_asset_by_path(asset_path):
    '''Get Unreal asset object by path'''
    if not asset_path:
        return None
    assetRegistry = unreal.AssetRegistryHelpers.get_asset_registry()
    asset_data = assetRegistry.get_assets_by_package_name(
        os.path.splitext(asset_path)[0]
    )
    if asset_data:
        return asset_data[0].get_asset()
    return None


def delete_node(node_name):
    '''Delete the given *node_name*'''
    unreal.EditorAssetLibrary.delete_asset(node_name)


def get_connected_objects_from_dcc_object(dcc_object_name):
    '''Return all objects connected to the given *dcc_object_name*'''
    objects = []
    dcc_object_node = None
    ftrack_nodes = get_ftrack_nodes()
    for node in ftrack_nodes:
        if node.endswith("{}.json".format(dcc_object_name)):
            dcc_object_node = node
            break
    if not dcc_object_node:
        return
    with open(dcc_object_node, 'r') as openfile:
        param_dict = json.load(openfile)
    id_value = param_dict.get(asset_const.ASSET_INFO_ID)
    for obj_path in get_current_scene_objects():
        asset = get_asset_by_path(obj_path)
        ftrack_value = unreal.EditorAssetLibrary.get_metadata_tag(
            asset, "ftrack"
        )
        if id_value == ftrack_value:
            objects.append(obj_path)
    return objects


def get_all_sequences(as_names=True):
    '''
    Returns a list of of all sequences names
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

# TODO: Find a better name for this fucntion. This is not a relative path.
def get_asset_relative_path(session, asset_version_entity):
    ftrack_task = asset_version_entity['task']
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
    return asset_import_task.imported_object_paths[0]


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


def rename_object_with_prefix(loaded_obj, prefix):
    '''This method allow renaming a UObject to put a prefix to work along
    with UE4 naming convention.
      https://github.com/Allar/ue4-style-guide'''
    assert loaded_obj != None
    new_name_with_prefix = ''
    if loaded_obj:
        object_ad = unreal.EditorAssetLibrary.find_asset_data(
            loaded_obj.get_path_name()
        )
        if object_ad:
            if unreal.EditorAssetLibrary.rename_asset(
                object_ad.object_path,
                str(object_ad.package_path)
                + '/'
                + prefix
                + '_'
                + str(object_ad.asset_name),
            ):
                new_name_with_prefix = '{}_{}'.format(
                    prefix, object_ad.asset_name
                )
    return new_name_with_prefix


def assets_to_paths(self, assets):
    result = []
    for asset in assets:
        result.append(asset.get_path_name())
    return result
