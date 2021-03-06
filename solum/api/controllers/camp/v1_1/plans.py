# -*- coding: utf-8 -*-
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import pecan
import wsmeext.pecan as wsme_pecan

from solum.api.controllers.camp.v1_1.datamodel import plans as model
from solum.api.controllers import common_types
from solum.common import exception


uri_string = '%s/camp/v1_1/plans/'
description_string = "Solum CAMP API plans collection resource."
param_uri_string = '%s/camp/v1_1/parameter_definitions/assembly_create_params'


class Controller():
    """CAMP v1.1 plans controller."""

    @exception.wrap_wsme_controller_exception
    @wsme_pecan.wsexpose(model.Plans)
    def index(self):
        return model.Plans(uri=uri_string % pecan.request.host_url,
                           name='Solum_CAMP_plans',
                           type='plans',
                           description=description_string,
                           plan_links=[
                               common_types.Link(href='http://tbd.com/',
                                                 target_name='TBD')
                           ],
                           parameter_definitions_uri=param_uri_string %
                           pecan.request.host_url)
