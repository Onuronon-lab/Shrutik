/**
 * Vite Caching Configuration
 * Optimizes caching strategies for faster subsequent builds
 */

const path = require('path');
const fs = require('fs');

/**
 * Cache configuration for different environments
 */
const cacheConfig = {
  // Development caching strategies
  development: {
    // Dependency pre-bundling cache
    optimizeDeps: {
      // Cache location
      cacheDir: 'node_modules/.vite',
      // Force re-optimization when these files change
      force: false,
      // Include patterns for better caching
      include: ['react', 'react-dom', 'react-router-dom', 'zustand', 'axios'],
    },

    // File system cache settings
    fs: {
      // Allow caching of node_modules
      cachedChecks: true,
      // Optimize file watching
      strict: false,
    },

    // Server cache settings
    server: {
      // Enable HTTP caching for static assets
      headers: {
        'Cache-Control': 'public, max-age=31536000',
      },
    },
  },

  // Production caching strategies
  production: {
    // Build cache optimization
    build: {
      // Enable build cache
      cache: true,
      // Optimize asset caching
      assetsInlineLimit: 4096,
      // Enable CSS code splitting for better caching
      cssCodeSplit: true,
    },

    // Rollup cache settings
    rollup: {
      // Enable Rollup cache
      cache: true,
      // Optimize chunk caching
      preserveEntrySignatures: 'strict',
    },
  },
};

/**
 * Get cache configuration for current environment
 */
function getCacheConfig(mode = 'development') {
  return cacheConfig[mode] || cacheConfig.development;
}

/**
 * Clear Vite cache
 */
function clearCache() {
  const cacheDir = path.join(process.cwd(), 'node_modules', '.vite');

  if (fs.existsSync(cacheDir)) {
    console.log('🧹 Clearing Vite cache...');
    fs.rmSync(cacheDir, { recursive: true, force: true });
    console.log('✅ Cache cleared successfully');
  } else {
    console.log('ℹ️  No cache to clear');
  }
}

/**
 * Get cache statistics
 */
function getCacheStats() {
  const cacheDir = path.join(process.cwd(), 'node_modules', '.vite');

  if (!fs.existsSync(cacheDir)) {
    return {
      exists: false,
      size: 0,
      files: 0,
    };
  }

  let totalSize = 0;
  let fileCount = 0;

  function calculateSize(dir) {
    const files = fs.readdirSync(dir);

    files.forEach(file => {
      const filePath = path.join(dir, file);
      const stats = fs.statSync(filePath);

      if (stats.isDirectory()) {
        calculateSize(filePath);
      } else {
        totalSize += stats.size;
        fileCount++;
      }
    });
  }

  try {
    calculateSize(cacheDir);

    return {
      exists: true,
      size: totalSize,
      sizeFormatted: formatBytes(totalSize),
      files: fileCount,
      location: cacheDir,
    };
  } catch (error) {
    return {
      exists: false,
      error: error.message,
    };
  }
}

/**
 * Format bytes to human readable format
 */
function formatBytes(bytes, decimals = 2) {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];

  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

/**
 * Optimize cache for current project
 */
function optimizeCache() {
  console.log('🔧 Optimizing Vite cache configuration...');

  const stats = getCacheStats();

  if (stats.exists) {
    console.log(`📊 Current cache: ${stats.sizeFormatted} (${stats.files} files)`);

    // If cache is too large, suggest cleanup
    if (stats.size > 500 * 1024 * 1024) {
      // 500MB
      console.log('⚠️  Cache is large, consider clearing it periodically');
    }
  }

  // Check for optimal cache settings
  const packageJson = path.join(process.cwd(), 'package.json');

  if (fs.existsSync(packageJson)) {
    const pkg = JSON.parse(fs.readFileSync(packageJson, 'utf8'));
    const depCount = Object.keys(pkg.dependencies || {}).length;

    console.log(`📦 Dependencies: ${depCount}`);

    if (depCount > 20) {
      console.log('💡 Consider aggressive dependency pre-bundling for better cache performance');
    }
  }

  console.log('✅ Cache optimization complete');
}

// CLI interface
if (require.main === module) {
  const command = process.argv[2];

  switch (command) {
    case 'clear':
      clearCache();
      break;

    case 'stats':
      const stats = getCacheStats();
      console.log('📊 Cache Statistics:');
      console.log(JSON.stringify(stats, null, 2));
      break;

    case 'optimize':
      optimizeCache();
      break;

    default:
      console.log('Vite Cache Management');
      console.log('Usage:');
      console.log('  node .vitecache.config.js clear    - Clear cache');
      console.log('  node .vitecache.config.js stats    - Show cache stats');
      console.log('  node .vitecache.config.js optimize - Optimize cache');
  }
}

module.exports = {
  getCacheConfig,
  clearCache,
  getCacheStats,
  optimizeCache,
  formatBytes,
};
