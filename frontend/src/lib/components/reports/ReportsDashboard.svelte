<script>
    import { onMount } from 'svelte';
    import { writable } from 'svelte/store';
    import ReportGenerator from './ReportGenerator.svelte';
    import ReportList from './ReportList.svelte';
    import ReportScheduler from './ReportScheduler.svelte';
    import ReportAnalytics from './ReportAnalytics.svelte';

    let activeTab = 'generate';
    let reportTypes = [];
    let reportFormats = [];
    let loading = false;
    let error = null;

    // Stores
    const reports = writable([]);
    const schedules = writable([]);
    const analytics = writable(null);

    // API Base URL
    const API_BASE = 'http://localhost:38527/api/v1';

    onMount(async () => {
        await loadInitialData();
    });

    async function loadInitialData() {
        loading = true;
        error = null;

        try {
            // Load report types and formats
            const [typesResponse, formatsResponse] = await Promise.all([
                fetch(`${API_BASE}/reports/types`),
                fetch(`${API_BASE}/reports/formats`)
            ]);

            reportTypes = await typesResponse.json();
            reportFormats = await formatsResponse.json();

            // Load user reports and analytics
            await Promise.all([
                loadReports(),
                loadAnalytics()
            ]);

        } catch (err) {
            console.error('Error loading initial data:', err);
            error = 'Failed to load report data';
        } finally {
            loading = false;
        }
    }

    async function loadReports() {
        try {
            const response = await fetch(`${API_BASE}/reports`, {
                headers: {
                    'Authorization': `Bearer demo-token-${Date.now()}`
                }
            });
            const data = await response.json();
            reports.set(data.reports || []);
        } catch (err) {
            console.error('Error loading reports:', err);
        }
    }

    async function loadAnalytics() {
        try {
            const response = await fetch(`${API_BASE}/reports/analytics`, {
                headers: {
                    'Authorization': `Bearer demo-token-${Date.now()}`
                }
            });
            const data = await response.json();
            analytics.set(data);
        } catch (err) {
            console.error('Error loading analytics:', err);
        }
    }

    async function handleReportGenerated(event) {
        const reportResponse = event.detail;
        console.log('Report generated:', reportResponse);
        
        // Refresh reports list
        await loadReports();
        await loadAnalytics();
        
        // Switch to reports tab to show the new report
        activeTab = 'reports';
    }

    async function handleReportDeleted(event) {
        console.log('Report deleted:', event.detail);
        await loadReports();
        await loadAnalytics();
    }

    function setActiveTab(tab) {
        activeTab = tab;
    }
</script>

