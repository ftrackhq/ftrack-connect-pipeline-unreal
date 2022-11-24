# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import os
import sys
import ftrack_api
import logging
import functools
import shutil

logger = logging.getLogger('ftrack_connect_pipeline_unreal.discover')

plugin_base_dir = os.path.normpath(
    os.path.join(os.path.abspath(os.path.dirname(__file__)), '..')
)
python_dependencies = os.path.join(plugin_base_dir, 'dependencies')
sys.path.append(python_dependencies)


def on_discover_pipeline_unreal(session, event):
    from ftrack_connect_pipeline_unreal import (
        __version__ as integration_version,
    )

    data = {
        'integration': {
            "name": 'ftrack-connect-pipeline-unreal',
            'version': integration_version,
        }
    }

    return data


def on_launch_pipeline_unreal(session, event):
    '''Handle application launch and add environment to *event*.'''

    pipeline_unreal_base_data = on_discover_pipeline_unreal(session, event)

    # Discover plugins from definitions
    definitions_plugin_hook = os.getenv("FTRACK_DEFINITION_PLUGIN_PATH")
    plugin_hook = os.path.join(definitions_plugin_hook, 'unreal', 'python')
    unreal_script_path = os.path.join(plugin_base_dir, 'resource', 'scripts')

    pipeline_unreal_base_data['integration']['env'] = {
        'FTRACK_EVENT_PLUGIN_PATH.prepend': plugin_hook,
        'PYTHONPATH.prepend': python_dependencies,
        'QT_PREFERRED_BINDING.set': 'PySide2',
    }

    # Verify that init script is installed centrally
    unreal_editor_exe = event['data']['command'][0]
    # 'C:\\Program Files\\Epic Games\\UE_5.1\\Engine\\Binaries\\Win64\\UnrealEditor.exe'
    engine_path = os.path.realpath(
        os.path.join(unreal_editor_exe, '..', '..', '..')
    )
    script_destination = os.path.join(
        engine_path, 'Content', 'Python', 'init_unreal.py'
    )
    if not os.path.exists(script_destination):
        script_source = os.path.join(unreal_script_path, 'init_unreal.py')
        logger.warning(
            'Attempting to install Unreal init script "{}" > "{}"'.format(
                script_source, script_destination
            )
        )
        try:
            shutil.copy(script_source, script_destination)
        except PermissionError as pe:
            logger.exception(pe)
            logger.error(
                'Could not install Unreal init script, make sure you have write permissions to "{}"!'.format(
                    script_destination
                )
            )
            raise
    selection = event['data'].get('context', {}).get('selection', [])
    if selection:
        entity = session.get('Context', selection[0]['entityId'])
        if entity.entity_type == 'Task':
            pipeline_unreal_base_data['integration']['env'][
                'FTRACK_CONTEXTID.set'
            ] = str(entity['id'])
            pipeline_unreal_base_data['integration']['env']['FS.set'] = str(
                entity['parent']['custom_attributes'].get('fstart', '1.0')
            )
            pipeline_unreal_base_data['integration']['env']['FE.set'] = str(
                entity['parent']['custom_attributes'].get('fend', '100.0')
            )
            pipeline_unreal_base_data['integration']['env']['FPS.set'] = str(
                entity['parent']['custom_attributes'].get('fps', '24')
            )

    return pipeline_unreal_base_data


def register(session):
    '''Subscribe to application launch events on *registry*.'''
    if not isinstance(session, ftrack_api.session.Session):
        return

    handle_discovery_event = functools.partial(
        on_discover_pipeline_unreal, session
    )

    session.event_hub.subscribe(
        'topic=ftrack.connect.application.discover and '
        'data.application.identifier=unreal*'
        ' and data.application.version >= 5.00',
        handle_discovery_event,
        priority=40,
    )

    handle_launch_event = functools.partial(on_launch_pipeline_unreal, session)

    session.event_hub.subscribe(
        'topic=ftrack.connect.application.launch and '
        'data.application.identifier=unreal*'
        ' and data.application.version >= 5.00',
        handle_launch_event,
        priority=40,
    )
