#!/bin/bash

git config receive.denyCurrentBranch updateInstead
git config receive.advertisePushOptions true

if [[ $(hostname) =~ .*vpn.* ]];
then
    git config core.hooksPath ../scripts/hooks/vpn/
else
    git config core.hooksPath ../scripts/hooks/switch/
fi
