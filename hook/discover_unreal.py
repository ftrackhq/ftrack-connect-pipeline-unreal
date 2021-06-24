# :coding: utf-8
# :copyright: Copyright (c) 2014-2021 ftrack

import ftrack_api
import functools
import logging
import os
import sys


NAME = 'ftrack-connect-pipeline-unreal-engine'

logger = logging.getLogger('{}.hook'.format(NAME.replace('-','_')))


plugin_base_dir = os.path.normpath(
    os.path.join(
        os.path.abspath(
            os.path.dirname(__file__)
        ),
        '..'
    )
)

python_dependencies = os.path.abspath(
    os.path.join(
        plugin_base_dir,
        'dependencies'
    )
)


sys.path.append(python_dependencies)


def on_discover_pipeline_unreal(session, event):

    from ftrack_connect_pipeline_unreal_engine import __version__ as integration_version

    data = {
        'integration': {
            'name': 'ftrack-connect-pipeline-unreal-engine',
            'version': integration_version
        }
    }

    return data


def on_launch_pipeline_unreal(session, event):
    ''' Handle application launch and add environment to *event*. '''
    pipeline_unreal_base_data = on_discover_pipeline_unreal(session, event)

    definitions_plugin_hook = os.getenv('FTRACK_DEFINITION_PLUGIN_PATH')
    plugin_hook = os.path.join(definitions_plugin_hook, 'unreal', 'python')

    # Determine if py3k or not by looking at version number
    is_py3k = True
    try:
        variant = event['data']['application']['variant'].split(' ')[0]
        if (1000 * int(variant.split('.')[0]) +
            int(variant.split('.')[1])) < (1000 * 4 + 26):
            is_py3k = False
    except:
        import traceback
        print(traceback.format_exc())


    pipeline_maya_base_data['integration']['env'] = {
        'FTRACK_EVENT_PLUGIN_PATH.prepend': plugin_hook,
        'PYTHONPATH.prepend': python_dependencies,
        'QT_PREFERRED_BINDING.set': 'PySide2' if is_py3k else 'PySide',
        'FTRACK_CONTEXTID.set': entity['entityId'],
        'FTRACK_CONTEXTTYPE.set': entity['entityType']
    }

    selection = event['data'].get('context', {}).get('selection', [])

    if selection and e.__class__.__name__ == 'Task':
        task = e
        pipeline_maya_base_data['integration']['env']['FS.set'] = str(
            task['parent']['custom_attributes'].get('fstart', '1.0'))
        pipeline_maya_base_data['integration']['env']['FE.set'] = str(
            task['parent']['custom_attributes'].get('fend', '100.0'))
        pipeline_maya_base_data['integration']['env']['FPS.set'] = str(
            task['parent']['custom_attributes'].get('fps', '24'))
    return pipeline_maya_base_data


def register(session):
    '''Subscribe to application launch events on *registry*.'''
    if not isinstance(session, ftrack_api.session.Session):
        return

    handle_discovery_event = functools.partial(
        on_discover_pipeline_unreal,
        session
    )

    session.event_hub.subscribe(
        'topic=ftrack.connect.application.discover'
        ' and data.application.identifier=unreal*'
        ' and data.application.version>=4.26',
        handle_discovery_event, priority=40
    )

    handle_launch_event = functools.partial(
        on_launch_pipeline_unreal,
        session
    )    

    session.event_hub.subscribe(
        'topic=ftrack.connect.application.launch'
        ' and data.application.identifier=unreal*'
        ' and data.application.version>=4.26',
        handle_launch_event, priority=40
    )