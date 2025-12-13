/**
 * Source Map Configuration
 * Optimizes source maps for different environments and debugging scenarios
 */

/**
 * Source map configurations for different environments
 */
const sourcemapConfigs = {
  // Development: Inline source maps for fastest debugging
  development: {
    js: 'inline-source-map',
    css: true,
    // Include all source content for offline debugging
    includeContent: true,
    // Include source names for better debugging
    includeNames: true,
  },

  // Production: Separate source maps for deployment flexibility
  production: {
    js: 'hidden-source-map',
    css: false,
    // Don't include source content in production
    includeContent: false,
    // Include names for error tracking
    includeNames: true,
  },

  // Testing: Inline source maps for coverage and debugging
  test: {
    js: 'inline-source-map',
    css: true,
    includeContent: true,
    includeNames: true,
  },

  // Staging: Separate source maps with content for debugging
  staging: {
    js: 'source-map',
    css: true,
    includeContent: true,
    includeNames: true,
  },
};

/**
 * Get source map configuration for environment
 */
function getSourcemapConfig(env = 'development') {
  return sourcemapConfigs[env] || sourcemapConfigs.development;
}

/**
 * Vite source map configuration
 */
function getViteSourcemapConfig(env = 'development') {
  const config = getSourcemapConfig(env);

  // Map to Vite sourcemap options
  const viteSourcemap = (() => {
    switch (config.js) {
      case 'inline-source-map':
        return 'inline';
      case 'source-map':
        return true;
      case 'hidden-source-map':
        return 'hidden';
      default:
        return false;
    }
  })();

  return {
    sourcemap: viteSourcemap,
    css: {
      devSourcemap: config.css,
    },
  };
}

/**
 * Source map optimization recommendations
 */
function getSourcemapRecommendations(env = 'development') {
  const recommendations = [];

  switch (env) {
    case 'development':
      recommendations.push('Using inline source maps for fastest debugging');
      recommendations.push('CSS source maps enabled for style debugging');
      break;

    case 'production':
      recommendations.push('Using hidden source maps for error tracking without exposing source');
      recommendations.push('CSS source maps disabled for smaller bundle size');
      recommendations.push('Consider uploading source maps to error tracking service');
      break;

    case 'test':
      recommendations.push('Using inline source maps for accurate test coverage');
      recommendations.push('All source content included for comprehensive testing');
      break;

    case 'staging':
      recommendations.push('Using separate source maps for debugging production issues');
      recommendations.push('Source content included for complete debugging experience');
      break;
  }

  return recommendations;
}

/**
 * Source map debugging utilities
 */
