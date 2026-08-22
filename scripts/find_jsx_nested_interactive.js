const fs = require('fs');
const path = require('path');

function getAllFiles(dir, exts = ['.tsx', '.jsx']) {
  let files = [];
  for (const item of fs.readdirSync(dir)) {
    const full = path.join(dir, item);
    const stat = fs.statSync(full);
    if (stat.isDirectory()) {
      if (item !== 'node_modules' && item !== '.next' && item !== '.git') {
        files = files.concat(getAllFiles(full, exts));
      }
    } else if (exts.some(ext => item.endsWith(ext))) {
      files.push(full);
    }
  }
  return files;
}

const files = getAllFiles(path.resolve(__dirname, '../apps/web/src'));

console.log(`Checking ${files.length} JSX/TSX files for nested interactive elements...`);

const interactiveTags = ['button', 'a', 'Link', 'input', 'select', 'textarea'];

// Simple regex heuristics for nesting
for (const file of files) {
  const content = fs.readFileSync(file, 'utf8');
  
  // Look for <button ... <button or <button ... <a or <a ... <button or <Link ... <button or <button ... <Link or <Link ... <Link
  const lines = content.split('\n');
  
  // Find multiline JSX structures:
  // Check for <Link or <a or <button open, followed by child interactive elements before closing tag
  let stack = [];
  lines.forEach((line, idx) => {
    // Check quick single-line nested interactives:
    if (/<button[^>]*>.*<(button|a|Link)[^>]*>/i.test(line) ||
        /<(a|Link)[^>]*>.*<(button|a|Link)[^>]*>/i.test(line)) {
      console.log(`[Single Line Issue] ${path.relative(process.cwd(), file)}:${idx + 1}`);
      console.log(`   ${line.trim()}`);
    }
  });

  // Also check pattern where button contains button or Link contains button across multiple lines
  // We can do regex match on the whole file
  const nestedPatterns = [
    /<(button)[^>]*>([\s\S]*?)<\/\1>/gi,
    /<(Link|a)[^>]*>([\s\S]*?)<\/\1>/gi,
  ];

  for (const pattern of nestedPatterns) {
    let match;
    while ((match = pattern.exec(content)) !== null) {
      const parentTag = match[1];
      const innerContent = match[2];
      
      // Check if innerContent contains another interactive tag opening
      const innerMatch = /<(button|Link|a|input|select|textarea)(\s|>)/i.exec(innerContent);
      if (innerMatch) {
        // Calculate line number
        const lineNumber = content.substring(0, match.index).split('\n').length;
        console.log(`[Nested Issue] in ${path.relative(process.cwd(), file)}:Line ${lineNumber}`);
        console.log(`   Parent: <${parentTag}> contains child: <${innerMatch[1]}>`);
        console.log(`   Snippet: ${match[0].slice(0, 180).replace(/\s+/g, ' ')}...`);
      }
    }
  }
}
