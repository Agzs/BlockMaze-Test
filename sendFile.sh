#!/bin/bash
#ssh-keyscan $2 >> ~/.ssh/known_hosts
sshpass -p 'test' scp docker/$1 alice@$2:$1
