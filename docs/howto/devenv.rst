=========================
 Development environment
=========================

To track python dependencies and easily bootstrap development environment Buildout_ is used.

Buildout config :doc:`reference </ref/buildout>`


Buildout Usage
==============

Bootstrapping environment
-------------------------

.. code-block:: bash

    git clone git@github.com:gamemine/gamemine.git
    cd gamemine
    python bootstrap.py
    ./bin/buildout
    ./bin/django syncdb --migrate

Then create ``project/local_settings.py`` to override your local
settings (e.g. DATABASES), see ``project/local_settings.py.sample`` for example.


Shortcuts
---------

``./bin/django`` is equivalent of ``manage.py``

``./bin/runserver`` is equivalent of ``./bin/django runserver``

.. code-block:: bash

   ./bin/runserver

``./bin/shell`` is equivalent of ``./bin/django shell_plus``

.. code-block:: bash

   ./bin/shell

Deployment
==========

Capistrano_ tool is used for deployment.

When deploying to staging ``integration`` branch is used, on production
-- ``master``. So don't forget to merge your changes to ``integration``
or ``master`` branch before deploying.

Usage examples:

.. code-block:: bash

   cd ~/path-to-your-gamemine-project-root  # Go to Gamemine project root on your local machine
   cap production deploy  # Deploying to production server
   cap staging deploy  # Deploying to staging server
   cap staging deploy:migrate  # Run migrations on staging


:doc:`More about deployment </howto/deployment>`.


.. _buildout: http://pypi.python.org/pypi/zc.buildout/1.5.2
.. _Capistrano: https://github.com/capistrano/capistrano/wiki/2.x-Getting-Started
