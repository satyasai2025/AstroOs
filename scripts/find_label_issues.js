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
const labelViolations = [];

for (const file of files) {
  const content = fs.readFileSync(file, 'utf8');

  // Match native <input ...> and <textarea ...>
  const tagRegex = /<(input|textarea)\b([^>]*)\/?>/gi;
  let match;

  while ((match = tagRegex.exec(content)) !== null) {
    const tag = match[1];
    const attrs = match[2];

    // Check type="hidden" or type="button" or type="submit" or type="reset" or type="image"
    if (/type=["'](hidden|button|submit|reset|image)["']/i.test(attrs)) {
      continue;
    }

    const hasAriaLabel = /aria-label=/i.test(attrs);
    const hasAriaLabelledBy = /aria-labelledby=/i.test(attrs);
    const hasId = /id=/i.test(attrs);
    const hasTitle = /title=/i.test(attrs);

    // If it has no aria-label, aria-labelledby, or id (which could be linked to <label htmlFor=...>)
    if (!hasAriaLabel && !hasAriaLabelledBy && !hasId && !hasTitle) {
      const lines = content.substring(0, match.index).split('\n');
      labelViolations.push({
        file: path.relative(process.cwd(), file),
        line: lines.length,
        tag,
        snippet: match[0].replace(/\s+/g, ' ')
      });
    } else if (hasId && !hasAriaLabel && !hasAriaLabelledBy) {
      // Check if the id is actually referenced by a <label htmlFor="..."> in the file
      const idMatch = attrs.match(/id=["']([^"']+)["']/i) || attrs.match(/id=\{([^}]+)\}/i);
      if (idMatch) {
        const idVal = idMatch[1];
        const labelRegex = new RegExp(`<label\\b[^>]*htmlFor=["'{]${idVal}["'}]`, 'i');
        if (!labelRegex.test(content) && !content.includes(`htmlFor={`) && !content.includes(`htmlFor=`)) {
          const lines = content.substring(0, match.index).split('\n');
          labelViolations.push({
            file: path.relative(process.cwd(), file),
            line: lines.length,
            tag,
            snippet: match[0].replace(/\s+/g, ' '),
            reason: `id="${idVal}" not linked to any <label htmlFor="...">`
          });
        }
      }
    }
  }
}

console.log(`Found ${labelViolations.length} form element label violations:\n`);
labelViolations.forEach(v => {
  console.log(`- ${v.file}:${v.line} -> <${v.tag}> ${v.reason || 'Missing accessible label (aria-label, aria-labelledby, or <label htmlFor>)'}`);
  console.log(`   ${v.snippet}\n`);
});
