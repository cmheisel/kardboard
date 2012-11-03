Vagrant::Config.run do |config|
  # Setup the box
  config.vm.box = "lucid64"
  config.vm.box_url = "http://files.vagrantup.com/lucid64.box"

  # Forward guest port 80 to host port 4567
  config.vm.forward_port 80, 4000

  config.vm.provision :puppet do |puppet|
    puppet.manifests_path = "puppet/manifests"
    puppet.manifest_file = "default.pp"
    puppet.module_path = "puppet/modules"
  end
end