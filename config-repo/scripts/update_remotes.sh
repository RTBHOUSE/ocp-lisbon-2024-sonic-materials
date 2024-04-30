#!/bin/bash

for remote in $(git remote); do
  git remote remove $remote
done

$GIT_SERVER="git.local"
$SWITCH_MASTER_DOMAIN="oob.local"
$SWITCH_REPO_PATH="/opt/sonic-config-repo"
$REPO_NAME="sonic-config"

# Origin - domyslny push
git config branch.main.remote origin
git config branch.main.merge refs/heads/main
git remote add origin ssh://${USER}@$GIT_SERVER/$REPO_NAME
git remote set-url --add --push origin ssh://${USER}@$GIT_SERVER/$REPO_NAME


# OOB VPN servers, they keep the repo for clone during ztp
git remote add vpns ssh://${USER}@$GIT_SERVER/$REPO_NAME
git remote set-url --add --push vpns ssh://${USER}@$GIT_SERVER/$REPO_NAME
# Add your vpn servers there

# Switches
shopt -s nullglob
for dir in config/switches/*/
do
    dir=${dir%*/} # remove trailing slash
    dir=${dir##*/} # get relpath
    for file in config/switches/$dir/*
    do
        domain=$dir
        switch=`basename $file| sed 's/\.yaml//g'`
        sw_alias="$switch.$domain"
        git remote add $sw_alias ssh://${USER}@$GIT_SERVER/$REPO_NAME
        git remote set-url --add --push $sw_alias ssh://${USER}@$GIT_SERVER/$REPO_NAME
        git remote set-url --add --push $sw_alias ssh://root@$sw_alias.${SWITCH_MASTER_DOMAIN}${SWITCH_REPO_PATH}/.git
    done
done
