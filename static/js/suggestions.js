// Suggestions Management Module
class SuggestionsManager {
    constructor() {
        this.suggestions = [];
        this.currentFilters = {
            status: '',
            category: ''
        };
        
        this.initializeElements();
        this.bindEvents();
        this.loadSuggestions();
        this.loadSuggestionStats();
    }
    
    initializeElements() {
        // Main elements
        this.generateBtn = document.getElementById('generate-suggestions-btn');
        this.suggestionsFilter = document.getElementById('suggestions-filter');
        this.categoryFilter = document.getElementById('category-filter');
        this.suggestionsList = document.getElementById('suggestions-list');
        this.noSuggestions = document.getElementById('no-suggestions');
        
        // Stats elements
        this.totalSuggestions = document.getElementById('total-suggestions');
        this.pendingSuggestions = document.getElementById('pending-suggestions');
        this.implementedSuggestions = document.getElementById('implemented-suggestions');
        this.implementationRate = document.getElementById('implementation-rate');
    }
    
    bindEvents() {
        // Generate button
        this.generateBtn?.addEventListener('click', () => this.generateSuggestions());
        
        // Filters
        this.suggestionsFilter?.addEventListener('change', (e) => this.applyFilters());
        this.categoryFilter?.addEventListener('change', (e) => this.applyFilters());
        
        // Listen for WebSocket suggestions updates
        if (window.wsManager) {
            window.wsManager.addMessageHandler('new_suggestions', (data) => {
                this.handleNewSuggestions(data);
            });
        }
    }
    
