<script>
	import '../app.css';
	import Sidebar from '$lib/components/Sidebar.svelte';
	import Header from '$lib/components/Header.svelte';
	import NotificationToast from '$lib/components/NotificationToast.svelte';
	import { sidebarOpen, healthStatus } from '$lib/stores';
	import { onMount } from 'svelte';
	import { apiService } from '$lib/api';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';

	let isAuthenticated = false;
	let isAuthPage = false;

	// Check if current page is an auth page
	$: isAuthPage = $page.url.pathname.startsWith('/auth');

	// Initialize sidebar state and backend health check
	onMount(async () => {
		// Check authentication
		const token = localStorage.getItem('access_token');
		isAuthenticated = !!token;

		// If not authenticated and not on auth page, redirect to login
		if (!isAuthenticated && !isAuthPage) {
			goto('/auth/login');
			return;
		}

		// If authenticated and on auth page, redirect to dashboard
		if (isAuthenticated && isAuthPage) {
			goto('/');
			return;
		}

		// Set default sidebar state based on screen size
		if (typeof window !== 'undefined') {
			const isLargeScreen = window.innerWidth >= 1024;
			sidebarOpen.set(isLargeScreen);
		}

		// Check backend health
		const checkHealth = async () => {
			try {
				const response = await apiService.healthCheck();
				healthStatus.set(response);
			} catch (error) {
				console.error('Health check failed:', error);
				healthStatus.set({ status: 'unhealthy', environment: 'unknown', version: 'unknown' });
			}
		};

		// Initial health check
		await checkHealth();

		// Set up periodic health check (every 30 seconds)
		const interval = setInterval(checkHealth, 30000);

		// Cleanup on unmount
		return () => clearInterval(interval);
	});
</script>

{#if isAuthPage}
	<!-- Auth pages without sidebar/header -->
	<slot />
{:else if isAuthenticated}
	<!-- Authenticated app layout -->
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
{:else}
	<!-- Loading or redirecting -->
	<div class="min-h-screen flex items-center justify-center bg-gray-50">
		<div class="text-center">
			<svg class="animate-spin w-8 h-8 text-blue-600 mx-auto mb-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
				<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
				<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
			</svg>
			<p class="text-gray-600">Loading...</p>
		</div>
	</div>
{/if}

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
		background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
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
		padding: 0;
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
