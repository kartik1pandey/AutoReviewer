// AutoReviewer Frontend - Backend Integration
// Automatically detect which backend is available

// Production backend URL - loaded from config.js
let API_URL = typeof PRODUCTION_BACKEND_URL !== 'undefined' && PRODUCTION_BACKEND_URL 
    ? PRODUCTION_BACKEND_URL 
    : 'http://localhost:5000';  // Fallback to localhost for development

let currentReport = null;  // Store full report for detail views

// Try to detect which backend is running
async function detectBackend() {
    const indicator = document.getElementById('backendIndicator');
    
    // If production backend URL is set, use it directly
    if (typeof PRODUCTION_BACKEND_URL !== 'undefined' && PRODUCTION_BACKEND_URL && PRODUCTION_BACKEND_URL !== '') {
        API_URL = PRODUCTION_BACKEND_URL;
        console.log('Using Production API:', PRODUCTION_BACKEND_URL);
        indicator.textContent = '🤖 Using Production Backend';
        indicator.style.color = '#10b981';
        
        // Verify backend is accessible
        try {
            const response = await fetch(`${API_URL}/api/status`);
            if (response.ok) {
                console.log('✅ Backend is accessible');
                return;
            }
        } catch (e) {
            console.warn('⚠️ Backend may be sleeping (Render free tier). First request will wake it up.');
            indicator.textContent = '⏳ Backend waking up (Render free tier)...';
            indicator.style.color = '#f59e0b';
        }
        return;
    }
    
    // Development mode - try localhost backends
    console.log('Development mode - checking localhost backends...');
    
    // Try CrewAI backend first (localhost)
    try {
        const response = await fetch('http://localhost:5001/api/status');
        if (response.ok) {
            API_URL = 'http://localhost:5001';
            console.log('Using CrewAI Backend (port 5001)');
            indicator.textContent = '🤖 Using CrewAI Backend (AI-Powered Analysis)';
            indicator.style.color = '#10b981';
            return;
        }
    } catch (e) {
        // CrewAI backend not available
    }
    
    // Try original backend
    try {
        const response = await fetch('http://localhost:5000/api/health');
        if (response.ok) {
            API_URL = 'http://localhost:5000';
            console.log('Using Original Backend (port 5000)');
            indicator.textContent = '⚡ Using Original Backend (Fast Analysis)';
            indicator.style.color = '#f59e0b';
            return;
        }
    } catch (e) {
        // Original backend not available
    }
    
    console.warn('No backend detected. Using default:', API_URL);
    indicator.textContent = '⚠️ Backend not detected - Please start the server';
    indicator.style.color = '#ef4444';
}

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    await detectBackend();  // Detect which backend is running
    setupEventListeners();
    checkBackendStatus();
});

function setupEventListeners() {
    const uploadSection = document.getElementById('uploadSection');
    const fileInput = document.getElementById('fileInput');
    
    // File input change
    fileInput.addEventListener('change', handleFileSelect);
    
    // Drag and drop
    uploadSection.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadSection.classList.add('dragover');
    });
    
    uploadSection.addEventListener('dragleave', () => {
        uploadSection.classList.remove('dragover');
    });
    
    uploadSection.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadSection.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            handleFileSelect({ target: fileInput });
        }
    });
}

async function checkBackendStatus() {
    try {
        // Use correct endpoint based on backend
        const endpoint = API_URL.includes('5001') ? '/api/status' : '/api/health';
        const response = await fetch(`${API_URL}${endpoint}`);
        const data = await response.json();
        console.log('Backend status:', data);
    } catch (error) {
        console.error('Backend not available:', error);
        // Don't show alert, just log - backend detection already handled this
    }
}

function handleFileSelect(event) {
    const file = event.target.files[0];
    
    if (!file) return;
    
    if (!file.name.endsWith('.pdf')) {
        alert('Please select a PDF file');
        return;
    }
    
    uploadPaper(file);
}

