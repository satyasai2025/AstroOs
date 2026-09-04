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

  // If a <select has options={ or label=, it was the custom <Select component from @/components/ui/Select
  const regex = /<select\b([^>]*?(?:options=\{|\blabel=)[^>]*?)>/gi;
  content = content.replace(regex, (match, attrs) => {
    // Clean any accidental aria-label="Selected chart id" etc if needed
    const cleanAttrs = attrs.replace(/\s*aria-label="[^"]*"/g, '');
    return `<Select${cleanAttrs}>`;
  });

  if (content !== original) {
    fs.writeFileSync(file, content, 'utf8');
    console.log(`Restored custom <Select> in: ${path.relative(process.cwd(), file)}`);
  }
}
