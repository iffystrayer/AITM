<script>
    import { createEventDispatcher } from 'svelte';

    export let reportTypes = [];
    export let reportFormats = [];
    export let API_BASE;

    const dispatch = createEventDispatcher();

    let selectedType = 'executive_summary';
    let selectedFormat = 'html';
    let selectedProjects = ['project_001', 'project_002']; // Mock project IDs
    let includeCharts = true;
    let includeMitre = true;
    let includeRecommendations = true;
    let audienceLevel = 'executive';
    let dateRange = null;
    let customSections = [];
    let loading = false;
    let error = null;
    let success = null;

    // Available projects (in real app, this would come from API)
    const availableProjects = [
        { id: 'project_001', name: 'E-commerce Platform', description: 'Online shopping application' },
        { id: 'project_002', name: 'Mobile Banking App', description: 'Mobile financial services' },
        { id: 'project_003', name: 'IoT Device Network', description: 'Smart home device ecosystem' },
        { id: 'project_004', name: 'Healthcare Portal', description: 'Patient management system' }
    ];

    async function generateReport() {
        if (!selectedProjects.length) {
            error = 'Please select at least one project';
            return;
        }

        loading = true;
        error = null;
        success = null;

        try {
            const requestData = {
                report_type: selectedType,
                format: selectedFormat,
                project_ids: selectedProjects,
                include_charts: includeCharts,
                include_mitre_mapping: includeMitre,
                include_recommendations: includeRecommendations,
                audience_level: audienceLevel,
                date_range: dateRange,
                custom_sections: customSections
            };

            const response = await fetch(`${API_BASE}/reports/generate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer demo-token-${Date.now()}`
                },
                body: JSON.stringify(requestData)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            success = `Report generation started successfully! Report ID: ${result.report_id}`;
            
            // Dispatch event to parent component
            dispatch('reportGenerated', result);

            // Reset form
            resetForm();

        } catch (err) {
            console.error('Error generating report:', err);
            error = `Failed to generate report: ${err.message}`;
        } finally {
            loading = false;
        }
    }

    async function generateSampleReport() {
        loading = true;
        error = null;

        try {
            const url = `${API_BASE}/reports/sample?report_type=${selectedType}&format=${selectedFormat}`;
            
            if (selectedFormat === 'html') {
                // Open HTML report in new tab
                window.open(url, '_blank');
                success = 'Sample report generated and opened in new tab!';
            } else {
                // Download other formats
                const response = await fetch(url);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const blob = await response.blob();
                const downloadUrl = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = downloadUrl;
                a.download = `sample_report.${selectedFormat}`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(downloadUrl);
                document.body.removeChild(a);
                
                success = 'Sample report downloaded successfully!';
            }

        } catch (err) {
            console.error('Error generating sample report:', err);
            error = `Failed to generate sample report: ${err.message}`;
        } finally {
            loading = false;
        }
    }

    function resetForm() {
        selectedProjects = ['project_001', 'project_002'];
        includeCharts = true;
        includeMitre = true;
        includeRecommendations = true;
        audienceLevel = 'executive';
        dateRange = null;
        customSections = [];
    }

    function toggleProject(projectId) {
        const index = selectedProjects.indexOf(projectId);
        if (index > -1) {
            selectedProjects = selectedProjects.filter(id => id !== projectId);
        } else {
            selectedProjects = [...selectedProjects, projectId];
        }
    }

    function formatReportTypeName(type) {
        return type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }

    function formatFormatName(format) {
        return format.toUpperCase();
    }
</script>

