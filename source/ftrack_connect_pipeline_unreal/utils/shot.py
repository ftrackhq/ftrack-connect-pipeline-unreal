# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import logging

from ftrack_connect_pipeline.utils import (
    str_context,
)

logger = logging.getLogger(__name__)


def push_shot_to_server(
    sequence_context_id, shot_name, session, start=None, end=None
):
    '''Created a shot named *shot_name* in the sequence with the given *sequence_context_id*,
    using the supplied *session*. If shot exists, return the existing shot. Updates shot
    start and end frames if they are different from the supplied values *start* and *end*.
    '''

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
