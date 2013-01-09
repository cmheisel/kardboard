class pythondev {
    include pythondev::modules
    package { 'python2.6':
        ensure => installed,
    }
}