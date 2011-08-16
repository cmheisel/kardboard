define add_user($email) {
    $username = $title

    user { $username:
            comment => "$email",
            home    => "/home/$username",
            shell   => "/bin/bash",
            groups  => 'admin',
            ensure => present,
            managehome => true,
    }


    file { "/home/$username/":
            ensure  => directory,
            owner   => $username,
            group   => $username,
            mode    => 750,
            require => [ User[$username], ]
    }

    file { "/home/$username/.ssh":
            ensure  => directory,
            owner   => $username,
            group   => $username,
            mode    => 700,
            require => File["/home/$username/"]
    }


    # now make sure that the ssh key authorized files is around
    file { "/home/$username/.ssh/authorized_keys":
            ensure  => present,
            owner   => $username,
            group   => $username,
            mode    => 600,
            require => File["/home/$username/"]
    }
}

define add_ssh_key($key, $type) {
    $username = $title

    ssh_authorized_key{ "${username}_${key}":
            ensure  => present,
            key     => $key,
            type    => $type,
            user    => $username,
    }

}