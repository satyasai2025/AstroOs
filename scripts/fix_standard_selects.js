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

for (const file of files) {
  let content = fs.readFileSync(file, 'utf8');
  let original = content;

  // If a file has <Select ...> and later </select>, change <Select to <select
  // Or if it contains <option
  content = content.replace(/<Select\b([^>]*?)(?=>[\s\S]*?<\/select>)/gi, (match, attrs) => {
    return `<select${attrs}`;
  });

  if (content !== original) {
    fs.writeFileSync(file, content, 'utf8');
    console.log(`Fixed standard select in: ${path.relative(process.cwd(), file)}`);
  }
}
