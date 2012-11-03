class pythondev::modules {
  package { [ 'python2.6-dev', 'python-virtualenv', ]:
    ensure => 'installed',
  }
}