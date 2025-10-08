/**
 * Release Notes Management System
 * Handles displaying and managing release notes in the ImageCrop application
 */

class ReleaseNotesManager {
    constructor() {
        this.modal = null;
        this.currentVersion = null;
        this.currentNotes = null;
        this.translations = {};
        this.init();
    }

    init() {
        this.createModal();
        this.setupEventListeners();
    }

    createModal() {
        // Create modal HTML structure
        const modalHTML = `
            <div id="release-notes-modal" class="release-notes-modal">
                <div class="release-notes-content">
                    <div class="release-notes-header">
                        <div>
                            <h2 class="release-notes-title">Release Notes</h2>
                            <span class="release-notes-version" id="release-notes-version"></span>
                        </div>
                        <button class="release-notes-close" id="release-notes-close">&times;</button>
                    </div>
                    <div class="release-notes-body">
                        <div class="release-notes-tabs">
                            <button class="release-notes-tab active" data-tab="overview">Overview</button>
                            <button class="release-notes-tab" data-tab="changes">Changes</button>
                            <button class="release-notes-tab" data-tab="raw">Raw Notes</button>
                        </div>
                        <div id="release-notes-overview" class="release-notes-tab-content active">
                            <div id="release-notes-loading" class="release-notes-loading">
                                Loading release notes...
                            </div>
                        </div>
                        <div id="release-notes-changes" class="release-notes-tab-content">
                            <!-- Changes content will be populated here -->
                        </div>
                        <div id="release-notes-raw" class="release-notes-tab-content">
                            <!-- Raw content will be populated here -->
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Add modal to body
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        this.modal = document.getElementById('release-notes-modal');
    }

    setupEventListeners() {
        // Close modal events
        const closeBtn = document.getElementById('release-notes-close');
        closeBtn.addEventListener('click', () => this.closeModal());

        // Click outside to close
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.closeModal();
            }
        });

        // Escape key to close
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.modal.style.display === 'block') {
                this.closeModal();
            }
        });

        // Tab switching
        const tabs = document.querySelectorAll('.release-notes-tab');
        tabs.forEach(tab => {
            tab.addEventListener('click', () => this.switchTab(tab.dataset.tab));
        });
    }

    switchTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.release-notes-tab').forEach(tab => {
            tab.classList.toggle('active', tab.dataset.tab === tabName);
        });

        // Update tab content
        document.querySelectorAll('.release-notes-tab-content').forEach(content => {
            content.classList.toggle('active', content.id.includes(tabName));
        });
    }

    async showReleaseNotes(version = null) {
        this.currentVersion = version;
        this.openModal();
        this.showLoading();

        try {
            const url = version 
                ? `/api/release-notes/${version}`
                : '/api/release-notes/latest';
            
            const response = await fetch(url);
            const data = await response.json();

            if (response.ok && data.status === 'success') {
                this.currentNotes = data;
                this.renderReleaseNotes(data);
            } else {
                this.showError(data.message || 'Failed to load release notes');
            }
        } catch (error) {
            console.error('Error loading release notes:', error);
            this.showError('Network error loading release notes');
        }
    }

    renderReleaseNotes(data) {
        // Update version in header
        const versionElement = document.getElementById('release-notes-version');
        versionElement.textContent = `v${data.version}`;

        // Render overview tab
        this.renderOverview(data);
        
        // Render changes tab
        this.renderChanges(data);
        
        // Render raw tab
        this.renderRaw(data);
    }

    renderOverview(data) {
        const overviewContainer = document.getElementById('release-notes-overview');
        
        let html = '';

        // Meta information
        if (data.published_at || data.source) {
            html += '<div class="release-notes-meta">';
            if (data.published_at) {
                const date = new Date(data.published_at).toLocaleDateString();
                html += `<div class="release-notes-meta-item">📅 ${date}</div>`;
            }
            html += `<div class="release-notes-meta-item">📦 Source: ${data.source}</div>`;
            html += '</div>';
        }

        // Summary
        if (data.parsed && data.parsed.summary) {
            html += `
                <div class="release-notes-summary">
                    <h3>📋 Summary</h3>
                    <p>${this.escapeHtml(data.parsed.summary)}</p>
                </div>
            `;
        }

        // Highlights
        if (data.parsed && data.parsed.highlights && data.parsed.highlights.length > 0) {
            html += '<div class="release-notes-highlights">';
            html += '<h3>✨ Highlights</h3>';
            html += '<ul class="release-notes-list">';
            data.parsed.highlights.forEach(highlight => {
                html += `<li class="release-notes-item ${highlight.category}">${this.escapeHtml(highlight.text)}</li>`;
            });
            html += '</ul>';
            html += '</div>';
        }

        // Quick stats
        if (data.parsed && data.parsed.total_changes) {
            html += `
                <div class="release-notes-summary">
                    <h3>📊 Quick Stats</h3>
                    <p>Total changes: ${data.parsed.total_changes}</p>
                    <p>Highlights: ${data.parsed.highlights ? data.parsed.highlights.length : 0}</p>
                </div>
            `;
        }

        // Links
        html += '<div class="release-notes-links">';
        if (data.html_url) {
            html += `<a href="${data.html_url}" target="_blank" class="release-notes-link">View on GitHub</a>`;
        }
        if (data.download_url) {
            html += `<a href="${data.download_url}" target="_blank" class="release-notes-link secondary">Download</a>`;
        }
        html += '</div>';

        overviewContainer.innerHTML = html;
    }

    renderChanges(data) {
        const changesContainer = document.getElementById('release-notes-changes');
        
        if (!data.parsed || !data.parsed.sections || data.parsed.sections.length === 0) {
            changesContainer.innerHTML = '<div class="release-notes-error">No structured changes available</div>';
            return;
        }

        let html = '';
        data.parsed.sections.forEach(section => {
            html += '<div class="release-notes-section">';
            html += `<h2>${this.escapeHtml(section.title)}</h2>`;
            
            if (section.summary) {
                html += `<p>${this.escapeHtml(section.summary)}</p>`;
            }

            if (section.items && section.items.length > 0) {
                html += '<ul class="release-notes-list">';
                section.items.forEach(item => {
                    html += `<li class="release-notes-item ${item.category}">${this.escapeHtml(item.text)}</li>`;
                });
                html += '</ul>';
            }
            
            html += '</div>';
        });

        changesContainer.innerHTML = html;
    }

    renderRaw(data) {
        const rawContainer = document.getElementById('release-notes-raw');
        
        const content = data.body || data.content || 'No raw content available';
        
        // Simple markdown-like rendering
        let html = this.escapeHtml(content)
            .replace(/^### (.*$)/gim, '<h3>$1</h3>')
            .replace(/^## (.*$)/gim, '<h2>$1</h2>')
            .replace(/^# (.*$)/gim, '<h1>$1</h1>')
            .replace(/^\- (.*$)/gim, '<li>$1</li>')
            .replace(/^\* (.*$)/gim, '<li>$1</li>')
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br>');

        // Wrap consecutive <li> elements in <ul>
        html = html.replace(/(<li>.*?<\/li>)(?:\s*<li>.*?<\/li>)*/g, (match) => {
            return '<ul>' + match + '</ul>';
        });

        rawContainer.innerHTML = `<div style="line-height: 1.6;">${html}</div>`;
    }

    showLoading() {
        const overviewContainer = document.getElementById('release-notes-overview');
        overviewContainer.innerHTML = '<div class="release-notes-loading">Loading release notes...</div>';
        
        const changesContainer = document.getElementById('release-notes-changes');
        changesContainer.innerHTML = '<div class="release-notes-loading">Loading changes...</div>';
        
        const rawContainer = document.getElementById('release-notes-raw');
        rawContainer.innerHTML = '<div class="release-notes-loading">Loading content...</div>';
    }

    showError(message) {
        const errorHTML = `<div class="release-notes-error">❌ ${this.escapeHtml(message)}</div>`;
        
        document.getElementById('release-notes-overview').innerHTML = errorHTML;
        document.getElementById('release-notes-changes').innerHTML = errorHTML;
        document.getElementById('release-notes-raw').innerHTML = errorHTML;
    }

    openModal() {
        this.modal.style.display = 'block';
        document.body.style.overflow = 'hidden';
    }

    closeModal() {
        this.modal.style.display = 'none';
        document.body.style.overflow = '';
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    setTranslations(translations) {
        this.translations = translations;
    }
}

// Initialize release notes manager when DOM is loaded
let releaseNotesManager = null;

document.addEventListener('DOMContentLoaded', () => {
    releaseNotesManager = new ReleaseNotesManager();
});

// Export for external use
window.ReleaseNotesManager = ReleaseNotesManager;
window.showReleaseNotes = (version) => {
    if (releaseNotesManager) {
        releaseNotesManager.showReleaseNotes(version);
    }
};