#!/usr/bin/env node

import { execSync } from 'child_process';
import { readFileSync, existsSync } from 'fs';
import { join } from 'path';

console.log('🔍 Analyzing bundle and dependencies...\n');

// Check if build directory exists
const buildDir = join(process.cwd(), 'build');
if (!existsSync(buildDir)) {
  console.log('❌ Build directory not found. Running build first...');
  try {
    execSync('npm run build', { stdio: 'inherit' });
  } catch (error) {
    console.error('❌ Build failed:', error.message);
    process.exit(1);
  }
}

// Analyze bundle sizes
console.log('📊 Bundle Analysis:');
console.log('==================');

try {
  // Get build stats
  const buildStats = execSync('du -sh build/*', { encoding: 'utf8' });
  console.log(buildStats);

  // Get detailed file sizes
  const jsFiles = execSync('find build -name "*.js" -exec du -h {} \\; | sort -hr', {
    encoding: 'utf8',
  });
  console.log('\n📦 JavaScript Files (largest first):');
  console.log(jsFiles);

  const cssFiles = execSync('find build -name "*.css" -exec du -h {} \\; | sort -hr', {
    encoding: 'utf8',
  });
  console.log('\n🎨 CSS Files:');
  console.log(cssFiles);
} catch (error) {
  console.error('❌ Error analyzing build:', error.message);
}

// Analyze dependencies
console.log('\n📋 Dependency Analysis:');
console.log('======================');

try {
  const packageJson = JSON.parse(readFileSync('package.json', 'utf8'));
  const dependencies = Object.keys(packageJson.dependencies || {});
  const devDependencies = Object.keys(packageJson.devDependencies || {});

  console.log(`📦 Production dependencies: ${dependencies.length}`);
  console.log(`🛠️  Development dependencies: ${devDependencies.length}`);

  // Check for potentially unused dependencies
  console.log('\n🔍 Checking for potentially unused dependencies...');

  const potentiallyUnused = [];

  for (const dep of dependencies) {
    try {
      // Simple check - look for imports in source files
      const grepResult = execSync(
        `grep -r "from '${dep}'" src/ || grep -r "import.*'${dep}'" src/ || true`,
        { encoding: 'utf8' }
      );
      if (!grepResult.trim()) {
        potentiallyUnused.push(dep);
      }
    } catch (error) {
      // Ignore grep errors
    }
  }

  if (potentiallyUnused.length > 0) {
    console.log('⚠️  Potentially unused dependencies:');
    potentiallyUnused.forEach(dep => console.log(`   - ${dep}`));
  } else {
    console.log('✅ All dependencies appear to be used');
  }
} catch (error) {
  console.error('❌ Error analyzing dependencies:', error.message);
}

// Check for duplicate dependencies
console.log('\n🔄 Checking for duplicate dependencies...');
try {
  const duplicates = execSync('npm ls --depth=0 2>&1 | grep "WARN" || echo "No warnings found"', {
    encoding: 'utf8',
  });
  console.log(duplicates);
} catch (error) {
  console.log('No duplicate dependency warnings found');
}

console.log('\n✅ Analysis complete!');
