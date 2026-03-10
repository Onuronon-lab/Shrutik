#!/usr/bin/env node

import { execSync } from 'child_process';
import { readFileSync } from 'fs';

console.log('🔍 Checking for unused imports using TypeScript compiler...\n');

try {
  // Run TypeScript compiler with noUnusedLocals and noUnusedParameters
  const result = execSync('npx tsc --noEmit --noUnusedLocals --noUnusedParameters', {
    encoding: 'utf8',
    stdio: 'pipe',
  });

  console.log('✅ No unused imports found!');
} catch (error) {
  const output = error.stdout || error.stderr || '';

  if (output.includes('is declared but its value is never read')) {
    console.log('⚠️  Found unused imports/variables:');
    console.log(output);
  } else if (output.includes('error TS')) {
    console.log('❌ TypeScript compilation errors (not related to unused imports):');
    console.log(output);
  } else {
    console.log('✅ No unused imports found!');
  }
}

console.log('\n✅ Check complete!');
