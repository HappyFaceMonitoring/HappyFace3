******************
Module Development
******************

Modules are the building blocks that give HappyFace its functionality. Specifically, they
 1) download and parse data to store it in a database
 2) retrieve data from a database and render it to HTML

These actions are represented by the :mod:`render.py` and :mod:`acquire.py` entry scripts. In order to do their work, they need to interact with the core of HappyFace and have to obey the rules for modules, otherwise the functionality of external tools and HappyFace itself can be disturbed.

Module Basics
=============
The module source code is located somewhere within the modules directory of the HappyFace setup, by default it is just the modules/ subdirectory. At startup, everything inside this directory and any subdirectory that looks like a python module is imported and module wide source code is executed.

In one of these files is the source code of our example module. The module itself is a class derived from :class:`hf.module.ModuleBase` that must implement a certain subset of methods, as well as specify a set of class-level variables describing configuration and database layout

Additionally, a HTML template file with the same name as the class is expected along with the file the class is in. This template contains the formatting information for the web output.

.. _database_layout:

Database Layout
---------------

Associated with each module is a so called module table in the database and an arbitrary number of subtables.

One entry is added to the module table every time :mod:`acquire.py` is called. By default, it contains the only a minimal set of columns, but can be extended with the :data:`table_columns` variable in the module definition. For the module developer, the following columns are of interest

 term status
    A numerical value. Its meaning is as follows
     * 0.66 <= status <= 1.0  The module is happy/normal operation
     * 0.33 <= status < 0.66  Neutral, there are things going wrong slightly.
     * 0.0  <= status < 0.33  Unhappy, something is very wrong with the monitored modules
     * status = -1            An error occured during module execution
     * status = -2            Data could not be retrieved (download failed etc.)

 next term source_url
    An URL to the data source, if applicable. At the moment only a single URL can be specified, this is to be regarded as a current limitation of HappyFace.
    
.. todo:: Draw graph with database relations


.. _mod-dev-subtable:

Subtable System
^^^^^^^^^^^^^^^
.. todo:: Describe subtable system

Example
-------
A minimalistic, working example of a Python module is presented here

.. code-block:: python

 # Module Definition
 import hf
 from sqlalchemy import *
 
 class Dummy(hf.module.ModuleBase):
     config_keys = {'test': ('A config variable that is directly passed into the database', '')}
     table_columns = [Column('test',  INT)], []
 
     def extractData(self):
         return {
             "status": '',
             "test": int(self.config['test'])
         }

.. code-block:: html

 ## HTML Template
 <%inherit file="/module_base.html" />
 
 <%def name="content()">
 <p>${dataset['test']}</p>
 </%def>

A detailed description of the module class variables and methods are found in the next section. The `Mako Templating Engine <http://http://www.makotemplates.org/>`_ is used for parsing the HTML template, please consult the Mako Documentation for more information about the syntax.

Module Class Reference
======================
The module class is derived from :class:`hf.module.ModuleBase` and the naming should be CamelCased. For the database table names, the CamelCase name is converted to camel_case.

Any class defiving from :class:`hf.module.ModuleBase` found in the modules directory somewhere is considered a HappyFace module. It is then checked if 

Special Class Variables
-----------------------
HappyFace makes use of class wide variables to define several aspects of the module.

.. data:: config_keys

    *required*

    A dictionary where the keys correspond to module specific keys in the configuration file and the value is a tuple of two strings. The first string is a description of the variable and the second one a string with the default value (e.g. empty string).

    This is used by the :mod:`hf.tools.modconfig` to generate empty configurations for a module.

.. data:: config_hint

    *optional*

    A plain string with general information about the configuration of the module. Used by :mod:`hf.tools.modconfig` where it is put at the top of the automatically generated configuration, if specified.

.. data:: table_columns

    *required*

    A tuple with two lists in it.
    1) A list of sqlalchemy Column objects. These columns are added to the module table and usually suffice for the module operation
    2) A list of strings, they are the names of columns in the module table that point to files in the archive directory.

.. data:: subtable_columns

    *optional*

    A dictionary where the key is the name of the subtable, e.g. *details*, and the values are tuples like :data:`table_colums`. They are the data columns for the subtable and the corresponding archive links. For more information about subtables, see :ref:`mod-dev-subtable`
    
    The subtable names are not passed to the database as they are, but are prepended with the module name to ensure uniqueness. Therefore, two modules can use the same subtable name without problems.

Class Methods
-------------
:class:`hf.module.ModuleBase` does provide several convenience functions that are used when the HTML weboutput is created, as well as default implementations for some optional actions the module can perform. The functions are called during different steps of the HappyFace acquire and render run and perform specific actions.

In total, the user must implement at least one method, :meth:`hf.module.ModuleBase.extractData`, to populate the database and optionally, a set of the following methods
* :meth:`hf.module.ModuleBase.prepareAcquisition`
* :meth:`hf.module.ModuleBase.fillSubtables`
* :meth:`hf.module.ModuleBase.getTemplateData`

Please refer to the linked documentation of :class:`hf.module.ModuleBase` and the :ref:`mod-dev-step-guide`. for implementation details 

HTML Templates, Generating Output
=================================

.. _mod-dev-step-guide:

Step-by-Step Guide
==================
