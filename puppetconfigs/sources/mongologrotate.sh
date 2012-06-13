#!/bin/bash

# See http://www.mongodb.org/display/DOCS/Logging
supervisorctl stop all
killall -SIGUSR1 mongod
supervisorctl start all