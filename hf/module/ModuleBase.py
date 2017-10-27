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
from hf.module.module import __module_class_list as _module_class_list
from hf.module.module import __column_file_list as _column_file_list
from mako.template import Template
import cherrypy as cp
import logging
import traceback
import os
import re
from sqlalchemy import Integer, Float, Numeric, Table, Column, Sequence, Text, Integer, Float, ForeignKey
from sqlalchemy.exc import DatabaseError


class ModuleMeta(type):
    """
    Meta Class of :class:`ModuleBase <hf.module.ModuleBase>`.

    Its purpose is checking for the declarative module specification as described in :ref:`mod-dev-classvars`,
    as well as registering module classes in the system and creating additional variables based on the
    declaration.
    """

    def __init__(self, name, bases, dct):
        # if we are the ModuleBase class we do nothing
        if name == "ModuleBase":
            super(ModuleMeta, self).__init__(name, bases, dct)
            return

        # check for errors in the implementation of the 3. party Module given
        if "config_keys" not in dct:
            raise hf.exceptions.ModuleProgrammingError(name, "No config_keys dictionary specified")
        if "config_hint" not in dct:
            #raise hf.exceptions.ModuleProgrammingError(name, "No configuration hint config_hint specified (empty string possible)")
            self.config_hint = ''
        if "table_columns" not in dct:
            raise hf.exceptions.ModuleProgrammingError(name, "table_colums not specified")
        if "subtable_columns" not in dct:
            self.subtable_columns = {}

        if "use_smart_filling" not in dct:
            self.use_smart_filling = False

        self.subtables = {}

        #if none of the errors triggered we are able to instantiate the class.
        super(ModuleMeta, self).__init__(name, bases, dct)

        # check if methods are implemented
        if not hasattr(self, 'extractData'):
            raise hf.exceptions.ModuleProgrammingError(name, "extractData not implemented")

        # check if a module of that name has not allready been created.
        if name in _module_class_list:
            raise hf.exceptions.ConfigError('A module with the name %s was already imported!' % name)
        self.module_name = name
        _module_class_list[name] = self

        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        tabname = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

        try:
            tab = self.generateModuleTable(tabname, self.table_columns[0])
            for fc in self.table_columns[1]:
                self.addColumnFileReference(tab, fc)
        except Exception, e:
            raise hf.exceptions.ModuleProgrammingError(name, "Generating module table failed: " + str(e))
        for sub, (columns, fc_list) in self.subtable_columns.iteritems():
            try:
                tab = self.generateModuleSubtable(sub, columns)
                for fc in fc_list:
                    self.addColumnFileReference(tab, fc)
            except Exception, e:
                raise hf.exceptions.ModuleProgrammingError(name, "Generating subtable %s failed: %s" % (sub, str(e)))

        del self.table_columns
        try:
            del self.subtable_columns
        except Exception:
            pass

    def generateModuleTable(self, tabname, columns):
        if self.use_smart_filling:
            columns.append(Column("sf_data_id", Integer, ForeignKey("mod_" + tabname + ".id"), index=True))

        table = Table("mod_" + tabname, hf.database.metadata,
            *([
                Column('id', Integer, Sequence("mod_" + tabname + '_id_seq'), primary_key=True),
                Column('instance', Text, ForeignKey("module_instances.instance"), index=True),
                Column('run_id', Integer, ForeignKey("hf_runs.id"), index=True, ),
                Column('status', Float),
                Column('description', Text),
                Column('instruction', Text),
                Column('error_string', Text),
                Column('source_url', Text),
            ] + columns))
        self.module_table = table
        table.module_class = self
        return table

    def generateModuleSubtable(self, name, columns):
        tabname = "sub_" + self.module_table.name[4:] + '_' + name
        table = Table(tabname,
            hf.database.metadata,
            *([
                Column('id', Integer, Sequence(tabname + '_id_seq'), primary_key=True),
                Column('parent_id', Integer, ForeignKey(self.module_table.c.id), index=True),
            ] + columns))
        self.subtables[name] = table
        table.module_class = self
        return table

    def addColumnFileReference(self, table, column):
        name = table.name if isinstance(table, Table) else table
        _column_file_list[name] = _column_file_list[name] + [column] if name in _column_file_list else [column]


