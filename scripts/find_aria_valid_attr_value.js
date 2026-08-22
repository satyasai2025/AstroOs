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
const issues = [];

for (const file of files) {
  const content = fs.readFileSync(file, 'utf8');
  const lines = content.split('\n');

  lines.forEach((line, idx) => {
    const lineNum = idx + 1;

    // Pattern 1: aria-controls={someVar} where someVar could be undefined/null
    // aria-controls must be a valid ID reference
    const controlsMatch = line.match(/aria-controls=\{([^}]+)\}/);
    if (controlsMatch) {
      const expr = controlsMatch[1].trim();
      // If it's a template literal or conditional that could yield empty string
      if (expr.includes('`') || expr.includes('||') || expr.includes('&&') || expr.includes('?')) {
        issues.push({
          file: path.relative(process.cwd(), file),
          line: lineNum,
          attr: 'aria-controls',
          expr,
          reason: 'Could produce empty string or undefined (must be valid ID ref)'
        });
      }
    }

    // Pattern 2: aria-labelledby or aria-describedby with expression
    ['aria-labelledby', 'aria-describedby', 'aria-owns', 'aria-activedescendant'].forEach(attr => {
      const re = new RegExp(`${attr}=\\{([^}]+)\\}`);
      const m = line.match(re);
      if (m) {
        const expr = m[1].trim();
        if (!expr.startsWith('"') && !expr.startsWith("'")) {
          issues.push({
            file: path.relative(process.cwd(), file),
            line: lineNum,
            attr,
            expr,
            reason: 'Dynamic ID reference - could be empty/undefined at runtime'
          });
        }
      }
    });

    // Pattern 3: aria-expanded/aria-selected on element without proper role
    // Check if aria-selected is on a <button> or <div> without role="tab" or role="option"
    if (line.includes('aria-selected=')) {
      // Check if this line or nearby lines have role="tab" or role="option" or role="gridcell"
      const contextStart = Math.max(0, idx - 5);
      const contextEnd = Math.min(lines.length - 1, idx + 5);
      const context = lines.slice(contextStart, contextEnd + 1).join(' ');
      if (!context.includes('role="tab"') && !context.includes('role="option"') && 
          !context.includes('role="gridcell"') && !context.includes('role="treeitem"') &&
          !context.includes('role="row"') && !context.includes('role="columnheader"') &&
          !context.includes('role="rowheader"')) {
        issues.push({
          file: path.relative(process.cwd(), file),
          line: lineNum,
          attr: 'aria-selected',
          expr: line.trim(),
          reason: 'aria-selected used without role="tab|option|gridcell|treeitem|row"'
        });
      }
    }

    // Pattern 4: aria-expanded with non-boolean expression that renders as string
    if (line.includes('aria-expanded={') || line.includes('aria-haspopup={')) {
      const m = line.match(/(aria-expanded|aria-haspopup)=\{([^}]+)\}/);
      if (m) {
        const expr = m[2].trim();
        // If expr is a variable name that could be a string not "true"/"false"
        if (m[1] === 'aria-haspopup' && !['true', 'false', '"true"', '"false"', '"menu"', '"listbox"', '"tree"', '"grid"', '"dialog"'].includes(expr)) {
          // Check if it's a JSX boolean expression
          if (!expr.includes('===') && !expr.includes('!==') && !expr.includes('?') && !expr.includes('!') && expr !== 'true' && expr !== 'false') {
            issues.push({
              file: path.relative(process.cwd(), file),
              line: lineNum,
              attr: m[1],
              expr,
              reason: `Expression may not produce valid value for ${m[1]}`
            });
          }
        }
      }
    }
  });
}

console.log(`\nFound ${issues.length} potential aria-valid-attr-value issues:\n`);
issues.forEach(iss => {
  console.log(`${iss.reason}`);
  console.log(`  File: ${iss.file}:${iss.line}`);
  console.log(`  Attr: ${iss.attr}`);
  console.log(`  Expr: ${iss.expr}\n`);
});
