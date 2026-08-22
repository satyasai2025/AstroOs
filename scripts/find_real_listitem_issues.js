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
const listViolations = [];

for (const file of files) {
  const content = fs.readFileSync(file, 'utf8');

  // Find <ul> or <ol> that contains direct child non-li elements
  // Like <ul ...>\n  {something && <div...>} or <ul ...>\n  <div...>
  const ulRegex = /<(ul|ol)\b([^>]*)>([\s\S]*?)<\/\1>/gi;
  let match;

  while ((match = ulRegex.exec(content)) !== null) {
    const tag = match[1];
    const body = match[3];

    // Check if body has conditional fallback like <p> or <div> or <span> not wrapped in <li>
    const directNonLi = body.match(/\{[^}]*?\?\s*<(div|p|span|button|a)\b/gi);
    if (directNonLi) {
      const lines = content.substring(0, match.index).split('\n');
      listViolations.push({
        file: path.relative(process.cwd(), file),
        line: lines.length,
        message: `Conditional non-<li> element directly inside <${tag}>`,
        snippet: match[0].slice(0, 180).replace(/\s+/g, ' ')
      });
    }

    // Check if body directly starts with a tag other than <li> or {
    const directChildTag = /^\s*<(?!li|\/|!--|\{|React\.Fragment)([a-zA-Z0-9_]+)/m.exec(body);
    if (directChildTag) {
      const lines = content.substring(0, match.index).split('\n');
      listViolations.push({
        file: path.relative(process.cwd(), file),
        line: lines.length,
        message: `Direct <${directChildTag[1]}> tag directly inside <${tag}>`,
        snippet: match[0].slice(0, 180).replace(/\s+/g, ' ')
      });
    }
  }
}

console.log(`Found ${listViolations.length} direct listitem violations:`);
listViolations.forEach(v => {
  console.log(`- ${v.file}:${v.line} -> ${v.message}`);
  console.log(`   ${v.snippet}\n`);
});
