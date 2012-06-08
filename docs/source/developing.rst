Developing kardboard
=====================

Quickstart
------------

To get a local version of kardboard up and running suitable for developing against, you can follow this quickstart guide.

.. code-block:: bash


    # Install python, virtualenv and mongodb using your favorite system package manager here.
    # aptitude install gcc python2.6 python2.6-dev python-virtualenv redis-server mongodb
    # These may differ on your local environment. In particular, a different python version
    # may be present locally. Use of the python and python-dev metapackages on debian is encouraged.
    # If using OSX, you should at least install mongo and redis. We recommend using Homebrew_.
.. _Homebrew: https://github.com/mxcl/homebrew
    # brew install mongodb redis

    # Get the source, using your own fork most likely
    git clone git@github.com:cmheisel/kardboard.git

    # Make a virtualenv
    cd kardboard
    virtualenv .kve

    # Turn it on
    source ./.kve/bin/activate

    # Install the requirements
    pip install -r requirements.txt

    # Start mongo and drop it into the background
    mkdir var
    mongod --fork --logpath=./var/mongo.log --dbpath=./var/

    # Start redis (only if you're running celery)
    redis-server /usr/local/etc/redis.conf

    # Ensure the module is on sys.path
    # Failed to import module kardboard errors occur otherwise.
    python setup.py develop

    # Start the celery process
    python kardboard/manage.py celeryd -B

    # Start the server
    python kardboard/runserver.py
