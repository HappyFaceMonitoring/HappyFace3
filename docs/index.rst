.. HappyFace documentation master file, created by
   sphinx-quickstart on Fri Aug 24 13:48:45 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

=========================================
HappyFace – The Meta Monitoring Framework
=========================================


* Powerful site specific monitoring system for data from multiple input sources.
* Collects, processes, rates and presents all important monitoring information
* for the overall status and the services of a local or Grid computing site. 

* Monitoring data is subdivided in multiple categories.
* Each category is subdivided in multiple modules which corresponds to one single test.
* Simple rating system: -1 = no info / error; status float value = 0.0 .. 1.0 (critical .. fine)
* The overall status of the categories can be calculated from the individual module statii with different algorithms. 

Contents
========
.. toctree::
   :maxdepth: 2

   installation.rst
   module_dev.rst
   api.rst
   core.rst
   
Documentation Todos
===================

.. todolist::

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
