class memcache {
    package {'memcached':
        ensure => installed,
    }

    service {'memcached':
      ensure => running,
      enable => true,
      name => 'memcached',
      require => Package['memcached'],
    }
}