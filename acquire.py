#!/usr/bin/env python

import hf
import os, datetime, traceback
import ConfigParser

if __name__ == '__main__':
    cfg_dir = None
    hf.hf_dir = os.path.dirname(os.path.abspath(__file__))
    hf.configtools.readConfiguration()
    hf.configtools.importModules()
    
    hf.database.connect(implicit_execution = True)
    hf.database.metadata.create_all()
    
    category_list = hf.configtools.createCategoryObjects()
    
    time = datetime.datetime.now()
    result = hf.module.database.hf_runs.insert().values(time=time).execute()
    run = {"id":result.inserted_primary_key[0], "time":time}
    
    print "Prepare data acquisition"
    for category in category_list:
        print "  %s..." % category.config["name"],
        category.prepareAcquisition(run)
        print "done"
    
    hf.downloadService.performDownloads(time)
    
    print "Acquire data and fill database"
    for category in category_list:
        print "  %s..." % category.config["name"],
        category.acquire(run)
        print "done"
    
    hf.database.disconnect()