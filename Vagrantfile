Vagrant.configure("2") do |config|
  config.vm.box = "ubuntu/jammy64"
  config.vm.provider "virtualbox" do |vb|
    vb.memory = 4096
    vb.cpus = 4
  end
  config.vm.synced_folder ".", "/vagrant", mount_options: ["dmode=775,fmode=664"]

  config.vm.provision "shell", inline: <<-SHELL
    set -e
    sudo apt-get update
    sudo apt-get install -y openjdk-17-jdk python3-pip git unzip zlib1g-dev libffi-dev libssl-dev libncurses5
    python3 -m pip install --upgrade pip
    python3 -m pip install buildozer Cython kivy
    cd /vagrant/android
    buildozer -v android debug
  SHELL
end