async function uploadPaper(file) {
    // Show loading
    document.getElementById('uploadSection').style.display = 'none';
    document.getElementById('loadingSection').classList.add('active');
    document.getElementById('resultSection').classList.remove('active');
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        // Use correct endpoint based on backend
        const endpoint = API_URL.includes('5001') ? '/api/review' : '/api/review/upload';
        
        const response = await fetch(`${API_URL}${endpoint}`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Handle different response formats
        if (data.report) {
            // Both backends return report in data.report
            displayResults(data.report);
        } else if (data.success) {
            // Fallback
            displayResults(data);
        } else {
            throw new Error(data.error || 'Review failed');
        }
    } catch (error) {
        console.error('Error:', error);
        alert(`Error: ${error.message}\n\nPlease make sure the backend server is running.`);
        resetForm();
    }
}

function displayResults(report) {
    // Store full report for detail views
    currentReport = report;
    
    // Hide loading, show results
    document.getElementById('loadingSection').classList.remove('active');
    document.getElementById('resultSection').classList.add('active');
    
    // Handle different report formats
    let assessment, metadata, agentReviews, paperData;
    
    if (report.final_assessment) {
        // CrewAI backend format
        assessment = parseFinalAssessment(report.final_assessment);
        metadata = report.paper_metadata || {};
        agentReviews = report.agent_reviews || {};
        paperData = report.paper_data || {};  // Full paper data
    } else {
        // Original backend format
        assessment = {
            overall_score: report.overall_score || 'N/A',
            recommendation: report.recommendation || 'N/A',
            detailed_scores: {
                novelty: report.novelty_score || 0,
                soundness: report.soundness_score || 0,
                experiments: report.experiments_score || 0,
                formatting: report.formatting_score || 0
            },
            issues: report.issues || []
        };
        metadata = {
            abstract_length: report.abstract_length || 0,
            sections_count: report.sections_count || 0,
            references_count: report.references_count || 0,
            figures_count: report.figures_count || 0,
            tables_count: report.tables_count || 0
        };
        agentReviews = report.agent_reviews || {};
        paperData = report.paper_data || {};
    }
    
    // Display overall score
    document.getElementById('overallScore').textContent = 
        typeof assessment.overall_score === 'number' ? 
        assessment.overall_score.toFixed(1) : assessment.overall_score;
    
    // Display recommendation
    const recommendationEl = document.getElementById('recommendation');
    const recommendation = assessment.recommendation || 'N/A';
    recommendationEl.textContent = recommendation;
    recommendationEl.className = 'recommendation ' + recommendation.toLowerCase().replace(/\s+/g, '-');
    
    // Display detailed scores
    displayDetailedScores(assessment.detailed_scores);
    
    // Display issues
    displayIssues(assessment.issues);
    
    // Display metadata with click handlers
    displayMetadata(metadata, paperData);
    
    // Display agent details with better formatting
    displayAgentDetails(agentReviews);
}

function parseFinalAssessment(assessmentText) {
    const result = {
        overall_score: null,
        recommendation: null,
        detailed_scores: {},
        issues: []
    };
    
    // Extract overall score
    const scoreMatch = assessmentText.match(/Overall Score:\*\*\s*([\d.]+)/i);
    if (scoreMatch) {
        result.overall_score = parseFloat(scoreMatch[1]).toFixed(1);
    }
    
    // Extract recommendation
    const recMatch = assessmentText.match(/Recommendation:\*\*\s*(\w+)/i);
    if (recMatch) {
        result.recommendation = recMatch[1];
    }
    
    // Extract detailed scores
    const noveltyMatch = assessmentText.match(/Novelty:\*\*\s*([\d.]+)/i);
    const soundnessMatch = assessmentText.match(/Soundness:\*\*\s*([\d.]+)/i);
    const experimentsMatch = assessmentText.match(/Experiments:\*\*\s*([\d.]+)/i);
    const formattingMatch = assessmentText.match(/Formatting:\*\*\s*([\d.]+)/i);
    
    if (noveltyMatch) result.detailed_scores.novelty = parseFloat(noveltyMatch[1]);
    if (soundnessMatch) result.detailed_scores.soundness = parseFloat(soundnessMatch[1]);
    if (experimentsMatch) result.detailed_scores.experiments = parseFloat(experimentsMatch[1]);
    if (formattingMatch) result.detailed_scores.formatting = parseFloat(formattingMatch[1]);
    
    // Extract issues
    const issuesSection = assessmentText.match(/Complete List of Issues:\*\*(.*?)(?=\*\*|$)/is);
    if (issuesSection) {
        const issueMatches = issuesSection[1].match(/\d+\.\s*\*\*([^:]+):\*\*([^\n]+)/g);
        if (issueMatches) {
            result.issues = issueMatches.map(issue => {
                const match = issue.match(/\d+\.\s*\*\*([^:]+):\*\*([^\n]+)/);
                return {
                    category: match[1].trim(),
                    description: match[2].trim()
                };
            });
        }
    }
    
    return result;
}

