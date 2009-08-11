from ModuleBase import *
from XMLParsing import *

class dCacheInfo(ModuleBase):

    def __init__(self,category,timestamp,storage_dir):

        # inherits from the ModuleBase Class
        ModuleBase.__init__(self,category,timestamp,storage_dir)

	config = self.readConfigFile('./happycore/dCacheInfo')
        self.readDownloadRequests(config)
	self.addCssFile(config,'./happycore/dCacheInfo')

        self.dsTag = 'dcach_poolinfo_xml'

                      
    def getPoolInfo(self,poolgroupname):

        if not self.dsTag in self.downloadRequest:
            err = 'Error: Could not find required tag: '+self.dsTag+'\n'
            sys.stdout.write(err)
            self.error_message +=err
            return -1

        dl_error,sourceFile = self.downloadService.getFile(self.downloadRequest[self.dsTag])
        if dl_error != "":
            self.error_message+= dl_error
            return

	source_tree,xml_error = XMLParsing().parse_xmlfile_minidom(sourceFile)
        self.error_message += xml_error

        ##############################################################################
        # if xml parsing fails, abort the test; 
	# self.status will be pre-defined -1
        if source_tree == "": return

#        poolref = 'cms-write-tape-pools'

        poolInfo = {}

        for pools in source_tree.getElementsByTagName('pools'):
            for pool in pools.getElementsByTagName('pool'):
                
                accept = False
                for poolgoups in pool.getElementsByTagName('poolgroupref'):
                    if poolgoups.getAttribute('name').count(poolgroupname):
                        accept = True
                if accept==True:
                    poolInfo[pool.getAttribute('name')] = {}
                    spaceValues = {}
                    for space in pool.getElementsByTagName('space'):
                        for metric in space.getElementsByTagName('metric'):
                            spaceValues[metric.getAttribute('name')] = metric.firstChild.data

                    poolInfo[pool.getAttribute('name')] = spaceValues



        return poolInfo

    def printPoolInfo(self,poolInfo):

        for pool in poolInfo.keys():
            print pool
            for val in poolInfo[pool].keys():
                print ' -- '+val+" "+poolInfo[pool][val]

            used  =  int(poolInfo[pool]['used'])
            free  =  int(poolInfo[pool]['free'])
            precious  =  int(poolInfo[pool]['precious'])
            total = int(poolInfo[pool]['total'])
            print "Total ="+str(total-used-free)
           

                
        print len(poolInfo)
     
