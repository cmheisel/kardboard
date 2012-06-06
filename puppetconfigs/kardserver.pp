# Set global package provider
Package { provider => 'aptitude' }

#################### Imports
import "helpers.pp"
import "classes/*"
include mongodb


################# Packages without dependencies
file { '/etc/apt/sources.list':
  ensure => file,
  owner => 'root',
  group => 'root',
  source => '/root/kardconfig/sources/prod-sources.list',
}

exec {'aptitude-update':
    user => 'root',
    path => '/usr/bin:/bin',
    command => 'aptitude update',
    logoutput => on_failure,
    require => File['/etc/apt/sources.list'],
}

package {'apache2':
  ensure => absent,
}

service {'apache2':
  ensure => stopped,
  enable => false,
  name => 'apache2',
  require => Package['apache2'],
}

package { 'gcc':
  ensure => installed,
  require => Exec['aptitude-update'],
}

package { 'git-core':
  ensure => installed,
  require => Exec['aptitude-update'],
}

package {'python2.6':
  ensure => installed,
  require => Exec['aptitude-update'],
}

package {'curl':
  ensure => installed,
  require => Exec['aptitude-update'],
}

package {'python2.6-dev':
  ensure => installed,
  require => Exec['aptitude-update'],
}

package {'python-setuptools':
    ensure => installed,
    require => Exec['aptitude-update'],
}

package {'python-virtualenv':
  ensure => installed,
  require => Package['python-setuptools'],
}

# needed by gunicorn
package {'libevent-1.4-2':
  ensure => installed,
  require => Exec['aptitude-update'],
}

# needed by gunicorn
package {'libevent-dev':
  ensure => installed,
  require => Exec['aptitude-update'],
}

# Used for storing queue messages in
package {'redis-server':
  ensure => installed,
  provider => dpkg,
  source => "/root/kardconfig/sources/redis-server_2.2.11-3_amd64.deb"
}

service {'redis-server':
  ensure => running,
  enable => true,
  name => 'redis-server',
  require => Package['redis-server'],
}

# Used for cache
package {'memcached':
    ensure => installed,
}

service {'memcached':
  ensure => running,
  enable => true,
  name => 'memcached',
  require => Package['memcached'],
}

file {'/bin/runinenv':
  ensure => file,
  owner => 'root',
  group => 'root',
  mode => 755,
  source => '/root/kardconfig/sources/runinenv.sh'
}

######################## Set up user
add_user { "kardboard":
  email => "YOUREMAIL@YOURDOMAIN.COM",
}

add_ssh_key { "kardboard":
  key => "YOURKEYHERE",
  type => "ssh-dss"
}

file { "/etc/sudoers":
    owner => root,
    group => root,
    mode => 440,
    source => "/root/kardconfig/sources/sudoers",
    require => User['kardboard'],
}

################################ Mongodb
mongodb::setup { "kardboard": }


################################## Install kardboard
file { '/home/kardboard/logs':
  ensure => directory,
  owner => 'kardboard',
  group => 'kardboard',
  require => [User['kardboard'], ],
}

file { '/home/kardboard/kardboardve':
  ensure => directory,
  owner => 'kardboard',
  group => 'kardboard',
  recurse => true,
  require => [User['kardboard'], Service['mongodb'], Service['memcached'],]
}

file { '/home/kardboard/kardboardve/src':
  ensure => directory,
  owner => 'kardboard',
  group => 'kardboard',
  require => File['/home/kardboard/kardboardve'],
}

file { '/home/kardboard/kardboardve/etc':
  ensure => directory,
  owner => 'kardboard',
  group => 'kardboard',
  require => File['/home/kardboard/kardboardve'],
}

file { '/home/kardboard/kardboardve/etc/kardboard-prod.cfg':
  ensure => file,
  owner => 'kardboard',
  group => 'kardboard',
  source => '/root/kardconfig/sources/kardboard-prod.cfg',
  require => File['/home/kardboard/kardboardve/etc'],
}

file { '/home/kardboard/kardboardve/etc/newrelic.ini':
  ensure => file,
  owner => 'kardboard',
  group => 'kardboard',
  source => '/root/kardconfig/sources/newrelic.ini',
  require => File['/home/kardboard/kardboardve/etc'],
}

file {'/home/kardboard/kardboardve/etc/gunicorn.py':
  ensure => file,
  owner => 'kardboard',
  group => 'kardboard',
  source => '/root/kardconfig/sources/gunicorn.py',
  require => File['/home/kardboard/kardboardve/etc'],
}

exec { 'kardboardve':
  user => 'kardboard',
  path => '/usr/bin:/bin',
  command => 'cd /home/kardboard/kardboardve/; virtualenv --no-site-packages .',
  unless => ['ls /home/kardboard/kardboardve | grep bin', ],
  logoutput => on_failure,
  require => [File['/home/kardboard/kardboardve'], Package['python-virtualenv'],],
}

file { '/home/kardboard/kardboardve/lib/python2.6/site-packages/':
  ensure => directory,
  owner => 'kardboard',
  group => 'kardboard',
  require => File['/home/kardboard/kardboardve'],
}

file { '/home/kardboard/kardboardve/lib/python2.6/site-packages/measuredapp.py':
  ensure => file,
  owner => 'kardboard',
  group => 'kardboard',
  source => '/root/kardconfig/sources/measuredapp.py',
  require => [File['/home/kardboard/kardboardve/lib/python2.6/site-packages/'], Exec['kardboardve']],
}

