# -*- coding: utf-8 -*-
#
# Copyright 2012 Institut für Experimentelle Kernphysik - Karlsruher Institut für Technologie
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

"""
.. data:: module_instance

    Test

.. data:: hf_runs

    123

"""

import hf.database
from sqlalchemy import *

module_instances = Table("module_instances", hf.database.metadata,
    Column("instance", Text, primary_key=True),
    Column("module", Text)
)

hf_runs = Table("hf_runs", hf.database.metadata,
    Column("id", Integer, Sequence('module_instances_id_seq'), primary_key=True),
    Column("time", DateTime, unique=True),
    Column("completed", Boolean, default=True),
)