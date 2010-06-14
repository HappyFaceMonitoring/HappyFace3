#!/usr/bin/python

import DBSAPI_v2.dbsApi
from grid_control import utils, DatasetError, datasets
from grid_control.datasets import DataProvider

def createDBSAPI(url):
	if url == '':
		url = 'http://cmsdbsprod.cern.ch/cms_dbs_prod_global/servlet/DBSServlet'
	if not 'http://' in url:
		url = 'http://cmsdbsprod.cern.ch/%s/servlet/DBSServlet' % url
	return DBSAPI_v2.dbsApi.DbsApi({'version': 'DBS_2_0_6', 'level': 'CRITICAL', 'url': url})

