<script>
    export let analytics;

    function formatPercentage(value) {
        return Math.round(value * 10) / 10 + '%';
    }
</script>

<div class="analytics">
    {#if $analytics}
        <div class="analytics-grid">
            <!-- Summary Cards -->
            <div class="analytics-section">
                <h3>📊 Report Generation Summary</h3>
                <div class="metric-cards">
                    <div class="metric-card">
                        <div class="metric-value">{$analytics.summary.total_reports}</div>
                        <div class="metric-label">Total Reports</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{$analytics.summary.completed_reports}</div>
                        <div class="metric-label">Completed</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{$analytics.summary.generating_reports}</div>
                        <div class="metric-label">In Progress</div>
                    </div>
                    <div class="metric-card success">
                        <div class="metric-value">{formatPercentage($analytics.summary.success_rate)}</div>
                        <div class="metric-label">Success Rate</div>
                    </div>
                </div>
            </div>

            <!-- Report Type Distribution -->
            <div class="analytics-section">
                <h3>📈 Report Types</h3>
                <div class="distribution-list">
                    {#each Object.entries($analytics.distributions.by_type) as [type, count]}
                        <div class="distribution-item">
                            <span class="type-name">{type.replace(/_/g, ' ')}</span>
                            <div class="type-bar">
                                <div class="type-fill" style="width: {count / Math.max(...Object.values($analytics.distributions.by_type)) * 100}%"></div>
                                <span class="type-count">{count}</span>
                            </div>
                        </div>
                    {/each}
                </div>
            </div>

            <!-- Format Distribution -->
            <div class="analytics-section">
                <h3>📄 Export Formats</h3>
                <div class="format-grid">
                    {#each Object.entries($analytics.distributions.by_format) as [format, count]}
                        <div class="format-card">
                            <div class="format-icon">
                                {#if format === 'pdf'}📋
                                {:else if format === 'html'}🌐
                                {:else if format === 'docx'}📄
                                {:else if format === 'json'}📊
                                {:else if format === 'markdown'}📝
                                {:else}📁{/if}
                            </div>
                            <div class="format-name">{format.toUpperCase()}</div>
                            <div class="format-count">{count} reports</div>
                        </div>
                    {/each}
                </div>
            </div>

            <!-- Recent Activity -->
            <div class="analytics-section full-width">
                <h3>🚀 Recent Activity</h3>
                <div class="activity-cards">
                    <div class="activity-card">
                        <div class="activity-icon">📅</div>
                        <div class="activity-content">
                            <div class="activity-value">{$analytics.recent_activity.reports_last_30_days}</div>
                            <div class="activity-label">Reports Last 30 Days</div>
                        </div>
                    </div>
                    <div class="activity-card">
                        <div class="activity-icon">⏰</div>
                        <div class="activity-content">
                            <div class="activity-value">{$analytics.recent_activity.scheduled_reports}</div>
                            <div class="activity-label">Active Schedules</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    {:else}
        <div class="no-data">
            <div class="no-data-icon">📊</div>
            <h3>No Analytics Data</h3>
            <p>Generate some reports to see analytics here.</p>
        </div>
    {/if}
</div>

<style>
    .analytics {
        width: 100%;
    }

    .analytics-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 30px;
    }

    .analytics-section {
        background: white;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        padding: 25px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }

    .analytics-section.full-width {
        grid-column: 1 / -1;
    }

    .analytics-section h3 {
        margin: 0 0 20px 0;
        font-size: 1.2rem;
        font-weight: 600;
        color: #374151;
    }

    .metric-cards {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
        gap: 15px;
    }

    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 8px;
        text-align: center;
    }

    .metric-card.success {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    }

    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        margin-bottom: 5px;
    }

    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .distribution-list {
        display: flex;
        flex-direction: column;
        gap: 15px;
    }

    .distribution-item {
        display: flex;
        align-items: center;
        gap: 15px;
    }

    .type-name {
        font-weight: 500;
        color: #374151;
        min-width: 120px;
        text-transform: capitalize;
    }

    .type-bar {
        flex: 1;
        background: #f3f4f6;
        border-radius: 20px;
        height: 8px;
        position: relative;
        display: flex;
        align-items: center;
        justify-content: flex-end;
        padding-right: 10px;
    }

    .type-fill {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        height: 100%;
        border-radius: 20px;
        transition: width 0.3s ease;
    }

    .type-count {
        font-size: 0.8rem;
        font-weight: 600;
        color: #6b7280;
        position: absolute;
        right: 8px;
    }

    .format-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
        gap: 15px;
    }

    .format-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 20px;
        text-align: center;
        transition: all 0.2s ease;
    }

    .format-card:hover {
        border-color: #667eea;
        background: #f8faff;
    }

    .format-icon {
        font-size: 2rem;
        margin-bottom: 10px;
    }

    .format-name {
        font-weight: 600;
        color: #374151;
        margin-bottom: 5px;
    }

    .format-count {
        font-size: 0.9rem;
        color: #6b7280;
    }

    .activity-cards {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 20px;
    }

    .activity-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 20px;
        display: flex;
        align-items: center;
        gap: 15px;
    }

    .activity-icon {
        font-size: 2rem;
        opacity: 0.8;
    }

    .activity-content {
        flex: 1;
    }

    .activity-value {
        font-size: 1.8rem;
        font-weight: bold;
        color: #374151;
        margin-bottom: 5px;
    }

    .activity-label {
        font-size: 0.9rem;
        color: #6b7280;
        font-weight: 500;
    }

    .no-data {
        text-align: center;
        padding: 60px 20px;
        background: #f8fafc;
        border-radius: 12px;
        border: 2px dashed #d1d5db;
    }

    .no-data-icon {
        font-size: 4rem;
        margin-bottom: 20px;
        opacity: 0.5;
    }

    .no-data h3 {
        margin: 0 0 10px 0;
        color: #374151;
    }

    .no-data p {
        color: #6b7280;
        margin: 0;
    }

    @media (max-width: 768px) {
        .analytics-grid {
            grid-template-columns: 1fr;
            gap: 20px;
        }

        .metric-cards {
            grid-template-columns: repeat(2, 1fr);
        }

        .format-grid {
            grid-template-columns: repeat(3, 1fr);
        }

        .activity-cards {
            grid-template-columns: 1fr;
        }
    }
</style>
