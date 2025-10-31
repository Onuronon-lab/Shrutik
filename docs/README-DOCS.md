# Shrutik Documentation Setup

This directory contains the source files for the Shrutik documentation website, built with [mdBook](https://rust-lang.github.io/mdBook/).

## 📚 About mdBook

mdBook is a utility to create modern online books from Markdown files. It's similar to Gitiles or GitBook but focused on creating documentation from Markdown source files.

### Features

- **📖 Book-like structure** with chapters and sections
- **🔍 Built-in search** functionality
- **📱 Mobile-friendly** responsive design
- **🎨 Syntax highlighting** for code blocks
- **🔗 Cross-references** and internal linking
- **📋 Copy buttons** for code examples
- **🌙 Dark/light themes**
- **📊 MathJax support** (if needed)
- **🚀 Fast static site generation**

## 🛠️ Setup

### Prerequisites

Install mdBook using one of these methods:

#### Option 1: Using Cargo (Rust)
```bash
# Install Rust if you haven't already
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Install mdBook
cargo install mdbook
```

#### Option 2: Pre-built Binaries
Download from [mdBook releases](https://github.com/rust-lang/mdBook/releases)

#### Option 3: Package Managers
```bash
# macOS with Homebrew
brew install mdbook

# Ubuntu/Debian
sudo apt install mdbook

# Arch Linux
sudo pacman -S mdbook
```

### Verify Installation
```bash
mdbook --version
```

## 🚀 Quick Start

### Using the Build Script (Recommended)
```bash
# Watch for changes and serve with live reload
./scripts/build-docs.sh

# Or specific commands
./scripts/build-docs.sh build    # Build static files
./scripts/build-docs.sh serve    # Serve locally
./scripts/build-docs.sh clean    # Clean build artifacts
./scripts/build-docs.sh test     # Test for issues
```

### Manual Commands
```bash
# Build the documentation
mdbook build

# Serve locally with live reload
mdbook serve --port 3000

# Test for broken links
mdbook test

# Clean build artifacts
rm -rf book/
```

## 📁 Directory Structure

```
docs/
├── SUMMARY.md              # Book structure and navigation
├── README.md               # Introduction page
├── getting-started.md      # Quick start guide
├── docker-local-setup.md   # Docker setup
├── local-development.md    # Local development
├── architecture.md         # System architecture
├── api-reference.md        # API documentation
├── contributing.md         # Contributing guide
├── troubleshooting.md      # Common issues
├── faq.md                  # Frequently asked questions
├── flowcharts/             # System flow diagrams
│   ├── README.md
│   ├── voice-recording-flow.md
│   ├── transcription-workflow.md
│   └── system-architecture.md
└── theme/                  # Custom styling
    ├── custom.css          # Custom CSS
    └── custom.js           # Custom JavaScript

book.toml                   # mdBook configuration
```

## ⚙️ Configuration

The `book.toml` file contains the mdBook configuration:

```toml
[book]
title = "Shrutik Documentation"
authors = ["Shrutik Team"]
description = "Complete documentation for Shrutik - Voice Data Collection Platform"
src = "docs"
language = "en"

[output.html]
default-theme = "navy"
git-repository-url = "https://github.com/Onuronon-lab/Shrutik"
edit-url-template = "https://github.com/Onuronon-lab/Shrutik/edit/main/docs/{path}"
additional-css = ["theme/custom.css"]
additional-js = ["theme/custom.js"]
```

## 🎨 Customization

### Custom CSS (`docs/theme/custom.css`)
- Shrutik branding colors
- Enhanced code block styling
- Callout boxes for notes/warnings
- Responsive design improvements
- Print-friendly styles

### Custom JavaScript (`docs/theme/custom.js`)
- Copy buttons for code blocks
- Enhanced navigation
- Search improvements
- Keyboard shortcuts (Ctrl+K for search)
- Table of contents generation

## 📝 Writing Documentation

### Markdown Features

mdBook supports standard Markdown plus:

```markdown
# Headers with auto-generated anchors

**Bold text** and *italic text*

`inline code` and code blocks:

```bash
# Commands with syntax highlighting
./scripts/build-docs.sh serve
```

> Blockquotes for important notes

- Bulleted lists
- [Internal links](getting-started.md)
- [External links](https://github.com/Onuronon-lab/Shrutik)

| Tables | Are | Supported |
|--------|-----|-----------|
| Col 1  | Col 2 | Col 3   |
```

### Custom Elements

Our custom CSS/JS adds support for:

```markdown
> **📋 Note**: This creates a blue info callout box

> **⚠️ Warning**: This creates a yellow warning box

> **✅ Success**: This creates a green success box

> **❌ Error**: This creates a red error box
```

### Navigation Structure

Edit `docs/SUMMARY.md` to modify the book structure:

```markdown
# Summary

[Introduction](README.md)

# Getting Started
- [Quick Start](getting-started.md)
- [Docker Setup](docker-local-setup.md)

# Advanced
- [Architecture](architecture.md)
- [API Reference](api-reference.md)
```

## 🚀 Deployment

### GitHub Pages (Automatic)

The documentation is automatically deployed to GitHub Pages via GitHub Actions (`.github/workflows/deploy-docs.yml`):

1. **Trigger**: Push to `main` branch with changes in `docs/` or `book.toml`
2. **Build**: GitHub Actions builds the documentation
3. **Deploy**: Automatically deploys to GitHub Pages
4. **URL**: Available at `https://onuronon-lab.github.io/Shrutik/`

### Manual Deployment

```bash
# Build the documentation
mdbook build

# Deploy the book/ directory to your web server
rsync -av book/ user@server:/var/www/docs/

# Or use any static site hosting service
```

### Custom Domain

To use a custom domain:

1. Add `CNAME` file to the `book/` directory
2. Configure DNS to point to GitHub Pages
3. Update `book.toml` with the custom domain

## 🔧 Development Workflow

### Adding New Pages

1. Create the Markdown file in `docs/`
2. Add it to `docs/SUMMARY.md`
3. Test locally with `./scripts/build-docs.sh`
4. Commit and push to trigger deployment

### Updating Existing Pages

1. Edit the Markdown file
2. Test locally with live reload
3. Commit and push changes

### Adding Images

```markdown
![Alt text](images/screenshot.png)
```

Store images in `docs/images/` directory.

### Cross-References

```markdown
See the [Getting Started](getting-started.md) guide.
Link to specific sections: [Docker Setup](docker-local-setup.md#prerequisites)
```

## 🧪 Testing

### Local Testing
```bash
# Test for broken links and other issues
./scripts/build-docs.sh test

# Or manually
mdbook test
```

### CI/CD Testing

The GitHub Actions workflow includes:
- **Build test**: Ensures the book builds without errors
- **Link checking**: Validates internal links
- **Markdown linting**: Checks markdown formatting
- **Spell checking**: Catches typos and spelling errors

## 📊 Analytics & Monitoring

### GitHub Pages Analytics

Monitor documentation usage through:
- GitHub repository insights
- GitHub Pages traffic analytics
- Custom analytics (if configured)

### User Feedback

Encourage feedback through:
- "Edit this page" links on each page
- GitHub Issues for documentation problems
- Discord community for questions

## 🤝 Contributing to Documentation

### Guidelines

1. **Clear and concise**: Write for your audience
2. **Examples**: Include practical examples
3. **Screenshots**: Add visuals when helpful
4. **Testing**: Test all commands and code examples
5. **Links**: Keep internal links up to date

### Review Process

1. Create a branch for documentation changes
2. Make your edits
3. Test locally with `./scripts/build-docs.sh`
4. Submit a pull request
5. Address review feedback
6. Merge and deploy automatically

## 🆘 Troubleshooting

### Common Issues

**mdBook not found**:
```bash
# Install mdBook
cargo install mdbook
```

**Build fails**:
```bash
# Check for syntax errors in Markdown
mdbook test

# Clean and rebuild
./scripts/build-docs.sh clean
./scripts/build-docs.sh build
```

**Broken links**:
```bash
# Test for broken links
mdbook test
```

**Styling issues**:
- Check `docs/theme/custom.css`
- Validate CSS syntax
- Test in different browsers

### Getting Help

- **mdBook Documentation**: https://rust-lang.github.io/mdBook/
- **GitHub Issues**: Report documentation problems
- **Discord Community**: Ask questions in real-time

---

## 🎉 Happy Documenting!

This setup provides a professional, maintainable documentation system for Shrutik. The combination of mdBook's features with our custom styling creates an excellent user experience for both readers and contributors.

**Questions?** Join our [Discord community](https://discord.gg/9hZ9eW8ARk) or [create an issue](https://github.com/Onuronon-lab/Shrutik/issues/new).