$title = "AI-HiveMind-MVP-Deploy-Key"

# Generate SSH key pair
ssh-keygen -t ed25519 -C "$title" -f "deploy_key" -N ""

# Output the public key for GitHub
Write-Host "=== Public Key for GitHub ==="
Get-Content "deploy_key.pub"

# Output instructions
Write-Host "=== Instructions ==="
Write-Host "1. Copy the public key above"
Write-Host "2. Go to: https://github.com/RonaSkull/AI-HiveMind-MVP/settings/keys/new"
Write-Host "3. Enter the title: $title"
Write-Host "4. Paste the public key in the 'Key' field"
Write-Host "5. Check 'Allow write access' if needed"
Write-Host "6. Click 'Add key'"

# Save the private key for later use
Move-Item "deploy_key" "deploy_key_private"
Write-Host "=== Private key saved as 'deploy_key_private' ==="
Write-Host "=== Process Complete ==="
