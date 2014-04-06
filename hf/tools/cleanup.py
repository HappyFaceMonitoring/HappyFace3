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
import logging


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
    parser = argparse.ArgumentParser(description="Remove old datasets from HappyFace database")
    #parser.add_argument("-d", "--days", nargs=1, metavar="N",
                        #help="Operate on the data of the past N days")
    #parser.add_argument("-s", "--start", nargs=1, metavar="ISOSTART",
                        #help="ISO-date when the selected timerange bla")
    parser.add_argument("-v", "--verbose", action="store_true", default=False,
                        help="Increase verbosity of output")
    subparsers = parser.add_subparsers(dest="subparser_name")
    parser_dict = {}

    sub = subparsers.add_parser("list-modules", help="List detected modules.")
    parser_dict[sub.prog.split()[-1]] = sub
    sub.add_argument("-u", "--used", action="store_true", default=False,
                     help="List only modules used by the configuration.")
    sub.add_argument("-n", "--not-used", action="store_true", default=False,
                     help="List only modules found in the database but unreferenced in the configuration.")
    sub.set_defaults(func=_list_modules)

    sub = subparsers.add_parser("clear",
                                help="Remove unused data from configured modules.",
                                description="""Remove all data from used modules in specified timerange.
Data from unused tables is not removed. Database backend dependent cleanup,
e.g. SQLite VACUUM is \033[1m\033[31mnot\033[0m performed.""")
    parser_dict[sub.prog.split()[-1]] = sub
    sub.add_argument("-i", "--interactive",
                     action="store_true", default=False,
                     help="Ask before cleaning a table. Ignores --silent.")
    sub.add_argument("--all", action="store_true", default=False,
                        help="Remove all data from database.")
    sub.add_argument("-d", "--days", nargs=1, metavar="N",
                        help="Remove data older than N days.")
    sub.add_argument("--stop-date", nargs=1, metavar="ISODATE_STOP",
                        help="Data before ISODATE_STOP is removed from the database. Use ISO date format 'YYYY-MM-DD HH:MM'.")
    sub.add_argument("--start-date", nargs=1, metavar="ISODATE_START",
                        help="Data after ISODATE_START is removed from the database. Use ISO date format 'YYYY-MM-DD HH:MM'. Be caution when using this, potentialy new and useful data is removed! Use with --stop-date.")
    sub.add_argument("--silent", action="store_true", default=False,
                     help="Do not ask for user confirmation on critical actions.")
    sub.set_defaults(func=_clear)

    args = parser.parse_args()
    tools.load_env()
    logger = logging.getLogger()
    for handlers in logger.handlers:
        logger.removeHandler(handlers)
    logger.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(levelname)s: %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    ch = logging.FileHandler(os.path.join(hf.hf_dir, "log", "tool-cleanup.log"))
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    hf.database.metadata.reflect(hf.database.engine)
    args.func(parser_dict[args.subparser_name], args)
    # check no-action commands
    #if args.days is not None:
        #now = datetime.datetime.now()
        #timerange = [(now-datetime.timedelta(int(args.days[0]), 0, 0)), now]
    #if args.list_modules:
        #list_modules()
    #else:
        #for instance, module, module_table, used in\
            #sorted(get_module_instances(), key=lambda x: x[1]):
            #print "Clearing {0}".format(instance)
            #clear_contents(instance, module, module_table,
                           #keep_files=args.keep_files, timerange=timerange)


def confirm(message, silent=False):
    if silent:
        return True
    print message, "[Y/n]"
    line = sys.stdin.readline().strip().lower()
    while line not in ("y", "n", ""):
        line = sys.stdin.readline().strip().lower()
    return line != "n"


def get_module_instances():
    # classes_by_mod_table = dict((table_name, cls) for hf.module.module.__)
    module_instances = hf.module.database.module_instances
    ret = set()
    for table_name, table in hf.database.metadata.tables.iteritems():
        if not table_name.startswith("mod_"):
            continue
        query = select([table.c.instance, module_instances.c.module]).\
                where(table.c.instance == module_instances.c.instance).\
                distinct()
        for inst, mod in query.execute():
            if hf.module.moduleClassLoaded(mod):
                # is instance it really in configuration?
                used = inst in hf.module.config.sections()
            else:
                used = None
            ret.add((inst, mod, table, used))
    query = select([module_instances.c.instance, module_instances.c.module]).\
            distinct()
    for inst, mod in query.execute():
        if hf.module.moduleClassLoaded(mod):
            # is instance it really in configuration?
            used = inst in hf.module.config.sections()
        else:
            used = None
        try:
            table = hf.module.getModuleClass(mod).module_table
            ret.add((inst, mod, table, used))
        except hf.exceptions.ConfigError:
            continue
    ret = [a for a in ret]
    return ret


