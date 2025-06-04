# Download and install act
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/nektos/act/master/install.sh" -OutFile "install-act.sh"

# Make the script executable
chmod +x install-act.sh

# Run the installation script
./install-act.sh

# Add act to PATH
$env:Path += ";$env:USERPROFILE\bin"
