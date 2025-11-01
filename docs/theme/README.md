# Shrutik Documentation Theme

This directory contains custom styling and interactive features for the Shrutik documentation site.

## Files

### `custom.css`
Enhanced styling for the mdBook documentation including:
- **Shrutik Brand Colors**: Custom color palette with gradients
- **Enhanced Typography**: Better readability and visual hierarchy
- **Interactive Elements**: Hover effects and transitions
- **Responsive Design**: Mobile-optimized layouts
- **Component Styling**: Enhanced tables, code blocks, blockquotes
- **Status Badges**: Color-coded badges for different content types

### `mermaid-zoom.js`
Interactive functionality for Mermaid diagrams:
- **Zoom Controls**: Mouse wheel and button controls
- **Pan Support**: Drag to move around zoomed diagrams
- **Fullscreen Mode**: View complex diagrams in fullscreen
- **Keyboard Shortcuts**: Quick zoom and navigation
- **Touch Support**: Mobile-friendly interactions
- **Auto-enhancement**: Automatically enhances all Mermaid diagrams

## Features

### 🎨 Visual Enhancements
- Gradient headers with Shrutik branding
- Improved sidebar navigation
- Enhanced search results
- Professional code block styling
- Better spacing and typography

### 🔧 Interactive Diagrams
- **Zoom**: Use mouse wheel or +/- buttons
- **Pan**: Drag to move around when zoomed
- **Reset**: Double-click or press '0' to reset
- **Fullscreen**: Click fullscreen button or press Ctrl+F
- **Mobile**: Touch-friendly controls

### 📱 Responsive Design
- Mobile-optimized layouts
- Touch-friendly interactions
- Proper scaling for all screen sizes

## Usage

The theme is automatically applied when building the documentation with mdBook. No additional setup required.

### Keyboard Shortcuts (when hovering over diagrams)
- `+` or `=`: Zoom in
- `-`: Zoom out  
- `0`: Reset zoom
- `Ctrl+F`: Toggle fullscreen
- `Escape`: Exit fullscreen

### Mouse/Touch Controls
- **Mouse wheel**: Zoom in/out
- **Drag**: Pan around (when zoomed)
- **Double-click**: Reset zoom
- **Touch**: Pinch to zoom, drag to pan

## Customization

To modify the theme:

1. Edit `custom.css` for visual styling
2. Edit `mermaid-zoom.js` for interactive behavior
3. Rebuild documentation with `mdbook build`

## Browser Support

- Modern browsers with ES6+ support
- Mobile browsers with touch events
- Fullscreen API support for fullscreen mode