<div class="report-generator">
    {#if success}
        <div class="success-message">
            <p>✅ {success}</p>
            <button on:click={() => success = null}>Dismiss</button>
        </div>
    {/if}

    {#if error}
        <div class="error-message">
            <p>❌ {error}</p>
            <button on:click={() => error = null}>Dismiss</button>
        </div>
    {/if}

    <form on:submit|preventDefault={generateReport} class="generator-form">
        <div class="form-grid">
            <!-- Report Type Selection -->
            <div class="form-section">
                <h3>📊 Report Type</h3>
                <div class="radio-group">
                    {#each reportTypes as type}
                        <label class="radio-option">
                            <input 
                                type="radio" 
                                bind:group={selectedType} 
                                value={type} 
                            />
                            <span class="radio-label">
                                <strong>{formatReportTypeName(type)}</strong>
                                <small>
                                    {#if type === 'executive_summary'}
                                        High-level overview for executives
                                    {:else if type === 'technical_detailed'}
                                        Detailed technical analysis
                                    {:else if type === 'compliance_audit'}
                                        Compliance framework assessment
                                    {:else}
                                        {formatReportTypeName(type)} report
                                    {/if}
                                </small>
                            </span>
                        </label>
                    {/each}
                </div>
            </div>

            <!-- Format Selection -->
            <div class="form-section">
                <h3>📄 Export Format</h3>
                <div class="format-grid">
                    {#each reportFormats as format}
                        <label class="format-option">
                            <input 
                                type="radio" 
                                bind:group={selectedFormat} 
                                value={format}
                            />
                            <span class="format-label">
                                <div class="format-icon">
                                    {#if format === 'pdf'}📋
                                    {:else if format === 'html'}🌐
                                    {:else if format === 'docx'}📄
                                    {:else if format === 'json'}📊
                                    {:else if format === 'markdown'}📝
                                    {:else}📁{/if}
                                </div>
                                <strong>{formatFormatName(format)}</strong>
                            </span>
                        </label>
                    {/each}
                </div>
            </div>

            <!-- Project Selection -->
            <div class="form-section full-width">
                <h3>🎯 Projects to Include</h3>
                <div class="project-grid">
                    {#each availableProjects as project}
                        <label class="project-option">
                            <input 
                                type="checkbox" 
                                checked={selectedProjects.includes(project.id)}
                                on:change={() => toggleProject(project.id)}
                            />
                            <span class="project-info">
                                <strong>{project.name}</strong>
                                <small>{project.description}</small>
                            </span>
                        </label>
                    {/each}
                </div>
            </div>

            <!-- Options -->
            <div class="form-section">
                <h3>⚙️ Report Options</h3>
                <div class="options-group">
                    <label class="checkbox-option">
                        <input type="checkbox" bind:checked={includeCharts} />
                        <span>Include Charts and Visualizations</span>
                    </label>
                    <label class="checkbox-option">
                        <input type="checkbox" bind:checked={includeMitre} />
                        <span>Include MITRE ATT&CK Mapping</span>
                    </label>
                    <label class="checkbox-option">
                        <input type="checkbox" bind:checked={includeRecommendations} />
                        <span>Include Recommendations</span>
                    </label>
                </div>
            </div>

            <!-- Audience Level -->
            <div class="form-section">
                <h3>👥 Target Audience</h3>
                <select bind:value={audienceLevel} class="select-input">
                    <option value="executive">Executive Level</option>
                    <option value="technical">Technical Team</option>
                    <option value="operational">Operations Team</option>
                </select>
            </div>
        </div>

        <div class="form-actions">
            <button 
                type="submit" 
                class="primary-button" 
                disabled={loading || !selectedProjects.length}
            >
                {#if loading}
                    <span class="loading-spinner"></span>
                    Generating Report...
                {:else}
                    🚀 Generate Report
                {/if}
            </button>

            <button 
                type="button" 
                class="secondary-button" 
                disabled={loading}
                on:click={generateSampleReport}
            >
                📋 Generate Sample
            </button>

            <button 
                type="button" 
                class="tertiary-button" 
                disabled={loading}
                on:click={resetForm}
            >
                🔄 Reset Form
            </button>
        </div>
    </form>
</div>

<style>
    .report-generator {
        max-width: 800px;
        margin: 0 auto;
    }

    .success-message, .error-message {
        padding: 15px 20px;
        border-radius: 8px;
        margin-bottom: 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .success-message {
        background: #d1fae5;
        border: 1px solid #a7f3d0;
        color: #065f46;
    }

    .error-message {
        background: #fee2e2;
        border: 1px solid #fca5a5;
        color: #dc2626;
    }

    .success-message button, .error-message button {
        padding: 5px 10px;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        font-size: 0.9rem;
        font-weight: 500;
    }

    .success-message button {
        background: #059669;
        color: white;
    }

    .error-message button {
        background: #dc2626;
        color: white;
    }

    .generator-form {
        background: #f8fafc;
        border-radius: 12px;
        padding: 30px;
        border: 1px solid #e2e8f0;
    }

    .form-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 30px;
        margin-bottom: 30px;
    }

    .form-section {
        background: white;
        padding: 20px;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
    }

    .form-section.full-width {
        grid-column: 1 / -1;
    }

    .form-section h3 {
        margin: 0 0 15px 0;
        font-size: 1.1rem;
        font-weight: 600;
        color: #374151;
    }

    .radio-group {
        display: flex;
        flex-direction: column;
        gap: 10px;
    }

    .radio-option {
        display: flex;
        align-items: flex-start;
        gap: 10px;
        padding: 12px;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .radio-option:hover {
        border-color: #667eea;
        background: #f8faff;
    }

    .radio-option input[type="radio"] {
        margin-top: 2px;
    }

    .radio-label {
        display: flex;
        flex-direction: column;
        gap: 4px;
    }

    .radio-label strong {
        font-weight: 600;
        color: #374151;
    }

    .radio-label small {
        color: #6b7280;
        font-size: 0.9rem;
    }

    .format-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
        gap: 10px;
    }

    .format-option {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 15px;
        border: 2px solid #e2e8f0;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s ease;
        background: white;
    }

    .format-option:hover {
        border-color: #667eea;
        background: #f8faff;
    }

    .format-option input[type="radio"]:checked + .format-label {
        color: #667eea;
    }

    .format-option input[type="radio"] {
        display: none;
    }

    .format-label {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 8px;
        text-align: center;
    }

    .format-icon {
        font-size: 1.5rem;
    }

    .project-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 15px;
    }

    .project-option {
        display: flex;
        align-items: flex-start;
        gap: 12px;
        padding: 15px;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s ease;
        background: white;
    }

    .project-option:hover {
        border-color: #667eea;
        background: #f8faff;
    }

    .project-info {
        display: flex;
        flex-direction: column;
        gap: 4px;
    }

    .project-info strong {
        font-weight: 600;
        color: #374151;
    }

    .project-info small {
        color: #6b7280;
        font-size: 0.9rem;
    }

    .options-group {
        display: flex;
        flex-direction: column;
        gap: 12px;
    }

    .checkbox-option {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 10px;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .checkbox-option:hover {
        border-color: #667eea;
        background: #f8faff;
    }

    .select-input {
        width: 100%;
        padding: 12px;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        background: white;
        font-size: 1rem;
    }

    .form-actions {
        display: flex;
        gap: 15px;
        justify-content: center;
        flex-wrap: wrap;
    }

    .primary-button, .secondary-button, .tertiary-button {
        padding: 12px 24px;
        border: none;
        border-radius: 8px;
        font-size: 1rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s ease;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .primary-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }

    .primary-button:hover:not(:disabled) {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }

    .primary-button:disabled {
        opacity: 0.6;
        cursor: not-allowed;
    }

    .secondary-button {
        background: #f3f4f6;
        color: #374151;
        border: 1px solid #d1d5db;
    }

    .secondary-button:hover:not(:disabled) {
        background: #e5e7eb;
        transform: translateY(-1px);
    }

    .tertiary-button {
        background: transparent;
        color: #6b7280;
        border: 1px solid #d1d5db;
    }

    .tertiary-button:hover:not(:disabled) {
        color: #374151;
        border-color: #9ca3af;
    }

    .loading-spinner {
        width: 16px;
        height: 16px;
        border: 2px solid transparent;
        border-top: 2px solid currentColor;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }

    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }

    @media (max-width: 768px) {
        .form-grid {
            grid-template-columns: 1fr;
            gap: 20px;
        }

        .format-grid {
            grid-template-columns: repeat(3, 1fr);
        }

        .project-grid {
            grid-template-columns: 1fr;
        }

        .form-actions {
            flex-direction: column;
            align-items: stretch;
        }
    }
</style>
