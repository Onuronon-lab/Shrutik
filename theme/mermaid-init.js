// Initialize Mermaid for mdBook
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Mermaid
    if (typeof mermaid !== 'undefined') {
        mermaid.initialize({
            startOnLoad: false,
            theme: 'dark',
            themeVariables: {
                primaryColor: '#2563eb',
                primaryTextColor: '#ffffff',
                primaryBorderColor: '#1e40af',
                lineColor: '#64748b',
                sectionBkgColor: '#1f2937',
                altSectionBkgColor: '#374151',
                gridColor: '#4b5563',
                secondaryColor: '#3b82f6',
                tertiaryColor: '#1e293b'
            }
        });

        // Find all mermaid code blocks and render them
        const mermaidBlocks = document.querySelectorAll('code.language-mermaid');
        mermaidBlocks.forEach((block, index) => {
            const graphDefinition = block.textContent;
            
            // Create a div to hold the rendered graph
            const graphDiv = document.createElement('div');
            graphDiv.className = 'mermaid';
            graphDiv.textContent = graphDefinition;
            graphDiv.style.textAlign = 'center';
            graphDiv.style.margin = '20px 0';
            
            // Replace the code block with the graph div
            block.parentNode.replaceWith(graphDiv);
        });

        // Render all mermaid diagrams
        mermaid.run();
    }
});