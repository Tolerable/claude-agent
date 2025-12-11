#!/usr/bin/env node
/**
 * Path Guard Hook for Claude Code
 *
 * PURPOSE: HARD BLOCK file operations outside allowed directories.
 * This ensures Claude CANNOT touch your main projects, only the research repo.
 *
 * SETUP:
 * 1. Copy this file to ~/.claude/hooks/path-guard.js
 * 2. Edit ALLOWED_PATHS and BLOCKED_PATHS for your system
 * 3. Add to your Claude settings.json:
 *    {
 *      "hooks": {
 *        "PreToolUse": [{
 *          "matcher": "Write|Edit|Bash",
 *          "command": "node ~/.claude/hooks/path-guard.js"
 *        }]
 *      }
 *    }
 *
 * HOW IT WORKS:
 * - Reads tool input from stdin (Claude passes this automatically)
 * - Checks if the file path is in allowed/blocked lists
 * - Outputs JSON: { "decision": "allow" } or { "decision": "block", "message": "..." }
 * - Claude CANNOT proceed if blocked - it's not a suggestion, it's a hard stop
 */

const fs = require('fs');
const path = require('path');

// ============================================================================
// CONFIGURE THESE FOR YOUR SYSTEM
// ============================================================================

// Paths Claude IS allowed to modify (your research repo clone)
const ALLOWED_PATHS = [
  // CHANGE THIS to your local claude-agent repo path
  'C:\\Users\\YourName\\Projects\\claude-agent\\',
  '/home/yourname/projects/claude-agent/',

  // Add other safe paths if needed
];

// Paths Claude is NEVER allowed to touch (your main work)
const BLOCKED_PATHS = [
  // CHANGE THESE to your important project paths
  'C:\\Users\\YourName\\Projects\\my-game\\',
  '/home/yourname/projects/my-game/',

  // Protect your Claude configs from being overwritten
  '~/.claude/CLAUDE.md',
  '~/.claude/settings.json',

  // Add any other critical paths
];

// ============================================================================
// HOOK LOGIC - Don't modify unless you know what you're doing
// ============================================================================

function expandPath(p) {
  // Expand ~ to home directory
  if (p.startsWith('~')) {
    const home = process.env.HOME || process.env.USERPROFILE;
    return path.join(home, p.slice(1));
  }
  return p;
}

function normalizePath(p) {
  // Normalize for comparison (handle Windows/Unix differences)
  return path.normalize(expandPath(p)).toLowerCase();
}

function isPathBlocked(filePath) {
  const normalized = normalizePath(filePath);

  // Check explicit blocks first
  for (const blocked of BLOCKED_PATHS) {
    if (normalized.startsWith(normalizePath(blocked))) {
      return { blocked: true, reason: `Path is in BLOCKED_PATHS: ${blocked}` };
    }
  }

  // Check if in allowed paths
  for (const allowed of ALLOWED_PATHS) {
    if (normalized.startsWith(normalizePath(allowed))) {
      return { blocked: false };
    }
  }

  // Default: BLOCK anything not explicitly allowed
  return { blocked: true, reason: 'Path not in ALLOWED_PATHS (default deny)' };
}

function extractFilePath(toolInput) {
  // Try to find file path from various tool input formats
  if (!toolInput) return null;

  // Direct file_path parameter (Write, Edit, Read tools)
  if (toolInput.file_path) return toolInput.file_path;

  // Command parameter (Bash tool) - try to extract paths
  if (toolInput.command) {
    // Look for obvious file paths in the command
    // This is a simplified check - you may want to enhance it
    const pathMatches = toolInput.command.match(/[A-Za-z]:\\[^\s"']+|\/[^\s"']+/g);
    if (pathMatches && pathMatches.length > 0) {
      // Return the first path found - could be enhanced to check all
      return pathMatches[0];
    }
  }

  return null;
}

async function main() {
  // Read tool input from stdin
  let input = '';
  for await (const chunk of process.stdin) {
    input += chunk;
  }

  let toolInput;
  try {
    toolInput = JSON.parse(input);
  } catch (e) {
    // Can't parse input, allow by default (might not be a file operation)
    console.log(JSON.stringify({ decision: 'allow' }));
    return;
  }

  const filePath = extractFilePath(toolInput);

  if (!filePath) {
    // No file path detected, allow (probably not a file operation)
    console.log(JSON.stringify({ decision: 'allow' }));
    return;
  }

  const result = isPathBlocked(filePath);

  if (result.blocked) {
    console.log(JSON.stringify({
      decision: 'block',
      message: `PATH GUARD: Operation blocked.\n\nPath: ${filePath}\nReason: ${result.reason}\n\nThis file is outside the allowed research project scope. If you need to modify files outside claude-agent/, ask your user first.`
    }));
  } else {
    console.log(JSON.stringify({ decision: 'allow' }));
  }
}

main().catch(err => {
  console.error('Path guard error:', err);
  // On error, block by default (fail safe)
  console.log(JSON.stringify({
    decision: 'block',
    message: `PATH GUARD ERROR: ${err.message}. Blocking operation for safety.`
  }));
});
