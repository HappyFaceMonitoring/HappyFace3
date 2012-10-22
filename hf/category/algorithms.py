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

def worst(category):
    """
    Category status is the worst lowest status of all modules of the same
    type as the category (only plots or rated modules, depending) with
    positive status value (no error, data acquisition succeeded).
    'unrated' modules are always per definition excluded.
    
    If there is no correct module with positive status, the
    category status is set to -1 (no information).
    """
    status = 1.0
    for mod in category.module_list:
        if mod.dataset is None:
            continue
        if status > mod.dataset['status'] >= 0 and mod.type == category.type:
            status = mod.dataset['status']
    return status

def weighted(category):
    """
    Category status is the average over each weighted module status. Unrated
    modules are not taken into account, as well as modules with negative status value.
    """
    status = 0.0
    total = 0.0
    for mod in category.module_list:
        if mod.dataset is None: # equivalent to status == -1 :P
            continue
        if mod.dataset['status'] >= 0 and mod.type != "unrated":
            status += mod.dataset['status'] * mod.weigth
            total += mod.dataset*mod.weight
    
    return status/total