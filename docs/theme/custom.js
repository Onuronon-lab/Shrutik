// Custom JavaScript for Shrutik Documentation

document.addEventListener('DOMContentLoaded', function() {
    // Add copy buttons to code blocks
    addCopyButtons();
    
    // Add callout boxes
    processCallouts();
    
    // Add badges
    processBadges();
    
    // Add custom navigation
    enhanceNavigation();
    
    // Add version info
    addVersionInfo();
});

function addCopyButtons() {
    const codeBlocks = document.querySelectorAll('pre code');
    
    codeBlocks.forEach(function(codeBlock) {
        const pre = codeBlock.parentNode;
        const button = document.createElement('button');
        
        button.className = 'copy-button';
        button.textContent = 'Copy';
        button.style.cssText = `
            position: absolute;
            top: 8px;
            right: 8px;
            background: #374151;
            color: white;
            border: none;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            cursor: pointer;
            opacity: 0;
            transition: opacity 0.2s;
        `;
        
        pre.style.position = 'relative';
        pre.appendChild(button);
        
        pre.addEventListener('mouseenter', function() {
            button.style.opacity = '1';
        });
        
        pre.addEventListener('mouseleave', function() {
            button.style.opacity = '0';
        });
        
        button.addEventListener('click', function() {
            const text = codeBlock.textContent;
            navigator.clipboard.writeText(text).then(function() {
                button.textContent = 'Copied!';
                button.style.background = '#10b981';
                
                setTimeout(function() {
                    button.textContent = 'Copy';
                    button.style.background = '#374151';
                }, 2000);
            });
        });
    });
}

function processCallouts() {
    const content = document.querySelector('.content');
    if (!content) return;
    
    // Process blockquotes and convert them to callouts
    const blockquotes = content.querySelectorAll('blockquote');
    
    blockquotes.forEach(function(blockquote) {
        const text = blockquote.textContent.trim();
        let type = 'info';
        
        if (text.includes('⚠️') || text.includes('Warning') || text.includes('warning')) {
            type = 'warning';
        } else if (text.includes('✅') || text.includes('Success') || text.includes('success')) {
            type = 'success';
        } else if (text.includes('❌') || text.includes('Error') || text.includes('error')) {
            type = 'error';
        }
        
        blockquote.className = `callout ${type}`;
    });
}

function processBadges() {
    const content = document.querySelector('.content');
    if (!content) return;
    
    // Convert text patterns to badges
    const badgePatterns = [
        { pattern: /\[NEW\]/g, class: 'success' },
        { pattern: /\[UPDATED\]/g, class: 'info' },
        { pattern: /\[DEPRECATED\]/g, class: 'warning' },
        { pattern: /\[REMOVED\]/g, class: 'error' },
        { pattern: /\[BETA\]/g, class: 'warning' },
        { pattern: /\[STABLE\]/g, class: 'success' }
    ];
    
    badgePatterns.forEach(function(badge) {
        content.innerHTML = content.innerHTML.replace(badge.pattern, function(match) {
            const text = match.slice(1, -1); // Remove brackets
            return `<span class="badge ${badge.class}">${text}</span>`;
        });
    });
}

function enhanceNavigation() {
    // Add smooth scrolling to anchor links
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    
    anchorLinks.forEach(function(link) {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Highlight current section in navigation
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
            if (entry.isIntersecting) {
                const id = entry.target.id;
                const navLink = document.querySelector(`a[href="#${id}"]`);
                if (navLink) {
                    // Remove active class from all nav links
                    document.querySelectorAll('.nav-chapters a').forEach(function(link) {
                        link.classList.remove('active');
                    });
                    // Add active class to current link
                    navLink.classList.add('active');
                }
            }
        });
    }, {
        rootMargin: '-20% 0px -80% 0px'
    });
    
    // Observe all headings
    document.querySelectorAll('h1, h2, h3').forEach(function(heading) {
        if (heading.id) {
            observer.observe(heading);
        }
    });
}

