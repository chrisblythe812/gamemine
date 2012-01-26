===================
 Deploying project
===================

Capistrano_ tool is used for deployment.

When deploying to staging ``integration`` branch is used, on production
-- ``master``. So don't forget to merge your changes to ``integration``
or ``master`` branch before deploying.


Bootstrapping production/staging server
=========================================

.. code-block:: bash

    apt-get install git-core python-dev libpq-dev zlib1g-dev libfreetype6-dev libjpeg62-dev libpng12-dev libmemcached-dev
    mkdir /var/www/gamemine
    mkdir /var/www/gamemine/releases


On your dev environment you will need to install ruby and rubygems, then

.. code-block:: bash

    sudo gem install capistrano
    git clone git@github.com:gamemine/gamemine.git
    cd gamemine
    # For production
    cap production deploy:migrations
    # For staging
    cap staging deploy:migrations

On server you may create
``/var/www/gamemine/shared/local_settings.py`` if needed to override
some settings, see ``project/local_settings.py.sample`` for example.
Then

.. code-block:: bash

    cp -R /var/www/gamemine/lib/melissa/linux /usr/local/lib/melissa
    echo /usr/local/lib/melissa > /etc/ld.so.conf.d/melissa.conf
    ldconfig


Sample apache config
====================

.. code-block:: bash

    <VirtualHost *:80>
        ServerName test.gamemine.com
        DocumentRoot /var/www/gamemine/current
        ErrorLog /var/www/gamemine/shared/error.log
        Alias /m/media/ /var/www/gamemine/shared/media/
        Alias /m/ /var/www/gamemine/current/project/site_media/static/
         
        WSGIDaemonProcess gamemine maximum-requests=1000
        WSGIProcessGroup gamemine
        WSGIScriptAlias / /var/www/gamemine/current/bin/django.wsgi process-group=gamemine
     
    </VirtualHost>


Sample production crontab
=========================

.. code-block:: bash

    */5 * * * * /var/www/gamemine/current/bin/django cart purge
    #####*/5 * * * * /var/www/gamemine/current/bin/django cart update_order_items
     
    */5 * * * * /var/www/gamemine/current/bin/django rent purge
    */1 * * * * /var/www/gamemine/current/bin/django send_mail
    0,20,40 * * * * /var/www/gamemine/current/bin/django retry_deferred
    */1 * * * * /var/www/gamemine/current/bin/django rent process_matrix
    */1 * * * * /var/www/gamemine/current/bin/django rent process_cancellations
     
    0 3,7,11,15,19 * * * /var/www/gamemine/current/bin/django rent recurring_billing
    0 4,8,12,16,20 * * * /var/www/gamemine/current/bin/django rent delinquent_billing
    0 22 * * * /var/www/gamemine/current/bin/django rent move_orders
    ######0 2 * * * /var/www/gamemine/current/bin/django rent send_empty_list_nofitications
    30 3,7,11,15,19 * * * /var/www/gamemine/current/bin/django claims take_penalty_paymentns
    30 4,8,12,16,20 * * * /var/www/gamemine/current/bin/django rent charge_held
    45 * * * * /var/www/gamemine/current/bin/django rent reactivate_held
     
    0  3,7,11,15,19 * * * /var/www/gamemine/current/bin/django rent update_shipped_statuses
    30 4,8,12,16,20 * * * /var/www/gamemine/current/bin/django cart update_shipped_statuses
     
    #####0 0 * * * /var/www/gamemine/current/bin/django trade notify_cancelled_expired
    0 0 * * * /var/www/gamemine/current/bin/django muze update
    0 1 * * * /var/www/gamemine/current/bin/django muze update-media
     
    5,15,25,35,45,55 * * * * /var/www/gamemine/current/bin/django catalog fix_counters
    0,10,20,30,40,50 * * * * /var/www/gamemine/current/bin/django catalog update_rent_status
    0 0 * * */1 /var/www/gamemine/current/bin/django catalog update_caches
     
    30 */1 * * * /var/www/gamemine/current/bin/django endicia recredit
    13 */2 * * * /var/www/gamemine/current/bin/django ingram
     
    0 0 * * sat /var/www/gamemine/current/bin/django ingramdb update
    0 * * * * /var/www/gamemine/current/bin/django send_newsletter


.. _Capistrano: https://github.com/capistrano/capistrano/wiki/2.x-Getting-Started
