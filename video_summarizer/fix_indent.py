
import sys

input_file = 'app.py'
output_file = 'app.py'

with open(input_file, 'r') as f:
    lines = f.readlines()

new_lines = []
deindent_mode = False
skip_next = False

for i, line in enumerate(lines):
    # Detection logic
    if "if adj_key not in st.session_state:" in line:
        new_lines.append(line)
        deindent_mode = True
        # The next line (705) MUST remain indented inside the if
        # So we append it as-is and skip processing it in next iteration
        # BUT wait, the loop continues.
        # line i+1 is `                        st.session_state[adj_key] = ...`
        # We append it now.
        if i + 1 < len(lines):
             new_lines.append(lines[i+1])
        skip_next = True
        continue
    
    if skip_next:
        skip_next = False
        continue
        
    if deindent_mode:
        # Check for end condition
        if "# Subtitle Editor (Smart Vizard Support)" in line:
            deindent_mode = False
            new_lines.append(line)
        else:
            # check if line is empty or just whitespace
            if not line.strip():
                new_lines.append(line)
            # De-indent by 4 spaces
            elif line.startswith("    "):
                new_lines.append(line[4:])
            else:
                layout_break = True # Should not happen unless logic error
                new_lines.append(line)
    else:
        new_lines.append(line)

with open(output_file, 'w') as f:
    f.writelines(new_lines)
print("Indentation fixed.")
