#!/usr/bin/env node

/**
 * Phase 1 Validation Script
 * Validates that all MSALAuthProvider imports have been replaced with AuthProvider
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

function searchFiles(dir, extensions = ['.tsx', '.ts', '.js', '.jsx']) {
  const files = [];

  function traverse(currentDir) {
    const items = fs.readdirSync(currentDir);

    for (const item of items) {
      const fullPath = path.join(currentDir, item);
      const stat = fs.statSync(fullPath);

      if (stat.isDirectory() && !item.startsWith('.') && item !== 'node_modules') {
        traverse(fullPath);
      } else if (stat.isFile() && extensions.some(ext => item.endsWith(ext))) {
        files.push(fullPath);
      }
    }
  }

  traverse(dir);
  return files;
}

function validatePhase1() {
  console.log('🔍 Phase 1 Validation: Authentication Unification');
  console.log('==================================================\n');

  const srcDir = path.join(path.dirname(__dirname), 'src');
  const files = searchFiles(srcDir);

  let msalImports = 0;
  let authProviderImports = 0;
  let unifiedImports = 0;

  const issues = [];

  for (const file of files) {
    const content = fs.readFileSync(file, 'utf8');
    const relativePath = path.relative(process.cwd(), file);

    // Check for MSALAuthProvider imports
    if (content.includes('MSALAuthProvider')) {
      msalImports++;
      issues.push(`❌ ${relativePath} - Still importing MSALAuthProvider`);
    }

    // Check for AuthProvider imports
    if (content.includes('from "@/components/auth/AuthProvider"') ||
        content.includes('from "./AuthProvider"')) {
      authProviderImports++;
    }

    // Check for UnifiedAuthProvider imports
    if (content.includes('from "@/components/auth/UnifiedAuthProvider"') ||
        content.includes('from "./UnifiedAuthProvider"')) {
      unifiedImports++;
    }
  }

  console.log('📊 Import Analysis:');
  console.log(`   - MSALAuthProvider imports: ${msalImports}`);
  console.log(`   - AuthProvider imports: ${authProviderImports}`);
  console.log(`   - UnifiedAuthProvider imports: ${unifiedImports}`);
  console.log(`   - Total files scanned: ${files.length}\n`);

  if (issues.length > 0) {
    console.log('🚨 Issues Found:');
    issues.forEach(issue => console.log(`   ${issue}`));
    console.log('');
  }

  // Check if MSALAuthProvider.tsx still exists
  const msalProviderPath = path.join(srcDir, 'components', 'auth', 'MSALAuthProvider.tsx');
  const msalExists = fs.existsSync(msalProviderPath);

  console.log('🏗️  Architecture Files:');
  console.log(`   - MSALAuthProvider.tsx exists: ${msalExists ? '✅ (compatibility shim)' : '❌'}`);
  console.log(`   - AuthProvider.tsx exists: ${fs.existsSync(path.join(srcDir, 'components', 'auth', 'AuthProvider.tsx')) ? '✅' : '❌'}`);
  console.log(`   - UnifiedAuthProvider.tsx exists: ${fs.existsSync(path.join(srcDir, 'components', 'auth', 'UnifiedAuthProvider.tsx')) ? '✅' : '❌'}`);

  // Check if MSALAuthProvider is a compatibility shim
  if (msalExists) {
    const msalContent = fs.readFileSync(msalProviderPath, 'utf8');
    const isCompatibilityShim = msalContent.includes('UnifiedAuthProvider') &&
                                msalContent.includes('backward compatibility');
    console.log(`   - MSALAuthProvider is compatibility shim: ${isCompatibilityShim ? '✅' : '❌'}`);
  }

  console.log('\n🎯 Phase 1 Status:');
  if (msalImports === 0 && authProviderImports > 0) {
    console.log('✅ Phase 1 COMPLETE: All imports successfully migrated to AuthProvider');
  } else if (msalImports > 0) {
    console.log('🟡 Phase 1 IN PROGRESS: Some imports still need migration');
  } else {
    console.log('❌ Phase 1 FAILED: Issues detected in authentication setup');
  }

  return {
    complete: msalImports === 0 && authProviderImports > 0,
    msalImports,
    authProviderImports,
    issues
  };
}

// Run validation
const result = validatePhase1();
process.exit(result.complete ? 0 : 1);
