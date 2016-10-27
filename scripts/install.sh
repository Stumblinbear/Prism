#!/bin/bash

# TODO: build-base libffi-dev python3-dev

VERSION='latest'
if ! [[ -z $1 ]]; then
  VERSION=$1
fi

# Pretty functions. Because I can.
poofs=0
function poof { output ">${1}"; poofs=$((poofs+1)); }
function paaf { poofs=$((poofs-1)); }
function appt { echo -e -n '\e[2m'; if [[ $poofs -gt 0 ]]; then for z in $(seq 1 $poofs); do echo -n $1; done; fi; }
function output { echo -e -n '\e[1m\e[90m::> '; appt '|'; echo -e "\e[0m${1}"; }
function info { echo -e -n '\e[1m\e[34mii> '; appt '|'; echo -e "\e[0m${1}"; }
function good { echo -e -n '\e[1m\e[32moo> '; appt '|'; echo -e "\e[0m${1}"; }
function error { echo -e -n '\e[1m\e[31m::> '; appt '!'; echo -e "\e[0m${1}" 1>&2; }
function die { echo -e -n '\e[1m\e[31mXT> '; appt '!'; echo -e "\e[0m\e[1m\e[97m\e[41m${1}\e[0m" 1>&2; exit 1; }
function prompt { echo -e -n '\e[1m\e[33m??> '; echo -e -n "\e[0m${1} "; }
function wait {
  { $2 & } &> /dev/null
  pid=$!
  trap "kill $pid &> /dev/null" EXIT
  spin='o.  .oO'
  i=1; j=0
  while [[ $(ps -p $pid -o pid=) ]]; do
    echo -e -n "\e[0K\r${spin:$i:1}${spin:$j:1}> "; appt '|'; echo -e -n "\e[0m${1}"
    i=$(((i+1)%7)); j=$(((j+1)%7))
    sleep .1
  done
  echo -e -n "\e[0K\r${spin:0:1}${spin:0:1}> "; appt '|'; echo -e "\e[0m${1}"
  trap - EXIT
}

if [ "$(id -u)" != "0" ]; then
 error 'This script must be run as root'
 exit 1
fi

output '------=\e[1mPrism Install\e[0m=------'
output

if [ -d "/opt/prism-panel/bin/prism-panel" ]; then
  die 'Prism is already installed'
fi


if ! $(python3 --version &> /dev/null); then
  error 'Python3 not found.'
  if $(apt-get --version &> /dev/null); then
    wait 'Installing python3.4' 'apt-get -y install python3.4'
  elif $(yum --version &> /dev/null); then
    prompt 'There'"'"'s a python3 version available in the EPEL Repository. Use that one? '
    read -p '[y/n] ' -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
      poof 'Installing python3'
        wait 'Adding EPEL Repository' 'yum -y install epel-release'
        wait 'Installing python3.4' 'yum -y install python34'
        wait 'Downloading get-pip.py' 'curl -O https://bootstrap.pypa.io/get-pip.py'
        wait 'Installing pip' '/usr/bin/python3.4 get-pip.py'
        rm -f get-pip.py
        wait 'Installing python34-devel' 'yum -y install python34-devel'
        wait 'Installing libffi-devel' 'yum -y install libffi-devel'
      paaf
    else
      die 'Unable to install python3.'
    fi
  else
    die 'Unsupported package manager.'
  fi
  if ! $(python3 --version &> /dev/null); then
    die 'Python3 failed to install.'
  fi
fi

if ! $(pip3 &> /dev/null); then
  error 'Python pip3 is not installed'
  exit 1
fi

poof 'Verifying dependencies'
  if ! $(curl --version &> /dev/null); then
    die 'Curl is not installed'
  fi

  if ! $(tar --version &> /dev/null); then
    die 'Tar is not installed'
  fi

  if $(pip3 freeze | grep virtualenv &> /dev/null); then
    info 'Virtualenv is installed'
  else
    wait 'Installing virtualenv' 'pip3 install virtualenv'
    if ! $(pip3 freeze | grep virtualenv &> /dev/null); then
      die 'Virtualenv install failed'
    fi
    good 'Virtualenv installed successfully'
  fi
paaf

cd /tmp
TMP_DIR=$(mktemp -d)
cd $TMP_DIR

poof 'Downloading Prism'
  output "Searching for ${VERSION}"

  case "$VERSION" in
    "latest")
      RELEASE_LINK=$(curl -s https://api.github.com/repos/CodingForCookies/Prism/releases/latest | grep 'tarball_url' | cut -d\" -f4)
      ;;
    "current")
      RELEASE_LINK='https://github.com/CodingForCookies/Prism/archive/master.tar.gz'
      ;;
    *)
      die 'Unknown version type'
      ;;
    esac

  wait 'Fetching' "curl -o prism.tar.gz ${RELEASE_LINK}"
  wait "Extracting release: $(basename $RELEASE_LINK)" 'tar -zxf prism.tar.gz'

  output 'Removing tar file'
  rm -f prism.tar.gz

  cd $(ls)
paaf

poof 'Actually installing, now'
  output 'Moving files'
  mkdir /opt/prism-panel &> /dev/null
  mv -f bin /opt/prism-panel/ &> /dev/null
  mv -f prism /opt/prism-panel/ &> /dev/null
  mv -f prism-panel.service /lib/systemd/system/ &> /dev/null
  mv -f LICENSE /opt/prism-panel/ &> /dev/null
  mv -f requirements.txt /opt/prism-panel/ &> /dev/null
  mv -f scripts/uninstall.sh /opt/prism-panel/uninstall.sh &> /dev/null

  cd /opt/
  poof 'Setting up virtual environment'
    wait 'Creating environment' 'virtualenv -p python3 prism-panel'

    cd prism-panel
    poof 'Installing prism requirements'
      source bin/activate
      while read p; do
        if [[ -z "${p// }" ]]; then
          continue
        fi
        DEPEND_NAME=$(echo $p | egrep -o '^[^<>=]+')
        poof "Verifying ${DEPEND_NAME}"
          if $(pip3 freeze | grep -i ${DEPEND_NAME}= &> /dev/null); then
            info "${DEPEND_NAME} is installed"
          else
            wait "Installing ${DEPEND_NAME}" "pip3 install ${p}"
            if ! $(pip3 freeze | grep -i ${DEPEND_NAME}= &> /dev/null); then
              die "${DEPEND_NAME} install failed"
            fi
            good "${DEPEND_NAME} installed successfully"
          fi
        paaf
      done < requirements.txt
      deactivate
    paaf
  paaf
paaf

poof 'Cleanup'
  output 'Removing temporary folder'
  rm -rf $TMP_DIR
paaf

output

prompt 'You'\''re good to go! Starting Prism, now!'

cd /opt/prism-panel/bin/
source activate
  python3 prism-panel -n
deactivate

{ systemctl start prism-panel & } &> /dev/null
