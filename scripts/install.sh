#!/bin/bash

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

if ! $(pip &> /dev/null); then
  error 'Python pip is not installed'
  exit 1
fi

poof 'Verifying dependencies'
  if ! $(wget --version &> /dev/null); then
    die 'Wget is not installed'
  fi

  if ! $(tar --version &> /dev/null); then
    die 'Tar is not installed'
  fi

  if $(pip freeze | grep virtualenv &> /dev/null); then
    info 'Virtualenv is installed'
  else
    wait 'Installing virtualenv' 'pip install virtualenv'
    if ! $(pip freeze | grep virtualenv &> /dev/null); then
      die 'Virtualenv install failed'
    fi
    good 'Virtualenv installed successfully'
  fi
paaf

cd /tmp
TMP_DIR=$(mktemp -d)
cd $TMP_DIR

poof 'Downloading Prism'
  output 'Searching for latest'
  RELEASE_LINK=$(curl -s https://api.github.com/repos/CodingForCookies/Prism/releases/latest | grep 'tarball_url' | cut -d\" -f4)

  wait 'Fetching' "wget ${RELEASE_LINK}"
  RELEASE_TAG=$(ls)

  wait "Extracting release: ${RELEASE_TAG}" "tar -zxf ${RELEASE_TAG}"

  output 'Removing tar file'
  rm $RELEASE_TAG

  cd $(ls)
paaf

poof 'Actually installing, now'
  output 'Moving files'
  mkdir /opt/prism-panel &> /dev/null
  mv bin /opt/prism-panel/ &> /dev/null
  mv prism /opt/prism-panel/ &> /dev/null
  mv etc/init.d/prism-panel /etc/init.d/
  mv LICENSE /opt/prism-panel/ &> /dev/null
  mv requirements.txt /opt/prism-panel/ &> /dev/null

  cd /opt/
  poof 'Setting up virtual environment'
    wait 'Creating environment' 'virtualenv -p python3 prism-panel'

    cd prism-panel
    poof 'Installing pip requirements'
      source bin/activate
      while read p; do
        if [[ -z "${p// }" ]]; then
          continue
        fi
        DEPEND_NAME=$(echo $p | egrep -o '^[^<>=]+')
        poof "Verifying ${DEPEND_NAME}"
          if $(pip freeze | grep -i ${DEPEND_NAME}= &> /dev/null); then
            info "${DEPEND_NAME} is installed"
          else
            wait "Installing ${DEPEND_NAME}" "pip install ${p}"
            if ! $(pip freeze | grep -i ${DEPEND_NAME}= &> /dev/null); then
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

prompt 'You'\''re good to go! Would you like to start Prism, now? '
read -p '[y/n] ' -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    good 'Attempting to start Prism'
fi
