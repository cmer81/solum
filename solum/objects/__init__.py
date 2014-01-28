# Copyright 2013 - Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Common functionality for the application object model

The object model must be initialized at service start via

  solum.objects.load()

and all objects should be retrieved via

  solum.objects.registry.<class>

in application code.
"""

from oslo.config import cfg

from solum.objects import registry
from solum.openstack.common import importutils

db_opts = [
    cfg.StrOpt('backend',
               default='sqlalchemy',
               help='The backend to use for persistence'),
    cfg.StrOpt('schema_mode',
               default='new',
               help="The version of the schema that should be "
                    "running: 'old', 'transition', 'new'")
]

CONF = cfg.CONF
CONF.register_opts(db_opts, "database")

_BACKEND_MAPPING = {'sqlalchemy': 'solum.objects.sqlalchemy'}


def transition_schema():
    """Is the new schema in write-only mode."""
    return cfg.CONF.database.schema_mode == 'transition'


def new_schema():
    """Should objects be writing to the new schema."""
    return cfg.CONF.database.schema_mode != 'old'


def load():
    """Ensure that the object model is initialized."""
    registry.clear()
    backend_name = CONF.database.backend
    backend_path = _BACKEND_MAPPING.get(backend_name, backend_name)
    backend_mod = importutils.import_module(backend_path)
    backend_mod.load()


registry = registry.Registry()