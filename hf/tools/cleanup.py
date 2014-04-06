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
Remove old datasets from database
"""

import traceback
import sys
import hf
import datetime
import os
from hf.module.database import hf_runs
from hf.downloadservice import downloadService
import tools


try:
    import argparse
except ImportError:
    import hf.external.argparse as argparse
from sqlalchemy import select, func


def just(n, seq):
    """
    http://stackoverflow.com/a/10300081
    """
    it = iter(seq)
    for _ in range(n - 1):
        yield next(it, None)
    yield tuple(it)


def execute():
    parser = argparse.ArgumentParser("Remove old datasets from HappyFace database")
    parser.add_argument("-d", "--days", nargs=1, metavar="N",
                        help="Remove datasets older than N days")
    parser.add_argument("--keep-files",
                        action="store_true", default=False,
                        help="Do not remove linked files from database. Faster but USE WITH CARE!")
    parser.add_argument("--check-file-integrity", action="store_true",
                        default=False,
                        help="Check archived files for reference in database. Will be removed when --remove-unreferenced is specified")
    parser.add_argument("--remove-unreferenced",
                        action="store_true", default=False,
                        help="Used with --check-file-integrity")
    parser.add_argument("-v", "--verbose", action="store_true",
                        default=False, help="Verbose output")
    parser.add_argument("-i", "--interactive",
                        action="store_true", default=False,
                        help="Ask before performing deletions.")
    parser.add_argument("--list-modules",
                        action="store_true", default=False,
                        help="List all modules present in database and their configuration status")
    parser.add_argument("--drop-unused-modules",
                        help="Drop  tables of all unused modules")
    parser.add_argument("--drop-module", nargs="+", metavar="dropmodule",
                        help="Drop tables of all specified modules")
    args = parser.parse_args()
    tools.load_env()
    hf.database.metadata.reflect(hf.database.engine)
    # check no-action commands
    if args.days is not None:
        now = datetime.datetime.now()
        timerange = [(now-datetime.timedelta(int(args.days[0]), 0, 0)), now]
    if args.list_modules:
        list_modules()
    else:
        for instance, module, module_table, used in\
            sorted(get_module_instances(), key=lambda x: x[1]):
            print "Clearing {0}".format(instance)
            clear_contents(instance, module, module_table,
                           keep_files=args.keep_files, timerange=timerange)


def get_module_instances():
    #classes_by_mod_table = dict((table_name, cls) for hf.module.module.__)
    module_instances = hf.module.database.module_instances
    ret = []
    for table_name, table in hf.database.metadata.tables.iteritems():
        if not table_name.startswith("mod_"):
            continue
        query = select([table.c.instance, module_instances.c.module]).\
                where(table.c.instance == module_instances.c.instance).\
                distinct()
        for inst, mod in query.execute():
            used = hf.module.moduleClassLoaded(mod)
            if used:
                # is instance it really in configuration?
                used = inst in hf.module.config.sections()
            ret.append((inst, mod, table, used))
    return ret


def list_modules():
    fmt = "{instance:>35} {module:>30} {oldest:>10} {status:}"
    hf_runs = hf.module.database.hf_runs
    print "\033[1m\033[31", fmt.format(instance="Instance",
                                       module="Module",
                                       oldest="Oldest Age",
                                       status="Status"), "\033[0m"
    prev_module = None
    for instance, module, module_table, used in sorted(get_module_instances(),
                                                       key=lambda x: x[1]):
        expr = select([hf_runs.c.time])\
               .where(hf_runs.c.id ==
                      module_table.c.run_id) \
               .where(module_table.c.instance == instance)\
               .order_by(hf_runs.c.time.asc())
        oldest = expr.execute().fetchone()[0]
        age_days = (datetime.datetime.now()-oldest).days
        print fmt.format(instance=instance,
                         module=module if module != prev_module else "| ",
                         oldest="{0}d".format(age_days),
                         status=("used" if used else "\033[1m\033[31munused\033[0m"))
        if module != prev_module:
            prev_module = module


def clear_contents(module_instance_name, module,
                   module_table, timerange=None, keep_files=False):
    subtables = dict(filter(lambda x: x[0].startswith("sub_"+module_table.name[4:]+"_"),
                            hf.database.metadata.tables.iteritems()))
    ModuleClass = None
    if not keep_files:
        try:
            ModuleClass = hf.module.getModuleClass(module)
        except Exception:
            print "\033[1m\033[31mWarning: \033[0mModule class for '{0}' not available, archive files will not be removed!".format(module)
    columns = [module_table.c.id, hf_runs.c.time]
    if ModuleClass:
        columns.extend(list(map(lambda x: getattr(module_table.c, x),
                                hf.module.getColumnFileReference(module_table))))

    def where_clauses(query):
        query = query.where(module_table.c.instance == module_instance_name)
        query = query.where(module_table.c.run_id == hf_runs.c.id)
        if timerange:
            query = query.where(hf_runs.c.time < timerange[0])
        return query
    
    query = where_clauses(select(columns))
    cnt = where_clauses(select([func.count(hf_runs.c.id)]))\
          .execute().fetchone()[0]
    to_delete = []
    for i, x in enumerate(list(query.execute())):
        ###
        # Find files from main and subtables
        entry_id, time, files = just(3, x)
        print i, "of", cnt
        files_to_delete = []
        for filename in filter(lambda x: x and len(x) > 0, files):
            filepath = downloadService.getArchivePath({'time': time},
                                                      filename)
            files_to_delete.append(filepath)
        for sub in subtables.itervalues():
            columns = [sub.c.id]
            if ModuleClass:
                columns.extend(list(map(lambda x: getattr(sub.c, x),
                               hf.module.getColumnFileReference(sub))))
            query = select(columns).where(sub.c.parent_id == entry_id)
            for x in list(query.execute()):
                sub_id, files = just(2, x)
                for filename in filter(lambda x: x and len(x) > 0, files):
                    filepath = downloadService.getArchivePath({'time': time},
                                                              filename)
                    files_to_delete.append(filepath)
        try:
            with hf.database.engine.begin() as conn:
                for sub in subtables.itervalues():
                    conn.execute(sub.delete(sub.c.parent_id == entry_id))
                conn.execute(module_table.delete(module_table.c.id == entry_id))
            for filepath in files_to_delete:
                try:
                    os.unlink(os.path.abspath(filepath))
                except OSError:
                    pass
        except Exception, e:
            traceback.print_exc()
