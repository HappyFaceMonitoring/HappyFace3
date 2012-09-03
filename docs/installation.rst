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

Configuration
=============
Since the configuration in HappyFace is rather flexible, the :ref:`next chapter <config_maintenance>` is devoted to the configuration of HappyFace.

For testing purposes, you can download an `example configuration <http://www-ekp.physik.uni-karlsruhe.de/~sroecker/files/hf3_config.tar.gz>`_ and extract it into a subdirectory called config/ in the HappyFace directory.

Running HappyFace in an Development Environment
===============================================
You should have a configured copy of HappyFace by now. Let the path to it be */path/to/HappyFace*.

You can now manually run

.. code-block:: bash

    python acquire.py

to populate the database. By running

.. code-block:: bash
    
    python render.py

you start a local webserver, by default listening to port 8080, so you can access your instance at `<http://localhost:8080/>`_. If you change the Python source files, the server process automatically reloads itself, so you can keep it running in a separate shell all the time.

.. note:: If you make syntax errors while programming, the server shuts down completely and you need to manually restart it.

The development server can, if properly configured be used to drive the site, too, since CherryPy claims the server to be powerful and reliable enough. But we advice to use Apache in a production environment, because it has better SSL support. Particularily, SSL certificate authorization is **not** possible with the built-in server.

.. _hf-apache-wsgi:

Setting up HappyFace with Apache2 and mod_wsgi
==============================================
You should have a configured copy of HappyFace by now and an installed an Apache web server. Let the path to it be */path/to/HappyFace* and let it belong to a user called *hfuser*. We want the HappyFace instance to be mounted at / of the URL path.

To run HappyFace with Apache, we advice you to use mod_wsgi, so make sure it is installed and enabled in your Apache server. See the Apache documentation if you need help with that.

You have to tell WSGI where the *render.py* script of HappyFace is located, as well as the URL where to mount it with the *WSGIScriptAlias* directive.

The Apache process needs to be restarted if the source code or configuration of HappyFace changed, otherwise changes take not effect. Because this usually requires root privileges, any user in the position to update HappyFace would also need root privileges. This is undesirable in most environments, so you should separate the Python process.

To do this, the *WSGIDaemonProcess* is used to spawn new processes in a process group. A single process group is usually okay for multiple HF instances. For every virtual host with a WSGIScriptAlias specification, you have to tell Apache to separate the processes with the *WSGIProcessGroup* directive.

The *WSGIScriptAlias* and *WSGIDaemonProcess* have many options that may be of use. Consult the `mod_wsgi documentation <http://code.google.com/p/modwsgi/wiki/ConfigurationDirective>`_ for a full overview of their options.

An example configuration looks something like this

.. code-block:: apache

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

The Apache configuration for HappyFace needs to be duplicated for both the plain text HTTP as well as encrypted HTTPS configuration. To avoid code duplication, you should put the configuration inside the *VirtualHost* blocks into a separate file that is included with the *Include* statement.

.. _apache_cert:

Apache Configuration
^^^^^^^^^^^^^^^^^^^^
We have to tell Apache2 to use SSL and client certificates, first. We assume you already have SSL certificates for your server as-well as the root certificate of the users you want to accept.

The root certificate(s) is/are the first line of authentification, the client certificate must match the given root certificates, otherwise access is automatically forbidden.

.. code-block:: apache

    NameVirtualHost *:443
    <VirtualHost *:443>
            ServerAdmin admin@example.com
            ServerName happyface.example.com:80

            SSLEngine On
            # Replace these paths with your own certificates
            SSLCertificateFile    /etc/apache2/server.crt
            SSLCertificateKeyFile /etc/apache2/server.key
            SSLCACertificateFile  /etc/apache2/gridka-root-cert.crt # alt.: SSLCACertificateDirectory

            SSLOptions      StdEnvVars
            SSLVerifyClient Optional  # Optional or Required

    #       [...] Place usual HF config here
    </VirtualHost>


The *SSLOptions* tells Apache to pass the required SSL informations to HappyFace. The *SSLVerifyClient* directive switches on client verification. Two reasonable settings are *optional*, which allows users without certificate to use SSL to access the site, and *require*, which has broader browsers support.

HappyFace Configuration
^^^^^^^^^^^^^^^^^^^^^^^
Apache now asks a client to show a certificate and checks if it is valid. We need to tell HappyFace which distinguished names (DN) are valid and to which categories and modules the access is restricted.

Because we only cover installation, deployment and Apache configuration in this chapter, we ask you to refer to :ref:`config_certs` for detailed information.