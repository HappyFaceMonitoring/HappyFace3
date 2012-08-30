************
Installation
************

Please read :ref:`basics` before trying to install HappyFace, as it might save you from some headaches.

Dependencies
============
HappyFace currently requires the following Python dependencies (Debian package names)

* python (version >= 2.6)
* python-cherrypy3
* python-sqlalchemy (version >= 0.5)
* python-migrate (for *dbupdate*-tool)
* python-mako

The following are some optional packages

* python-sqlite
* python-psycopg2
* python-matplotlib
* python-lxml
* more database adaptors

Getting the Source
==================
The simplest way is to checkout the current source code from the HappyFace repository

.. code-block:: none

    $ svn co https://ekptrac.physik.uni-karlsruhe.de/public/HappyFace/branches/v3.0 HappyFace


At this point, there are no modules available, you have to get them separately from any source you like. For example, checkout the Karlsruhe modules

.. code-block:: none

    $ cd HappyFace
    $ svn co https://ekptrac.physik.uni-karlsruhe.de/public/HappyFaceModules/trunk modules

Basic Configuration
===================
(see `Email in Trac <https://ekptrac.physik.uni-karlsruhe.de/trac/HappyFace/wiki/Version_3_email>`_)

Running HappyFace in an Development Environment
===============================================
You should have a configured copy of HappyFace by now. Let the path to it be */path/to/HappyFace*.

(see `Email in Trac <https://ekptrac.physik.uni-karlsruhe.de/trac/HappyFace/wiki/Version_3_email>`_)

Setting up HappyFace with Apache2 and mod_wsgi
==============================================
You should have a configured copy of HappyFace by now and an installed an Apache web server. Let the path to it be */path/to/HappyFace* and let it belong to a user called *hfuser*. We want the HappyFace instance to be mounted at / of the URL path.

To run HappyFace with Apache, we advice you to use mod_wsgi, so make sure it is installed and enabled in your Apache server. See the Apache documentation if you need help with that.

You have to tell WSGI where the *render.py* script of HappyFace is located, as well as the URL where to mount it with the *WSGIScriptAlias* directive.

The Apache process needs to be restarted if the source code or configuration of HappyFace changed, otherwise changes take not effect. Because this usually requires root privileges, any user in the position to update HappyFace would also need root privileges. This is undesirable in most environments, so you should separate the Python process.

To do this, the *WSGIDaemonProcess* is used to spawn new processes in a process group. A single process group is usually okay for multiple HF instances. For every virtual host with a WSGIScriptAlias specification, you have to tell Apache to separate the processes with the *WSGIProcessGroup* directive.

The *WSGIScriptAlias* and *WSGIDaemonProcess* have many options that may be of use. Consult the `mod_wsgi documentation <http://code.google.com/p/modwsgi/wiki/ConfigurationDirective>`_ for a full overview of their options.

An example configuration looks something like this

.. code-block:: none

    <VirtualHost *:80>
            ServerAdmin admin@example.com
            ServerName happyface.example.com:80

            <Directory />
                    Order deny,allow
                    Deny from all
            </Directory>

            WSGIScriptAlias / /path/to/HappyFace/render.py

            ## OPTIONAL: have HappyFace run in a separate process belonging to the HappyFace user
            WSGIDaemonProcess happyface user=hfuser
            WSGIProcessGroup  happyface

    </VirtualHost>

Certificate Authorization with Apache2
======================================
HappyFace can be configured to restrict access on certain modules to a small group of users. These users can identify themselves with a client certificate. For this to work, both HappyFace as well as Apache2 need special configuration.

.. note:: Certificate authorization does **not** work with the development server.

Apache Configuration
^^^^^^^^^^^^^^^^^^^^
We have to tell Apache2 to use SSL and client certificates, first. We assume you already have SSL certificates for your server as-well as the root certificate of the users you want to accept.

.. code-block:: none

    NameVirtualHost *:443
    <VirtualHost *:443>
            ServerAdmin admin@example.com
            ServerName happyface.example.com:80

            SSLEngine On
            # Replace these paths with your own certificates
            SSLCertificateFile    /etc/apache2/server.crt
            SSLCertificateKeyFile /etc/apache2/server.key
            SSLCACertificateFile  /etc/apache2/gridka-root-cert.crt

            SSLOptions      StdEnvVars
            SSLVerifyClient Optional  # Optional or Required

    #       [...] Place usual HF config here
    </VirtualHost>


The *SSLOptions* tells Apache to pass the required SSL informations to HappyFace. The *SSLVerifyClient* directive switches on client verification. Two reasonable settings are *optional*, which allows users without certificate to use SSL to access the site, and *require*, which has broader browsers support.

HappyFace Configuration
^^^^^^^^^^^^^^^^^^^^^^^
.. todo:: [auth] section in HappyFace config and access option in module and category config. 