class ModuleBase:
    """ Base class for HappyFace modules.
        A module provides two core functions:

        1) Acquisition of data through the methods

            1) prepareAcquisition: Specify the files to download
            2) extractData: Return a dictionary with data to fill into the database
            3) fillSubtables: to write the datasets for the modules subtables

        2) Rendering the module by returning a template data dictionary in method getTemplateData.

        Because thread-safety is required for concurrent rendering, the module itself
        MUST NOT save its state during rendering. The modules functions are internally
        accessed by the ModuleProxy class.

        The status of the module represents a quick overview over the current module
        status and fitness.

        * 0.66 <= status <= 1.0  The module is happy/normal operation
        * 0.33 <= status < 0.66  Neutral, there are things going wrong slightly.
        * 0.0  <= status < 0.33  Unhappy, something is very wrong with the monitored modules
        * status = -1            An error occured during module execution
        * status = -2            Data could not be retrieved (download failed etc.)

        The category status is calculated with a user specified algorithm from the statuses
        of the modules in the category. If there is missing data or an error, the category
        index icon is changed, too.

        In practice, there is no "visual" difference between status -1 and -2, but there might
        be in future.

        .. note::

            A lot of the configuration is done with class variables in the derived class.
            All special variables are listed :ref:`here <mod-dev-classvars>`.

            Internaly, they are used to generate the database *Table* objects, generate
            default configuration and set whether the :ref:`smart filling mechanism <mod-dev-smart_filling>`
            shall be used.

        It makes use of the :class:`ModuleMeta <hf.module.ModuleBase.ModuleMeta>` class internally.

        .. attribute:: module_table

            Sqlalchemy *Table* object of the modules main data table

        .. attribute:: smart_filling_current_dataset

            The data dictionary from the last run with data or *None* if the module never
            inserted data in the databae before.

            .. note::
                Has a meaning only if :attr:`.use_smart_filling` is *True* and in the methods
                :meth:`.prepareAcquisition`, :meth:`.extractData` and :meth:`.getTemplateData`.

                Otherwise it is always *None*.

            Use *self.smart_filling_current_dataset["id"]* as parent ID for accessing data in subtables,
            since it belongs to the correct run containing data.

            In :meth:`.getTemplateData`, it is equal to :attr:`.dataset` if the run to display
            stored data.

            See :ref:`mod-dev-smart_filling` for more information,

        .. attribute:: smart_filling_keep_data

            Boolean flag to indicate that data shall be stored for the current run.
            If it is set to *False*, :meth:`.fillSubtables` is not called.

            .. note::
                Attribute is ignored if set outside of :meth:`.extractData`.

            .. warning::
                The default on module creation is *None*, causing an exception to
                be thrown if you don't set the flag to *True* or *False* in :meth:`.extractData`!

            See :ref:`mod-dev-smart_filling` for more information,

        .. attribute:: subtables

            A dictionary of sqlalchemy *Table* objects, with their given names
            as key.

        .. attribute:: source_url

            A list URLs for all the data sources of this module. You should set this already in
            prepare acquisition, otherwise the soruce URLs won't be displayed on the web output
            in case of an error.

            .. note::
                HappyFace will **not** quote your URL except pipes! Because the pipe symbol | is used as path
                separator internaly, the URL must not contain pipes, so HappyFace replaces them by the encoded
                equivalent %7C.

            If *source_url* is None (default), the respective entry in the data dictionary returned
            by :meth:`extractData <hf.module.ModuleBase.extractData>` is used. See also :ref:`smart filling <database_layout>`.
            This ensures backward compatibility with older versions of HappyFace.

        .. attribute:: module_name

            The name of the module class.

            .. note:: This is **not** the name of a specific instance!

        .. attribute:: instance_name

            The name of the instance of the module currently processed.

        .. attribute:: short_name

            A short variant of the instance name. This will mainly be used in
            the fastnav bar and is useful if the name is very
            descriptive and therefore quite long.

            The short name is specified with the short_name variable in the
            module configuration. If not specified, the
            long name will be
            used and :attr:`explicit_short_name <hf.module.ModuleBase.explicit_short_name>`
            will be set to *False*.

            .. seealso:: :ref:`config_module_variables`

        .. attribute:: explicit_short_name

            Flag indicating whether the short name in
            :attr:`short_name <hf.module.ModuleBase.short_name>` was specified
            explicitly in the module configuration or is just the
            normal name is used.

            This is currently used in the module information panel to show the
            short name only if it was not "auto generated".

            .. seealso:: :ref:`config_module_variables`

        .. attribute:: config

            A dictionary with the module configuration

        .. attribute:: run

            Only available in :meth:`.getTemplateData`. A dictionary
            with the *id* and *time* of the current run to be displayed.

        .. attribute:: dataset

            Only available in :meth:`.getTemplateData`. The data dictionary from
            the module table for the currently processed run.

        .. attribute:: category

            A reference to the :class:`hf.category.Category` object where the module is in.

        .. attribute:: template

            The Mako *Template* object.

        .. attribute:: weigth

            The 0..1 weight used in some category rating algorithms.

        .. attribute:: type

            Either *plots*, *rated* or *unrated*.

        .. attribute:: error_string

            In case of an error this attribute contains the error string,
            otherwise it is an empty string.

            It is the error string from the database except downloaded files
            if the data can be retrieved. When no data is found in the database,
            or retrieving it failed, a new error string is generated.

        .. attribute:: downloaded_files:

            When an error occured, this list provides information about
            input files. It is a list of pairs. The first item is the source
            URL of the file, the second is the URL to the temporary directory
            containing it.

        .. method:: extractData()

            Mandatory function to process some data and return it in a format that can be used to
            populate the module table. Downloaded files, e.g. in XML format, should be parsed here.

            If a part of the extracted data cannot be stored in the module table, but must be passed to
            a subtable, save it in a class variable. Then, save it into the databe with your own
            implementation of :meth:`fillSubtables`.

            For more information about subtables

            :return: A dictionary where the names of module table columns and the values are the data
                    to be inserted into the database. If a column is specified as a file column,
                    objects with an *getArchiveFilename()* method are accepted. This is the case for
                    :class:`hf.downloadservice.DownloadFile`, returned by the download service.
    """

    __metaclass__ = ModuleMeta

    config_defaults = {
        'description': '',
        'instruction': '',
        'type': 'rated',
        'weight': '1.0',
    }

    # set by hf.module.importModuleClasses
    filepath = None

    def __init__(self, instance_name, config, run, dataset, template):
        self.logger = logging.getLogger(self.__module__ + '(' + instance_name + ')')
        self.config = config
        self.module_name = self.__class__.module_name
        self.module_table = self.__class__.module_table
        self.subtables = self.__class__.subtables
        self.instance_name = instance_name
        try:
            self.short_name = self.config["short_name"]
            self.explicit_short_name = True
        except hf.exceptions.ConfigError:
            self.short_name = self.config["name"]
            self.explicit_short_name = False
        self.run = run
        self.dataset = dataset
        self.template = template
        # set by CategoryProxy.getCategroy() after creating specific module instances
        self.category = None
        self.source_url = None

        self.smart_filling_current_dataset = None
        self.smart_filling_keep_data = None

        if self.use_smart_filling:
            tab = self.module_table
            self.smart_filling_current_dataset = tab.select().where(tab.c.sf_data_id == None) \
                    .order_by(tab.c.id).limit(1).execute().fetchone()
            if self.smart_filling_current_dataset:
                self.smart_filling_current_dataset = dict(self.smart_filling_current_dataset)
            self.logger.debug("SF dataset: " + str(self.smart_filling_current_dataset))

        if self.dataset and "error_string" in self.dataset:
            error_info = self.dataset['error_string'].split("\0")
            if len(error_info) == 1:
                self.error_string = error_info[0]
                self.downloaded_files = []
            else:
                self.error_string = error_info[0]
                self.downloaded_files = [info.split("|||")
                                         for info in error_info[1:]]

        else:
            self.error_string = ''
            self.downloaded_files = []

        if not "type" in self.config:
            self.type = "unrated"
            self.logger.warn("Module type not specified, using 'unrated'")
        else:
            self.type = self.config['type']
        if self.type not in ('rated', 'plots', 'unrated'):
            self.logger.warn("Unknown module type '%s', using 'unrated'" % self.type)
            self.type = "unrated"

        if not "weight" in self.config:
            self.weight = 0.0
            self.logger.warn("Module weight not specified, ignore in calculations")
        else:
            try:
                self.weight = float(self.config['weight'])
            except Exception:
                self.logger.warn("Module weight not numeric, using 0.0")

    def prepareAcquisition(self):
        """
        **Override** this method if your module needs to download data,
        or has to perform some other action prior to the data acquisition run.
        """
        pass

    def fillSubtables(self, module_entry_id):
        """
        **Override** this method if your module uses subtables, to fill
        them with the data from :meth:`extractData`.

        To fill the subtable, you need the sqlalchemy table class and issue
        one or more insert statements. The Table classes are available in
        the :attr:`subtables` dictionary, where the
        key is the name specified in :data:`subtable_columns`.

        .. note::

            This function is not called if smart filling is used and the current data does not need to be stored. Namely,
            :attr:`.use_smart_filling` is *True* and :attr:`.smart_filling_keep_data` is *False*.

        For more information about subtables, see :ref:`mod-dev-subtable`

        :param module_entry_id: The ID of the module table entry that works as parent to
                                the subtable entries added by this call.
        :type module_entry_id: integer

        To fill a list of col->value dictionaries in an object attribute to a subtable
        called *details*, the following implementation can be used

        .. code-block:: python

         def fillSubtables(self, module_entry_id)
             table = self.subtables['details']
             for entry in self.extra_data:
                 table.insert().execute(dict(parent_id=module_entry_id, **entry))

        Actually, the insert accepts a list of dictionaries, but because we do
        not have the parent ID in the dicts yet, we cannot add it directly.

        An inline version using generator expressions would look like this

        .. code-block:: python

         def fillSubtables(self, module_entry_id)
             self.subtables['details'].insert().execute([dict(parent_id=module_entry_id, **row) for row in self.extra_data])

        Finally, a short, readable variant

        .. code-block:: python

         def fillSubtables(self, module_entry_id)
             self.extra_data = map(lambda x: x['parent_id'] = module_entry_id, self.extra_data)
             self.subtables['details'].insert().execute(self.extra_data)
        """
        pass

    def getTemplateData(self):
        """
        **Override** this method if your template requires special
        preprocessing of data or you have data in subtables.

        The :attr:`.dataset` and :attr:`.run` attributes are
        available in this method.

        :return: A dictionary that extends the Mako template namespace.
        """
        return {"dataset": self.dataset, "run": self.run}

    def __unicode__(self):
        return self.instance_name

    def __str__(self):
        return self.instance_name

    def getStatusString(self):
        """
        Get a string describing the status of the module.

        Depending of the module type the string is different, it can
        be used for example to get the name of an icon.

        It is one of *noinfo*, *happy*, *neutral*,
        *unhappy*, *unavail_plot*, *avail_plot*.

        .. note::
            This method only works in the render process.

        :rtype: string
        """
        if self.isUnauthorized():
            return 'noinfo' if self.type == 'rated' else 'unavail_plot'
        icon = 'unhappy'
        if self.dataset is None:
            icon = 'unhappy' if self.type == 'rated' else 'unavail_plot'
        else:
            if self.type == 'rated':
                if self.dataset['status'] > 0.66:
                    icon = 'happy'
                elif self.dataset['status'] > 0.33:
                    icon = 'neutral'
                else:
                    icon = 'unhappy'
            elif self.type == 'unrated':
                icon = 'happy'
            else:
                icon = 'avail_plot' if self.dataset['status'] > 0.9 else 'unavail_plot'
        return icon

    def url(self, only_anchor=True, time=None):
        """
        Get the URL to this module.

        :param only_anchor: If true, only the anchor part is returned
        :param time: If not None, the timestamp is included within the URL
        :type time: datetime or None
        """
        # something along ?date=2012-03-24&amp;time=17:20&amp;t=batchsys&amp;m=${module.instance_name}
        return ('' if only_anchor else self.category.url(time=time)) + u"#" + self.instance_name

    @hf.url.absoluteUrl
    def ajaxUrl(self):
        """
        Get the URL where AJAX requests to the modules are processed.

        If the module does not implement the :meth:`.ajax` method, accessing this URL
        returns a *404 File Not Found* response.
        """
        return "ajax/{0}/{1}".format(self.instance_name, self.run["id"])

    def getStatusIcon(self):
        """
        Get URL to a large status icon for the current module state.

        This function uses the icons located in *path.template_icons_url*.

        .. note::
            This method only works in the render process.
        """
        return os.path.join(hf.config.get('paths', 'template_icons_url'),
                            'mod_' + self.getStatusString() + '.png')

    def getNavStatusIcon(self):
        """
        Get URL to a small status icon for the current module state.

        This function uses the icons located in *path.template_icons_url*.

        .. note::
            This method only works in the render process.
        """
        return os.path.join(hf.config.get('paths', 'template_icons_url'),
                            'nav_' + self.getStatusString() + '.png')

    def getPlotableColumns(self):
        """
        Get the names of all columns than can be plotted, that is they
        are numerical and probably no IDs.

        :rtype: list
        """
        blacklist = ['id', 'run_id', 'instance', 'description',
                     'instruction', 'error_string', 'source_url']
        types = [Integer, Float, Numeric]

        def isnumeric(cls):
            for t in types:
                if isinstance(cls, t):
                    return True
            return False
        numerical_cols = filter(lambda x: isnumeric(x.type), self.module_table.columns)
        return [col.name for col in numerical_cols if col.name not in blacklist]

    def isAccessRestricted(self):
        """
        Find out if access to the module is restricted.

        :rtype: boolean
        :return: * True if a valid certificate is required to access the module
                 * False if access is open to anyone
        """
        return self.config['access'] != 'open'

    def isUnauthorized(self):
        """
        Check if the user from this request is authorized to access the module.
        This takes into account the module restriction and the user certificate,
        if available.

        .. note:: This method only works in the render process.

        :rtype: boolean
        :return: * True if the user must not access the module
                 * False if the user may access the module
        """
        return self.config['access'] == 'restricted' and not cp.request.cert_authorized

    def getPlotableColumnsWithSubtables(self):
        """
        Get the names of all columns than can be plotted, that is they
        are numerical and probably no IDs, for the module table and
        all subtables.

        The key of the module table is the empty string.

        :rtype: dict (subtable => list of columns)
        """
        cols = {'': self.getPlotableColumns()}

        blacklist = ['id', 'parent_id']
        types = [Integer, Float, Numeric]

        def isnumeric(cls):
            for t in types:
                if isinstance(cls, t):
                    return True
            return False

        for name, table in self.subtables.iteritems():
            numerical_cols = filter(lambda x: isnumeric(x.type), table.columns)
            cols[name] = [col.name
                          for col in numerical_cols
                          if col.name not in blacklist]

        return cols

    def getAllColumnsWithSubtables(self):
        """
        Get the names of all columns for the module table and
        all subtables. The key of the module table is the empty
        string, the other keys are the names of the subtables.

        :rtype: dict (subtable => list of columns)
        """
        blacklist = ['id', 'instance', 'description',
                     'instruction', 'error_string', 'source_url']
        blacklist_sub = ['id', 'parent_id']
        cols = {'': [col.name
                     for col in self.module_table.columns
                     if col.name not in blacklist]}
        for name, table in self.subtables.iteritems():
            cols[name] = [col.name
                          for col in table.columns
                          if col.name not in blacklist_sub]

        return cols

    def render(self):
        """
        Return a string with the rendered HTML module
        """
        module_html = ''
        if self.template is None:
            return '<p class="error">Rendering module %s failed because template was not loaded</p>' % self.instance_name
        if self.isUnauthorized():
            return '<p class="error">Access to Module %s is restricted, please log in with your certificate.</p>' % self.instance_name
        try:
            template_data = {
                'module': self,
                'data_stale': self.run['stale'],
                'run': self.run,
                'hf': hf
            }
            # make error string a bit more fancy
            #if self.error_string and ":" in self.error_string:
            #    self.error_string = re.sub(r"^([^:]+:)", "<strong>\\1</strong>", self.error_string)
            if self.dataset is None:
                template_data['no_data'] = True
                template_data['error_occured'] = True
            elif self.error_string:
                template_data.update(self.getTemplateData())
                template_data['no_data'] = False
                template_data['error_occured'] = True
            else:
                try:
                    template_data.update(self.getTemplateData())
                    template_data['no_data'] = False
                    template_data['error_occured'] = False
                except DatabaseError, e:
                    template_data['no_data'] = True
                    template_data['error_occured'] = True
                    self.error_string = "A database error occured. Probably the database schema needs to be updated!"
                    self.logger.error("Rendering failed: " + str(e))
                    self.logger.error(traceback.format_exc())
            module_html = self.template.render_unicode(**template_data)
        except Exception, e:
            module_html = "<p class='error' id='%s'>Final rendering of '%s' failed completely! Please refer to the log files</p>" % (self.instance_name, self.instance_name)
            self.logger.error("Rendering failed: " + str(e))
            self.logger.error(traceback.format_exc())
        return module_html
