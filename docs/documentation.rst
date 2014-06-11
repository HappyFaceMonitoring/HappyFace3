*************
Documentation
*************

The documentation you are currently reading is generated using `Sphinx <http://sphinx-doc.org/>`_, the standard Python documentation generator that is also used for the Python reference manual.

It works alot like documentation generators for other languages, like `Doxygen <http://doxygen.org>`_ for C++ or `JavaDoc <http://www.oracle.com/technetwork/java/javase/documentation/index-jsp-135444.html>`_ for Java, using a bunch of text files in the *docs/* directory, as well as formatted `docstrings <http://www.python.org/dev/peps/pep-0257/>`_ inside the HappyFace source code as a basis to generate documentation in different formats. By default, Sphinx can generate documentation as plain HTML and LaTeX, as well as more exoctic formats like HTML-help, qthelp and JSON objects. The markup-language used by Sphinx is an `extended <http://sphinx-doc.org/rest.html>`_ verison of `reStructuredText (reST). <http://docutils.sourceforge.net/rst.html>`_

.. note::

    This is **not** intended to be a Sphinx Tutorial! Only the common commands and guidelines to write and generate HappyFace documentation are presented. You are urged to read more about

Building HTML
=============

This is probably the most common option. Open your favourite shell and cd into the *docs/* directory. To generate the documentation, issue the following command

.. code-block:: bash

    make html
    
That’s it! You will now find the documentation in *docs/_build/html*.

.. note::

    Because HappyFace is written in Python 2, you have to use the Python 2 version of Sphinx. Luckily, at the time of writing, the default Python version in most Linux distribution is Python 2.7, so you don’t have to worry.
    
    If you use for example ArchLinux or a Gentoo with Python 3, you have to set the environment variable SPHINXBUILD to sphinx-build2 and call *make* with the *-e* flag.

Building LaTeX
==============

All information from the previous section applies here! With that in mind, just issue

.. code-block:: bash

    make latex

This will generate a bunch of files in *docs/_build/latex*, including a Makefile. To generate either a PostScript or PDF version of the documentation, call one of the following makes. Of course, you can also generate both, if you like.

.. code-block:: bash

    cd _build/latex
    make all-pdf
    make all-ps
    
Writing Documentation
=====================

The basic procedure to write documentation is adding or extending *\*.rst* files in the *docs/* directory and include them from *index.rst* or some other file.

Here are some tips

- Make use of cross references! They make it easier to understand the overall structure.

- Look at other documentation files from HappyFace!

- Look at Sphinx documentation from other projects! There is usually a link to show the code that generated the current page on each page.

- Make sure the Python code is correct! Sometimes you wonder why the generated docs are wrong, often the Python code contains some error. Check the make output carefuly.
    
API Documentation
-----------------

Generating documentation from the source code is very convenient, since you will have an always up-to-date documentation for source code without worrying about reflecting changes in the source to the docs.

The first is adding docstrings to classes and functions in the source code. Actually, this is optional, because Sphinx can also generate basic documentation for undocumented members, but this is of course of limited usefullness. These docstrings have to be formated in `Sphinx compatible reST. <http://sphinx-doc.org/rest.html>`_ You then have to add a *.rst* file in the *docs/* directory. For core documentation, the naming scheme is *core_MODULE.rst*. Don’t forget to mention the file in *core.rst* or *index.rst* as applicable, otherwise it is not included in the generated documentation!

The content of your new module reST file is fairly simple, since we to use `Autodoc Extension <http://sphinx-doc.org/ext/autodoc.html>`_ from Sphinx. For example, your file looks like

.. code-block:: rest

    ==================================
    mod:`hf.example` -- Example Module
    ==================================

    .. automodule:: hf.example
        :members:
        :undoc-members:

