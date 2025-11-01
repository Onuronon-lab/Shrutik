// Enhanced Mermaid Diagram Interactions for Shrutik Documentation

(function() {
    'use strict';
    
    // Wait for DOM to be ready
    function ready(fn) {
        if (document.readyState !== 'loading') {
            fn();
        } else {
            document.addEventListener('DOMContentLoaded', fn);
        }
    }
    
    // Initialize Mermaid with custom configuration
    function initMermaid() {
        if (typeof mermaid !== 'undefined') {
            mermaid.initialize({
                startOnLoad: true,
                theme: 'default',
                themeVariables: {
                    primaryColor: '#6366f1',
                    primaryTextColor: '#1f2937',
                    primaryBorderColor: '#4f46e5',
                    lineColor: '#6b7280',
                    secondaryColor: '#8b5cf6',
                    tertiaryColor: '#06b6d4',
                    background: '#ffffff',
                    mainBkg: '#ffffff',
                    secondBkg: '#f8fafc',
                    tertiaryBkg: '#f1f5f9'
                },
                flowchart: {
                    useMaxWidth: true,
                    htmlLabels: true,
                    curve: 'basis'
                },
                sequence: {
                    useMaxWidth: true,
                    wrap: true,
                    width: 150,
                    height: 65
                },
                gantt: {
                    useMaxWidth: true,
                    leftPadding: 75,
                    gridLineStartPadding: 35
                }
            });
        }
    }
    
    // Add zoom and pan functionality to Mermaid diagrams
    function enhanceMermaidDiagrams() {
        const mermaidElements = document.querySelectorAll('.mermaid');
        
        mermaidElements.forEach((element, index) => {
            // Skip if already enhanced
            if (element.classList.contains('enhanced')) return;
            
            // Mark as enhanced
            element.classList.add('enhanced');
            
            // Create container wrapper
            const container = document.createElement('div');
            container.className = 'mermaid-container';
            container.id = `mermaid-container-${index}`;
            
            // Wrap the mermaid element
            element.parentNode.insertBefore(container, element);
            container.appendChild(element);
            
            // Create zoom controls
            const controls = document.createElement('div');
            controls.className = 'mermaid-zoom-controls';
            controls.innerHTML = `
                <button class="zoom-btn zoom-in" title="Zoom In" data-action="zoom-in">+</button>
                <button class="zoom-btn zoom-out" title="Zoom Out" data-action="zoom-out">−</button>
                <button class="zoom-btn zoom-reset" title="Reset Zoom" data-action="zoom-reset">⌂</button>
                <button class="zoom-btn fullscreen" title="Fullscreen" data-action="fullscreen">⛶</button>
            `;
            
            container.appendChild(controls);
            
            // Initialize zoom state
            let scale = 1;
            let translateX = 0;
            let translateY = 0;
            let isDragging = false;
            let startX = 0;
            let startY = 0;
            
            // Apply transform
            function applyTransform() {
                element.style.transform = `translate(${translateX}px, ${translateY}px) scale(${scale})`;
                element.style.transformOrigin = 'center center';
            }
            
            // Zoom functions
            function zoomIn() {
                scale = Math.min(scale * 1.2, 3);
                applyTransform();
            }
            
            function zoomOut() {
                scale = Math.max(scale / 1.2, 0.5);
                applyTransform();
            }
            
            function resetZoom() {
                scale = 1;
                translateX = 0;
                translateY = 0;
                applyTransform();
            }
            
            function toggleFullscreen() {
                if (!document.fullscreenElement) {
                    container.requestFullscreen().catch(err => {
                        console.log(`Error attempting to enable fullscreen: ${err.message}`);
                    });
                } else {
                    document.exitFullscreen();
                }
            }
            
            // Event listeners for controls
            controls.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                
                const action = e.target.dataset.action;
                switch (action) {
                    case 'zoom-in':
                        zoomIn();
                        break;
                    case 'zoom-out':
                        zoomOut();
                        break;
                    case 'zoom-reset':
                        resetZoom();
                        break;
                    case 'fullscreen':
                        toggleFullscreen();
                        break;
                }
            });
            
            // Mouse wheel zoom
            container.addEventListener('wheel', (e) => {
                e.preventDefault();
                
                const rect = container.getBoundingClientRect();
                const centerX = rect.width / 2;
                const centerY = rect.height / 2;
                
                if (e.deltaY < 0) {
                    zoomIn();
                } else {
                    zoomOut();
                }
            });
            
            // Touch/Mouse drag to pan
            let startTranslateX = 0;
            let startTranslateY = 0;
            
            function startDrag(clientX, clientY) {
                isDragging = true;
                startX = clientX;
                startY = clientY;
                startTranslateX = translateX;
                startTranslateY = translateY;
                element.style.cursor = 'grabbing';
            }
            
            function drag(clientX, clientY) {
                if (!isDragging) return;
                
                const deltaX = clientX - startX;
                const deltaY = clientY - startY;
                
                translateX = startTranslateX + deltaX;
                translateY = startTranslateY + deltaY;
                
                applyTransform();
            }
            
            function endDrag() {
                isDragging = false;
                element.style.cursor = 'grab';
            }
            
            // Mouse events
            element.addEventListener('mousedown', (e) => {
                if (scale > 1) {
                    e.preventDefault();
                    startDrag(e.clientX, e.clientY);
                }
            });
            
            document.addEventListener('mousemove', (e) => {
                if (isDragging) {
                    drag(e.clientX, e.clientY);
                }
            });
            
            document.addEventListener('mouseup', endDrag);
            
            // Touch events
            element.addEventListener('touchstart', (e) => {
                if (e.touches.length === 1 && scale > 1) {
                    e.preventDefault();
                    const touch = e.touches[0];
                    startDrag(touch.clientX, touch.clientY);
                }
            });
            
            element.addEventListener('touchmove', (e) => {
                if (e.touches.length === 1 && isDragging) {
                    e.preventDefault();
                    const touch = e.touches[0];
                    drag(touch.clientX, touch.clientY);
                }
            });
            
            element.addEventListener('touchend', (e) => {
                if (e.touches.length === 0) {
                    endDrag();
                }
            });
            
            // Double-click to reset
            element.addEventListener('dblclick', (e) => {
                e.preventDefault();
                resetZoom();
            });
            
            // Keyboard shortcuts
            document.addEventListener('keydown', (e) => {
                if (container.matches(':hover') || document.fullscreenElement === container) {
                    switch (e.key) {
                        case '+':
                        case '=':
                            e.preventDefault();
                            zoomIn();
                            break;
                        case '-':
                            e.preventDefault();
                            zoomOut();
                            break;
                        case '0':
                            e.preventDefault();
                            resetZoom();
                            break;
                        case 'f':
                        case 'F':
                            if (e.ctrlKey || e.metaKey) {
                                e.preventDefault();
                                toggleFullscreen();
                            }
                            break;
                        case 'Escape':
                            if (document.fullscreenElement) {
                                document.exitFullscreen();
                            }
                            break;
                    }
                }
            });
            
            // Fullscreen change handler
            document.addEventListener('fullscreenchange', () => {
                const fullscreenBtn = controls.querySelector('.fullscreen');
                if (document.fullscreenElement === container) {
                    fullscreenBtn.innerHTML = '⛶';
                    fullscreenBtn.title = 'Exit Fullscreen';
                    container.classList.add('fullscreen-active');
                } else {
                    fullscreenBtn.innerHTML = '⛶';
                    fullscreenBtn.title = 'Fullscreen';
                    container.classList.remove('fullscreen-active');
                }
            });
            
            // Add tooltip for interaction hints
            const tooltip = document.createElement('div');
            tooltip.className = 'mermaid-tooltip';
            tooltip.innerHTML = `
                <div style="font-size: 0.75rem; color: #6b7280; text-align: center; margin-top: 0.5rem;">
                    💡 <strong>Tip:</strong> Use mouse wheel to zoom, drag to pan, double-click to reset
                </div>
            `;
            container.appendChild(tooltip);
        });
    }
    
    // Add custom styles for fullscreen mode
    function addFullscreenStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .mermaid-container.fullscreen-active {
                background: white;
                padding: 2rem;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .mermaid-container.fullscreen-active .mermaid {
                max-width: 90vw;
                max-height: 90vh;
                margin: 0;
            }
            
            .mermaid-tooltip {
                opacity: 0.7;
                transition: opacity 0.3s ease;
            }
            
            .mermaid-container:hover .mermaid-tooltip {
                opacity: 1;
            }
            
            @media (max-width: 768px) {
                .mermaid-tooltip {
                    display: none;
                }
            }
        `;
        document.head.appendChild(style);
    }
    
    // Initialize everything when DOM is ready
    ready(() => {
        initMermaid();
        addFullscreenStyles();
        
        // Initial enhancement
        enhanceMermaidDiagrams();
        
        // Re-enhance when new content is loaded (for SPA navigation)
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'childList') {
                    mutation.addedNodes.forEach((node) => {
                        if (node.nodeType === Node.ELEMENT_NODE) {
                            if (node.classList && node.classList.contains('mermaid')) {
                                setTimeout(enhanceMermaidDiagrams, 100);
                            } else if (node.querySelector && node.querySelector('.mermaid')) {
                                setTimeout(enhanceMermaidDiagrams, 100);
                            }
                        }
                    });
                }
            });
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    });
    
    // Export for manual initialization if needed
    window.ShrutikDocs = {
        enhanceMermaidDiagrams: enhanceMermaidDiagrams,
        initMermaid: initMermaid
    };
})();