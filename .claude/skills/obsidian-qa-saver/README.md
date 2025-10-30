# Obsidian Q&A Saver Skill

Save Q&A conversations to Obsidian notes with proper formatting, metadata, and organization.

## Quick Start

When you want to save a conversation to Obsidian, simply say:

- "Save this conversation to Obsidian"
- "Export this explanation to my notes"
- "Can you save that to my Obsidian vault?"

Claude will ask you:
1. Where to save it (folder/project)
2. What to title the note
3. What tags to add

Then it will automatically format and save the note with proper metadata.

## What This Skill Does

- ✅ Converts Q&A dialogue into document-style notes
- ✅ Adds YAML frontmatter with timestamps and tags
- ✅ Creates project links to related notes
- ✅ Organizes notes into topic/project folders
- ✅ Preserves code blocks with syntax highlighting
- ✅ Generates searchable, reference-ready content

## Example Usage

**User:** "Save our discussion about Python `__init__.py` files to Obsidian"

**Claude will:**
1. Ask: "What project folder should this go in?"
2. Suggest title: "Understanding Python __init__.py Files"
3. Extract and format the Q&A as an article
4. Add tags: `#python`, `#modules`, `#fundamentals`
5. Save to: `{Vault}/Python Learning/Understanding Python __init__.py Files.md`
6. Confirm: "✓ Saved to your Obsidian vault"

## File Structure

```
obsidian-qa-saver/
├── SKILL.md                           # Main skill documentation
├── scripts/
│   └── save_to_obsidian.py           # Python script for saving notes
├── assets/
│   └── obsidian-note-template.md     # Template for note structure
└── README.md                          # This file
```

## Script Usage

The `save_to_obsidian.py` script can be used standalone:

```bash
python scripts/save_to_obsidian.py \
  --vault-path "/path/to/obsidian/vault" \
  --folder "Python Learning" \
  --title "Understanding __init__.py Files" \
  --content "# Content here..." \
  --tags "python,modules,fundamentals" \
  --links "[[Python Packages]],[[Project Structure]]"
```

## Configuration

The skill needs your Obsidian vault path. Claude will ask for it when first using the skill.

To find your vault path:
1. Open Obsidian
2. Go to Settings → Files & Links
3. Look for "Vault folder" path

## Features

### Content Transformation

Converts conversational Q&A:
```
User: How do __init__.py files work?
Assistant: __init__.py files tell Python that a directory is a package...
```

Into document-style notes:
```markdown
## How __init__.py Files Work

__init__.py files tell Python that a directory is a package. They serve several purposes:

### Making Directories Into Packages

[Formatted explanation with headers and structure]
```

### Metadata Management

Automatically adds:
- Creation timestamp
- Update timestamp
- Tags (lowercase, kebab-case)
- Project links
- Aliases (for alternative names)

### Organization

- **By Topic/Project**: Organizes into folders like "Python Learning", "Elios Project"
- **Smart Naming**: Creates descriptive, searchable titles
- **No Duplication**: Handles filename conflicts automatically

## Tips for Best Results

1. **Be Specific About Topics**: Say "Save this to my Elios Project notes" rather than just "Save this"
2. **Use Descriptive Titles**: Let Claude suggest a title based on content
3. **Add Context**: Mention related notes for automatic linking
4. **Review Tags**: Claude will suggest tags, but you can customize them

## Common Use Cases

- **Technical Explanations**: Save architecture discussions, code explanations
- **Project Decisions**: Document design choices and requirements
- **Learning Notes**: Capture educational content and tutorials
- **Setup Instructions**: Save configuration and setup steps
- **Code Snippets**: Archive useful code examples with explanations

## Troubleshooting

**Vault not found:**
- Provide the full path to your Obsidian vault
- Check the path in Obsidian settings

**File already exists:**
- Claude will suggest adding a timestamp
- Or choose a different title

**Script not working:**
- Ensure Python 3 is installed
- Check file permissions on vault folder

## Integration

Works well with other skills:
- **docs-seeker**: Save discovered documentation
- **chrome-devtools**: Save web scraping results
- **skill-creator**: Document skill development discussions

## Version

Version: 1.0.0
Created: 2025-01-31