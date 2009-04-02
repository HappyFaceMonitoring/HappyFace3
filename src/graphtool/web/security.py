
from graphtool.database.queries import SqlQueries

def security_parser(rows, **kw):
    if len(rows) > 1:
        return True, kw
    if len(rows) == 0:
        return False, kw
    try:
        if len(rows) == 1 and int(rows[0][0]) > 0:
            return True, kw
    except:
        return False, kw
    return False, kw

def role_list(rows, **kw):
    roles = []
    for row in rows:
        roles.append(row[0])
    return roles, kw

class Security(SqlQueries):

    def authenticate(self, auth_command, dn, access, *args, **kw):
        cmd_args = args
        cmd_name = auth_command

        if cmd_name in self.commands.keys():
            cmd_func = getattr(self, cmd_name)
        else:
            raise Exception("Authentication command name %s not known" % cmd_name)
        values = {'dn': dn, 'access': access}
        results, metadata = cmd_func(**values)
        if results:
            return True
        return False

    def list_roles(self, auth_command, dn):
        cmd_name = 'list_' + auth_command

        if cmd_name in self.commands.keys():
            cmd_func = getattr(self, cmd_name)
        else:
            raise Exception("Authentication command name %s not known" % cmd_name)
        values = {'dn': dn}
        results, metadata = cmd_func(**values)
        return results

class DenyAll(SqlQueries):

    def authenticate(self, auth_command, dn, access, *args, **kw):
        return False

    def list_roles(self, auth_command, dn):
        return []
