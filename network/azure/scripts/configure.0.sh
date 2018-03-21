#!/bin/bash

sudo apt-get -y update
sudo apt-get -y install linux-image-extra-$(uname -r) linux-image-extra-virtual
sudo apt-get -y update
sudo apt-get -y install apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
sudo apt-get -y update
sudo apt-get -y install docker-ce

USER="lambda";
HOMEDIR="/home/$USER";
CONFIG_LOG_FILE_PATH="$HOMEDIR/config.log";
ARTIFACTS_URL_PREFIX="https://raw.githubusercontent.com/hashblock/hashblock-exchange/master/docker/compose";

cd $HOMEDIR;
sudo -u $USER /bin/bash -c "wget -N ${ARTIFACTS_URL_PREFIX}/hashblock-node.0.yaml";

FAILED_EXITCODE=0;
sudo -u $AZUREUSER docker-compose -f /home/$AZUREUSER/hashblock-node.0.yaml up >> $CONFIG_LOG_FILE_PATH 2>&1;
FAILED_EXITCODE=$?
if [ $FAILED_EXITCODE -ne 0 ]; then
    echo "FAILED_EXITCODE: $FAILED_EXITCODE " >> $CONFIG_LOG_FILE_PATH;
    exit $FAILED_EXITCODE;
else
    echo "======== Deployment successful! ======== " >> $CONFIG_LOG_FILE_PATH;
    exit 0;
fi
