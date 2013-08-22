.. _fileupload:

**************
File Uploading
**************

Sometimes HappyFace is unable to acquire some data because of access restrictions, for example if data is only available on an non-reachable VM inside a computing center. To get the data to HappyFace, the external machine can push the data using an upload mechanism. Technicaly, it is an authentication protected HTTP POST file upload.

Configuration
-------------
All upload related options are in the **[upload]** section if the HappyFace config. The default configuration is

.. code:: ini
    
    [upload]
    enabled = False
    directory = /tmp/hf_upload
    # HTTP Authentification method: digest or basic
    auth_method = digest
    realm = HappyFace Upload
    # path to passwd file
    htpasswd = 

It should be straightforward to enable the upload interface with that information. Please note that the *auth_method* option is currently ignored, since only *basic* is implemented.

You can deside whether you want to server target directory over an webserver or not, HappyFace will necessarily help you here, since it can be simply done in the webserver of you choice. If you want to serve it over the web with the help of HappyFace, upload somewhere beneath *static/* directory, which is served over the web in any case.

Basic Auth and .htpasswd
++++++++++++++++++++++++

Basic auth requires a file where the usernames and encrypted (hashed) passwords are stored. This is the default and at the moment only auth method.

The auth credentials are stored in a htpasswd-file, its location is specified by the *htpasswd* option. The file is typicaly hidden and therefore named *.htpasswd*. It **must not** be served over the web. Usernames and encrypted passwords are stored colon-separated, on entry per line. HappyFace will use the platforms crypt(3), so any hash you generate with crypt(3) on your system should work with HappyFace.

An example file for the user *user* and the password *password* would look like this

.. code::

    user:$1$OMMYPmcc$o5uV8vtA.iMlY8LWQqNOF/
    
Digest Auth
+++++++++++

Digest authentication uses a more complex challenge during initiation and can authenticate users safely over an unencrypted channel without sending plain-text passwords. Unfortunately, they don't work with the *.htpasswd* files and need their own files. This is not implemented yet!

Usage
-----
From an HTTP perspective, we have to send a form with a field named *file* that contains the file we want to upload. To do this manualy, you could copy this piece of HTML to a file and open it with your browser.

.. code:: html

    <html>
     <body>
      <h2>HappyFace file upload</h2>
       <form action="YOUR_HAPPYFACE_INSTANCE/upload" method="post" enctype="multipart/form-data">
        filename: <input type="file" name="file" /><br />
        <input type="submit" value="Upload" />
       </form>
     </body>
    </html>

Any realworld application would use some command line program to push the file. In this example, consider the *curl* program

.. code:: bash

    curl -F "file=@Path/To/File;filename=FilenameOn.Server" -u USERNAME:PASSWORD URL

Security Considerations
-----------------------
At the moment, only HTTP Basic Auth is supported, so the auth credentials can be obtained by eavesdropping. If an attacker gets hold on a valid auth, the harddrive can be filled. To prevent password leakage, use HTTPS to upload files and maybe enforce the usage of HTTPS with a webserver redirect. Also, a quota on the target folder is probably not a bad idea.

In future, digest auth will be available, making uploads potentialy secure even in HTTP. Another plan is to use the cert auth infrastracture, implicitly enforcing HTTPS.