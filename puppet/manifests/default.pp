# Set global package provider
Package { provider => 'aptitude' }
import "logrotate"
include git
include devtools
include pythondev
include redis
include memcache

include mongodb
mongodb::setup { "kardboard": }
logrotate::rule { 'mongodb':
  path         => '/var/log/mongodb/*.log',
  rotate       => 2,
  rotate_every => 'day',
  postrotate   => 'killall -SIGUSR1 mongod',
}


import "kardboard"
class { 'kardboard':
# TODO
#    get runserver working
#    get celery working
#    integrate mongo backup script
#    get supervisor installed
    kbuser => 'vagrant',
    src => '/vagrant',
    conf => '/vagrant/kardboard-local.cfg',
    server => 'gunicorn',
}

# logrotate for kardboard
# install nginx to front kardboard