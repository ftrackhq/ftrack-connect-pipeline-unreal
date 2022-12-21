# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack
import copy
import os.path

from ftrack_connect_pipeline import constants as core_constants

from ftrack_connect_pipeline.definition.definition_object import (
    DefinitionObject,
    DefinitionList,
)

from ftrack_connect_pipeline_qt.client.publish import QtPublisherClientWidget
from ftrack_connect_pipeline_qt.client.publish.batch import (
    QtBatchPublisherClientWidget,
)
from ftrack_connect_pipeline_qt.ui.utility.widget import dialog
import ftrack_connect_pipeline_qt.constants as qt_constants

import ftrack_connect_pipeline_unreal.constants as unreal_constants
from ftrack_connect_pipeline_unreal.utils import (
    custom_commands as unreal_utils,
)


class UnrealQtPublisherClientWidget(QtPublisherClientWidget):
    ui_types = [
        constants.UI_TYPE,
        qt_constants.UI_TYPE,
        unreal_constants.UI_TYPE,
    ]
    '''Unreal single version publisher widget'''

    def __init__(self, event_manager, parent=None):
        super(UnrealQtPublisherClientWidget, self).__init__(
            event_manager, parent=parent
        )
        self.setWindowTitle('Unreal Pipeline Publisher')
        self.resize(350, 800)

    def get_theme_background_style(self):
        return 'unreal'


class UnrealQtBatchPublisherClientWidget(QtBatchPublisherClientWidget):
    '''Unreal multiple versions publisher widget'''

    def __init__(
        self, event_manager, assets, title=None, run=False, parent=None
    ):
        self._assets = assets
        self._run = run
        super(UnrealQtBatchPublisherClientWidget, self).__init__(
            event_manager, title=title, parent=parent
        )

    def post_build(self):
        super(UnrealQtBatchPublisherClientWidget, self).post_build()
        self.definitionsPopulated.connect(self._publish_assets)

    def _publish_assets(self, definitions):
        '''
        Definitions
        Build and run the batch publisher based on assets, exclude assets that have not changed
        since last publish'''
        project_context_id = unreal_utils.get_project_level_context()
        data = []
        for asset_path in self._assets:
            # Locate the asset info
            do_publish = False
            param_dict = None
            dcc_object_name, param_dict = unreal_utils.get_asset_info(
                asset_path
            )
            if dcc_object_name is None:
                # Not tracked yet, that's fine
                do_publish = True
            else:
                # TODO: Check if the asset has changed since last publish
                do_publish = True
            if do_publish is True:
                # Locate suitable definition
                definition = None
                if asset_path.endswith('.uasset'):
                    definition_match = 'asset'
                elif asset_path.endswith('.umap'):
                    definition_match = 'level'
                else:
                    dialog.ModalDialog(
                        self,
                        message='Could not determine publisher from asset file: {}'.format(
                            asset_path
                        ),
                    )
                    return
                for _definition in definitions:
                    if _definition['name'].lower().find(definition_match) > -1:
                        definition = _definition
                        break
                if definition is None:
                    dialog.ModalDialog(
                        self,
                        message='Could not find a suitable {} publisher!'.format(
                            definition_match
                        ),
                    )
                    return
                # Create the asset build
                asset_build = unreal_utils.ensure_project_level_asset_build()
                # Find existing asset
                asset_name = os.path.splitext(os.path.basename(asset_path))[
                    0
                ]  # Preserve asset name
                asset = self.session.query(
                    'Asset where parent.id is "{}" and name is "{}"'.format(
                        asset_build['id'], asset_name
                    )
                ).first()
                asset_id = None
                if asset:
                    asset_id = asset['id']
                # Build the publisher definition
                definition_fragment = None
                for d_component in definition.get_all(
                    type=core_constants.COMPONENT
                ):
                    component_name_effective = d_component['name']
                    if component_name_effective.lower() != 'snapshot':
                        continue

                    # Construct definition fragment
                    definition_fragment = DefinitionObject({})
                    for key in definition:
                        if key == core_constants.COMPONENTS:
                            definition_fragment[key] = DefinitionList(
                                [DefinitionObject(d_component.to_dict())]
                            )
                            definition_fragment.get_first(
                                type=core_constants.COMPONENT
                            )['name'] = component_name_effective
                        else:
                            # Copy the category
                            definition_fragment[key] = copy.deepcopy(
                                definition[key]
                            )
                            if key != core_constants.CONTEXTS:
                                continue
                            # Inject context ident
                            for plugin in definition_fragment[key].get_all(
                                type=core_constants.CONTEXT,
                                category=core_constants.PLUGIN,
                            ):
                                if not 'options' in plugin:
                                    plugin['options'] = {}
                                # Store contexst data
                                plugin['options'][
                                    'parent_context_id'
                                ] = asset_build['id']
                                if asset_id:
                                    plugin['options']['asset_id'] = asset_id
                                else:
                                    plugin['options'][
                                        'asset_name'
                                    ] = asset_name
                                plugin['options']['is_valid_name'] = True

                if not definition_fragment:
                    dialog.ModalDialog(
                        self,
                        message='{} publisher does not contain expected "snapshot" component!'.format(
                            definition['name']
                        ),
                    )
                    return
                data.append(
                    {
                        'asset_path': asset_path,
                        'dcc_object_name': dcc_object_name,
                        'asset_info': param_dict,
                        'definition': definition_fragment,
                    }
                )
