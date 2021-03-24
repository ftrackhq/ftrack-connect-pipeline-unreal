# :coding: utf-8
# :copyright: Copyright (c) 2020 ftrack

import ftrack_api
import functools
import logging
import os
import sys


NAME = 'ftrack-connect-pipeline-unreal-engine'
VERSION = '0.1.0'

logger = logging.getLogger('{}.hook'.format(NAME.replace('-','_')))

def on_application_launch(session, event):
    ''' Handle application launch and add environment to *event*. '''
    logger.info('launching: {}'.format(NAME))

    plugin_base_dir = os.path.normpath(
        os.path.join(
            os.path.abspath(
                os.path.dirname(__file__)
            ),
            '..'
        )
    )

    python_dependencies = os.path.abspath(os.path.join(plugin_base_dir, 'dependencies'))
    unreal_path = os.path.abspath(
        os.path.join(plugin_base_dir, 'resource')
    )

    sys.path.append(python_dependencies)

    #ftrack_connect_installation_path = os.path.dirname(sys.executable)
    #print('@@@; ftrack_connect_installation_path: {}'.format(ftrack_connect_installation_path))
    #ftrack_connect_installation_path = "C:\\Program Files (x86)\\ftrack-connect-package-1.1.2"
    ftrack_connect_installation_path = "/Applications/ftrack-connect 2.app/Contents/MacOS"

    entity = event['data']['context']['selection'][0]
    e = session.get('Context', entity['entityId'])

    definitions_plugin_hook = os.getenv("FTRACK_DEFINITION_PLUGIN_PATH")
    plugin_hook = os.path.join(definitions_plugin_hook, 'unreal')

    # Determine if py3k or not by looking at version number
    is_py3k = True
    try:
        variant = event['data']['application']['variant'].split(" ")[0]
        if (1000 * int(variant.split(".")[0]) + int(variant.split(".")[1])) < (1000 * 4 + 26):
            is_py3k = False
    except:
        import traceback
        print(traceback.format_exc())

    data = {
        'integration': {
            "name": 'ftrack-connect-pipeline-unreal-engine',
            'version': VERSION,
            'env': {
                'FTRACK_EVENT_PLUGIN_PATH.prepend': plugin_hook,
                'PYTHONPATH.prepend': python_dependencies,
                'QT_PREFERRED_BINDING.set': "PySide2" if is_py3k else "PySide",
                'FTRACK_CONTEXTID.set': entity['entityId'],
                'FTRACK_CONTEXTTYPE.set': entity['entityType'],
            }
        }
    }
    if e.__class__.__name__ == "Task":
        task = e
        data['integration']['env']['FS.set'] = task['parent']['custom_attributes'].get('fstart', '1.0')
        data['integration']['env']['FE.set'] = task['parent']['custom_attributes'].get('fend', '100.0')
        data['integration']['env']['FPS.set'] = task['parent']['custom_attributes'].get('fps', '24')
    print('@@@; Unreal hook returning: {}'.format(data))
    return data


def register(session):
    '''Subscribe to application launch events on *registry*.'''
    if not isinstance(session, ftrack_api.session.Session):
        return

    handle_event = functools.partial(
        on_application_launch,
        session
    )
    logger.info('registering :{}'.format(NAME))
    session.event_hub.subscribe(
        'topic=ftrack.connect.application.discover'
        ' and data.application.identifier=unreal*'
        ' and data.application.version>=4.26',
        handle_event, priority=40
    )
    session.event_hub.subscribe(
        'topic=ftrack.connect.application.launch'
        ' and data.application.identifier=unreal*'
        ' and data.application.version>=4.26',
        handle_event, priority=40
    )