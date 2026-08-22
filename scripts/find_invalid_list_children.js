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
const violations = [];

for (const file of files) {
  const content = fs.readFileSync(file, 'utf8');

  // Check 1: <ul> or <ol> that directly contains <div>, <p>, <span>, <Link>, <a> without <li>
  // Match <(ul|ol)[^>]*>([\s\S]*?)<\/\1>
  const listRegex = /<(ul|ol)\b([^>]*)>([\s\S]*?)<\/\1>/gi;
  let match;
  while ((match = listRegex.exec(content)) !== null) {
    const listTag = match[1];
    const listAttrs = match[2];
    const listBody = match[3];

    // Check if listBody contains direct child tags other than <li>, { ... }, or whitespace
    // Remove comments
    const cleanBody = listBody.replace(/\{\/\*[\s\S]*?\*\/\}/g, '');
    
    // Find all immediate tags in body
    const directTags = cleanBody.match(/<([A-Za-z0-9_]+)/g) || [];
    for (const dt of directTags) {
      const tagName = dt.substring(1);
      // Valid list children in JSX can be li, or React components / map expressions
      if (['div', 'p', 'span', 'a', 'Link', 'button', 'header', 'footer', 'section', 'article'].includes(tagName)) {
        const lines = content.substring(0, match.index).split('\n');
        violations.push({
          file: path.relative(process.cwd(), file),
          line: lines.length,
          type: 'invalid_child_in_list',
          message: `<${listTag}> contains invalid child <${tagName}> (only <li> or role="listitem" allowed)`,
          snippet: match[0].slice(0, 150).replace(/\s+/g, ' ')
        });
      }
    }
  }
}

console.log(`Found ${violations.length} potential listitem violations:`);
violations.forEach(v => {
  console.log(`- ${v.file}:${v.line} -> ${v.message}`);
  console.log(`   ${v.snippet}\n`);
});
