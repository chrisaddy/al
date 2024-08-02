Output demos/note-add.gif

Set Shell bash
Set FontSize 16
Set Width 1200
Set Height 600

# Set a simple prompt silently
Hide
    Type "export PS1='$ '" Enter
    Type 'clear' Enter
Show

# Type a command in the terminal.
Type 'al note add' Enter
Sleep 1s

Type 'i'
Type 'hello world'
Sleep 1s
Escape
Type 'ZZ' Enter
Sleep 500ms


Type 'al note search hello world' Enter

Sleep 5s
