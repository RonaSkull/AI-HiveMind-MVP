import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
// ethers will be available from hre (Hardhat Runtime Environment)
// dotenv configuration is handled by hardhat.config.cjs

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function main() {
    const [deployer] = await hre.ethers.getSigners();
    console.log("Deploying contracts with the account:", deployer.address);

    const expectedDeployer = process.env.DEPLOYER_ADDRESS;
    if (expectedDeployer) {
        if (deployer.address.toLowerCase() !== expectedDeployer.toLowerCase()) {
            console.error(`Deployer address mismatch. Expected: ${expectedDeployer}, Got: ${deployer.address}`);
            console.error("Please ensure METAMASK_PRIVATE_KEY in .env.development corresponds to the DEPLOYER_ADDRESS.");
            process.exit(1);
        }
        console.log("Deployer address matches expected DEPLOYER_ADDRESS:", expectedDeployer);
    } else {
        console.warn("Warning: DEPLOYER_ADDRESS environment variable not set in .env.development. Skipping deployer address verification.");
        // Consider making this an error if DEPLOYER_ADDRESS is mandatory for your workflow:
        // console.error("Error: DEPLOYER_ADDRESS not set. Please set it in .env.development.");
        // process.exit(1);
    }

    const balance = await deployer.getBalance();
    console.log("Account balance:", hre.ethers.utils.formatEther(balance), "ETH");

    const AINFTVault = await hre.ethers.getContractFactory("AINFTVault");
    console.log(`Deploying AINFTVault with revenueWallet set to: ${deployer.address}`);
    const vault = await AINFTVault.deploy(deployer.address); // The deployer's address is passed as revenueWallet
    
    await vault.deployed(); // Wait for the deployment transaction to be mined
    console.log("AINFTVault deployed to:", vault.address);

    // Save/Update contract address in .env.development
    const envPath = path.resolve(__dirname, '../.env.development');
    let envContent = "";
    if (fs.existsSync(envPath)) {
        envContent = fs.readFileSync(envPath, 'utf8');
    }

    const lines = envContent.split('\n');
    let contractAddressExists = false;
    const newLines = lines.map(line => {
        if (line.startsWith('CONTRACT_ADDRESS=')) {
            contractAddressExists = true;
            return `CONTRACT_ADDRESS=${vault.address}`;
        }
        return line;
    }).filter(line => line.trim() !== ''); // Remove any empty lines that might have resulted from split

    if (!contractAddressExists) {
        newLines.push(`CONTRACT_ADDRESS=${vault.address}`);
    }
    
    // Ensure a trailing newline for POSIX compatibility and cleaner git diffs
    fs.writeFileSync(envPath, newLines.join('\n') + '\n', 'utf8');
    console.log(`Contract address ${vault.address} has been saved to .env.development`);
}

main()
    .then(() => process.exit(0))
    .catch(error => {
        console.error(error);
        process.exit(1);
    });
