#!/usr/bin/env node

/**
 * Development Performance Monitor
 * Monitors HMR performance and development server metrics
 */

const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

class DevPerformanceMonitor {
  constructor() {
    this.metrics = {
      startTime: 0,
      hmrUpdates: [],
      serverStartTime: 0,
      initialBuildTime: 0,
      memoryUsage: [],
    };
    this.isMonitoring = false;
  }

  startMonitoring() {
    console.log('🔍 Starting development performance monitoring...\n');

    this.isMonitoring = true;
    this.metrics.startTime = Date.now();

    // Start the development server with monitoring
    this.startDevServer();

    // Monitor memory usage periodically
    this.startMemoryMonitoring();

    // Setup graceful shutdown
    this.setupShutdownHandlers();
  }

  startDevServer() {
    console.log('🚀 Starting development server...');

    const serverStart = Date.now();

    // Start Vite dev server
    const devServer = spawn('npm', ['run', 'dev'], {
      stdio: 'pipe',
      cwd: process.cwd(),
    });

    let initialBuildComplete = false;

    devServer.stdout.on('data', data => {
      const output = data.toString();

      // Detect server ready
      if (output.includes('Local:') && !initialBuildComplete) {
        this.metrics.serverStartTime = Date.now() - serverStart;
        this.metrics.initialBuildTime = this.metrics.serverStartTime;
        initialBuildComplete = true;

        console.log(`✅ Server ready in ${(this.metrics.serverStartTime / 1000).toFixed(2)}s`);
        console.log('📊 Monitoring HMR performance...\n');
      }

      // Detect HMR updates
      if (output.includes('hmr update') || output.includes('page reload')) {
        const updateTime = Date.now();
        this.metrics.hmrUpdates.push({
          timestamp: updateTime,
          type: output.includes('page reload') ? 'reload' : 'hmr',
          output: output.trim(),
        });

        // Calculate HMR speed (if we have previous updates)
        if (this.metrics.hmrUpdates.length > 1) {
          const lastUpdate = this.metrics.hmrUpdates[this.metrics.hmrUpdates.length - 2];
          const timeDiff = updateTime - lastUpdate.timestamp;

          if (timeDiff < 5000) {
            // Only count if within 5 seconds (likely related)
            console.log(`⚡ HMR update in ${timeDiff}ms`);
          }
        }
      }

      // Forward output
      process.stdout.write(output);
    });

    devServer.stderr.on('data', data => {
      const output = data.toString();

      // Log warnings and errors
      if (output.includes('warning') || output.includes('error')) {
        console.warn(`⚠️  ${output.trim()}`);
      }

      // Forward error output
      process.stderr.write(output);
    });

    devServer.on('close', code => {
      console.log(`\n🛑 Development server exited with code ${code}`);
      this.generateReport();
      process.exit(code);
    });

    // Store reference for cleanup
    this.devServer = devServer;
  }

  startMemoryMonitoring() {
    const monitorMemory = () => {
      if (!this.isMonitoring) return;

      const usage = process.memoryUsage();
      this.metrics.memoryUsage.push({
        timestamp: Date.now(),
        rss: usage.rss,
        heapUsed: usage.heapUsed,
        heapTotal: usage.heapTotal,
        external: usage.external,
      });

      // Keep only last 100 measurements
      if (this.metrics.memoryUsage.length > 100) {
        this.metrics.memoryUsage.shift();
      }

      // Schedule next measurement
      setTimeout(monitorMemory, 10000); // Every 10 seconds
    };

    // Start monitoring after a delay
    setTimeout(monitorMemory, 5000);
  }

  setupShutdownHandlers() {
    const shutdown = () => {
      console.log('\n🔄 Shutting down monitoring...');
      this.isMonitoring = false;

      if (this.devServer) {
        this.devServer.kill('SIGTERM');
      }

      this.generateReport();
      process.exit(0);
    };

    process.on('SIGINT', shutdown);
    process.on('SIGTERM', shutdown);
  }

