#!/bin/bash

/KWH/datalogger/config/setConf.sh DOMAIN $1 
echo "setconf DOMAIN $1" > /KWH/datalogger/transceive/sms/commands/DOMAIN.log