    async generateSuggestions() {
        if (!this.generateBtn) return;
        
        // Show loading state
        this.setGenerateButtonLoading(true);
        
        try {
            const response = await fetch('/api/suggestions/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            
            // Show success message
            showToast('Success', `Generated ${result.suggestions.length} new suggestions!`, 'success');
            
            // Reload suggestions and stats
            await this.loadSuggestions();
            await this.loadSuggestionStats();
            
            // Scroll to suggestions section
            document.querySelector('.suggestions-section')?.scrollIntoView({ behavior: 'smooth' });
            
        } catch (error) {
            console.error('Error generating suggestions:', error);
            showToast('Error', `Failed to generate suggestions: ${error.message}`, 'error');
        } finally {
            this.setGenerateButtonLoading(false);
        }
    }
    
    async loadSuggestions() {
        try {
            const params = new URLSearchParams();
            if (this.currentFilters.status) {
                params.append('status', this.currentFilters.status);
            }
            if (this.currentFilters.category) {
                params.append('category', this.currentFilters.category);
            }
            
            const response = await fetch(`/api/suggestions?${params.toString()}`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            this.suggestions = data.suggestions;
            this.displaySuggestions();
            
        } catch (error) {
            console.error('Error loading suggestions:', error);
            this.showNoSuggestions();
        }
    }
    
    async loadSuggestionStats() {
        try {
            const response = await fetch('/api/suggestions/stats');
            if (!response.ok) return;
            
            const stats = await response.json();
            this.updateStatsDisplay(stats);
            
        } catch (error) {
            console.error('Error loading suggestion stats:', error);
        }
    }
    
    displaySuggestions() {
        if (!this.suggestionsList) return;
        
        if (this.suggestions.length === 0) {
            this.showNoSuggestions();
            return;
        }
        
        this.hideNoSuggestions();
        this.suggestionsList.innerHTML = '';
        
        this.suggestions.forEach(suggestion => {
            const suggestionElement = this.createSuggestionElement(suggestion);
            this.suggestionsList.appendChild(suggestionElement);
        });
    }
    
    createSuggestionElement(suggestion) {
        const div = document.createElement('div');
        div.className = `suggestion-card ${suggestion.priority}-priority ${suggestion.status}`;
        div.setAttribute('data-id', suggestion.id);
        
        const categoryClass = suggestion.category.replace(/_/g, '-');
        const priorityIcon = this.getPriorityIcon(suggestion.priority);
        const statusBadge = this.getStatusBadge(suggestion.status);
        const impactIcon = this.getImpactIcon(suggestion.impact_score);
        
        div.innerHTML = `
            <div class=\"suggestion-header\">
                <div class=\"suggestion-meta\">
                    <span class=\"category-badge ${categoryClass}\">${this.formatCategory(suggestion.category)}</span>
                    <span class=\"priority-badge ${suggestion.priority}\">${priorityIcon} ${suggestion.priority.toUpperCase()}</span>
                    ${statusBadge}
                </div>
                <div class=\"suggestion-actions\">
                    <button class=\"btn-icon\" onclick=\"suggestionsManager.toggleSuggestion('${suggestion.id}')\">
                        <i class=\"fas fa-chevron-down\"></i>
                    </button>
                </div>
            </div>
            
            <div class=\"suggestion-content\">
                <h3 class=\"suggestion-title\">${suggestion.title}</h3>
                <p class=\"suggestion-description\">${suggestion.description}</p>
                
                <div class=\"suggestion-metrics\">
                    <div class=\"metric\">
                        <i class=\"fas fa-bullseye\"></i>
                        <span>Impact: ${suggestion.impact_score}/100 ${impactIcon}</span>
                    </div>
                    <div class=\"metric\">
                        <i class=\"fas fa-clock\"></i>
                        <span>Effort: ${this.formatEffort(suggestion.effort_estimate)}</span>
                    </div>
                    <div class=\"metric\">
                        <i class=\"fas fa-calendar\"></i>
                        <span>Generated: ${this.formatDate(suggestion.generated_at)}</span>
                    </div>
                </div>
            </div>
            
            <div class=\"suggestion-details\" style=\"display: none;\">
                <div class=\"expected-outcome\">
                    <h4><i class=\"fas fa-target\"></i> Expected Outcome</h4>
                    <p>${suggestion.expected_outcome || 'No specific outcome defined.'}</p>
                </div>
                
                <div class=\"action-items\">
                    <h4><i class=\"fas fa-tasks\"></i> Action Items</h4>
                    ${this.renderActionItems(suggestion.action_items)}
                </div>
                
                <div class=\"suggestion-status-controls\">
                    <h4><i class=\"fas fa-cog\"></i> Status Management</h4>
                    <div class=\"status-buttons\">
                        <button class=\"btn btn-outline ${suggestion.status === 'pending' ? 'active' : ''}\" 
                                onclick=\"suggestionsManager.updateSuggestionStatus('${suggestion.id}', 'pending')\">
                            <i class=\"fas fa-clock\"></i> Pending
                        </button>
                        <button class=\"btn btn-outline ${suggestion.status === 'in_progress' ? 'active' : ''}\" 
                                onclick=\"suggestionsManager.updateSuggestionStatus('${suggestion.id}', 'in_progress')\">
                            <i class=\"fas fa-play\"></i> In Progress
                        </button>
                        <button class=\"btn btn-success ${suggestion.status === 'implemented' ? 'active' : ''}\" 
                                onclick=\"suggestionsManager.updateSuggestionStatus('${suggestion.id}', 'implemented')\">
                            <i class=\"fas fa-check\"></i> Implemented
                        </button>
                        <button class=\"btn btn-secondary ${suggestion.status === 'dismissed' ? 'active' : ''}\" 
                                onclick=\"suggestionsManager.updateSuggestionStatus('${suggestion.id}', 'dismissed')\">
                            <i class=\"fas fa-times\"></i> Dismissed
                        </button>
                    </div>
                    
                    <div class=\"notes-section\">
                        <textarea placeholder=\"Add notes about this suggestion...\" 
                                  id=\"notes-${suggestion.id}\" 
                                  class=\"form-textarea\">${suggestion.notes || ''}</textarea>
                    </div>
                </div>
            </div>
        `;
        
        return div;
    }
    
    toggleSuggestion(suggestionId) {
        const suggestionCard = document.querySelector(`[data-id="${suggestionId}"]`);
        if (!suggestionCard) return;
        
        const details = suggestionCard.querySelector('.suggestion-details');
        const chevron = suggestionCard.querySelector('.fa-chevron-down');
        
        if (details.style.display === 'none' || !details.style.display) {
            details.style.display = 'block';
            chevron.className = 'fas fa-chevron-up';
            suggestionCard.classList.add('expanded');
        } else {
            details.style.display = 'none';
            chevron.className = 'fas fa-chevron-down';
            suggestionCard.classList.remove('expanded');
        }
    }
    
    async updateSuggestionStatus(suggestionId, status) {
        try {
            const notesTextarea = document.getElementById(`notes-${suggestionId}`);
            const notes = notesTextarea?.value || '';
            
            const response = await fetch(`/api/suggestions/${suggestionId}/status`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ status, notes })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            showToast('Success', result.message, 'success');
            
            // Reload suggestions and stats
            await this.loadSuggestions();
            await this.loadSuggestionStats();
            
        } catch (error) {
            console.error('Error updating suggestion status:', error);
            showToast('Error', `Failed to update suggestion: ${error.message}`, 'error');
        }
    }
    
    applyFilters() {
        this.currentFilters.status = this.suggestionsFilter?.value || '';
        this.currentFilters.category = this.categoryFilter?.value || '';
        this.loadSuggestions();
    }
    
    updateStatsDisplay(stats) {
        if (this.totalSuggestions) {
            this.totalSuggestions.textContent = stats.total_suggestions || 0;
        }
        
        if (this.pendingSuggestions) {
            this.pendingSuggestions.textContent = stats.status_breakdown?.pending || 0;
        }
        
        if (this.implementedSuggestions) {
            this.implementedSuggestions.textContent = stats.status_breakdown?.implemented || 0;
        }
        
        if (this.implementationRate) {
            this.implementationRate.textContent = `${stats.implementation_rate || 0}%`;
        }
    }
    
    handleNewSuggestions(data) {
        showToast('New Suggestions', `${data.count} new suggestions generated!`, 'info');
        this.loadSuggestions();
        this.loadSuggestionStats();
    }
    
    showNoSuggestions() {
        if (this.suggestionsList) this.suggestionsList.style.display = 'none';
        if (this.noSuggestions) this.noSuggestions.style.display = 'block';
    }
    
    hideNoSuggestions() {
        if (this.suggestionsList) this.suggestionsList.style.display = 'block';
        if (this.noSuggestions) this.noSuggestions.style.display = 'none';
    }
    
    setGenerateButtonLoading(loading) {
        if (!this.generateBtn) return;
        
        if (loading) {
            this.generateBtn.disabled = true;
            this.generateBtn.innerHTML = '<i class=\"fas fa-spinner fa-spin\"></i> Generating...';
        } else {
            this.generateBtn.disabled = false;
            this.generateBtn.innerHTML = '<i class=\"fas fa-magic\"></i> Generate New Suggestions';
        }
    }
    
    // Helper methods
    formatCategory(category) {
        return category.split('_').map(word => 
            word.charAt(0).toUpperCase() + word.slice(1)
        ).join(' ');
    }
    
    formatEffort(effort) {
        const effortMap = {
            'low': 'Low (1-2 weeks)',
            'medium': 'Medium (2-4 weeks)', 
            'high': 'High (1-2 months)'
        };
        return effortMap[effort] || effort;
    }
    
    formatDate(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffTime = Math.abs(now - date);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        
        if (diffDays === 1) return 'Today';
        if (diffDays === 2) return 'Yesterday';
        if (diffDays <= 7) return `${diffDays} days ago`;
        
        return date.toLocaleDateString();
    }
    
    getPriorityIcon(priority) {
        const icons = {
            'high': '<i class=\"fas fa-exclamation-triangle\"></i>',
            'medium': '<i class=\"fas fa-info-circle\"></i>',
            'low': '<i class=\"fas fa-dot-circle\"></i>'
        };
        return icons[priority] || '';
    }
    
    getStatusBadge(status) {
        const badges = {
            'pending': '<span class=\"status-badge pending\"><i class=\"fas fa-clock\"></i> Pending</span>',
            'in_progress': '<span class=\"status-badge in-progress\"><i class=\"fas fa-play\"></i> In Progress</span>',
            'implemented': '<span class=\"status-badge implemented\"><i class=\"fas fa-check\"></i> Implemented</span>',
            'dismissed': '<span class=\"status-badge dismissed\"><i class=\"fas fa-times\"></i> Dismissed</span>'
        };
        return badges[status] || '';
    }
    
    getImpactIcon(score) {
        if (score >= 80) return '🔥';
        if (score >= 60) return '⭐';
        if (score >= 40) return '📈';
        return '📊';
    }
    
    renderActionItems(items) {
        if (!items || items.length === 0) {
            return '<p>No specific action items defined.</p>';
        }
        
        const listItems = items.map(item => `<li>${item}</li>`).join('');
        return `<ul class=\"action-items-list\">${listItems}</ul>`;
    }
}

// Global function for generating suggestions (called from HTML)
function generateSuggestions() {
    if (window.suggestionsManager) {
        window.suggestionsManager.generateSuggestions();
    }
}

// Initialize suggestions manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.suggestionsManager = new SuggestionsManager();
});
