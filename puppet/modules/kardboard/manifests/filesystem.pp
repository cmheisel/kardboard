class kardboard::filesystem($username, $vepath) {
    file { "/home/$username/$vepath":
        ensure => directory,
        owner => $username,
        group => $username,
        recurse => false,
        require => [File["/home/$username/"], ]
    }

    file { "/home/$username/$vepath/src":
      ensure => directory,
      owner => $username,
      group => $username,
      require => File["/home/$username/$vepath"],
    }

    exec { 'kardboardve':
      user => $username,
      path => '/usr/bin:/bin',
      cwd => "/home/$username/$vepath",
      command => "virtualenv --no-site-packages .",
      unless => ['ls /home/$username/$vepath | grep bin', ],
      logoutput => on_failure,
      require => [File["/home/$username/$vepath"], Package['python-virtualenv'],],
    }

}