exec { 'git-clone-kardboard':
  user => 'kardboard',
  path => '/usr/bin:/bin',
  command => 'cd /home/kardboard/kardboardve/src/; git clone git://github.com/cmheisel/kardboard.git',
  unless => 'ls /home/kardboard/kardboardve/src/ | grep kardboard',
  require => [Exec['kardboardve'], File['/home/kardboard/kardboardve/src'], Package['git-core'],],
}

exec { 'install-requirements':
  user => 'kardboard',
  path => '/home/kardboard/kardboardve/bin:/usr/bin:/bin',
  command => 'cd /home/kardboard/kardboardve/; source bin/activate; cd src/kardboard/; pip install -r requirements.txt',
  unless => 'ls /home/kardboard/kardboardve/lib/python2.6/site-packages/ | grep redis',
  logoutput => on_failure,
  require => [Package['gcc'], Package['python2.6-dev'], Package['python-virtualenv'], Exec['git-clone-kardboard'],]
}

exec { 'install-newrelic':
  user => 'kardboard',
  path => '/home/kardboard/kardboardve/bin:/usr/bin:/bin',
  command => 'cd /home/kardboard/kardboardve/; source bin/activate; cd src/kardboard/; pip install newrelic==1.2.1.265',
  unless => 'ls /home/kardboard/kardboardve/lib/python2.6/site-packages/ | grep newrelic-1.2.1.265',
  logoutput => on_failure,
  require => [Package['gcc'], Package['python2.6-dev'], Package['python-virtualenv'], Exec['install-requirements']]
}

exec { 'setup-develop':
  user => 'kardboard',
  path => '/home/kardboard/kardboardve/bin:/usr/bin:/bin',
  command => 'cd /home/kardboard/kardboardve/; source bin/activate; cd src/kardboard/; python setup.py develop',
  unless => 'ls /home/kardboard/kardboardve/lib/python2.6/site-packages/ | grep kardboard',
  require => Exec['install-requirements'],
}

############################### Supervisor
package { 'supervisor':
  ensure => installed,
  require => Exec['aptitude-update'],
}

file {'/etc/supervisor/conf.d/kardboard.conf':
  ensure => file,
  owner => 'root',
  group => 'root',
  source => '/root/kardconfig/sources/kardboard-supervisord.conf',
  require => Package['supervisor'],
}

service { 'supervisor':
  enable => true,
  ensure => running,
  subscribe => [File['/etc/supervisor/conf.d/kardboard.conf'], ],
  require => [Package["supervisor"], Exec['setup-develop'],],
  hasrestart => false,
  hasstatus => false,
}

################################ Nginx
user { "www-data":
        shell   => "/bin/bash",
        groups  => ["www-data", 'kardboard'],
        ensure => present,
        require => Group['kardboard'],
}

group { 'kardboard':
  ensure => present,
  require => User['kardboard'],
}

package { 'nginx':
  ensure => 'installed',
  require => [Service["supervisor"], User['www-data'],]
}

file { '/etc/nginx/sites-available/yourdomain.com':
  ensure => file,
  owner => 'root',
  group => 'root',
  source => '/root/kardconfig/sources/nginx.conf',
  require => [Package['nginx'], ],
}

file { '/etc/nginx/sites-enabled/yourdomain.com':
  ensure => link,
  target => '/etc/nginx/sites-available/yourdomain.com',
  require => File['/etc/nginx/sites-available/yourdomain.com'],
}

service { 'nginx':
  enable => true,
  ensure => running,
  subscribe => File['/etc/nginx/sites-available/yourdomain.com'],
  require => File['/etc/nginx/sites-enabled/yourdomain.com'],
}



############################### Cron jobs
file { '/home/kardboard/bin':
  ensure => directory,
  owner => 'kardboard',
  group => 'kardboard',
  require => User['kardboard'],
}

file { '/home/kardboard/.bash_profile':
  ensure => file,
  owner => 'kardboard',
  group => 'kardboard',
  mode => '655',
  source => '/root/kardconfig/sources/bash_profile.sh',
  require => User['kardboard'],
}

file {'/home/kardboard/bin/backupmongo.sh':
  ensure => file,
  owner => 'kardboard',
  group => 'kardboard',
  mode => '755',
  source => '/root/kardconfig/sources/backupmongo.sh',
  require => [Service['mongodb'], File['/home/kardboard/bin'],],
}

file {'/root/mongologrotate.sh':
  ensure => file,
  owner => 'root',
  group => 'root',
  mode => '755',
  source => '/root/kardconfig/sources/mongologrotate.sh',
  require => Service['mongodb'],
}

cron { 'backupmongo':
  command => '/home/kardboard/bin/backupmongo.sh > /home/kardboard/logs/backupmongo.log 2>&1',
  user => 'kardboard',
  minute => '*/10',
  require => [Service['mongodb'], File['/home/kardboard/bin/backupmongo.sh'], File['/home/kardboard/logs']],
}

cron { 'mongologrotate':
  command => '/root/mongologrotate.sh > /home/kardboard/logs/mongologrotate.log 2>&1',
  user => 'root',
  hour => '0',
  minute => '0',
  require => [ Service['mongodb'], File['/root/mongologrotate.sh'] ],
}

cron { 'logclear':
  command => 'rm -f /home/kardboard/logs/* 2>&1',
  user => 'root',
  hour => '0',
  minute => '0',
  weekday => '0',
  require => [File['/home/kardboard/logs'], ]
}

cron { 'mongologclear':
  command => 'rm -f /var/log/mongodb/*.log.* 2>&1',
  user => 'root',
  hour => '0',
  minute => '0',
  weekday => '0',
  require => [File['/home/kardboard/logs'], ]
}