function addVersionInfo() {
    // Add version info to the footer
    const content = document.querySelector('.content');
    if (!content) return;
    
    const footer = document.createElement('footer');
    footer.innerHTML = `
        <div style="margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #e5e7eb; text-align: center; color: #6b7280; font-size: 0.875rem;">
            <p>
                📚 Shrutik Documentation • 
                <a href="https://github.com/Onuronon-lab/Shrutik" target="_blank" style="color: #2563eb;">GitHub</a> • 
                <a href="https://discord.gg/9hZ9eW8ARk" target="_blank" style="color: #2563eb;">Discord</a>
            </p>
            <p style="margin-top: 0.5rem; font-size: 0.75rem;">
                Built with ❤️ for the open-source community
            </p>
        </div>
    `;
    
    content.appendChild(footer);
}

// Add keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + K to focus search
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const searchInput = document.querySelector('#searchbar');
        if (searchInput) {
            searchInput.focus();
        }
    }
    
    // Escape to clear search
    if (e.key === 'Escape') {
        const searchInput = document.querySelector('#searchbar');
        if (searchInput && document.activeElement === searchInput) {
            searchInput.value = '';
            searchInput.blur();
        }
    }
});

// Add search enhancements
function enhanceSearch() {
    const searchInput = document.querySelector('#searchbar');
    if (!searchInput) return;
    
    // Add placeholder text
    searchInput.placeholder = 'Search documentation... (Ctrl+K)';
    
    // Add search suggestions
    let searchTimeout;
    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(function() {
            // Custom search logic could go here
            console.log('Searching for:', searchInput.value);
        }, 300);
    });
}

// Initialize search enhancements
document.addEventListener('DOMContentLoaded', enhanceSearch);

// Add table of contents for long pages
function addTableOfContents() {
    const content = document.querySelector('.content');
    if (!content) return;
    
    const headings = content.querySelectorAll('h2, h3, h4');
    if (headings.length < 3) return; // Only add TOC for pages with multiple headings
    
    const toc = document.createElement('div');
    toc.className = 'table-of-contents';
    toc.innerHTML = '<h3>Table of Contents</h3>';
    
    const tocList = document.createElement('ul');
    
    headings.forEach(function(heading, index) {
        if (!heading.id) {
            heading.id = 'heading-' + index;
        }
        
        const li = document.createElement('li');
        const a = document.createElement('a');
        a.href = '#' + heading.id;
        a.textContent = heading.textContent;
        a.className = 'toc-' + heading.tagName.toLowerCase();
        
        li.appendChild(a);
        tocList.appendChild(li);
    });
    
    toc.appendChild(tocList);
    
    // Insert TOC after the first heading
    const firstHeading = content.querySelector('h1');
    if (firstHeading && firstHeading.nextElementSibling) {
        firstHeading.parentNode.insertBefore(toc, firstHeading.nextElementSibling);
    }
}

// Add TOC styles
const tocStyles = `
.table-of-contents {
    background: #f8fafc;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 1rem;
    margin: 1rem 0;
}

.table-of-contents h3 {
    margin-top: 0;
    margin-bottom: 0.5rem;
    color: #374151;
}

.table-of-contents ul {
    margin: 0;
    padding-left: 1rem;
}

.table-of-contents li {
    margin: 0.25rem 0;
}

.table-of-contents a {
    text-decoration: none;
    color: #2563eb;
}

.table-of-contents a:hover {
    text-decoration: underline;
}

.table-of-contents .toc-h3 {
    padding-left: 1rem;
    font-size: 0.9em;
}

.table-of-contents .toc-h4 {
    padding-left: 2rem;
    font-size: 0.85em;
}
`;

// Add TOC styles to the page
const style = document.createElement('style');
style.textContent = tocStyles;
document.head.appendChild(style);

// Initialize TOC
document.addEventListener('DOMContentLoaded', addTableOfContents);