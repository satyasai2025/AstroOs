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
let cleanedCount = 0;

for (const file of files) {
  let content = fs.readFileSync(file, 'utf8');
  let original = content;

  // Find aria-label="..." attributes containing CSS class strings like w-full, flex-1, bg-, rounded-, etc.
  content = content.replace(/aria-label=["'](w-full|flex-1|rounded|text-xs|bg-|border|px-|py-|outline-none)[^"']*["']/gi, (match) => {
    cleanedCount++;
    return 'aria-label="Input field"';
  });

  if (content !== original) {
    fs.writeFileSync(file, content, 'utf8');
    console.log(`Cleaned aria-labels in: ${path.relative(process.cwd(), file)}`);
  }
}

console.log(`\nCleaned ${cleanedCount} class-string aria-labels across codebase!`);