const debugUtils = {
  /**
   * Check if source maps are working correctly
   */
  validateSourcemaps(buildDir = 'build') {
    const fs = require('fs');
    const path = require('path');

    console.log('🔍 Validating source maps...');

    if (!fs.existsSync(buildDir)) {
      console.warn('⚠️  Build directory not found');
      return false;
    }

    // Check for JavaScript source maps
    const jsDir = path.join(buildDir, 'js');
    if (fs.existsSync(jsDir)) {
      const jsFiles = fs.readdirSync(jsDir).filter(file => file.endsWith('.js'));
      const mapFiles = fs.readdirSync(jsDir).filter(file => file.endsWith('.js.map'));

      console.log(`📄 JavaScript files: ${jsFiles.length}`);
      console.log(`🗺️  Source map files: ${mapFiles.length}`);

      // Check for inline source maps
      let inlineSourcemaps = 0;
      jsFiles.forEach(file => {
        const content = fs.readFileSync(path.join(jsDir, file), 'utf8');
        if (content.includes('//# sourceMappingURL=data:')) {
          inlineSourcemaps++;
        }
      });

      if (inlineSourcemaps > 0) {
        console.log(`📍 Inline source maps: ${inlineSourcemaps}`);
      }
    }

    // Check for CSS source maps
    const cssDir = path.join(buildDir, 'css');
    if (fs.existsSync(cssDir)) {
      const cssFiles = fs.readdirSync(cssDir).filter(file => file.endsWith('.css'));
      const cssMapFiles = fs.readdirSync(cssDir).filter(file => file.endsWith('.css.map'));

      console.log(`🎨 CSS files: ${cssFiles.length}`);
      console.log(`🗺️  CSS source maps: ${cssMapFiles.length}`);
    }

    console.log('✅ Source map validation complete');
    return true;
  },

  /**
   * Analyze source map sizes
   */
  analyzeSourcemapSizes(buildDir = 'build') {
    const fs = require('fs');
    const path = require('path');

    console.log('📊 Analyzing source map sizes...');

    let totalSourcemapSize = 0;
    let totalBundleSize = 0;

    function analyzeDirectory(dir, extension, mapExtension) {
      if (!fs.existsSync(dir)) return;

      const files = fs.readdirSync(dir);
      const sourceFiles = files.filter(file => file.endsWith(extension));
      const mapFiles = files.filter(file => file.endsWith(mapExtension));

      sourceFiles.forEach(file => {
        const filePath = path.join(dir, file);
        const size = fs.statSync(filePath).size;
        totalBundleSize += size;

        console.log(`  ${file}: ${(size / 1024).toFixed(2)}KB`);
      });

      mapFiles.forEach(file => {
        const filePath = path.join(dir, file);
        const size = fs.statSync(filePath).size;
        totalSourcemapSize += size;

        console.log(`  ${file}: ${(size / 1024).toFixed(2)}KB`);
      });
    }

    // Analyze JavaScript
    console.log('\n📄 JavaScript bundles:');
    analyzeDirectory(path.join(buildDir, 'js'), '.js', '.js.map');

    // Analyze CSS
    console.log('\n🎨 CSS bundles:');
    analyzeDirectory(path.join(buildDir, 'css'), '.css', '.css.map');

    // Summary
    console.log('\n📊 Summary:');
    console.log(`  Total bundle size: ${(totalBundleSize / 1024).toFixed(2)}KB`);
    console.log(`  Total source map size: ${(totalSourcemapSize / 1024).toFixed(2)}KB`);

    if (totalBundleSize > 0) {
      const ratio = ((totalSourcemapSize / totalBundleSize) * 100).toFixed(1);
      console.log(`  Source map overhead: ${ratio}%`);

      if (parseFloat(ratio) > 50) {
        console.warn('⚠️  Source maps are large relative to bundle size');
      }
    }
  },
};

// CLI interface
if (require.main === module) {
  const command = process.argv[2];
  const env = process.argv[3] || 'development';

  switch (command) {
    case 'config':
      console.log('Source Map Configuration:');
      console.log(JSON.stringify(getSourcemapConfig(env), null, 2));
      break;

    case 'vite':
      console.log('Vite Source Map Configuration:');
      console.log(JSON.stringify(getViteSourcemapConfig(env), null, 2));
      break;

    case 'recommendations':
      console.log('Source Map Recommendations:');
      getSourcemapRecommendations(env).forEach((rec, i) => {
        console.log(`  ${i + 1}. ${rec}`);
      });
      break;

    case 'validate':
      debugUtils.validateSourcemaps(process.argv[3]);
      break;

    case 'analyze':
      debugUtils.analyzeSourcemapSizes(process.argv[3]);
      break;

    default:
      console.log('Source Map Configuration Tool');
      console.log('Usage:');
      console.log('  node sourcemap.config.js config [env]        - Show config');
      console.log('  node sourcemap.config.js vite [env]          - Show Vite config');
      console.log('  node sourcemap.config.js recommendations [env] - Show recommendations');
      console.log('  node sourcemap.config.js validate [buildDir] - Validate source maps');
      console.log('  node sourcemap.config.js analyze [buildDir]  - Analyze sizes');
  }
}

module.exports = {
  getSourcemapConfig,
  getViteSourcemapConfig,
  getSourcemapRecommendations,
  debugUtils,
};