function displayDetailedScores(scores) {
    const container = document.getElementById('scoresGrid');
    container.innerHTML = '';
    
    const scoreLabels = {
        novelty: 'Novelty',
        soundness: 'Soundness',
        experiments: 'Experiments',
        formatting: 'Formatting'
    };
    
    for (const [key, label] of Object.entries(scoreLabels)) {
        const value = scores[key] || 'N/A';
        const scoreItem = document.createElement('div');
        scoreItem.className = 'score-item';
        scoreItem.innerHTML = `
            <h3>${label}</h3>
            <div class="value">${typeof value === 'number' ? value.toFixed(1) : value}</div>
        `;
        container.appendChild(scoreItem);
    }
}

function displayIssues(issues) {
    const container = document.getElementById('issuesContainer');
    container.innerHTML = '';
    
    if (!issues || issues.length === 0) {
        container.innerHTML = `
            <div class="no-issues">
                <h3>✅ No Major Issues Found</h3>
                <p>The paper meets basic quality standards.</p>
            </div>
        `;
        return;
    }
    
    const issuesSection = document.createElement('div');
    issuesSection.className = 'issues-section';
    issuesSection.innerHTML = '<h3>⚠️ Issues Identified</h3>';
    
    issues.forEach(issue => {
        const issueItem = document.createElement('div');
        issueItem.className = 'issue-item';
        issueItem.innerHTML = `<strong>${issue.category}:</strong> ${issue.description}`;
        issuesSection.appendChild(issueItem);
    });
    
    container.appendChild(issuesSection);
}

function displayMetadata(metadata, paperData) {
    const container = document.getElementById('metadataGrid');
    container.innerHTML = '';
    
    const metadataItems = [
        { 
            label: 'Abstract', 
            value: metadata.abstract_length || 0,
            clickable: true,
            dataKey: 'abstract',
            icon: '📝'
        },
        { 
            label: 'Sections', 
            value: metadata.sections_count || 0,
            clickable: true,
            dataKey: 'sections',
            icon: '📑'
        },
        { 
            label: 'References', 
            value: metadata.references_count || 0,
            clickable: true,
            dataKey: 'references',
            icon: '📚'
        },
        { 
            label: 'Figures', 
            value: metadata.figures_count || 0,
            clickable: true,
            dataKey: 'figures',
            icon: '📊'
        },
        { 
            label: 'Tables', 
            value: metadata.tables_count || 0,
            clickable: true,
            dataKey: 'tables',
            icon: '📋'
        }
    ];
    
    metadataItems.forEach(item => {
        const metadataItem = document.createElement('div');
        metadataItem.className = 'metadata-item' + (item.clickable ? ' clickable' : '');
        metadataItem.innerHTML = `
            <div class="label">${item.icon} ${item.label}</div>
            <div class="value">${item.value}</div>
            ${item.clickable && item.value > 0 ? '<div class="click-hint">Click to view</div>' : ''}
        `;
        
        if (item.clickable && item.value > 0) {
            metadataItem.style.cursor = 'pointer';
            metadataItem.addEventListener('click', () => showPaperDetail(item.dataKey, item.label));
        }
        
        container.appendChild(metadataItem);
    });
}

