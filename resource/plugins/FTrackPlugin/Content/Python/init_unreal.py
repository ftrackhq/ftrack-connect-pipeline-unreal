# :coding: utf-8
# :Copyright 2019 ftrack. All Rights Reserved.
import traceback
import sys
import os

load_integration = True

if 'FTRACK_CONNECT_DISABLE_INTEGRATION_LOAD' in os.environ and os.environ['FTRACK_CONNECT_DISABLE_INTEGRATION_LOAD'] == "1":
    print('Not loading ftrack integration during sequence render.')
    load_integration = False

if load_integration:
    try:
        import ftrack_connect_pipeline_unreal_engine.bootstrap
    except ImportError as error:
        try:
            # Attempt loading legacy integration
            import ftrack_connect_unreal_engine.bootstrap
        except ImportError as error:
            print (
                'ftrack connect Unreal plugin is not well initialized '
                'or you did not start Unreal from ftrack connect.'
                'Error {}'.format(error)
            )
            traceback.print_exc()
