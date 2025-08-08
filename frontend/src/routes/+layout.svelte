<script>
	import '../app.css';
	import Sidebar from '$lib/components/Sidebar.svelte';
	import Header from '$lib/components/Header.svelte';
	import NotificationToast from '$lib/components/NotificationToast.svelte';
	import { sidebarOpen } from '$lib/stores';
	import { onMount } from 'svelte';

	// Initialize sidebar state
	onMount(() => {
		// Set default sidebar state based on screen size
		if (typeof window !== 'undefined') {
			const isLargeScreen = window.innerWidth >= 1024;
			sidebarOpen.set(isLargeScreen);
		}
	});
</script>

<div class="app-container">
	<!-- Sidebar -->
	<Sidebar />
	
	<!-- Main Content Area -->
	<div class="main-content" class:sidebar-open={$sidebarOpen}>
		<!-- Header -->
		<Header />
		
		<!-- Page Content -->
		<main class="page-content">
			<slot />
		</main>
	</div>
	
	<!-- Notification Toast -->
	<NotificationToast />
</div>

<style>
	:global(html, body) {
		height: 100%;
		margin: 0;
		padding: 0;
		font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
	}

	:global(*, *::before, *::after) {
		box-sizing: border-box;
	}

	.app-container {
		display: flex;
		min-height: 100vh;
		background-color: #f9fafb;
	}

	.main-content {
		flex: 1;
		display: flex;
		flex-direction: column;
		margin-left: 4rem; /* Space for collapsed sidebar */
		transition: margin-left 0.3s ease-in-out;
		min-width: 0; /* Prevent flex item overflow */
	}

	.main-content.sidebar-open {
		margin-left: 16rem; /* Space for expanded sidebar */
	}

	.page-content {
		flex: 1;
		padding: 1.5rem;
		overflow-y: auto;
	}

	/* Mobile responsive adjustments */
	@media (max-width: 1024px) {
		.main-content {
			margin-left: 0;
		}

		.main-content.sidebar-open {
			margin-left: 0;
		}

		.page-content {
			padding: 1rem;
		}
	}

	/* Dark theme adjustments */
	:global(.dark) .app-container {
		background-color: #111827;
	}
</style>
