==========
 Buildout
==========

Installing eggs
===============

To install additional python packages update `eggs` section in `buildout.cfg`:

.. code-block:: bash

    eggs =
        psycopg2
        PIL
        reportlab
        django
        ipython
        ipdb
        ipdbplugin
        nose
        mocker
        django-nose
        django-debug-toolbar
        django-admin-tools
        django-sentry
        south
        gamemine


To add package from repository update `sources` section also:

.. code-block:: bash

    eggs =
        ...
        django-extensions

    [sources]
    django-extensions = git git://github.com/django-extensions/django-extensions.git





