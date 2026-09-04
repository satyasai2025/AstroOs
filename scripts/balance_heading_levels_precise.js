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
let totalAdjusted = 0;

for (const file of files) {
  let content = fs.readFileSync(file, 'utf8');
  let original = content;

  // 1. Convert full <h4 ...> ... </h4> to <h3 ...> ... </h3> when preceded by <h2
  // 2. Convert full <h3 ...> ... </h3> to <h2 ...> ... </h2> when preceded by <h1
  // We use precise matching on opening and closing tags simultaneously
  const tagBlockRegex = /<h([345])(\b[^>]*)>([\s\S]*?)<\/h\1>/gi;

  content = content.replace(tagBlockRegex, (fullMatch, tagNum, attrs, innerText) => {
    const level = parseInt(tagNum, 10);
    const targetLevel = level - 1; // Promote h3->h2, h4->h3, h5->h4
    return `<h${targetLevel}${attrs}>${innerText}</h${targetLevel}>`;
  });

  if (content !== original) {
    fs.writeFileSync(file, content, 'utf8');
    console.log(`Precise balanced heading tags in: ${path.relative(process.cwd(), file)}`);
    totalAdjusted++;
  }
}

console.log(`\nPrecise adjusted heading tags in ${totalAdjusted} files!`);
