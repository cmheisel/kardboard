class nginx(
    $kbuser = 'kardboard',
    $vepath = 'kardboardve'
    ) {
    user { "www-data":
            shell   => "/bin/bash",
            groups  => ["www-data", "$kbuser"],
            ensure => present,
    }

    package { 'nginx':
      ensure => 'installed',
      require => [Service["supervisor"], User['www-data'],]
    }

    file { '/etc/nginx/sites-available/kardboard':
      ensure => file,
      owner => 'root',
      group => 'root',
      content => template('kardboard/nginx.conf.erb'),
      require => [Package['nginx'], ],
    }

    file { '/etc/nginx/sites-enabled/kardboard':
      ensure => link,
      target => '/etc/nginx/sites-available/kardboard',
      require => File['/etc/nginx/sites-available/kardboard'],
    }

    file { '/etc/nginx/sites-enabled/default':
      ensure => absent,
      require => Package['nginx'],
    }

    service { 'nginx':
      enable => true,
      ensure => running,
      subscribe => File['/etc/nginx/sites-available/kardboard'],
      require => File['/etc/nginx/sites-enabled/kardboard'],
    }
}