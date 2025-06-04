@echo off
echo === Checking Workflow Progress ===

echo === Git Status ===
git status
echo.

echo === Workflow Files ===
for %%f in (.github\workflows\*.yml) do (
    echo.
    echo === %%f ===
    type "%%f"
    echo.
)
echo.

echo === Recent Git History ===
git log -n 5
echo.

echo === Environment Variables Check ===
set METAMASK_PRIVATE_KEY
set SEPOLIA_URL
set CONTRACT_ADDRESS
set QWEN_API_KEY
set HYPERSWARM_TOPIC
echo.

echo === Progress Check Complete ===
