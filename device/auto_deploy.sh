sudo mkdir -p /opt/wikkit
sudo chown $USER:$USER /opt wikkit
mkdir -p /opt/wikkit/signal
cp * /opt/wikkit/signal/

sudo apt-get install python-dev python-pip
sudo pip install psutil

echo -n "Enter the name of this device"
read servername

crontab -l > mycron
echo "@reboot python /opt/wikkit/signal/signal.py" >> mycron
crontab mycron
rm mycron

ssh -t rsa -b 4096 -C $servername@wikkit.dev

echo "TODO: edit the config.ini"
echo "      devID=<id>; devType=<type: pi or tk1>"
echo "      send the following public key to bo"

echo ~/.ssh/id_rsa.pub
