# = Class: kardboard
#
# Installs the kardboard application and necessary dependencies.
#
# == Parameters:
#
# $kbuser:: The user whom kardboard will be installed as. Defaults to +kardboard+
# $vepath:: The folder name for the virtualenv where the app is installed. Defaults to +kardboardve+

class kardboard($kbuser = 'kardboard', $vepath = 'kardboardve', $src = 'git') {
    import "filesystem"
    import "user"

    class { 'user':
        username => $kbuser,
    }
    class { 'filesystem':
        username => $kbuser,
        vepath => $vepath,
    }


    if $src != 'git' {
        # Must have passed a path to symlink
        exec { 'kardboard-src':
          user => $kbuser,
          path => '/usr/bin:/bin',
          cwd => "/home/$kbuser/$vepath/src/",
          command => "ln -s $src ./kardboard",
          unless => "ls /home/$kbuser/$vepath/src/ | grep kardboard",
          require => [Exec['kardboardve'], File["/home/$kbuser/$vepath/src/"],],
        }
    }
    else {
        fail("Haven't written puppet code to clone src from git yet")
    }

    exec { 'install-requirements':
      user => $kbuser,
      path => "/home/$kbuser/$vepath/bin:/usr/bin:/bin",
      cwd => "/home/$kbuser/$vepath/",
      command => "/home/$kbuser/$vepath/bin/pip install -r src/kardboard/requirements.txt",
      unless => "ls /home/$kbuser/$vepath/lib/python2.6/site-packages/ | grep unittest2",
      logoutput => on_failure,
      require => [Package['gcc'], Package['python2.6-dev'], Package['python-virtualenv'], Exec['kardboard-src'],]
    }

    # Needs runinvenv
    exec { 'setup-develop':
      user => $kbuser,
      path => "/home/$kbuser/$vepath/bin:/usr/bin:/bin",
      cwd => "/home/$kbuser/$vepath/src/kardboard/",
      command => "runinenv /home/$kbuser/$vepath python setup.py develop",
      unless => "ls /home/kardboard/$kbuser/lib/python2.6/site-packages/ | grep kardboard",
      require => [Exec['install-requirements'], File['/bin/runinenv'],],
    }

}