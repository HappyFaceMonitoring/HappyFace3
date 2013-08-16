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

import hf
import logging
import traceback
import os
from mako.template import Template
import cherrypy as cp
from sqlalchemy.exc import DatabaseError


class ModuleProxy:
    """
    The access class to actual instances of the module class.

    Since the module instances have to be independant and thread-safe
    for rendering, the common state is stored in the proxy, which
    creates a specific, run-time dependant module object for rendering.
    """

    def __init__(self, ModuleClass, instance_name, config):
        self.logger = logging.getLogger(self.__module__+'('+instance_name+')')
        self.ModuleClass = ModuleClass
        self.module_name = ModuleClass.module_name
        self.module_table = ModuleClass.module_table
        self.subtables = ModuleClass.subtables
        self.instance_name = instance_name
        self.config = config
        self.acquisitionModules = {}

        if 'access' not in self.config:
            self.config['access'] = 'open'
        if self.config['access'] not in ['open', 'restricted']:
            self.logger.warning("Unknown access option '%s', assume 'open'"% self.config['access'])
            self.config['access'] = 'open'

        # check if instance is in database and of correct type
        instance = hf.module.database.module_instances.select(hf.module.database.module_instances.c.instance==instance_name).execute().fetchone()
        if instance is None:
            hf.module.database.module_instances.insert().values(instance=instance_name, module=self.module_name).execute()
        elif instance["module"] != self.module_name:
            raise hf.ConsistencyError("The module type of instance '%s' changed" % instance_name)

        # get the common module template
        try:
            filename = os.path.join(os.path.dirname(self.ModuleClass.filepath), self.module_name+".html")
            self.template = Template(filename=filename, lookup=hf.template_escape_lookup)
            self.logger.debug(self.template.code)
        except Exception, e:
            self.logger.error("Cannot create template, " + str(e))
            self.logger.error(traceback.format_exc())
            self.template = None

    def isAccessRestricted(self):
        return self.config['access'] != 'open'

    def isUnauthorized(self):
        return (self.config['access'] == 'restricted' and
                not cp.request.cert_authorized)

    def prepareAcquisition(self, run):
        # create module instance solely for that purpose
        module = self.ModuleClass(self.instance_name, self.config,
                                  run, None, None)
        self.acquisitionModules[run['id']] = module
        try:
            module.prepareAcquisition()
        except Exception, e:
            exc_name = "Exception %s occured:" % str(e.__class__)
            module.logger.error(exc_name)
            if isinstance(e, hf.exceptions.ConfigError):
                exc_name = "Configuration Error:"
            module.error_string = exc_name + " " + str(e)
            module.logger.error("prepareAcquisition() failed: %s" % str(e))
            module.logger.error(traceback.format_exc())

    def acquire(self, run):
        module = self.acquisitionModules[run['id']]
        try:
            self.acquisitionModules[run['id']] = module
            data = {"instance": self.instance_name,
                    "run_id": run["id"],
                    "status": 1.0,
                    "error_string": module.error_string,
                    "source_url": "",
                    "description": self.config["description"],
                    "instruction": self.config["instruction"]
                    }
            dataExctractionSuccessfull = False
            try:
                if module.error_string:
                    data["status"] = 0.0
                else:
                    d = module.extractData()
                    data.update(d)

                    # we treat file columns specially!
                    # If they are None -> Empty String
                    # If they are a downloaded file obj -> getArchiveFilename
                    file_columns = hf.module.getColumnFileReference(module.module_table)
                    for col in file_columns:
                        if data[col] is None:
                            data[col] = ''
                        elif hasattr(data[col], 'getArchiveFilename'):
                            data[col] = data[col].getArchiveFilename()

                    if module.source_url:
                        if(isinstance(module.source_url, str)
                           or isinstance(module.source_url, unicode)):
                            module.source_url = module.source_url.replace("|", "%7C")
                            data["source_url"] = module.source_url
                        elif hasattr(module.source_url, "__iter__"):
                            module.source_url = map(lambda x: x.replace("|", "%7C"), module.source_url)
                            data["source_url"] = "|".join(module.source_url)
                        else:
                            raise hf.ModuleProgrammingError(
                                self.module_name,
                                "source_url has unexpected type {0}"
                                .format(type(module.source_url)))

                    # Set the data ID pointing to the actual data if smart filling is used.
                    if module.use_smart_filling:
                        if module.smart_filling_keep_data is None:
                            raise hf.ModuleRuntimeError("Smart filling is used but smart_filling_keep_data was not set!")
                        elif module.smart_filling_keep_data:
                            d["sf_data_id"] = None
                        else:
                            if module.smart_filling_current_dataset is None:
                                raise hf.ModuleRuntimeError("Smart filling was instructed to copy old dataset, but no data is available in past")

                            # remember where data is
                            data["sf_data_id"] = module.smart_filling_current_dataset["id"]

                            # copy over old data, ignoring certain fields
                            ignore = ["id", "run_id", "description",
                                      "instruction", "sf_data_id"]
                            data.update(dict(filter(
                                lambda x: x[0] not in ignore,
                                module.smart_filling_current_dataset.iteritems())))

                    dataExctractionSuccessfull = True
            except hf.DownloadError, e:
                self.logger.info("Data exctraction failed because of failed download: "+str(e))
                data.update({
                    "status": -1,
                    "error_string": str(e)
                })
            except hf.ModuleRuntimeError, e:
                self.logger.error("Runtime error during data exctraction: "+str(e))
                self.logger.error(traceback.format_exc())
                data.update({
                    "status": -1,
                    "error_string": str(e)
                })
            except hf.ModuleProgrammingError, e:
                self.logger.error("Programming error during data extraction: "+str(e))
                self.logger.error(traceback.format_exc())
                data.update({
                    "status": -1,
                    "error_string": str(e)
                })
            except Exception, e:
                self.logger.error("Data extraction failed: {0.__class__.__name__}: {0}".format(e))
                self.logger.error(traceback.format_exc())
                data.update({
                    "status": -1,
                    "error_string": str(e)
                })
            finally:
                print "ADD THE SHIT!", self.instance_name
                result = module.module_table.insert().values(**data).execute()

            # compatibility between different sqlalchemy versions
            try:
                inserted_id = result.inserted_primary_key[0]
            except AttributeError:
                inserted_id = result.last_inserted_ids()[0]

            if dataExctractionSuccessfull:
                try:
                    if((module.use_smart_filling and
                        module.smart_filling_keep_data) or
                       not module.use_smart_filling):
                        module.fillSubtables(inserted_id)
                except Exception, e:
                    self.logger.error("Filling subtables failed: "+str(e))
                    self.logger.error(traceback.format_exc())
                    if len(data["error_string"]) > 0:
                        data["error_string"] += "; "
                    data["error_string"] += str(e)
                    module.module_table.update().\
                        where(module.module_table.c.id == inserted_id).\
                        values(error_string=data["error_string"]).\
                        execute()

        except Exception, e:
            module.logger.error("data acquisition failed: %s" % str(e))
            module.logger.error(traceback.format_exc())
        finally:
            del self.acquisitionModules[run['id']]

    def getModule(self, run):
        """
        Generate a module instance object for a specific
        HappyFace run.
        """
        try:
            dataset = self.module_table.select(self.module_table.c.run_id==run["id"])\
                                               .where(self.module_table.c.instance ==
                                                      self.instance_name)\
                                               .execute()\
                                               .fetchone()
            if dataset is not None:
                file_columns = hf.module.getColumnFileReference(self.module_table)
                # create access objects for files if name is not empty, in this case None
                dataset = dict((col, (hf.downloadservice.File(run, val)
                                      if val else None)
                                if col in file_columns else val)
                               for col, val in dataset.items())
                dataset["source_url"] = dataset["source_url"].split("|")
        except DatabaseError, e:
            dataset = {
                'error_string': "Unable to acquire data for module. Probably the database schema needs an update!",
                'status': -1,
            }
            self.logger.error("Acquisition of module data failed: " + unicode(e))
            self.logger.error("Probably database schema needs update!")
            self.logger.error(traceback.format_exc())
        except Exception, e:
            dataset = {
                'error_string': "Unable to acquire data for module"
            }
            self.logger.error("Creation of time-specific module instance failed: " + unicode(e))
            self.logger.error(traceback.format_exc())
        module = self.ModuleClass(self.instance_name, self.config, run, dataset, self.template)
        return module


