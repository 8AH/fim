#!/bin/bash

# Function to install Docker
install_docker() {
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
    sudo usermod -aG docker $USER

    echo "Docker installed successfully."
}

# Function to install Homebrew
install_homebrew() {
    echo "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

    # Add Homebrew to PATH
    echo 'eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"' >> $HOME/.bashrc
    eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"

    echo "Homebrew installed successfully."
}

# Function to install oxker using Homebrew
install_oxker() {
    echo "Installing oxker..."
    brew install oxker
    echo "oxker installed successfully."
}

# Function to install Git
install_git() {
    echo "Installing Git..."
    sudo apt-get install -y git
    echo "Git installed successfully."
}

# Function to clone repository and set up
setup_repository() {
    echo "Cloning repository and setting up..."
    git clone https://github.com/8AH/jpjr.git
    cd jpjr/docker
    chmod +x ollama_entrypoint.sh
    docker compose up -d
    echo "Repository setup completed."
}

# Main script execution
main() {
    install_docker
    install_homebrew
    install_oxker
    install_git
    setup_repository
    oxker
}

echo "  
  ______     _____    ___ ___                  ____.__________ ____.__________ 
 /  __  \   /  _  \  /   |   \                |    |\______   \    |\______   \
 >      <  /  /_\  \/    ~    \   ______      |    | |     ___/    | |       _/
/   --   \/    |    \    Y    /  /_____/  /\__|    | |    /\__|    | |    |   \
\______  /\____|__  /\___|_  /            \________| |____\________| |____|_  /
       \/         \/       \/                                               \/ "


main