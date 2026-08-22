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
const listIssues = [];

for (const file of files) {
  const content = fs.readFileSync(file, 'utf8');

  // Check 1: <ul> or <ol> directly containing <div> or <Link or <button or <a (without <li>)
  // Check 2: <li> inside <div> (without <ul>/<ol>)
  
  // Let's use simple token stack parser for JSX
  const tagRegex = /<(\/)?([A-Za-z0-9_]+)([^>]*)(\/?)>/g;
  let match;
  let stack = [];

  while ((match = tagRegex.exec(content)) !== null) {
    const isClosing = match[1] === '/';
    const tagName = match[2];
    const attrs = match[3];
    const isSelfClosing = match[4] === '/' || attrs.trim().endsWith('/');

    if (!isClosing && !isSelfClosing) {
      const parent = stack.length > 0 ? stack[stack.length - 1] : null;

      // Check if <li> is inside a non-list parent
      if (tagName === 'li') {
        if (!parent || !['ul', 'ol'].includes(parent.tag)) {
          const lines = content.substring(0, match.index).split('\n');
          listIssues.push({
            file: path.relative(process.cwd(), file),
            line: lines.length,
            type: 'orphaned_li',
            details: `<li> is direct child of <${parent ? parent.tag : 'root'}> instead of <ul> or <ol>`,
            snippet: match[0]
          });
        }
      }

      // Check if <ul> or <ol> directly contains invalid children (not <li> and not Fragment and not map callback)
      if (parent && ['ul', 'ol'].includes(parent.tag) && !['li', 'script', 'template'].includes(tagName)) {
        const lines = content.substring(0, match.index).split('\n');
        listIssues.push({
          file: path.relative(process.cwd(), file),
          line: lines.length,
          type: 'invalid_ul_child',
          details: `<${parent.tag}> directly contains <${tagName}> instead of <li>`,
          snippet: match[0]
        });
      }

      stack.push({ tag: tagName, line: content.substring(0, match.index).split('\n').length });
    } else if (isClosing) {
      for (let i = stack.length - 1; i >= 0; i--) {
        if (stack[i].tag === tagName) {
          stack.splice(i, 1);
          break;
        }
      }
    }
  }
}

console.log(`Found ${listIssues.length} list / listitem structure issues:`);
listIssues.forEach(iss => {
  console.log(`- [${iss.type}] ${iss.file}:${iss.line} -> ${iss.details}`);
  console.log(`   Snippet: ${iss.snippet.slice(0, 100)}`);
});
