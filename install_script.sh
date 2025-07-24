#!/bin/bash

# Author: 8AH
# This script is designed to install "FIM" components on a fresh Ubuntu system. It includes Docker, NVIDIA Container Toolkit, Homebrew, Oxker, and Git.
# It uses dialog for a user-friendly interface and allows for both full and custom installations.

echo " 
 █████   █████  ██   ██         ██     ███████ ██ ███    ███ 
██   ██ ██   ██ ██   ██        ██      ██      ██ ████  ████ 
 █████  ███████ ███████       ██       █████   ██ ██ ████ ██ 
██   ██ ██   ██ ██   ██      ██        ██      ██ ██  ██  ██ 
 █████  ██   ██ ██   ██     ██         ██      ██ ██      ██ 
                                                             
                                                                       "

echo "Bienvenue dans le script d'installation de FIM.

Ce script est destiné uniquement à Ubuntu ou aux systèmes basés sur Ubuntu et installera dialog et curl s'ils ne sont pas présents.

Pour que FIM fonctionne, il installera Docker, NVIDIA Container Toolkit, Homebrew, Oxker et Git (personnalisable).

Il clonera également le dépôt FIM et le configurera pour vous.
Il extraira les modèles nécessaires pour ollama et speaches.
Veuillez vous assurer de disposer d'une connexion Internet stable avant de continuer.

Les privilèges sudo seront nécessaires pour installer les paquets et apporter des modifications au système.
Il n'est pas recommandé d'exécuter ce script en tant que root.
"

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
if command -v dialog &> /dev/null 
    then
        echo "Dialog is already installed."
    else
        echo "Installing dialog..."
        sudo apt update && sudo apt install -y dialog
fi

# Check and install curl if not present (should be)
if command -v curl &> /dev/null
    then
        echo "curl is already installed."
    else
        echo "curl is not installed. Installing now..."
        sudo apt update && sudo apt install curl -y 
fi

# Function to install Docker
install_docker() {
    if command -v docker &> /dev/null   
        then
            dialog --title "Installation terminée" --msgbox "Docker est déjà installé." 6 60
        else
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
    fi
}

# Function to install NVIDIA Container Toolkit
install_nvidia_container_toolkit() {
    # Check if nvidia drivers are installed
    if command -v nvidia-smi &> /dev/null
        then
            echo "NVIDIA drivers are already installed."
        else
            echo "NVIDIA drivers not found. Installing NVIDIA drivers..."
            sudo ubuntu-drivers install --gpgpu
        fi
    if command -v nvidia-ctk &> /dev/null
        then
            dialog --title "Installation terminée" --msgbox "NVIDIA Container Toolkit est déjà installé." 6 60
        else
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
    fi
}

# Function to install oxker using Homebrew. Install Homebrew if not present.
install_oxker() {
    if command -v brew &> /dev/null
        then
            echo "Homebrew is already installed."
        else
            echo "Installing Homebrew..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

            # Add Homebrew to PATH
            echo 'eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"' >> $HOME/.bashrc
            eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"

            echo "Homebrew installed successfully."
    fi
    if command -v oxker &> /dev/null
        then
            dialog --title "Installation terminée" --msgbox "Oxker est déjà installé." 6 60
        else
            echo "Installing oxker..."
            brew install oxker
            echo "oxker installed successfully."
    fi
}

# Function to clone repository and set up
setup_repository() {
    echo "Building Docker images..."
    docker compose -f FIM/docker/docker-compose.yml up -d
    
    # Download models for Ollama and Speaches using curl
    echo "Setting up models, it may take a while..."
    curl http://127.0.0.1:11434/api/pull -d '{"model": "llama3.1:8b"}' # Download the Llama model
    echo "Llama model downloaded."
    curl http://127.0.0.1:8000/v1/models/Systran/faster-whisper-large-v3 -X POST # Download the Whisper model
    echo "Whisper model downloaded."
    echo "Repository setup completed."
}

rebuild_fim() {
    echo "Rebuilding FIM..."
    docker compose -f ./docker/docker-compose.yml down
    docker compose -f ./docker/docker-compose.yml build fim
    docker compose -f ./docker/docker-compose.yml up -d
    docker image prune -f
    echo "FIM rebuilt successfully."
}


display_main_menu() {
    TEMP_FILE=$(mktemp /tmp/dialog.XXXXXX)

    dialog --clear --backtitle "Installation FIM" \
        --menu "Choisissez une option d'installation:" 15 60 2 \
        1 "Tout installer" \
        2 "Installation personnalisée" \
        3 "Rebuild FIM (intégrer les changements après modification du code)" \
        4 "Quitter" \
        2> "$TEMP_FILE"

    main_choice=$(cat "$TEMP_FILE")
    rm "$TEMP_FILE"

    case $main_choice in
        1)
            dialog --infobox "Installation de tous les composants..." 3 50
            install_docker
            install_nvidia_container_toolkit
            install_oxker
            setup_repository
            dialog --title "Installation terminée" --msgbox "Toutes les installations sont terminées." 6 60
            ;;
        2)
            display_custom_menu
            ;;
        3)
            dialog --infobox "Rebuild de FIM..." 3 50
            rebuild_fim
            dialog --title "Rebuild terminé" --msgbox "FIM a été reconstruit avec succès." 6 60
            ;;
        4)
            ;;
    esac
}

# Function to display custom installation menu
display_custom_menu() {
    TEMP_FILE=$(mktemp /tmp/dialog.XXXXXX)

    dialog --clear --backtitle "Installation FIM" \
        --title "Installation personnalisée" \
        --checklist "Utilisez ESPACE pour sélectionner/désélectionner les composants à installer:" 20 70 8 \
        "1" "Docker" OFF \
        "2" "NVIDIA Container Toolkit" OFF \
        "3" "Oxker" OFF \
        "4" "Configurer le repository" OFF \
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
                    dialog --infobox "Installation de Oxker..." 3 40
                    install_oxker
                    ;;
                4)
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