  generateReport() {
    if (this.metrics.hmrUpdates.length === 0 && this.metrics.serverStartTime === 0) {
      console.log('\n📊 No performance data collected');
      return;
    }

    console.log('\n📊 Development Performance Report');
    console.log('='.repeat(50));

    // Server startup time
    if (this.metrics.serverStartTime > 0) {
      console.log(`🚀 Server Start Time: ${(this.metrics.serverStartTime / 1000).toFixed(2)}s`);
    }

    // HMR performance
    if (this.metrics.hmrUpdates.length > 0) {
      console.log(`\n⚡ HMR Updates: ${this.metrics.hmrUpdates.length}`);

      // Calculate average HMR time
      const hmrTimes = [];
      for (let i = 1; i < this.metrics.hmrUpdates.length; i++) {
        const timeDiff =
          this.metrics.hmrUpdates[i].timestamp - this.metrics.hmrUpdates[i - 1].timestamp;
        if (timeDiff < 5000) {
          // Only count rapid updates
          hmrTimes.push(timeDiff);
        }
      }

      if (hmrTimes.length > 0) {
        const avgHmrTime = hmrTimes.reduce((sum, time) => sum + time, 0) / hmrTimes.length;
        const minHmrTime = Math.min(...hmrTimes);
        const maxHmrTime = Math.max(...hmrTimes);

        console.log(`  Average HMR Time: ${avgHmrTime.toFixed(0)}ms`);
        console.log(`  Fastest HMR: ${minHmrTime}ms`);
        console.log(`  Slowest HMR: ${maxHmrTime}ms`);
      }

      // Show recent updates
      console.log('\n  Recent Updates:');
      this.metrics.hmrUpdates.slice(-5).forEach((update, index) => {
        const time = new Date(update.timestamp).toLocaleTimeString();
        console.log(`    ${time} - ${update.type}`);
      });
    }

    // Memory usage
    if (this.metrics.memoryUsage.length > 0) {
      const latestMemory = this.metrics.memoryUsage[this.metrics.memoryUsage.length - 1];
      const initialMemory = this.metrics.memoryUsage[0];

      console.log('\n💾 Memory Usage:');
      console.log(`  Current RSS: ${(latestMemory.rss / 1024 / 1024).toFixed(2)}MB`);
      console.log(`  Current Heap: ${(latestMemory.heapUsed / 1024 / 1024).toFixed(2)}MB`);

      if (this.metrics.memoryUsage.length > 1) {
        const memoryGrowth = latestMemory.rss - initialMemory.rss;
        console.log(`  Memory Growth: ${(memoryGrowth / 1024 / 1024).toFixed(2)}MB`);
      }
    }

    // Performance recommendations
    this.generateDevRecommendations();

    // Save metrics
    this.saveDevMetrics();
  }

  generateDevRecommendations() {
    console.log('\n💡 Development Performance Recommendations:');

    const recommendations = [];

    // Check server start time
    if (this.metrics.serverStartTime > 10000) {
      recommendations.push(
        'Server startup is slow, consider optimizing dependencies or clearing cache'
      );
    }

    // Check HMR performance
    if (this.metrics.hmrUpdates.length > 0) {
      const hmrTimes = [];
      for (let i = 1; i < this.metrics.hmrUpdates.length; i++) {
        const timeDiff =
          this.metrics.hmrUpdates[i].timestamp - this.metrics.hmrUpdates[i - 1].timestamp;
        if (timeDiff < 5000) {
          hmrTimes.push(timeDiff);
        }
      }

      if (hmrTimes.length > 0) {
        const avgHmrTime = hmrTimes.reduce((sum, time) => sum + time, 0) / hmrTimes.length;

        if (avgHmrTime > 2000) {
          recommendations.push(
            'HMR updates are slow, consider reducing bundle size or optimizing dependencies'
          );
        } else if (avgHmrTime < 500) {
          recommendations.push('Excellent HMR performance! 🎉');
        }
      }
    }

    // Check memory usage
    if (this.metrics.memoryUsage.length > 1) {
      const latestMemory = this.metrics.memoryUsage[this.metrics.memoryUsage.length - 1];
      const initialMemory = this.metrics.memoryUsage[0];
      const memoryGrowth = latestMemory.rss - initialMemory.rss;

      if (memoryGrowth > 100 * 1024 * 1024) {
        // 100MB growth
        recommendations.push('Significant memory growth detected, check for memory leaks');
      }

      if (latestMemory.rss > 500 * 1024 * 1024) {
        // 500MB usage
        recommendations.push('High memory usage detected, consider optimizing or restarting');
      }
    }

    if (recommendations.length === 0) {
      recommendations.push('Development performance looks good! ✅');
    }

    recommendations.forEach((rec, index) => {
      console.log(`  ${index + 1}. ${rec}`);
    });
  }

  saveDevMetrics() {
    const metricsFile = path.join(process.cwd(), 'dev-performance-metrics.json');

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

      console.log(`\n💾 Development metrics saved to: ${metricsFile}`);
    } catch (error) {
      console.warn('⚠️  Could not save development metrics:', error.message);
    }
  }
}

// Run if called directly
if (require.main === module) {
  const monitor = new DevPerformanceMonitor();
  monitor.startMonitoring();
}

module.exports = DevPerformanceMonitor;
