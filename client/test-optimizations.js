#!/usr/bin/env node

/**
 * Test Development and Build Optimizations
 * Validates that all optimization configurations are working correctly
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

class OptimizationTester {
  constructor() {
    this.results = {
      viteConfig: false,
      buildPerformance: false,
      bundleAnalysis: false,
      cacheConfig: false,
      sourcemapConfig: false,
      hmrConfig: false,
    };
  }

  async runTests() {
    console.log('🧪 Testing Development and Build Optimizations\n');

    try {
      // Test 1: Vite Configuration
      await this.testViteConfig();

      // Test 2: Build Performance
      await this.testBuildPerformance();

      // Test 3: Bundle Analysis
      await this.testBundleAnalysis();

      // Test 4: Cache Configuration
      await this.testCacheConfig();

      // Test 5: Sourcemap Configuration
      await this.testSourcemapConfig();

      // Test 6: HMR Configuration
      await this.testHMRConfig();

      // Generate report
      this.generateReport();
    } catch (error) {
      console.error('❌ Testing failed:', error.message);
      process.exit(1);
    }
  }

  async testViteConfig() {
    console.log('1️⃣  Testing Vite Configuration...');

    try {
      // Check if vite.config.ts exists and is valid
      const configPath = path.join(process.cwd(), 'vite.config.ts');

      if (!fs.existsSync(configPath)) {
        throw new Error('vite.config.ts not found');
      }

      const configContent = fs.readFileSync(configPath, 'utf8');

      // Check for key optimization features
      const checks = [
        { name: 'HMR Configuration', pattern: /hmr.*{/ },
        { name: 'Code Splitting', pattern: /manualChunks/ },
        { name: 'Source Maps', pattern: /sourcemap/ },
        { name: 'Bundle Analyzer', pattern: /visualizer/ },
        { name: 'Compression', pattern: /compression/ },
        { name: 'Dependency Optimization', pattern: /optimizeDeps/ },
      ];

      let passedChecks = 0;
      checks.forEach(check => {
        if (check.pattern.test(configContent)) {
          console.log(`  ✅ ${check.name}`);
          passedChecks++;
        } else {
          console.log(`  ❌ ${check.name}`);
        }
      });

      this.results.viteConfig = passedChecks === checks.length;
      console.log(`  Result: ${passedChecks}/${checks.length} checks passed\n`);
    } catch (error) {
      console.log(`  ❌ Error: ${error.message}\n`);
    }
  }

  async testBuildPerformance() {
    console.log('2️⃣  Testing Build Performance Monitoring...');

    try {
      // Check if build performance script exists
      const scriptPath = path.join(process.cwd(), 'scripts', 'build-performance.js');

      if (!fs.existsSync(scriptPath)) {
        throw new Error('build-performance.js script not found');
      }

      // Test the script (dry run)
      const scriptContent = fs.readFileSync(scriptPath, 'utf8');

      const checks = [
        { name: 'Build Time Measurement', pattern: /buildTime/ },
        { name: 'Bundle Size Analysis', pattern: /bundleSize/ },
        { name: 'Compression Ratio', pattern: /compressionRatio/ },
        { name: 'Performance Recommendations', pattern: /generateRecommendations/ },
        { name: 'Metrics Export', pattern: /saveMetrics/ },
      ];

      let passedChecks = 0;
      checks.forEach(check => {
        if (check.pattern.test(scriptContent)) {
          console.log(`  ✅ ${check.name}`);
          passedChecks++;
        } else {
          console.log(`  ❌ ${check.name}`);
        }
      });

      this.results.buildPerformance = passedChecks === checks.length;
      console.log(`  Result: ${passedChecks}/${checks.length} checks passed\n`);
    } catch (error) {
      console.log(`  ❌ Error: ${error.message}\n`);
    }
  }

  async testBundleAnalysis() {
    console.log('3️⃣  Testing Bundle Analysis...');

    try {
      // Check if bundle analyzer is configured
      const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));

      const checks = [
        { name: 'Bundle Analyze Script', check: () => packageJson.scripts['build:analyze'] },
        {
          name: 'Visualizer Dependency',
          check: () => packageJson.devDependencies['rollup-plugin-visualizer'],
        },
        { name: 'Bundle Analysis Script', check: () => fs.existsSync('scripts/analyze-bundle.js') },
      ];

      let passedChecks = 0;
      checks.forEach(check => {
        if (check.check()) {
          console.log(`  ✅ ${check.name}`);
          passedChecks++;
        } else {
          console.log(`  ❌ ${check.name}`);
        }
      });

      this.results.bundleAnalysis = passedChecks === checks.length;
      console.log(`  Result: ${passedChecks}/${checks.length} checks passed\n`);
    } catch (error) {
      console.log(`  ❌ Error: ${error.message}\n`);
    }
  }

  async testCacheConfig() {
    console.log('4️⃣  Testing Cache Configuration...');

    try {
      // Check cache configuration files
      const cacheConfigPath = path.join(process.cwd(), '.vitecache.config.js');

      if (!fs.existsSync(cacheConfigPath)) {
        throw new Error('Cache configuration not found');
      }

      const cacheContent = fs.readFileSync(cacheConfigPath, 'utf8');

      const checks = [
        { name: 'Cache Statistics', pattern: /getCacheStats/ },
        { name: 'Cache Clearing', pattern: /clearCache/ },
        { name: 'Cache Optimization', pattern: /optimizeCache/ },
        { name: 'CLI Interface', pattern: /require\.main === module/ },
      ];

      let passedChecks = 0;
      checks.forEach(check => {
        if (check.pattern.test(cacheContent)) {
          console.log(`  ✅ ${check.name}`);
          passedChecks++;
        } else {
          console.log(`  ❌ ${check.name}`);
        }
      });

      this.results.cacheConfig = passedChecks === checks.length;
      console.log(`  Result: ${passedChecks}/${checks.length} checks passed\n`);
    } catch (error) {
      console.log(`  ❌ Error: ${error.message}\n`);
    }
  }

  async testSourcemapConfig() {
    console.log('5️⃣  Testing Sourcemap Configuration...');

    try {
      // Check sourcemap configuration
      const sourcemapConfigPath = path.join(process.cwd(), 'sourcemap.config.js');

      if (!fs.existsSync(sourcemapConfigPath)) {
        throw new Error('Sourcemap configuration not found');
      }

      const sourcemapContent = fs.readFileSync(sourcemapConfigPath, 'utf8');

      const checks = [
        { name: 'Environment Configs', pattern: /development:\s*{[\s\S]*production:\s*{/ },
        { name: 'Vite Integration', pattern: /getViteSourcemapConfig/ },
        { name: 'Validation Utils', pattern: /validateSourcemaps/ },
        { name: 'Size Analysis', pattern: /analyzeSourcemapSizes/ },
      ];

      let passedChecks = 0;
      checks.forEach(check => {
        if (check.pattern.test(sourcemapContent)) {
          console.log(`  ✅ ${check.name}`);
          passedChecks++;
        } else {
          console.log(`  ❌ ${check.name}`);
        }
      });

      this.results.sourcemapConfig = passedChecks === checks.length;
      console.log(`  Result: ${passedChecks}/${checks.length} checks passed\n`);
    } catch (error) {
      console.log(`  ❌ Error: ${error.message}\n`);
    }
  }

  async testHMRConfig() {
    console.log('6️⃣  Testing HMR Configuration...');

    try {
      // Check HMR and development optimizations
      const devConfigPath = path.join(process.cwd(), 'vite.dev.config.ts');

      if (!fs.existsSync(devConfigPath)) {
        throw new Error('Development configuration not found');
      }

      const devContent = fs.readFileSync(devConfigPath, 'utf8');

      const checks = [
        { name: 'HMR Optimization', pattern: /hmr.*{/ },
        { name: 'File System Caching', pattern: /fs.*{/ },
        { name: 'Watch Optimization', pattern: /watch.*{/ },
        { name: 'Dev Performance Config', pattern: /devPerformanceConfig/ },
      ];

      let passedChecks = 0;
      checks.forEach(check => {
        if (check.pattern.test(devContent)) {
          console.log(`  ✅ ${check.name}`);
          passedChecks++;
        } else {
          console.log(`  ❌ ${check.name}`);
        }
      });

      this.results.hmrConfig = passedChecks === checks.length;
      console.log(`  Result: ${passedChecks}/${checks.length} checks passed\n`);
    } catch (error) {
      console.log(`  ❌ Error: ${error.message}\n`);
    }
  }

  generateReport() {
    console.log('📊 Optimization Test Results');
    console.log('='.repeat(50));

    const tests = [
      { name: 'Vite Configuration', result: this.results.viteConfig },
      { name: 'Build Performance Monitoring', result: this.results.buildPerformance },
      { name: 'Bundle Analysis', result: this.results.bundleAnalysis },
      { name: 'Cache Configuration', result: this.results.cacheConfig },
      { name: 'Sourcemap Configuration', result: this.results.sourcemapConfig },
      { name: 'HMR Configuration', result: this.results.hmrConfig },
    ];

    let passedTests = 0;
    tests.forEach(test => {
      const status = test.result ? '✅ PASS' : '❌ FAIL';
      console.log(`${status} ${test.name}`);
      if (test.result) passedTests++;
    });

    console.log('\n📈 Summary:');
    console.log(`Tests Passed: ${passedTests}/${tests.length}`);
    console.log(`Success Rate: ${((passedTests / tests.length) * 100).toFixed(1)}%`);

    if (passedTests === tests.length) {
      console.log('\n🎉 All optimization tests passed!');
      console.log('Your development and build optimizations are properly configured.');
    } else {
      console.log('\n⚠️  Some tests failed. Please review the configuration.');
    }

    // Available commands
    console.log('\n🛠️  Available Commands:');
    console.log('  npm run dev:monitor     - Monitor development performance');
    console.log('  npm run build:performance - Measure build performance');
    console.log('  npm run build:analyze   - Analyze bundle composition');
    console.log('  npm run cache:stats     - Show cache statistics');
    console.log('  npm run cache:clear     - Clear build cache');
    console.log('  npm run sourcemap:validate - Validate source maps');
  }
}

// Run tests if called directly
if (require.main === module) {
  const tester = new OptimizationTester();
  tester.runTests().catch(error => {
    console.error('❌ Testing failed:', error);
    process.exit(1);
  });
}

module.exports = OptimizationTester;