function displayAgentDetails(agentReviews) {
    const container = document.getElementById('agentDetailsContainer');
    container.innerHTML = '';
    
    const agents = [
        { key: 'plagiarism', name: 'Plagiarism Detection', icon: '🔍' },
        { key: 'ai_detection', name: 'AI Content Detection', icon: '🤖' },
        { key: 'methodology', name: 'Methodology Review', icon: '🔬' },
        { key: 'results', name: 'Results Validation', icon: '📊' },
        { key: 'formatting', name: 'Formatting Compliance', icon: '📝' }
    ];
    
    agents.forEach(agent => {
        const review = agentReviews[agent.key] || 'No review available';
        
        const agentCard = document.createElement('div');
        agentCard.className = 'agent-card';
        
        // Create expandable card
        const cardId = `agent-${agent.key}`;
        const isExpanded = false;
        
        agentCard.innerHTML = `
            <div class="agent-header" onclick="toggleAgentCard('${cardId}')">
                <div class="agent-name">${agent.icon} ${agent.name}</div>
                <div class="expand-icon" id="${cardId}-icon">▼</div>
            </div>
            <div class="agent-content" id="${cardId}" style="display: none;">
                ${formatAgentReview(review)}
            </div>
        `;
        
        container.appendChild(agentCard);
    });
}

function toggleAgentCard(cardId) {
    const content = document.getElementById(cardId);
    const icon = document.getElementById(`${cardId}-icon`);
    
    if (content.style.display === 'none') {
        content.style.display = 'block';
        icon.textContent = '▲';
    } else {
        content.style.display = 'none';
        icon.textContent = '▼';
    }
}

