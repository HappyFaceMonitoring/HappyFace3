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
import logging, traceback, os
from mako.template import Template
import cherrypy as cp

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
            self.logger.warning("Unknown access option '%s', assume 'open'" % self.config['access'])
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
            self.template = Template(filename=filename, lookup=hf.template_lookup)
        except Exception, e:
            self.logger.error("Cannot create template, " + str(e))
            self.logger.debug(traceback.format_exc())
            self.template = None
            
    def isAccessRestricted(self):
        return self.config['access'] != 'open'
    
    def isUnauthorized(self):
        return self.config['access'] == 'restricted' and not cp.request.cert_authorized
        
    def prepareAcquisition(self, run):
        # create module instance solely for that purpose
        module = self.ModuleClass(self.instance_name, self.config, run, None, None)
        self.acquisitionModules[run['id']] = module
        try:
            module.prepareAcquisition()
        except Exception, e:
            module.logger.error("prepareAcquisition() failed: %s" % str(e))
            module.logger.debug(traceback.format_exc())
    
    def acquire(self, run):
        module = self.acquisitionModules[run['id']]
        try:
            self.acquisitionModules[run['id']] = module
            data = {"instance": self.instance_name,
                    "run_id": run["id"],
                    "status": 1.0,
                    "error_string": "",
                    "source_url": "",
                    "description": self.config["description"],
                    "instruction": self.config["instruction"]
                    }
            dataExctractionSuccessfull = False
            try:
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
                
                dataExctractionSuccessfull = True
            except Exception, e:
                self.logger.error("Data extraction failed: "+str(e))
                self.logger.debug(traceback.format_exc())
                data.update({
                    "status": -1,
                    "error_string": str(e)
                })
            finally:
                result = module.module_table.insert().values(**data).execute()
            
            # compatibility between different sqlalchemy versions
            try:
                inserted_id = result.inserted_primary_key[0]
            except AttributeError:
                inserted_id = result.last_inserted_ids()[0]
            
            if dataExctractionSuccessfull:
                try:
                    module.fillSubtables(inserted_id)
                except Exception, e:
                    self.logger.error("Filling subtables failed: "+str(e))
                    self.logger.debug(traceback.format_exc())
                    if len(data["error_string"]) > 0:
                        data["error_string"] += "; "
                    data["error_string"] += str(e)
                    module.module_table.update().where(module.module_table.c.id == inserted_id).values(error_string=data["error_string"]).execute()
        
        except Exception, e:
            module.logger.error("data acquisition failed: %s" % str(e))
            module.logger.debug(traceback.format_exc())
        finally:
            del self.acquisitionModules[run['id']]
    
    def getModule(self, run):
        """
        Generate a module instance object for a specific
        HappyFace run.
        """
        dataset = self.module_table.select(self.module_table.c.run_id==run["id"])\
                .where(self.module_table.c.instance==self.instance_name)\
                .execute()\
                .fetchone()
        if dataset is not None:
            file_columns = hf.module.getColumnFileReference(self.module_table)
            # create access objects for files if name is not empty, in this case None
            dataset = dict((col, (hf.downloadservice.File(run, val) if len(val)>0 else None) if col in file_columns else val) for col,val in dataset.items())
        template = self.template
        module = self.ModuleClass(self.instance_name, self.config, run, dataset, template)
        return module

    
