# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack
import threading
from functools import wraps
import logging
import os
import sys
import subprocess

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
            # return maya_utils.executeInMainThreadWithResult(f, *args, **kwargs)
            pass
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
    # return cmds.ls(type=asset_const.FTRACK_PLUGIN_TYPE)
    pass


def get_current_scene_objects():
    '''Returns all the objects in the scene'''
    # return set(cmds.ls(l=True))
    pass


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
    '''Check if node_name exist in the scene'''
    # return cmds.objExists(object_name)
    pass


def get_node(node_name):
    '''Return the Max node identified by name'''
    # return rt.getNodeByName(node_name, exact=True)
    pass


def delete_node(node):
    '''Delete the given *node*'''
    # return cmds.delete(object_name)
    pass


# (Only DCC with no live connections)
# def get_connected_objects_from_dcc_object(dcc_object_name):
#     '''Return all objects connected to the given *dcc_object_name*'''
#     # Get Unique id for a node using rt.getHandleByAnim(obj) and get the node
#     # from the unique id using rt.getAnimByHandler(id) please see the following
#     # link for more info: https://help.autodesk.com/view/MAXDEV/2023/ENU/?guid=GUID-25211F97-E81A-4D49-AFB6-50B30894FBEB
#     objects = []
#     dcc_object_node = rt.getNodeByName(dcc_object_name, exact=True)
#     if not dcc_object_node:
#         return
#     id_value = rt.getProperty(dcc_object_node, asset_const.ASSET_INFO_ID)
#     for parent in rt.rootScene.world.children:
#         children = [parent] + collect_children_nodes(parent)
#         for obj in children:
#             if rt.isProperty(obj, "ftrack"):
#                 if id_value == rt.getProperty(obj, "ftrack"):
#                     objects.append(obj)
#     return objects


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


def open_file(path, options=None):
    '''Native open file function'''
    # return cmds.file(path, o=True, f=True)
    pass


def import_file(path, options=None):
    '''Native import file function'''
    # return cmds.file(path, o=True, f=True)
    pass


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
    str_capture_args = ''
    if 'resolution' in options:
        resolution = options['resolution']  # On the form 320x240(4:3)
        parts = resolution.split('(')[0].split('x')
        str_capture_args += ' -ResX={} -ResY={}'.format(parts[0], parts[1])
    if 'movie_quality' in options:
        quality = int(options['movie_quality'])
        str_capture_args += ' -MovieQuality={}'.format(
            max(0, min(quality, 100))
        )
    return str_capture_args


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
        cmdline_args.append(capture_args)
        cmdline_args.append("-NoTextureStreaming")
        cmdline_args.append("-NoLoadingScreen")
        cmdline_args.append("-NoScreenMessages")
        return cmdline_args

    output_filepath = __generate_target_file_path(
        destination_path, content_name, image_format, frame
    )
    if os.path.isfile(output_filepath):
        # Must delete it first, otherwise the Sequencer will add a number
        # in the filename
        try:
            os.remove(output_filepath)
        except OSError as e:

            msg = (
                'Could not delete {}. The Sequencer will not be able to'
                ' exporters the movie to that file.'.format(output_filepath)
            )
            logger.error(msg)
            return False, {'message': msg}

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

    return os.path.isfile(output_filepath), output_filepath
