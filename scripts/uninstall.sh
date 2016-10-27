#!/bin/bash

# Pretty functions. Because I can.
poofs=0
function poof { output ">${1}"; poofs=$((poofs+1)); }
function paaf { poofs=$((poofs-1)); }
function appt { echo -e -n '\e[2m'; if [[ $poofs -gt 0 ]]; then for z in {1..$poofs}; do echo -n $1; done; fi; }
function output { echo -e -n '\e[1m\e[90m::> '; appt '|'; echo -e "\e[0m${1}"; }
function info { echo -e -n '\e[1m\e[34mii> '; appt '|'; echo -e "\e[0m${1}"; }
function good { echo -e -n '\e[1m\e[32moo> '; appt '|'; echo -e "\e[0m${1}"; }
function error { echo -e -n '\e[1m\e[31m::> '; appt '!'; echo -e "\e[0m${1}" 1>&2; }
function die { echo -e -n '\e[1m\e[31mXT> '; appt '!'; echo -e "\e[0m\e[1m\e[97m\e[41m${1}\e[0m" 1>&2; exit 1; }
function prompt { echo -e -n '\e[1m\e[33m??> '; echo -e -n "\e[0m${1} "; }

if [ "$(id -u)" != "0" ]; then
 error 'This script must be run as root'
 exit 1
fi

output '-----=\e[1mPrism Uninstall\e[0m=-----'
output

if [ ! -d "/opt/prism-panel" ]; then
  die 'Prism isn'"'"'t installed'
fi

prompt 'Are you sure you would like to uninstall Prism?'
read -p '[y/n] ' -n 1 -r
echo
if ! [[ $REPLY =~ ^[Yy]$ ]]; then
    die 'Uninstallation cancelled'
fi

KEEP_CONFIG=false
KEEP_PLUGINS=false

if [ -d "/opt/prism-panel/prism/config" ]; then
  prompt 'Would you like to keep Prism'"'"'s configurations? '
  read -p '[y/n] ' -n 1 -r
  echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
      KEEP_CONFIG=true
      good 'Keeping configurations'
  fi
fi

if [ -d "/opt/prism-panel/prism/plugins" ]; then
  prompt 'Would you like to keep Prism'"'"'s installed plugins? '
  read -p '[y/n] ' -n 1 -r
  echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
      KEEP_PLUGINS=true
      good 'Keeping plugins'
  fi
fi

if $KEEP_CONFIG || $KEEP_PLUGINS; then
  cd /tmp
  TMP_DIR=$(mktemp -d)
  cd $TMP_DIR

  if $KEEP_CONFIG; then
    info 'Saving config'
    mv /opt/prism-panel/prism/config .
  fi

  if $KEEP_PLUGINS; then
    info 'Saving plugins'
    mv /opt/prism-panel/prism/plugins .
  fi
fi

poof 'Removing files'
  output '/opt/prism-panel'
  rm -rf /opt/prism-panel

  output '/lib/systemd/system/prism-panel'
  rm -f /lib/systemd/system/prism-panel
paaf

if $KEEP_CONFIG || $KEEP_PLUGINS; then
  poof 'Restoring'
    mkdir /opt/prism-panel
    mkdir /opt/prism-panel/prism

    if $KEEP_CONFIG; then
      info 'Restored config'
      mv ./config /opt/prism-panel/prism/
    fi

    if $KEEP_PLUGINS; then
      info 'Restored plugins'
      mv ./plugins /opt/prism-panel/prism/
    fi

    rm -rf $TMP_DIR
  paaf
fi

good 'Prism uninstalled successfully'
