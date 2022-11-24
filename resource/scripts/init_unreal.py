# :coding: utf-8
# :Copyright 2019 ftrack. All Rights Reserved.
'''
Unreal Python entry point

This file is copied into the central Engine content folder by the application launcher hook.
'''
import traceback
import sys
import os

# Make sure framework is found, Unreal Python interpreter is not preloaded from PYTHONPATH
for p in os.environ['PYTHONPATH'].split(os.pathsep):
    print('[ftrack] Adding to sys path: "{}"\n'.format(p))
    sys.path.append(p)

load_integration = True

if (
    'FTRACK_CONNECT_DISABLE_INTEGRATION_LOAD' in os.environ
    and os.environ['FTRACK_CONNECT_DISABLE_INTEGRATION_LOAD'] == "1"
):
    print('Not loading ftrack integration during sequence render.')
    load_integration = False

if load_integration:
    try:
        import ftrack_connect_pipeline_unreal.bootstrap

        print('[ftrack] integration bootstrapped')
    except ImportError as error:
        print(
            'ftrack connect Unreal plugin is not well initialized '
            'or you did not start Unreal from ftrack connect? '
            'Error: {}'.format(error)
        )
        traceback.print_exc()
        raise