<div class="reports-dashboard">
    <div class="dashboard-header">
        <h1>📊 Reports & Analytics</h1>
        <p>Generate, manage, and schedule comprehensive security reports</p>
    </div>

    {#if loading}
        <div class="loading-spinner">
            <div class="spinner"></div>
            <p>Loading report data...</p>
        </div>
    {/if}

    {#if error}
        <div class="error-message">
            <p>⚠️ {error}</p>
            <button on:click={loadInitialData}>Retry</button>
        </div>
    {/if}

    {#if !loading && !error}
        <div class="dashboard-tabs">
            <nav class="tab-nav">
                <button 
                    class="tab-button" 
                    class:active={activeTab === 'generate'}
                    on:click={() => setActiveTab('generate')}
                >
                    🎯 Generate Report
                </button>
                <button 
                    class="tab-button" 
                    class:active={activeTab === 'reports'}
                    on:click={() => setActiveTab('reports')}
                >
                    📋 My Reports
                </button>
                <button 
                    class="tab-button" 
                    class:active={activeTab === 'schedule'}
                    on:click={() => setActiveTab('schedule')}
                >
                    ⏰ Scheduled Reports
                </button>
                <button 
                    class="tab-button" 
                    class:active={activeTab === 'analytics'}
                    on:click={() => setActiveTab('analytics')}
                >
                    📈 Analytics
                </button>
            </nav>

            <div class="tab-content">
                {#if activeTab === 'generate'}
                    <div class="tab-panel">
                        <h2>Generate New Report</h2>
                        <ReportGenerator 
                            {reportTypes} 
                            {reportFormats}
                            {API_BASE}
                            on:reportGenerated={handleReportGenerated}
                        />
                    </div>
                {/if}

                {#if activeTab === 'reports'}
                    <div class="tab-panel">
                        <h2>Generated Reports</h2>
                        <ReportList 
                            {reports}
                            {API_BASE}
                            on:reportDeleted={handleReportDeleted}
                            on:refresh={loadReports}
                        />
                    </div>
                {/if}

                {#if activeTab === 'schedule'}
                    <div class="tab-panel">
                        <h2>Scheduled Reports</h2>
                        <ReportScheduler 
                            {reportTypes}
                            {reportFormats}
                            {API_BASE}
                            {schedules}
                        />
                    </div>
                {/if}

                {#if activeTab === 'analytics'}
                    <div class="tab-panel">
                        <h2>Report Analytics</h2>
                        <ReportAnalytics {analytics} />
                    </div>
                {/if}
            </div>
        </div>
    {/if}
</div>

<style>
    .reports-dashboard {
        padding: 20px;
        max-width: 1200px;
        margin: 0 auto;
        min-height: 100vh;
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }

    .dashboard-header {
        text-align: center;
        margin-bottom: 40px;
        padding: 30px;
        background: white;
        border-radius: 15px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }

    .dashboard-header h1 {
        font-size: 2.5rem;
        margin: 0 0 10px 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    .dashboard-header p {
        font-size: 1.1rem;
        color: #666;
        margin: 0;
    }

    .loading-spinner {
        text-align: center;
        padding: 60px;
        background: white;
        border-radius: 15px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }

    .spinner {
        width: 50px;
        height: 50px;
        border: 4px solid #f3f3f3;
        border-top: 4px solid #667eea;
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin: 0 auto 20px;
    }

    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }

    .error-message {
        text-align: center;
        padding: 40px;
        background: #fee;
        border: 2px solid #f88;
        border-radius: 15px;
        color: #d33;
    }

    .error-message button {
        margin-top: 15px;
        padding: 10px 20px;
        background: #dc2626;
        color: white;
        border: none;
        border-radius: 8px;
        cursor: pointer;
        font-weight: 500;
        transition: background-color 0.3s ease;
    }

    .error-message button:hover {
        background: #b91c1c;
    }

    .dashboard-tabs {
        background: white;
        border-radius: 15px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        overflow: hidden;
        min-height: 600px;
    }

    .tab-nav {
        display: flex;
        background: #f8fafc;
        border-bottom: 1px solid #e2e8f0;
        padding: 0;
        margin: 0;
    }

    .tab-button {
        flex: 1;
        padding: 20px;
        background: none;
        border: none;
        cursor: pointer;
        font-size: 1rem;
        font-weight: 500;
        color: #64748b;
        transition: all 0.3s ease;
        position: relative;
    }

    .tab-button:hover {
        background: #e2e8f0;
        color: #475569;
    }

    .tab-button.active {
        background: white;
        color: #667eea;
        font-weight: 600;
    }

    .tab-button.active::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }

    .tab-content {
        padding: 0;
    }

    .tab-panel {
        padding: 30px;
        animation: fadeIn 0.3s ease-in;
    }

    .tab-panel h2 {
        margin: 0 0 30px 0;
        font-size: 1.5rem;
        color: #1e293b;
        font-weight: 600;
    }

    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    @media (max-width: 768px) {
        .reports-dashboard {
            padding: 10px;
        }

        .dashboard-header {
            padding: 20px;
        }

        .dashboard-header h1 {
            font-size: 2rem;
        }

        .tab-nav {
            flex-direction: column;
        }

        .tab-button {
            padding: 15px;
            text-align: left;
        }

        .tab-panel {
            padding: 20px;
        }
    }
</style>