def _list_modules(parser, args):
    fmt = "{instance:<35} {module:<30} {oldest:>10} {status:}"
    hf_runs = hf.module.database.hf_runs
    print "\033[1m\033[31", fmt.format(instance="Instance",
                                       module="Module",
                                       oldest="Oldest Age",
                                       status="Status"), "\033[0m"
    prev_module = None
    for instance, module, module_table, used in sorted(get_module_instances(),
                                                       key=lambda x: x[1]):
        if((args.used or args.not_used) and
           not (args.used and used) and
           not (args.not_used and not used)):
            continue
        expr = select([hf_runs.c.time])\
            .where(hf_runs.c.id ==
                   module_table.c.run_id) \
            .where(module_table.c.instance == instance)\
            .order_by(hf_runs.c.time.asc())
        try:
            oldest = expr.execute().fetchone()[0]
            age_days = str((datetime.datetime.now()-oldest).days)+"d"
        except TypeError:
            age_days = "N/A"

        if used is not None:
            status = ("used" if used else "\033[1m\033[31munused\033[0m")
        else:
            status = "\033[1m\033[31mNOT FOUND\033[0m"
        print fmt.format(instance=instance,
                         module=module if module != prev_module else " | ",
                         oldest=age_days,
                         status=status)
        prev_module = module


def _clear(parser, args):
    logger = logging.getLogger("clear")
    timerange = [None, None]
    if not (args.days or args.start_date or args.stop_date) and not args.all:
        parser.error("No timerange specified! To delete all data, use --all.")
    if args.days and (args.start_date or args.stop_date):
        parser.error("Cannot use --days with --start-date or --stop-date!")
    if args.days:
        timerange[1] = datetime.datetime.now() - datetime.timedelta(days=int(args.days[0]))
    else:
        if args.start_date:
            timerange[0] = datetime.datetime.strptime(
                args.start_date[0],
                "%Y-%m-%d %H:%M"
                )
        if args.stop_date:
            timerange[1] = datetime.datetime.strptime(
                args.stop_date[0],
                "%Y-%m-%d %H:%M"
                )
    if not confirm("--all specifed, you are about to delete all data! Continue?",
                   silent=args.silent):
        return
    to_remove = get_module_instances()
    for instance, mod, mod_table, used in get_module_instances():
        if not used:
            continue
        if args.interactive and not confirm(
                "Clear module {0} of type {1}?".format(
                    instance, mod)):
            continue
        logger.info("Clear module {0}, type {1}".format(
                    instance, mod))
        clear_contents(instance, mod, mod_table, timerange, logger)


def clear_contents(module_instance_name, module,
                   module_table, timerange, logger, keep_files=False):
    subtables = dict(filter(lambda x: x[0].startswith("sub_"+module_table.name[4:]+"_"),
                            hf.database.metadata.tables.iteritems()))
    ModuleClass = None
    if not keep_files:
        try:
            ModuleClass = hf.module.getModuleClass(module)
        except Exception:
            logger.warning("Module class for '{0}' not available, archive files will not be removed!".format(module))
    columns = [module_table.c.id, hf_runs.c.time]
    if ModuleClass:
        columns.extend(list(map(lambda x: getattr(module_table.c, x),
                                hf.module.getColumnFileReference(module_table))))

    def where_clauses(query):
        query = query.where(module_table.c.instance == module_instance_name)
        query = query.where(module_table.c.run_id == hf_runs.c.id)
        if timerange[0]:
            query = query.where(hf_runs.c.time > timerange[0])
        if timerange[1]:
            query = query.where(hf_runs.c.time < timerange[1])
        return query

    query = where_clauses(select(columns))
    cnt = where_clauses(select([func.count(hf_runs.c.id)]))\
          .execute().fetchone()[0]
    to_delete = []
    for i, x in enumerate(list(query.execute())):
        ###
        # Find files from main and subtables
        entry_id, time, files = just(3, x)
        sys.stdout.write("\33[2K\r{0} of {1}".format(i+1, cnt))
        sys.stdout.flush()
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
    else:
        sys.stdout.write("\n")
        sys.stdout.flush()