function formatAgentReview(review) {
    if (!review || review === 'No review available') {
        return '<p style="color: #999; font-style: italic;">No review available</p>';
    }
    
    // Convert markdown-style formatting to HTML
    let formatted = review;
    
    // Bold text: **text** -> <strong>text</strong>
    formatted = formatted.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    
    // Headers: ## Header -> <h4>Header</h4>
    formatted = formatted.replace(/^##\s+(.+)$/gm, '<h4>$1</h4>');
    
    // Bullet points: * item -> <li>item</li>
    formatted = formatted.replace(/^\*\s+(.+)$/gm, '<li>$1</li>');
    
    // Wrap consecutive <li> in <ul>
    formatted = formatted.replace(/(<li>.*<\/li>\n?)+/gs, '<ul>$&</ul>');
    
    // Numbered lists: 1. item -> <li>item</li>
    formatted = formatted.replace(/^\d+\.\s+(.+)$/gm, '<li>$1</li>');
    
    // Line breaks
    formatted = formatted.replace(/\n\n/g, '</p><p>');
    formatted = '<p>' + formatted + '</p>';
    
    // Clean up empty paragraphs
    formatted = formatted.replace(/<p>\s*<\/p>/g, '');
    
    return `<div class="agent-review-content">${formatted}</div>`;
}

function showPaperDetail(dataKey, title) {
    if (!currentReport) return;
    
    // Get paper data from report
    const paperData = currentReport.paper_data || {};
    
    let content = '';
    
    switch(dataKey) {
        case 'abstract':
            content = paperData.abstract || 'Abstract not available';
            break;
        case 'sections':
            const sections = paperData.sections || {};
            if (Object.keys(sections).length === 0) {
                content = 'Sections not available';
            } else {
                content = '<div class="sections-list">';
                for (const [name, text] of Object.entries(sections)) {
                    content += `
                        <div class="section-item">
                            <h4>${name.charAt(0).toUpperCase() + name.slice(1)}</h4>
                            <p>${text}</p>
                        </div>
                    `;
                }
                content += '</div>';
            }
            break;
        case 'references':
            const refs = paperData.references || [];
            if (refs.length === 0) {
                content = 'References not available';
            } else {
                content = '<ol class="references-list">';
                refs.forEach(ref => {
                    content += `<li>${ref}</li>`;
                });
                content += '</ol>';
            }
            break;
        case 'figures':
            const figCount = paperData.figures_count || currentReport.paper_metadata?.figures_count || 0;
            if (figCount === 0) {
                content = '<p style="color: #666;">This paper contains no figures.</p>';
            } else {
                content = `
                    <div style="background: #f0f9ff; padding: 20px; border-radius: 10px; border-left: 4px solid #3b82f6;">
                        <h3 style="color: #1e40af; margin-bottom: 15px;">📊 Figures Information</h3>
                        <p style="font-size: 1.1em; margin-bottom: 15px;">
                            This paper contains <strong>${figCount}</strong> figure(s).
                        </p>
                        <div style="background: white; padding: 15px; border-radius: 8px; margin-top: 15px;">
                            <h4 style="color: #3b82f6; margin-bottom: 10px;">What to Check:</h4>
                            <ul style="line-height: 1.8; color: #555;">
                                <li>All figures are properly labeled and numbered</li>
                                <li>Captions are clear and descriptive</li>
                                <li>Figures are referenced in the text</li>
                                <li>Image quality is sufficient</li>
                                <li>Axes and legends are clearly labeled</li>
                            </ul>
                        </div>
                        <p style="margin-top: 15px; color: #666; font-style: italic;">
                            💡 Note: Figure extraction from PDF is not yet implemented. 
                            Please refer to the original PDF to view the actual figures.
                        </p>
                    </div>
                `;
            }
            break;
        case 'tables':
            const tableCount = paperData.tables_count || currentReport.paper_metadata?.tables_count || 0;
            if (tableCount === 0) {
                content = '<p style="color: #666;">This paper contains no tables.</p>';
            } else {
                content = `
                    <div style="background: #f0fdf4; padding: 20px; border-radius: 10px; border-left: 4px solid #10b981;">
                        <h3 style="color: #065f46; margin-bottom: 15px;">📋 Tables Information</h3>
                        <p style="font-size: 1.1em; margin-bottom: 15px;">
                            This paper contains <strong>${tableCount}</strong> table(s).
                        </p>
                        <div style="background: white; padding: 15px; border-radius: 8px; margin-top: 15px;">
                            <h4 style="color: #10b981; margin-bottom: 10px;">What to Check:</h4>
                            <ul style="line-height: 1.8; color: #555;">
                                <li>All tables are properly numbered</li>
                                <li>Captions explain what the table shows</li>
                                <li>Tables are referenced in the text</li>
                                <li>Column headers are clear</li>
                                <li>Data is properly formatted</li>
                                <li>Statistical significance is indicated (if applicable)</li>
                            </ul>
                        </div>
                        <p style="margin-top: 15px; color: #666; font-style: italic;">
                            💡 Note: Table extraction from PDF is not yet implemented. 
                            Please refer to the original PDF to view the actual tables and their data.
                        </p>
                    </div>
                `;
            }
            break;
        default:
            content = 'Data not available';
    }
    
    // Create modal
    showModal(title, content);
}

function showModal(title, content) {
    // Remove existing modal if any
    const existingModal = document.getElementById('detailModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Create modal
    const modal = document.createElement('div');
    modal.id = 'detailModal';
    modal.className = 'modal';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h2>${title}</h2>
                <span class="modal-close" onclick="closeModal()">&times;</span>
            </div>
            <div class="modal-body">
                ${content}
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Show modal
    setTimeout(() => modal.classList.add('show'), 10);
    
    // Close on background click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeModal();
        }
    });
}

function closeModal() {
    const modal = document.getElementById('detailModal');
    if (modal) {
        modal.classList.remove('show');
        setTimeout(() => modal.remove(), 300);
    }
}

function resetForm() {
    document.getElementById('uploadSection').style.display = 'block';
    document.getElementById('loadingSection').classList.remove('active');
    document.getElementById('resultSection').classList.remove('active');
    document.getElementById('fileInput').value = '';
}
