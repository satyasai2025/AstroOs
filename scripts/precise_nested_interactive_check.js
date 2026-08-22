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

const interactiveElements = ['button', 'a', 'Link', 'input', 'select', 'textarea'];

files.forEach(file => {
  const content = fs.readFileSync(file, 'utf8');

  // Simple token based nesting detector for JSX
  // Match <(button|a|Link) and trace depth
  const regex = /<\/?([A-Za-z0-9_]+)(\s|>|\/)/g;
  let match;
  let stack = [];

  const lines = content.split('\n');

  function getLineCol(index) {
    const linesBefore = content.substring(0, index).split('\n');
    return { line: linesBefore.length, col: linesBefore[linesBefore.length - 1].length };
  }

  // Regex to find JSX elements
  const tagRegex = /<(\/)?([A-Za-z0-9_]+)([^>]*)(\/?)>/g;
  while ((match = tagRegex.exec(content)) !== null) {
    const isClosing = match[1] === '/';
    const tagName = match[2];
    const rest = match[3];
    const isSelfClosing = match[4] === '/' || rest.trim().endsWith('/');

    const isInteractive = ['button', 'a', 'Link'].includes(tagName);

    if (!isClosing && !isSelfClosing) {
      // Opening tag
      if (isInteractive) {
        // Check if stack already has an interactive element
        const parentInteractive = stack.find(s => ['button', 'a', 'Link'].includes(s.tag));
        if (parentInteractive) {
          const loc = getLineCol(match.index);
          console.log(`❌ Nested Interactive Found!`);
          console.log(`   File: ${path.relative(process.cwd(), file)}:${loc.line}`);
          console.log(`   Parent: <${parentInteractive.tag}> (opened line ${parentInteractive.line}) contains Child: <${tagName}>`);
          console.log(`   Snippet: ${match[0]}\n`);
        }
      }
      stack.push({ tag: tagName, line: getLineCol(match.index).line });
    } else if (isClosing) {
      // Find matching tag in stack from end
      for (let i = stack.length - 1; i >= 0; i--) {
        if (stack[i].tag === tagName) {
          stack.splice(i, 1);
          break;
        }
      }
    }
  }
});
