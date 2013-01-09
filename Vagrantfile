# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant::Config.run do |config|
  # Setup the box
  config.vm.box = "lucid64"
  config.vm.box_url = "http://files.vagrantup.com/lucid64.box"

  config.vm.network :hostonly, "33.33.33.33"
  # Forward host port 4000 to guest port 4000
  config.vm.forward_port 4000, 4000
  config.vm.forward_port 80, 8080

  config.vm.provision :puppet do |puppet|
    puppet.manifests_path = "puppet/manifests"
    puppet.manifest_file = "default.pp"
    puppet.module_path = "puppet/modules"
    puppet.options = "--verbose"
  end
end
