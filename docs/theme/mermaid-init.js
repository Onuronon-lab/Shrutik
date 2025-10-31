// Initialize Mermaid for mdBook
document.addEventListener('DOMContentLoaded', function() {
    // Check if Mermaid is loaded
    if (typeof mermaid !== 'undefined') {
        // Configure Mermaid
        mermaid.initialize({
            startOnLoad: true,
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
            },
            flowchart: {
                useMaxWidth: true,
                htmlLabels: true,
                curve: 'basis'
            },
            sequence: {
                diagramMarginX: 50,
                diagramMarginY: 10,
                actorMargin: 50,
                width: 150,
                height: 65,
                boxMargin: 10,
                boxTextMargin: 5,
                noteMargin: 10,
                messageMargin: 35,
                mirrorActors: true,
                bottomMarginAdj: 1,
                useMaxWidth: true,
                rightAngles: false,
                showSequenceNumbers: false
            },
            gantt: {
                titleTopMargin: 25,
                barHeight: 20,
                fontSizeFactor: 1,
                fontSize: 11,
                gridLineStartPadding: 35,
                bottomPadding: 50,
                numberSectionStyles: 4
            }
        });

        // Find all code blocks with mermaid class and render them
        const mermaidBlocks = document.querySelectorAll('code.language-mermaid');
        mermaidBlocks.forEach((block, index) => {
            const graphDefinition = block.textContent;
            const graphId = 'mermaid-graph-' + index;
            
            // Create a div to hold the rendered graph
            const graphDiv = document.createElement('div');
            graphDiv.id = graphId;
            graphDiv.className = 'mermaid-graph';
            graphDiv.style.textAlign = 'center';
            graphDiv.style.margin = '20px 0';
            
            // Replace the code block with the graph div
            block.parentNode.replaceWith(graphDiv);
            
            // Render the mermaid graph
            try {
                mermaid.render(graphId + '-svg', graphDefinition, (svgCode) => {
                    graphDiv.innerHTML = svgCode;
                });
            } catch (error) {
                console.error('Mermaid rendering error:', error);
                graphDiv.innerHTML = '<p style="color: red;">Error rendering diagram: ' + error.message + '</p>';
            }
        });
    } else {
        console.warn('Mermaid library not loaded');
    }
});