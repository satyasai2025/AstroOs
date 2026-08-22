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
const nestedViolations = [];

for (const file of files) {
  const content = fs.readFileSync(file, 'utf8');

  // Match <a ...> ... </a> and <button ...> ... </button>
  const outerRegex = /<(a|button)\b([^>]*)>([\s\S]*?)<\/\1>/gi;
  let match;

  while ((match = outerRegex.exec(content)) !== null) {
    const outerTag = match[1];
    const outerAttrs = match[2];
    const innerHTML = match[3];

    // Check if innerHTML contains another <button>, <a href>, <input>, <select>, <textarea>
    const innerInteractiveMatch = innerHTML.match(/<(button|a\s+[^>]*href|input|select|textarea)\b([^>]*)/i);
    if (innerInteractiveMatch) {
      const lines = content.substring(0, match.index).split('\n');
      nestedViolations.push({
        file: path.relative(process.cwd(), file),
        line: lines.length,
        outerTag,
        innerTag: innerInteractiveMatch[1],
        snippet: match[0].replace(/\s+/g, ' ').substring(0, 120)
      });
    }
  }
}

console.log(`Found ${nestedViolations.length} nested-interactive violations:\n`);
nestedViolations.forEach(v => {
  console.log(`- ${v.file}:${v.line} -> Outer <${v.outerTag}> contains Inner <${v.innerTag}>`);
  console.log(`   ${v.snippet}\n`);
});
