class pythondev::modules {
    package { [ 'python2.6-dev', 'python-virtualenv', ]:
        ensure => 'installed',
    }

    file {'/bin/runinenv':
        ensure => file,
        owner => 'root',
        group => 'root',
        mode => 755,
        source => 'puppet:///modules/pythondev/runinenv',
    }
}