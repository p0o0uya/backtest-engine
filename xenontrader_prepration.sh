#!/bin/bash
# Kernel is Ubuntu 20.04
USER='root'                        #No space in bash script variable definition
SERVER='54.38.212.90'
ssh $USER@$SERVER systemctl stop xenon_trader
scp -r ~/Documents/EN001_54.38.212.90/etc/xenontrader/ $USER@$SERVER:/etc/
scp -r ~/Documents/EN001_54.38.212.90/lib/systemd/system/ $USER@$SERVER:/lib/systemd/
ssh $USER@$SERVER rm /etc/xenontrader/output.log
ssh $USER@$SERVER rm /etc/xenontrader/error.log
ssh $USER@$SERVER systemctl daemon-reload
ssh $USER@$SERVER systemctl restart xenon_trader
# ssh $USER@$SERVER journalctl -u xenon_trader -f
# ssh $USER@$SERVER cat /etc/xenontrader/output.log