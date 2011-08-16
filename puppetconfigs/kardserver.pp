# Set global package provider
Package { provider => 'aptitude' }

#################### Imports
import "helpers.pp"
import "classes/*"
include mongodb


################# Packages without dependencies

package { 'gcc':
  ensure => installed,
}

package { 'git-core':
  ensure => installed,
}

package {'python2.6':
  ensure => installed,
}

package {'curl':
  ensure => installed,
}

package {'python2.6-dev':
  ensure => installed,
}

package {'python-virtualenv':
  ensure => installed,
}

# needed by gunicorn
package {'libevent-1.4-2':
  ensure => installed,
}

# needed by gunicorn
package {'libevent-dev':
  ensure => installed,
}

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

exec { 'git-clone-kardboard':
  user => 'kardboard',
  path => '/usr/bin:/bin',
  command => 'cd /home/kardboard/kardboardve/src/; git clone git://github.com/kardboard/kardboard.git',
  unless => 'ls /home/kardboard/kardboardve/src/ | grep kardboard',
  require => [Exec['kardboardve'], File['/home/kardboard/kardboardve/src'], Package['git-core']],
}

exec { 'install-requirements':
  user => 'kardboard',
  path => '/home/kardboard/kardboardve/bin:/usr/bin:/bin',
  command => 'cd /home/kardboard/kardboardve/; source bin/activate; cd src/kardboard/; pip install -E /home/kardboard/kardboardve/ -r requirements.txt',
  unless => 'ls /home/kardboard/kardboardve/lib/python2.6/site-packages/ | grep gevent',
  logoutput => on_failure,
  require => [Package['gcc'], Package['python2.6-dev'], Package['python-virtualenv'], Exec['git-clone-kardboard'],]
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
  subscribe => [File['/etc/supervisor/conf.d/kardboard.conf'], File['/home/kardboard/kardboardve/etc/kardboard-prod.cfg'],],
  require => [Package["supervisor"], Exec['setup-develop'],]
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
  require => Package['nginx'],
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

file {'/home/kardboard/bin/backupmongo.sh':
  ensure => file,
  owner => 'kardboard',
  group => 'kardboard',
  mode => '755',
  source => '/root/kardconfig/sources/backupmongo.sh',
  require => [Service['mongodb'], File['/home/kardboard/bin'],],
}

cron { 'backupmongo':
  command => '/home/kardboard/bin/backupmongo.sh > /home/kardboard/logs/backupmongo.log 2>&1',
  user => 'kardboard',
  minute => '*/10',
  require => [Service['mongodb'], File['/home/kardboard/bin/backupmongo.sh'], File['/home/kardboard/logs']],
}

cron { 'logclear':
  command => 'rm -f /home/kardboard/logs/* 2>&1',
  user => 'root',
  hour => '0',
  minute => '0',
  weekday => '0',
  require => [File['/home/kardboard/logs'], ]
}