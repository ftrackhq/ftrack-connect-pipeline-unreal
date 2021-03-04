# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import sys
import re
import os
import glob
import traceback

import logging

#import hou

from ftrack_connect_pipeline_unreal_engine.constants import asset as asset_const

logger = logging.getLogger(__name__)

def get_current_scene_objects():
    #return set(hou.node('/obj').glob('*'))
    return set([])
    
def get_ftrack_assets():
    result = []
    # for obj in hou.node('/').allSubChildren():
    #     if obj.parmTemplateGroup().findFolder('ftrack'):
    #         valueftrackId = obj.parm('component_id').eval()
    #         if valueftrackId != '':
    #             result.append(obj)
    return set(result)

def import_scene(path, context=None, options=None):
    '''
    Import the scene from the given *path*
    '''

    node = hou.node('/obj').createNode(
        'subnet', context['asset_name'])
    node.loadChildrenFromFile(path.replace('\\', '/'))
    node.setSelected(1)
    node.moveToGoodPosition()

    return node.path()

def merge_scene(path, context=None, options=None):
    '''
    Create LiveGroup from the given *path*
    '''
    if options.get('MergeOverwriteOnConflict') is True:
        hou.hipFile.merge(path.replace('\\', '/'), overwrite_on_conflict=True)
    else:
        hou.hipFile.merge(path.replace('\\', '/'))
    return path

def open_scene(path, context=None, options=None):
    '''
    Open unreal scene from the given *path*
    '''
    hou.hipFile.load(path.replace('\\', '/'))
    return path


