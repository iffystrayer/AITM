<script>
    export let reportTypes = [];
    export let reportFormats = [];
    export let API_BASE;
    export let schedules;

    let showCreateForm = false;
    let formData = {
        name: '',
        description: '',
        report_type: 'executive_summary',
        format: 'pdf',
        schedule_cron: '0 9 * * 1',
        email_recipients: []
    };

    function formatCron(cron) {
        // Simple cron description
        if (cron === '0 9 * * 1') return 'Weekly on Monday at 9:00 AM';
        if (cron === '0 9 1 * *') return 'Monthly on 1st at 9:00 AM';
        if (cron === '0 9 * * *') return 'Daily at 9:00 AM';
        return cron;
    }
</script>

<div class="scheduler">
    <div class="scheduler-header">
        <p>Schedule automated report generation - Coming soon!</p>
        <button class="create-button" disabled>
            ➕ Schedule New Report
        </button>
    </div>
    
    <div class="placeholder">
        <div class="placeholder-icon">⏰</div>
        <h3>Scheduled Reports</h3>
        <p>This feature will allow you to schedule automatic report generation on a recurring basis.</p>
        
        <div class="feature-list">
            <div class="feature-item">✓ Weekly, Monthly, or Custom schedules</div>
            <div class="feature-item">✓ Email delivery to stakeholders</div>
            <div class="feature-item">✓ Multiple report formats</div>
            <div class="feature-item">✓ Automatic project inclusion</div>
        </div>
    </div>
</div>

<style>
    .scheduler {
        text-align: center;
        padding: 40px;
    }

    .scheduler-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 40px;
    }

    .create-button {
        padding: 12px 24px;
        background: #e5e7eb;
        color: #9ca3af;
        border: none;
        border-radius: 8px;
        cursor: not-allowed;
    }

    .placeholder {
        background: #f8fafc;
        border: 2px dashed #d1d5db;
        border-radius: 12px;
        padding: 60px 40px;
    }

    .placeholder-icon {
        font-size: 4rem;
        margin-bottom: 20px;
    }

    .placeholder h3 {
        margin: 0 0 15px 0;
        color: #374151;
    }

    .placeholder p {
        color: #6b7280;
        margin-bottom: 30px;
    }

    .feature-list {
        display: flex;
        flex-direction: column;
        gap: 10px;
        max-width: 400px;
        margin: 0 auto;
    }

    .feature-item {
        color: #059669;
        font-weight: 500;
    }
</style>
