#!/bin/bash

# Author: 8AH
# This script is designed to install "JPJR" components on a fresh Ubuntu system. It includes Docker, NVIDIA Container Toolkit, Homebrew, Oxker, and Git.
# It uses dialog for a user-friendly interface and allows for both full and custom installations.

# Check if the OS is Ubuntu
if [ -f /etc/os-release ]; then
    . /etc/os-release
    if [ "$ID" != "ubuntu" ]; then
        echo "This script is intended for Ubuntu or Ubuntu-based systems only."
        echo "Detected OS: $NAME"
        exit 1
    fi
fi

# Check and install dialog if not present
if ! command -v dialog &> /dev/null; then
    echo "Installing dialog..."
    sudo apt-get update && sudo apt-get install -y dialog
fi

# Function to install Docker
install_docker() {
    if ! command -v docker &> /dev/null; then
        echo "Installing Docker..."
        # Install required packages
        sudo apt-get update
        sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common

        # Add Docker’s official GPG key
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -

        # Add Docker repository
        sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"

        # Install Docker
        sudo apt-get update
        sudo apt-get install -y docker-ce

        # Add the current user to the docker group
        sudo groupadd docker
        sudo usermod -aG docker $USER
        newgrp docker

        echo "Docker installed successfully."
    else
        dialog --title "Installation terminée" --msgbox "Docker is already installed." 6 60
    fi
}

# Function to install NVIDIA Container Toolkit
install_nvidia_container_toolkit() {
    # Check if nvidia drivers are installed
    if ! command -v nvidia-smi &> /dev/null; then
        echo "NVIDIA drivers not found. Installing NVIDIA drivers..."
        sudo ubuntu-drivers install --gpgpu
    fi
    if ! command -v nvidia-ctk &> /dev/null; then
        echo "NVIDIA Container Toolkit not found. Installing NVIDIA Container Toolkit..."
        echo "Installing NVIDIA Container Toolkit..."
        # Add the package repositories

        curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
        && curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
        sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
        sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

        sudo apt-get update
        export NVIDIA_CONTAINER_TOOLKIT_VERSION=1.17.8-1
        sudo apt-get install -y \
        nvidia-container-toolkit=${NVIDIA_CONTAINER_TOOLKIT_VERSION} \
        nvidia-container-toolkit-base=${NVIDIA_CONTAINER_TOOLKIT_VERSION} \
        libnvidia-container-tools=${NVIDIA_CONTAINER_TOOLKIT_VERSION} \
        libnvidia-container1=${NVIDIA_CONTAINER_TOOLKIT_VERSION}

        sudo nvidia-ctk runtime configure --runtime=docker

        # Restart Docker to apply changes
        sudo systemctl restart docker

        echo "NVIDIA Container Toolkit installed successfully."
    else
        dialog --title "Installation terminée" --msgbox "NVIDIA Container Toolkit is already installed." 6 60
    fi
}

# Function to install Homebrew
install_homebrew() {
    if ! command -v brew &> /dev/null; then
        echo "Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

        # Add Homebrew to PATH
        echo 'eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"' >> $HOME/.bashrc
        eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"

        echo "Homebrew installed successfully."
    else
        dialog --title "Installation terminée" --msgbox "Homebrew is already installed." 6 60
    fi
}

# Function to install oxker using Homebrew
install_oxker() {
    if ! command -v oxker &> /dev/null; then
        echo "Installing oxker..."
        brew install oxker
        echo "oxker installed successfully."
    else
        dialog --title "Installation terminée" --msgbox "oxker is already installed." 6 60
    fi

}

# Function to install Git
install_git() {
    if ! command -v git &> /dev/null; then
        echo "Installing Git..."
        sudo apt-get install -y git
        echo "Git installed successfully."
    else
        dialog --title "Installation terminée" --msgbox "Git is already installed." 6 60
    fi
    
}

# Function to clone repository and set up
setup_repository() {
    echo "Cloning repository and setting up..."
    git clone https://github.com/8AH/jpjr.git
    cd jpjr/docker
    sudo chmod +x ollama_entrypoint.sh # Make the entrypoint script executable for Ollama Container
    docker compose up -d
    echo "Repository setup completed."
}

display_main_menu() {
    TEMP_FILE=$(mktemp /tmp/dialog.XXXXXX)

    dialog --clear --backtitle "Installation JPJR" \
        --menu "Choisissez une option d'installation:" 15 60 2 \
        1 "Tout installer" \
        2 "Installation personnalisée" \
        2> "$TEMP_FILE"

    main_choice=$(cat "$TEMP_FILE")
    rm "$TEMP_FILE"

    case $main_choice in
        1)
            dialog --infobox "Installation de tous les composants..." 3 50
            install_docker
            install_nvidia_container_toolkit
            install_homebrew
            install_oxker
            install_git
            setup_repository
            oxker
            dialog --title "Installation terminée" --msgbox "Toutes les installations sont terminées." 6 60
            ;;
        2)
            display_custom_menu
            ;;
    esac
}

# Function to display custom installation menu
display_custom_menu() {
    TEMP_FILE=$(mktemp /tmp/dialog.XXXXXX)

    dialog --clear --backtitle "Installation JPJR" \
        --title "Installation personnalisée" \
        --checklist "Utilisez ESPACE pour sélectionner/désélectionner les composants à installer:" 20 70 8 \
        "1" "Docker" OFF \
        "2" "NVIDIA Container Toolkit" OFF \
        "3" "Homebrew" OFF \
        "4" "Oxker" OFF \
        "5" "Git" OFF \
        "6" "Cloner et configurer le repository" OFF \
        2> "$TEMP_FILE"

    choices=$(cat "$TEMP_FILE")
    rm "$TEMP_FILE"

    if [ $? -eq 0 ]; then
        for choice in $choices; do
            choice=$(echo "$choice" | tr -d '"')
            case $choice in
                1)
                    dialog --infobox "Installation de Docker..." 3 40
                    install_docker
                    ;;
                2)
                    dialog --infobox "Installation de NVIDIA Container Toolkit..." 3 50
                    install_nvidia_container_toolkit
                    ;;
                3)
                    dialog --infobox "Installation de Homebrew..." 3 40
                    install_homebrew
                    ;;
                4)
                    dialog --infobox "Installation de Oxker..." 3 40
                    install_oxker
                    ;;
                5)
                    dialog --infobox "Installation de Git..." 3 40
                    install_git
                    ;;
                6)
                    dialog --infobox "Configuration du repository..." 3 40
                    setup_repository
                    ;;
            esac
        done

        dialog --title "Installation terminée" --msgbox "Les composants sélectionnés ont été installés." 6 60
    fi
}


# Main script execution
main() {
    clear
    display_main_menu
    clear
}

main