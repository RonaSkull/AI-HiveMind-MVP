# PowerShell script to clean up sensitive values from repository history

# List of sensitive values to remove
$sensitiveValues = @(
    "0x05a4743525020c3a85057939ebfb283b5a1d08f26854265e0e849a98725d69b3",
    "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",
    "0xa0f536d1d1a8Bf63e200344Bda8a34b6d012745b",
    "0x114734b9d4227a65c905330A68eA4E4A02bB8d76"
)

# Remove sensitive values from history
foreach ($value in $sensitiveValues) {
    Write-Host "Removing sensitive value: $value"
    git filter-branch --force --index-filter "git rm --cached --ignore-unmatch $value" --prune-empty --tag-name-filter cat -- --all
}

# Force push to overwrite remote history
Write-Host "Force pushing to overwrite remote history"
git push origin --force --all
git push origin --force --tags

Write-Host "Cleanup complete. Please verify the security scanning alerts are now resolved."
