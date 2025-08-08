<script>
    import { currentPage } from '$lib/stores';
    import { onMount } from 'svelte';
    import ReportsDashboard from '$lib/components/reports/ReportsDashboard.svelte';

    onMount(() => {
        currentPage.set('reports');
    });
</script>

<svelte:head>
    <title>Reports & Analytics - AITM</title>
    <meta name="description" content="Generate and manage security reports with AITM's AI-powered threat modeling platform" />
</svelte:head>

<ReportsDashboard />
