Developing kardboard
=====================

Quickstart
------------

To get a local version of kardboard up and running suitable for developing against, you can follow this quickstart guide.

.. code-block:: bash
    # Install python, virtualenv and mongodb using your favorite system package manager here.

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

    # Start the server
    python kardboard/runserver.py