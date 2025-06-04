const fs = require('fs');
const path = require('path');

console.log('=== Checking Repository Settings ===');

// Check if we're in the correct directory
console.log(`Current directory: ${process.cwd()}`);

// Check package.json
if (fs.existsSync('package.json')) {
    const pkg = JSON.parse(fs.readFileSync('package.json'));
    console.log('\n=== Package.json ===');
    console.log(`Name: ${pkg.name}`);
    console.log(`Version: ${pkg.version}`);
    console.log(`Dependencies: ${Object.keys(pkg.dependencies).join(', ')}`);
}

// Check git status
console.log('\n=== Git Status ===');
const gitStatus = require('child_process').execSync('git status').toString();
console.log(gitStatus);

// Check environment variables
console.log('\n=== Environment Variables ===');
console.log(`Node.js version: ${process.version}`);
console.log(`Platform: ${process.platform}`);
console.log(`Architecture: ${process.arch}`);

// Check if we have access to required tools
console.log('\n=== Tool Availability ===');
try {
    console.log(`npm version: ${require('child_process').execSync('npm --version').toString().trim()}`);
} catch (e) {
    console.log('npm not available');
}

// Check if we can read required files
console.log('\n=== File Access ===');
const requiredFiles = [
    '.github/workflows/check-actions.yml',
    '.github/workflows/test-workflow.yml',
    'backend/dynamic_pricing.js'
];

requiredFiles.forEach(file => {
    try {
        if (fs.existsSync(file)) {
            console.log(`${file}: Found`);
        } else {
            console.log(`${file}: Not found`);
        }
    } catch (e) {
        console.log(`${file}: Error checking - ${e.message}`);
    }
});

console.log('\n=== Check Complete ===');
