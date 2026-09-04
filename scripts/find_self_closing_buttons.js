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
const selfClosingNonVoid = [];

for (const file of files) {
  const content = fs.readFileSync(file, 'utf8');
  // Match <button ... /> or <a ... /> across multiple lines
  const regex = /<(button|a|Link)\b([^>]*?)\/>/gs;
  let match;
  while ((match = regex.exec(content)) !== null) {
    const lines = content.substring(0, match.index).split('\n');
    selfClosingNonVoid.push({
      file: path.relative(process.cwd(), file),
      line: lines.length,
      tag: match[1],
      snippet: match[0]
    });
  }
}

console.log(`Found ${selfClosingNonVoid.length} self-closing non-void interactive tags:`);
selfClosingNonVoid.forEach(item => {
  console.log(`- ${item.file}:${item.line} <${item.tag} ... />`);
});
