const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const repoRoot = path.resolve(__dirname, '..', '..');
const srcEnv = path.join(repoRoot, 'environments', 'frontend', 'homologacao', '.env');
const destEnv = path.join(repoRoot, 'frontend', '.env');

if (fs.existsSync(srcEnv)) {
  fs.copyFileSync(srcEnv, destEnv);
  console.log('Copied homologacao .env to frontend/.env');
} else {
  console.warn('Homologacao .env not found at', srcEnv);
}

// Start dev server
execSync('npm run dev', { stdio: 'inherit', cwd: path.join(repoRoot, 'frontend') });
