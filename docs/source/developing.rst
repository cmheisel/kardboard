Developing kardboard
=====================

Using Vagrant
----------------
The way to develop on kardboard is via Vagrant_ , powered by the included Puppet files.

Default setup
~~~~~~~~~~~~~~~~~
.. code-block:: bash

    # Get the source, using your own fork most likely
    git clone git@github.com:cmheisel/kardboard.git

    cd kardboard
    vagrant up
    # ...wait...
    vagrant ssh
    touch kardboardve/src/kardboard/kardboard-local.cfg
    source kardboardve/bin/activate
    cd kardboardve/src/kardboard
    py.test kardboard


You now have a fully functional kardboard application running under production like environment.

* The application is served by gunicorn_ and nginx_ and is available at http://localhost:8080/ from your host machine. It runs at http://localhost:80/ on the guest.
* Memcache_ is running and used by the application
* Redis_ is running and used as the queue for your running celery_ process
* Both the application and celery_ processes are adminsitered through supervisord_
* You can restart both the application and the celery_ processes, say to pick up your changes, by doing the following:

.. code-block:: bash

    vagrant ssh
    sudo supervisorctl restart all

* Logs for the application, gunicorn_, nginx_ and celery_ are in /home/vagrant/logs/

Development server
~~~~~~~~~~~~~~~~~~

Testing against a production like environment is all well and good for you, like vegetables. But during development you'll likely want something tastier, like cookies, or a auto-reloading web server.

.. code-block:: bash

    vagrant ssh
    export KARDBOARD_SETTINGS=/vagrant/kardboard-local.cfg
    cd /home/vagrant/kardboardve/
    source bin/activate
    python src/kardboard/kardboard/runserver.py

The application is now available at http://localhost:5000/ from your host machine.



.. _Vagrant: http://www.vagrantup.com
.. _Puppet: http://puppetlabs.com
.. _celery: http://celeryproject.org
.. _nginx: http://nginx.org
.. _gunicorn: http://gunicorn.org
.. _supervisord: http://supervisord.org
.. _redis: http://redis.io
.. _memcache: http://memcached.org
