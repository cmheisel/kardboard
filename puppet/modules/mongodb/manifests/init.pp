class mongodb {
    exec { "apt-update":
        command => "/usr/bin/aptitude update",
        unless => "/usr/bin/which add-apt-repository",
    }

    package { "python-software-properties":
        ensure => installed,
        require => Exec['apt-update'],
    }

    exec { "10gen-apt-repo":
        path => "/bin:/usr/bin",
        command => "add-apt-repository 'deb http://downloads-distro.mongodb.org/repo/ubuntu-upstart dist 10gen'",
        unless => "cat /etc/apt/sources.list | grep 10gen",
        require => Package["python-software-properties"],
    }

    exec { "10gen-apt-key":
        path => "/bin:/usr/bin",
        command => "apt-key adv --keyserver keyserver.ubuntu.com --recv 7F0CEB10",
        unless => "apt-key list | grep 10gen",
        require => Exec["10gen-apt-repo"],
    }

    exec { "update-apt":
        path => "/bin:/usr/bin",
        command => "apt-get update",
        unless => "ls /usr/bin | grep mongo",
        require => Exec["10gen-apt-key"],
    }

    package { "mongodb-10gen":
        ensure => installed,
        require => Exec["update-apt"],
    }

    service { "mongodb":
        enable => true,
        ensure => running,
        subscribe => File['/etc/mongodb.conf'],
        require => Package["mongodb-10gen"],
    }

    file { '/etc/mongodb.conf':
      ensure => file,
      owner => 'root',
      group => 'root',
      source => 'puppet:///modules/mongodb/mongodb.conf',
      notify => Service['mongodb'],
      require => Package['mongodb-10gen'],
    }


    define setup {
        file { "/etc/init/mongodb.conf":
            content => template("mongodb/mongodb.init.conf.erb"),
            mode => "0644",
            notify => Service["mongodb"],
            require => Package["mongodb-10gen"],
        }
    }
}