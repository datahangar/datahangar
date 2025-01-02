#!/bin/bash

# client id
ID=$1

###### eth1 ######
ip addr add 10.${ID}.0.2/30 dev eth1
ip link set dev eth1 address aa:c1:ab:00:00:0${ID}
ip route add default via 10.${ID}.0.1 dev eth1
