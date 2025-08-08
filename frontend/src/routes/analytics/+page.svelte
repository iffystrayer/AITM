<script>
	import { onMount } from 'svelte';
	import { currentPage } from '$lib/stores';
	import AnalyticsDashboard from '$lib/components/analytics/AnalyticsDashboard.svelte';

	onMount(() => {
		currentPage.set('analytics');
	});
</script>

<svelte:head>
	<title>Analytics - AITM</title>
</svelte:head>

<AnalyticsDashboard />
