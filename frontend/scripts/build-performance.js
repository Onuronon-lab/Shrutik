#!/usr/bin/env node

/**
 * Build Performance Monitor
 * Tracks and reports build performance metrics for optimization insights
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

class BuildPerformanceMonitor {
  constructor() {
    this.startTime = Date.now();
    this.metrics = {
      buildTime: 0,
      bundleSize: {},
      chunkCount: 0,
      compressionRatio: {},
      dependencies: 0,
      warnings: [],
    };
  }

  async measureBuild() {
    console.log('🚀 Starting build performance measurement...\n');

    try {
      // Measure build time
      const buildStart = Date.now();

      // Run the build
      console.log('📦 Building application...');
      execSync('npm run build', {
        stdio: 'pipe',
        cwd: process.cwd(),
      });

      const buildEnd = Date.now();
      this.metrics.buildTime = buildEnd - buildStart;

      // Analyze build output
      await this.analyzeBuildOutput();

      // Generate report
      this.generateReport();
    } catch (error) {
      console.error('❌ Build failed:', error.message);
      process.exit(1);
    }
  }

  async analyzeBuildOutput() {
    const buildDir = path.join(process.cwd(), 'build');

    if (!fs.existsSync(buildDir)) {
      console.warn('⚠️  Build directory not found');
      return;
    }

    // Analyze bundle sizes
    this.analyzeBundleSizes(buildDir);

    // Count chunks
    this.countChunks(buildDir);

    // Analyze compression ratios
    this.analyzeCompression(buildDir);

    // Count dependencies
    this.countDependencies();
  }

  analyzeBundleSizes(buildDir) {
    const jsDir = path.join(buildDir, 'js');
    const cssDir = path.join(buildDir, 'css');

    // Analyze JavaScript bundles
    if (fs.existsSync(jsDir)) {
      const jsFiles = fs.readdirSync(jsDir).filter(file => file.endsWith('.js'));

      jsFiles.forEach(file => {
        const filePath = path.join(jsDir, file);
        const stats = fs.statSync(filePath);
        const sizeKB = (stats.size / 1024).toFixed(2);

        // Categorize by chunk type
        let category = 'other';
        if (file.includes('vendor')) category = 'vendor';
        else if (file.includes('main') || file.includes('index')) category = 'main';
        else if (file.includes('chunk')) category = 'async';

        if (!this.metrics.bundleSize[category]) {
          this.metrics.bundleSize[category] = [];
        }

        this.metrics.bundleSize[category].push({
          file,
          size: sizeKB,
          sizeBytes: stats.size,
        });
      });
    }

    // Analyze CSS bundles
    if (fs.existsSync(cssDir)) {
      const cssFiles = fs.readdirSync(cssDir).filter(file => file.endsWith('.css'));

      cssFiles.forEach(file => {
        const filePath = path.join(cssDir, file);
        const stats = fs.statSync(filePath);
        const sizeKB = (stats.size / 1024).toFixed(2);

        if (!this.metrics.bundleSize.css) {
          this.metrics.bundleSize.css = [];
        }

        this.metrics.bundleSize.css.push({
          file,
          size: sizeKB,
          sizeBytes: stats.size,
        });
      });
    }
  }

  countChunks(buildDir) {
    const jsDir = path.join(buildDir, 'js');

    if (fs.existsSync(jsDir)) {
      const jsFiles = fs.readdirSync(jsDir).filter(file => file.endsWith('.js'));
      this.metrics.chunkCount = jsFiles.length;
    }
  }

  analyzeCompression(buildDir) {
    const findCompressedFiles = (dir, ext) => {
      if (!fs.existsSync(dir)) return [];

      return fs
        .readdirSync(dir, { recursive: true })
        .filter(file => file.endsWith(ext))
        .map(file => {
          const filePath = path.join(dir, file);
          const stats = fs.statSync(filePath);
          return {
            file,
            size: stats.size,
          };
        });
    };

    // Find gzip files
    const gzipFiles = findCompressedFiles(buildDir, '.gz');
    const brotliFiles = findCompressedFiles(buildDir, '.br');

    // Calculate compression ratios
    gzipFiles.forEach(gzFile => {
      const originalFile = gzFile.file.replace('.gz', '');
      const originalPath = path.join(buildDir, originalFile);

      if (fs.existsSync(originalPath)) {
        const originalSize = fs.statSync(originalPath).size;
        const ratio = ((1 - gzFile.size / originalSize) * 100).toFixed(1);

        this.metrics.compressionRatio[originalFile] = {
          gzip: `${ratio}%`,
          originalSize: (originalSize / 1024).toFixed(2) + 'KB',
          gzipSize: (gzFile.size / 1024).toFixed(2) + 'KB',
        };
      }
    });
  }

  countDependencies() {
    try {
      const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));
      this.metrics.dependencies = Object.keys(packageJson.dependencies || {}).length;
    } catch (error) {
      console.warn('⚠️  Could not read package.json');
    }
  }

  generateReport() {
    console.log('\n📊 Build Performance Report');
    console.log('='.repeat(50));

    // Build time
    console.log(`⏱️  Build Time: ${(this.metrics.buildTime / 1000).toFixed(2)}s`);

    // Bundle sizes
    console.log('\n📦 Bundle Sizes:');
    Object.entries(this.metrics.bundleSize).forEach(([category, files]) => {
      const totalSize = files.reduce((sum, file) => sum + parseFloat(file.size), 0);
      console.log(`  ${category}: ${totalSize.toFixed(2)}KB (${files.length} files)`);

      // Show largest files in each category
      const sortedFiles = files.sort((a, b) => parseFloat(b.size) - parseFloat(a.size));
      sortedFiles.slice(0, 3).forEach(file => {
        console.log(`    - ${file.file}: ${file.size}KB`);
      });
    });

    // Chunk count
    console.log(`\n🧩 Total Chunks: ${this.metrics.chunkCount}`);

    // Compression ratios
    if (Object.keys(this.metrics.compressionRatio).length > 0) {
      console.log('\n🗜️  Compression Ratios:');
      Object.entries(this.metrics.compressionRatio).forEach(([file, data]) => {
        console.log(`  ${file}: ${data.originalSize} → ${data.gzipSize} (${data.gzip} reduction)`);
      });
    }

    // Dependencies
    console.log(`\n📚 Dependencies: ${this.metrics.dependencies}`);

    // Performance recommendations
    this.generateRecommendations();

    // Save metrics to file
    this.saveMetrics();
  }

  generateRecommendations() {
    console.log('\n💡 Performance Recommendations:');

    const recommendations = [];

    // Check bundle sizes
    Object.entries(this.metrics.bundleSize).forEach(([category, files]) => {
      const totalSize = files.reduce((sum, file) => sum + parseFloat(file.size), 0);

      if (category === 'vendor' && totalSize > 500) {
        recommendations.push(
          'Consider splitting vendor bundles further (current: ' + totalSize.toFixed(2) + 'KB)'
        );
      }

      if (category === 'main' && totalSize > 200) {
        recommendations.push(
          'Main bundle is large, consider code splitting (current: ' + totalSize.toFixed(2) + 'KB)'
        );
      }
    });

    // Check build time
    if (this.metrics.buildTime > 30000) {
      recommendations.push(
        'Build time is slow, consider optimizing dependencies or build configuration'
      );
    }

    // Check chunk count
    if (this.metrics.chunkCount > 20) {
      recommendations.push('Many chunks detected, consider consolidating related functionality');
    } else if (this.metrics.chunkCount < 5) {
      recommendations.push('Few chunks detected, consider more aggressive code splitting');
    }

    if (recommendations.length === 0) {
      console.log('  ✅ Build performance looks good!');
    } else {
      recommendations.forEach((rec, index) => {
        console.log(`  ${index + 1}. ${rec}`);
      });
    }
  }

  saveMetrics() {
    const metricsFile = path.join(process.cwd(), 'build', 'performance-metrics.json');

    try {
      fs.writeFileSync(
        metricsFile,
        JSON.stringify(
          {
            timestamp: new Date().toISOString(),
            ...this.metrics,
          },
          null,
          2
        )
      );

      console.log(`\n💾 Metrics saved to: ${metricsFile}`);
    } catch (error) {
      console.warn('⚠️  Could not save metrics file:', error.message);
    }
  }
}

// Run if called directly
if (require.main === module) {
  const monitor = new BuildPerformanceMonitor();
  monitor.measureBuild().catch(error => {
    console.error('❌ Performance monitoring failed:', error);
    process.exit(1);
  });
}

module.exports = BuildPerformanceMonitor;
