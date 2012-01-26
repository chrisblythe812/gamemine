=====================
 Management commands
=====================

Usage
=====

.. code-block:: bash

    ./bin/django <command> [options]

``command`` should be one of the commands listed in this document.
``options``, which is optional, should be zero or more of the options available
for the given command.


Available commands
==================

bulkmail
--------

.. code-block:: bash

    ./bin/django bulkmail

Sends mail in bulk.


cart
----

.. code-block:: bash

    ./bin/django cart <label>

Working with cart.

`Labels:`

**purge**

Purges expired users' ``BuyCarts``.

**update_shipped_statuses**

Updates shipment status from Endicia DB.

**update_order_items**

Allocates inventory for buy orders.

.. **fix_buy_orders**

.. Unknown

.. **load_inventory**

.. Unknown


rent
----

.. code-block:: bash

    ./bin/django rent <label>

Working with rent plans.

`Labels:`

**purge**

Sets ``MemberRentalPlan`` status to ``expired`` if expired.
Clears unconfirmed ``MemberRentalPlan``'s cancellations.
Purges ``RentLists`` without users.

**process_matrix**

Allocates inventory for buy orders (runs ``cart update_order_items``).
Cancels dead plans.
Cancels expired plans.
Creates ``RentOrder`` instances.

**process_cancellations**

Processes expired and canceled plans. Applies penalty payments.

**recurring_billing**

Makes recurring billing for each member.

**delinquent_billing**

Makes delinquent billing for each member.

**move_orders**

Updates ``RentItem.source_dc`` depending on ``Item`` presence DC.

**charge_held**

Charges on hold accounts.

**reactivate_held**

Makes all ``OnHold`` ``MemberRentalPlans`` ``Active`` (WTF?!).

**update_shipped_statuses**

Fetches shipment statuses from Endicia.

.. **test**

.. Unknown

.. **weight_matrix**

.. Unknown

.. **allocate_inventory_for_buy_orders**

.. Unknown

.. **fix**

.. Unknown

.. **send_empty_list_nofitications**

.. Unknown

.. **fix_rent_orders**

.. Unknown

.. **armageddon**

.. Unknown

.. **superfix**

.. Unknown

.. **cleanup_picked_list**

.. Unknown

.. **fml**

.. Unknown

.. **fix_refund**

.. Unknown

.. **fix_2x_speed**

.. Unknown

.. **fix_2x_speed2**

.. Unknown

claims
------

.. code-block:: bash

    ./bin/django claim <label>

`Labels:`

**take_penalty_paymentns**

Takes penalty payments for ``GameIsDamagedClaim`` and ``WrongGameClaim``.


muze
----

.. code-block:: bash

    ./bin/django muze <label>

`Labels:`

**update**

Downloads "inc_illustrated_latest_xml.zip" from Muze server.

**update-media**

Downloads videos, images, makes thumbs.


catalog
-------

.. code-block:: bash

    ./bin/django catalog <label>

`Labels:`

**fix_counters**

Recalculates ``Inventory.pre_owned``, ``DistributorItem.pre_owned``,
``Item.pre_owned``, ``Item.top_rental``, ``Item.hot_trade``,
``Item.sold_amount``, ``Item.rent_amount``, ``Item.trade_amount``.

**update_rent_status**

Recalculates ``Item.rent_status``.

**update_caches**

Updates ``Item.tag_list``, ``Item.genre_list``.


endicia
-------

.. code-block:: bash

    ./bin/django endicia <label>

`Labels:`

**recredit**

Credits endicia account if current balance <= $100.


ingram
------

.. code-block:: bash

    ./bin/django ingram


Downloads data from Ingram server. Updates ``Item`` attributes (price,
etc.)


ingramdb
--------

.. code-block:: bash

    ./bin/django ingramdb <label>

`Labels:`

**update**

Updates Ingram database.


send_newsletter
---------------

.. code-block:: bash

    ./bin/django send_newsletter


Sends newsletters to users.


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
