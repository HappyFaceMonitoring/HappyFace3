==============
Core Reference
==============

The HappyFace Core reference documents all classes and functions provided by HappyFace.

.. note::
    Hallo

.. module:: hf.module

.. autoclass:: ModuleBase
    :members:
        
    .. attribute:: module_table

    .. attribute:: subtables

    .. attribute:: module_name
        
    .. attribute:: instance
        
    .. attribute:: config
        
    .. attribute:: run
        
    .. attribute:: dataset
    
    .. attribute:: category
        
    .. attribute:: template

    .. attribute:: weigth

    .. attribute:: type
    
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
    

        
                
    
