import email
from email import policy

with open(r"C:\Users\rkmau\Downloads\Graph Visualization for Planets – Figma Make.mhtml", 'rb') as f:
    msg = email.message_from_binary_file(f, policy=policy.default)

for part in msg.walk():
    if part.get_content_type() == 'text/html':
        content = part.get_content()
        # Save to a text file
        with open('parsed_figma.html', 'w', encoding='utf-8') as out:
            out.write(content)
        print("Extracted HTML payload")
