
import threading, sys, cStringIO, traceback, re
from graphtool.base import GraphToolInfo
from graphtool.base.xml_config import XmlConfig

try:
  import cx_Oracle
  cx_Oracle.OPT_Threading = 1
  oracle_present = True
except:
  oracle_present = False

try:
  import MySQLdb
  mysql_present = True
except Exception, e:
  mysql_present = False

class DatabaseInfo( GraphToolInfo ):

  def __init__( self, *args, **kw ):
    super( DatabaseInfo, self ).__init__( *args, **kw )
    self.consume_keyword( 'conn' )
    self.consume_keyword( 'db' ) 
    self.getDbParams()
    self.conn = None
    
  def __getattr__( self, attr ):
    if attr == 'conn' and self.conn == None:
      my_conn = self.getConnection()
      self.conn = my_conn
      return my_conn
    elif attr == 'conn':
      return self.conn
    if attr == 'orcl':
      self.conn = self.restoreConnection( self.__getattr__( 'conn' ) )
      return self.conn
    else:
      return super( DatabaseInfo, self ).__getattr__( attr )

  def testConnection( self, conn ):
    try:
      if self.info['Interface'] == 'Oracle':
        test = 'select * from dual'
        curs = conn.cursor()
        curs.prepare( test )
        curs.execute( test )
        curs.fetchone()
        assert curs.rowcount > 0
        curs.close()
      elif self.info['Interface'] == 'MySQL':
        mysql_lock.acquire()
        test = 'select 1+1'
        curs = conn.cursor()
        curs.execute( test )
        curs.fetchall()
        assert curs.rowcount > 0
        curs.close()
        mysql_lock.release()
    except Exception, e:
      #print e
      return False
    return True

  def restoreConnection( self, conn ):
    if not self.testConnection( conn ):
      #print "Test connection failed!"
      self.killConnection( conn )
      conn = self.getConnection()
    return conn

  def killConnection( self, conn ):
    try:
      conn.rollback()
      conn.close()
    except:
      pass

  def getDbParams( self, *args ):
    if len(args) == 0:
      filename, section = self.db.split(':')
    elif len(args) == 1:
      filename, section = args[0].split(':')
    elif len(args) == 2:
      filename, section = args
    else:
      print "Wrong number of arguments to getDbParams (contact developers!)"
      sys.exit(-1)
    try:
      file = open( filename, 'r' )
    except:
      print "Unable to open specified DBParam file %s" % filename
      print "Check the path and the permissions."
      sys.exit(-1)
    rlines = file.readlines()
    info = {}
    start_section = False
    for line in rlines:
      if len(line.lstrip()) == 0 or line.lstrip()[0] == '#':
        continue
      tmp = line.split(); tmp[1] = tmp[1].strip()
      if tmp[0] == "Section" and tmp[1] == section:
        start_section = True
      if tmp[0] == "Section" and tmp[1] != section and start_section:
        break
      if start_section:
        info[tmp[0]] = tmp[1]
    if start_section == False:
      print "Could not find section named: %s" % section
      print "Check capitalization, contents of file.  Failing!"
      sys.exit(-1)
    self.info = info
    return info

  def getConnection( self, *args ):
    if len(args) == 0:
      info = self.info
    else:
      info = args[0]
      self.info = info
    if info['Interface'] == 'Oracle' and oracle_present == False:
      raise Exception( "Could not import Oracle DB module.  Abort!" )
    elif info['Interface'] == 'Oracle':
      orcl = cx_Oracle.connect(info['AuthDBUsername'] + '/' + \
        info['AuthDBPassword'] + '@' + info['Database'])
      curs = orcl.cursor()
      curs.execute('set role ' + info['AuthRole'] + ' identified by ' +
        info['AuthRolePassword'])
      curs.close()
      return orcl
    elif info['Interface'] == 'MySQL' and mysql_present == False:
      raise Exception( "Could not import MySQL DB module.  Abort!" )
    elif info['Interface'] == 'MySQL':
      kw = {}
      assignments = {'host':'Host', 'user':'AuthDBUsername',
                     'passwd':'AuthDBPassword', 'db':'Database',
                     'port':'Port' }
      for key in assignments.keys():
        if assignments[key] in info.keys():
          kw[key] = info[ assignments[key] ]
          if key == 'port':
            kw[key] = int(kw[key])
      conn = MySQLdb.connect( **kw )
      return conn
    else:
      raise Exception( "Unknown DB interface module: %s.  Abort!" % info['Interface'] )


class DatabaseInfoV2( XmlConfig ):

  def __init__( self, *args, **kw ):
    self.conn_manager = None
    super( DatabaseInfoV2, self ).__init__( *args, **kw )

  def parse_dom( self, *args, **kw ):
    super( DatabaseInfoV2, self ).parse_dom( *args, **kw )
    if 'connection_manager' in self.__dict__.keys():
      conn_man_name = self.connection_manager
    else:
      raise ValueError( "Connection Manager name not passed." )
    classes = self.find_classes( must_be_executable=False )
    if conn_man_name not in classes.keys():
      raise Exception( "Cannot find connection manager named %s" % conn_man_name )
    self.conn_manager = classes[ conn_man_name ]

  def execute_sql( self, sql_string, sql_var, conn=None, **kw ):

    try:
      conn = self.conn_manager.get_connection( conn )
      results = conn.execute_statement( sql_string, sql_var )
    except Exception, e:
      if len(e.args) == 1:
        msg = str(e.args[0])
        m = re.search('Unknown database \'(.*)\'', msg)
        if m:
          db = m.groups(0)
          raise Exception("Unknown database: %s" % db)
      out = cStringIO.StringIO()
      print >> out, "\nUnable to successfully query database, exception follows:\n"
      print >> out, e, "\n"
      print >> out, "Used sql:\n%s" % sql_string
      print >> out, "Used vars:", sql_var, "\n"
      traceback.print_exc( file=out )
      #print >> out, "Last Traceback:\n", last_traceback,'\n'
      raise Exception( out.getvalue() )

    return results

