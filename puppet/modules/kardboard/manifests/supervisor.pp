class supervisor(
    $conf,
    $server,
    $kbuser,
    $vepath) {

    package { 'supervisor':
      ensure => installed,
    }

    file {'/etc/supervisor/conf.d/kardboard.conf':
      ensure => file,
      owner => 'root',
      group => 'root',
      content => template("kardboard/kardboard-supervisord.conf.erb"),
      require => Package['supervisor'],
      notify => Service['supervisor'],
    }

    service { 'supervisor':
      enable => true,
      ensure => running,
      require => [Package["supervisor"], Exec['setup-develop'], Exec['install-requirements'], File['/bin/runinenv']],
      hasrestart => false,
      hasstatus => false,
      provider => init,
    }
}