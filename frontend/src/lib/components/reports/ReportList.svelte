<script>
    import { createEventDispatcher } from 'svelte';
    
    export let reports;
    export let API_BASE;

    const dispatch = createEventDispatcher();

    let loading = false;
    let selectedReport = null;
    let showPreview = false;

    function getStatusColor(status) {
        switch (status) {
            case 'completed': return '#10b981';
            case 'generating': return '#f59e0b';
            case 'processing': return '#3b82f6';
            case 'failed': return '#ef4444';
            default: return '#6b7280';
        }
    }

    function getStatusIcon(status) {
        switch (status) {
            case 'completed': return '✅';
            case 'generating': return '⏳';
            case 'processing': return '🔄';
            case 'failed': return '❌';
            default: return '❓';
        }
    }

    function formatReportType(type) {
        return type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }

    function formatFileSize(bytes) {
        if (!bytes) return 'Unknown';
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
    }

    function formatDate(dateString) {
        return new Date(dateString).toLocaleString();
    }

    async function downloadReport(report) {
        if (report.status !== 'completed' || !report.download_url) {
            alert('Report not ready for download');
            return;
        }

        try {
            const response = await fetch(`${API_BASE}${report.download_url}`, {
                headers: {
                    'Authorization': `Bearer demo-token-${Date.now()}`
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            // Get filename from headers or use default
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = `report_${report.report_id}.${report.format}`;
            
            if (contentDisposition) {
                const filenameMatch = contentDisposition.match(/filename="?(.+)"?/);
                if (filenameMatch) {
                    filename = filenameMatch[1];
                }
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

        } catch (error) {
            console.error('Error downloading report:', error);
            alert('Failed to download report');
        }
    }

    function previewReport(report) {
        if (report.status !== 'completed' || !report.preview_url) {
            alert('Report not ready for preview');
            return;
        }

        const previewUrl = `${API_BASE}${report.preview_url}`;
        window.open(previewUrl, '_blank', 'width=1200,height=800,scrollbars=yes,resizable=yes');
    }

    async function deleteReport(report) {
        if (!confirm(`Are you sure you want to delete the report "${report.title}"?`)) {
            return;
        }

        loading = true;

        try {
            const response = await fetch(`${API_BASE}/reports/${report.report_id}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer demo-token-${Date.now()}`
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            dispatch('reportDeleted', report.report_id);
            
        } catch (error) {
            console.error('Error deleting report:', error);
            alert('Failed to delete report');
        } finally {
            loading = false;
        }
    }

    async function checkReportStatus(report) {
        if (report.status === 'completed' || report.status === 'failed') {
            return;
        }

        try {
            const response = await fetch(`${API_BASE}/reports/${report.report_id}/status`, {
                headers: {
                    'Authorization': `Bearer demo-token-${Date.now()}`
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const status = await response.json();
            console.log('Updated status:', status);
            
            // In a real app, you'd update the reports store here
            dispatch('refresh');
            
        } catch (error) {
            console.error('Error checking report status:', error);
        }
    }
</script>

<div class="report-list">
    {#if $reports.length === 0}
        <div class="empty-state">
            <div class="empty-icon">📄</div>
            <h3>No Reports Generated Yet</h3>
            <p>Generate your first security report to see it listed here.</p>
        </div>
    {:else}
        <div class="reports-grid">
            {#each $reports as report (report.report_id)}
                <div class="report-card">
                    <div class="report-header">
                        <div class="report-title">
                            <h4>{report.title}</h4>
                            <div class="report-meta">
                                <span class="report-type">
                                    {formatReportType(report.report_type)}
                                </span>
                                <span class="report-format">
                                    {report.format.toUpperCase()}
                                </span>
                            </div>
                        </div>
                        <div 
                            class="status-badge" 
                            style="background-color: {getStatusColor(report.status)}20; color: {getStatusColor(report.status)}"
                        >
                            {getStatusIcon(report.status)} {report.status.toUpperCase()}
                        </div>
                    </div>

                    <div class="report-details">
                        <div class="detail-item">
                            <span class="detail-label">Generated:</span>
                            <span class="detail-value">{formatDate(report.generated_at)}</span>
                        </div>
                        
                        {#if report.file_size}
                            <div class="detail-item">
                                <span class="detail-label">Size:</span>
                                <span class="detail-value">{formatFileSize(report.file_size)}</span>
                            </div>
                        {/if}

                        <div class="detail-item">
                            <span class="detail-label">Projects:</span>
                            <span class="detail-value">{report.metadata.projects_count} project(s)</span>
                        </div>

                        <div class="detail-item">
                            <span class="detail-label">Audience:</span>
                            <span class="detail-value">{report.metadata.audience_level}</span>
                        </div>
                    </div>

                    <div class="report-actions">
                        {#if report.status === 'completed'}
                            <button 
                                class="action-button preview-button"
                                on:click={() => previewReport(report)}
                                title="Preview report"
                            >
                                👁️ Preview
                            </button>

                            <button 
                                class="action-button download-button"
                                on:click={() => downloadReport(report)}
                                title="Download report"
                            >
                                📥 Download
                            </button>
                        {:else if report.status === 'generating' || report.status === 'processing'}
                            <button 
                                class="action-button status-button"
                                on:click={() => checkReportStatus(report)}
                                title="Check status"
                            >
                                🔄 Check Status
                            </button>
                        {:else if report.status === 'failed'}
                            <div class="error-info">
                                <span>❌ Generation failed</span>
                            </div>
                        {/if}

                        <button 
                            class="action-button delete-button"
                            on:click={() => deleteReport(report)}
                            disabled={loading}
                            title="Delete report"
                        >
                            🗑️ Delete
                        </button>
                    </div>
                </div>
            {/each}
        </div>
    {/if}
</div>

<style>
    .report-list {
        width: 100%;
    }

    .empty-state {
        text-align: center;
        padding: 60px 20px;
        background: #f8fafc;
        border-radius: 12px;
        border: 2px dashed #d1d5db;
    }

    .empty-icon {
        font-size: 4rem;
        margin-bottom: 20px;
        opacity: 0.5;
    }

    .empty-state h3 {
        margin: 0 0 10px 0;
        color: #374151;
        font-size: 1.5rem;
    }

    .empty-state p {
        color: #6b7280;
        margin: 0;
        font-size: 1.1rem;
    }

    .reports-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
        gap: 20px;
    }

    .report-card {
        background: white;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        overflow: hidden;
        transition: all 0.3s ease;
    }

    .report-card:hover {
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        transform: translateY(-2px);
    }

    .report-header {
        padding: 20px 20px 0 20px;
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 15px;
    }

    .report-title {
        flex: 1;
    }

    .report-title h4 {
        margin: 0 0 8px 0;
        font-size: 1.1rem;
        font-weight: 600;
        color: #1f2937;
        line-height: 1.3;
    }

    .report-meta {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
    }

    .report-type, .report-format {
        font-size: 0.75rem;
        font-weight: 500;
        padding: 4px 8px;
        border-radius: 4px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .report-type {
        background: #ede9fe;
        color: #7c3aed;
    }

    .report-format {
        background: #dbeafe;
        color: #2563eb;
    }

    .status-badge {
        font-size: 0.75rem;
        font-weight: 600;
        padding: 6px 10px;
        border-radius: 20px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        white-space: nowrap;
    }

    .report-details {
        padding: 15px 20px;
        background: #f8fafc;
        border-top: 1px solid #e2e8f0;
        border-bottom: 1px solid #e2e8f0;
    }

    .detail-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }

    .detail-item:last-child {
        margin-bottom: 0;
    }

    .detail-label {
        font-size: 0.875rem;
        color: #6b7280;
        font-weight: 500;
    }

    .detail-value {
        font-size: 0.875rem;
        color: #374151;
        font-weight: 500;
    }

    .report-actions {
        padding: 15px 20px;
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
    }

    .action-button {
        flex: 1;
        min-width: 0;
        padding: 8px 12px;
        border: none;
        border-radius: 6px;
        font-size: 0.875rem;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s ease;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 4px;
    }

    .preview-button {
        background: #ede9fe;
        color: #7c3aed;
    }

    .preview-button:hover {
        background: #ddd6fe;
    }

    .download-button {
        background: #dcfce7;
        color: #16a34a;
    }

    .download-button:hover {
        background: #bbf7d0;
    }

    .status-button {
        background: #dbeafe;
        color: #2563eb;
    }

    .status-button:hover {
        background: #bfdbfe;
    }

    .delete-button {
        background: #fee2e2;
        color: #dc2626;
    }

    .delete-button:hover:not(:disabled) {
        background: #fecaca;
    }

    .delete-button:disabled {
        opacity: 0.5;
        cursor: not-allowed;
    }

    .error-info {
        flex: 1;
        text-align: center;
        font-size: 0.875rem;
        color: #dc2626;
        font-weight: 500;
    }

    @media (max-width: 768px) {
        .reports-grid {
            grid-template-columns: 1fr;
            gap: 15px;
        }

        .report-header {
            flex-direction: column;
            align-items: flex-start;
        }

        .status-badge {
            align-self: flex-end;
        }

        .action-button {
            font-size: 0.8rem;
            padding: 6px 10px;
        }
    }
</style>
