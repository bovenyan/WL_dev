# _Device Configuration Guide_

Follow this page to configure Wikkit Sensors

## Configure Hardware Support
  - Expand file system, Enable camera
    sudo raspi-config

  - Verify the filesystem and camera are enabled
    sudo raspistill -o test.jpg
    sudo df -h

## Install ServoBlaster
  - Clone the repository 
    git clone https://github.com/richardghirst/PiBits.git

  - Install ServoBlaster
    cd PiBits/ServoBlaster/user/
    make
    sudo make install

  - Verify Installation:
    servod

## Configure Repository
  - Edit source.list
    sudo apt-get install vim
    vim /etc/apt/sources.list

  - Add the following repositories in China. Replace if necessary. 
    http://mirrors.ustc.edu.cn/raspbian/raspbian/
    http://mirrors.zju.edu.cn/raspbian/raspbian/

    sudo apt-get update

## Register Device
  - Create Stanza with ID in Server 
    INSERT into DEVICE_DEV (id) VALUES (<id No.>)

  - Generate ssh-key 
    ssh-keygen -t rsa -b 4096 -C "rasPi<id No.>@wikkit.dev"
    
    Empty password
    
  - Add the public key to dev@<server IP>

  - Verify registration with
    ssh dev@<server IP>
    
  - Create `~/.ssh/config`
        

## Install basic tools
    sudo apt-get install python-pip python-dev
    sudo pip install psutil requests ConfigParser

## Install WikkitDev device repositories
  - Create directories
    sudo mkdir /opt/wikkit
    sudo mkdir /opt/wikkit/signal
    sudo chown pi:pi /opt/wikkit
    sudo chown pi:pi /opt/wikkit/signal

  - Clone this repository and install the contents in the device folder in /opt/wikkit/signal
    
  - Modify `config.ini`
    ```ini
    devId=<id No.>
    devType=<type>
    mgmtSleep=2
    opSleep=600
    ```
    
  - Run the python to run in background
        sudo python signal.py >  

  - Add autostart on boot 
    crontab -e 
    @reboot python /opt/wikkit/signal/signal.py > /opt/wikkit/signal/signal.log

## Install OpenCV
  - Install dependent packages
    sudo apt-get -y install build-essential cmake cmake-curses-gui pkg-config libpng12-0 libpng12-dev libpng++-dev libpng3 libpnglite-dev zlib1g-dbg zlib1g zlib1g-dev pngtools libtiff4-dev libtiff4 libtiffxx0c2 libtiff-tools libeigen3-dev 
    sudo apt-get -y install libjpeg8 libjpeg8-dev libjpeg8-dbg libjpeg-progs ffmpeg libavcodec-dev libavcodec53 libavformat53 libavformat-dev libgstreamer0.10-0-dbg libgstreamer0.10-0 libgstreamer0.10-dev libxine1-ffmpeg libxine-dev libxine1-bin libunicap2 libunicap2-dev swig libv4l-0 libv4l-dev python-numpy libpython2.6 python-dev python2.6-dev libgtk2.0-dev 

  - Clone repository 
    wget http://sourceforge.net/projects/opencvlibrary/files/opencv-unix/2.4.8/opencv-2.4.8.zip/download opencv-2.4.8.zip
    
  - Compile and make
    unzip opencv-2.4.8.zip
    cd opencv-2.4.8
    mkdir release
    cd release
    ccmake ../    
    make -j 2
    sudo make install
