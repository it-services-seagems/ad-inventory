const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const repoRoot = path.resolve(__dirname, '..', '..');
const srcEnv = path.join(repoRoot, 'environments', 'frontend', 'production', '.env');
const destEnv = path.join(repoRoot, 'frontend', '.env');

if (fs.existsSync(srcEnv)) {
  fs.copyFileSync(srcEnv, destEnv);
  console.log('Copied production .env to frontend/.env');
} else {
  console.warn('Production .env not found at', srcEnv);
}

// Build production assets
execSync('npm run build', { stdio: 'inherit', cwd: path.join(repoRoot, 'frontend') });
