sudo mkdir -p /opt/wikkit
sudo chown $USER:$USER /opt wikkit
mkdir -p /opt/wikkit/signal
cp * /opt/wikkit/signal/

crontab -l > mycron
echo "@reboot python /opt/wikkit/signal/signal.py" >> mycron
crontab mycron
rm mycron

echo "TODO: edit the config.ini"
echo "      devID=<id>; devType=<type: pi or tk1>"
echo "      send ~/.ssh/id_rsa.pub to bo"
