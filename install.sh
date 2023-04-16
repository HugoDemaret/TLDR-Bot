#!/usr/bin/env bash
cat << 'EOF'
  _____ _           ____  ____
 |_   _| |      _  |  _ \|  _ \
   | | | |     (_) | | | | |_) |
   | | | |___   _  | |_| |  _ <
   |_| |_____| ( ) |____/|_| \_\
               |/
  Too  Long    ;   Didn't Read
EOF


# •===========================•
#    DISTRIBUTION  DETECTION  #
# •===========================•

# Detects the Linux distribution
echo "Detecting Linux distribution..."
declare -A osInfo;
osInfo[/etc/debian_version]="apt-get install -y"
osInfo[/etc/centos-release]="yum install -y"
osInfo[/etc/fedora-release]="dnf install -y"
osInfo[/etc/arch-release]="pacman -S --noconfirm"

for f in ${!osInfo[@]}
do
    if [[ -f $f ]];then
        package_manager=${osInfo[$f]}
    fi
done

if [[ -z $package_manager ]]; then
    echo "Linux distribution not detected."
    exit 1
fi

echo "Linux distribution detected."


# •===========================•
#    DISTRIBUTION  UPDATE     #
# •===========================•

#Update the package manager depending on the distribution
echo "Updating the package manager..."
# If debian based :
if [[ $package_manager == *"apt-get"* ]]; then
    sudo apt-get update -y && sudo apt-get upgrade -y
fi
# If redhat based :
if [[ $package_manager == *"yum"* ]]; then
    sudo yum update -y
fi
# If fedora based :
if [[ $package_manager == *"dnf"* ]]; then
    sudo dnf update -y
fi
# If arch based :
if [[ $package_manager == *"pacman"* ]]; then
    sudo pacman -Syu --noconfirm
fi
echo "Package manager updated."

# •===========================•
#       USER CONFIG           #
# •===========================•


# Asking if user wants the bot to run in a screen session, docker container, or just run the bot normally
echo "Do you want to run the bot in a screen session, docker container, or just run the bot normally?"
echo "1. Screen Session"
echo "2. Docker Container"
echo "3. Run the bot normally"
read -p "Enter your choice: " choice


# •===========================•
#       PACKAGE INSTALL       #
# •===========================•

normal_package="git python3.10 python3-pip"
docker_package="git docker docker-compose"
screen_package="git python3.10 python3-pip screen"


# Install the packages depending on the choice
echo "Installing packages..."
# If user wants to run the bot in a screen session
if [ $choice -eq 1 ]; then
    sudo $package_manager $screen_package
fi
# If user wants to run the bot in a docker container
if [ $choice -eq 2 ]; then
    sudo $package_manager $docker_package
fi
# If user wants to run the bot normally
if [ $choice -eq 3 ]; then
    sudo $package_manager $normal_package
fi
echo "Packages installed."


# •===========================•
#      DOWNLOAD REPOSITORY    #
# •===========================•



# Download the bot from GitHub
echo "Downloading the bot from GitHub..."
git clone https://github.com/HugoDemaret/TLDR-Bot.git
cd TLDR-Bot
rm -rf .git



# Asking for the bot token

echo "Please enter your discord bot token:"
read -p "Enter your token: " token

# Replacing the token in the config file
sed -i "s/your_token_here/$token/g" .env

# Asking for the admin accounts : the accounts that can use the admin commands
echo "Please enter the admin accounts (separated by a comma):"
read -p "Enter the admin accounts: " admin_accounts

# Replacing the admin accounts in the config file
sed -i "s/your_admin_accounts_here/$admin_accounts/g" .env


# Asks if user wants to run the bot directly after configuration
echo "Do you want to run the bot directly after configuration?"
echo "1. Yes"
echo "2. No"
read -p "Enter your choice: " run_choice


########## Install requirements function ##########


# Install requirements.txt function (for screen session and normal run)
function install_requirements {
    echo "Installing requirements.txt..."
    pip3 install -r requirements.txt
}


########## Remove files functions ##########

# Remove unnecessary files function (for normal run)
function remove_files_normal {
    rm -rf docker-compose.yml
    rm -rf Dockerfile
    rm -rf run-screen.sh
    rm -rf run-docker.sh
    rm -rf README.md
    rm -rf LICENSE
    rm -rf .gitignore
    rm -rf .git
}


# Remove unnecessary files function (for screen session)
function remove_files_screen {
    rm -rf docker-compose.yml
    rm -rf Dockerfile
    rm -rf README.md
    rm -rf LICENSE
    rm -rf .gitignore
    rm -rf .git
}

# Remove unnecessary files function (for docker container)
function remove_files_docker {
    rm -rf run-default.sh
    rm -rf README.md
    rm -rf LICENSE
    rm -rf .gitignore
    rm -rf .git
}


########## Install ##########

# If user wants to run the bot in a screen session
if [ $choice -eq 1 ]; then
  # Install requirements.txt
    echo "Installing requirements.txt..."
    install_requirements
    echo "Requirements.txt installed."

  # Remove unnecessary files
    echo "Removing unnecessary files..."
    remove_files_screen
    echo "Unnecessary files removed."
fi

# If user wants to run the bot in a docker container
if [ $choice -eq 2 ]; then

  # Remove unnecessary files
    echo "Removing unnecessary files..."
    remove_files_docker
    echo "Unnecessary files removed."
fi


# If user wants to run the bot normally
if [ $choice -eq 3 ]; then
  # Install requirements.txt
    echo "Installing requirements.txt..."
    install_requirements
    echo "Requirements.txt installed."

  # Remove unnecessary files
    echo "Removing unnecessary files..."
    remove_files_normal
    echo "Unnecessary files removed."
fi


########## Run the bot ##########

echo "Installation finished."

# If user wants to run the bot directly after configuration
if [ $run_choice -eq 1 ]; then
  # If user wants to run the bot in a screen session
  if [ $choice -eq 1 ]; then
    # Run the bot in a screen session
    echo "Running the bot in a screen session..."
    chmod +x run-screen.sh
    ./run-screen.sh
    echo "Bot running in a screen session."
  fi

  # If user wants to run the bot in a docker container
  if [ $choice -eq 2 ]; then
    # Run the bot in a docker container
    echo "Running the bot in a docker container..."
    chmod +x run-docker.sh
    ./run-docker.sh
    echo "Bot running in a docker container."
  fi

  # If user wants to run the bot normally
  if [ $choice -eq 3 ]; then
    # Run the bot normally
    echo "Running the bot normally..."
    chmod +x run-default.sh
    ./run-default.sh
    echo "Bot running normally."
  fi
fi
# Else
if [ $run_choice -eq 2 ]; then
  echo "The bot will not run directly after configuration."
  echo "Please run the bash script needed to run the bot."
  # If user wants to run the bot in a screen session
  if [ $choice -eq 1 ]; then
    echo "To run the bot in a screen session, run the run-screen.sh bash script."
    chmod +x run-screen.sh
  fi
  # If user wants to run the bot in a docker container
  if [ $choice -eq 2 ]; then
    echo "To run the bot in a docker container, run the run-docker.sh bash script."
    chmod +x run-docker.sh
  fi
  # If user wants to run the bot normally
  if [ $choice -eq 3 ]; then
    echo "To run the bot normally, run the run-default.sh bash script."
    chmod +x run-default.sh
  fi
fi
