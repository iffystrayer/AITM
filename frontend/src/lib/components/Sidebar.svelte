<script>
	import { sidebarOpen, currentPage, isBackendHealthy } from '$lib/stores';
	import { page } from '$app/stores';

	// Navigation items
	const navItems = [
		{
			name: 'Dashboard',
			href: '/',
			icon: `<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2V7zm16 0V9a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2h14a2 2 0 002-2V7z"/>
			</svg>`,
			page: 'dashboard'
		},
		{
			name: 'Projects',
			href: '/projects',
			icon: `<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/>
			</svg>`,
			page: 'projects'
		},
		{
			name: 'Analysis',
			href: '/analysis',
			icon: `<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
			</svg>`,
			page: 'analysis'
		},
		{
			name: 'Assets',
			href: '/assets',
			icon: `<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/>
			</svg>`,
			page: 'assets'
		},
		{
			name: 'Reports',
			href: '/reports',
			icon: `<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
			</svg>`,
			page: 'reports'
		},
		{
			name: 'MITRE ATT&CK',
			href: '/mitre',
			icon: `<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
			</svg>`,
			page: 'mitre'
		}
	];

	function toggleSidebar() {
		sidebarOpen.update(open => !open);
	}

	function navigateTo(pageName) {
		currentPage.set(pageName);
	}
</script>

<aside 
	class="sidebar" 
	class:open={$sidebarOpen}
>
	<!-- Sidebar Header -->
	<div class="sidebar-header">
		<div class="flex items-center space-x-3">
			<div class="logo-container">
				<svg class="w-8 h-8 text-blue-600" fill="currentColor" viewBox="0 0 24 24">
					<path d="M12 2L2 7v10c0 5.55 3.84 9.74 9 11 5.16-1.26 9-5.45 9-11V7l-10-5z"/>
				</svg>
			</div>
			{#if $sidebarOpen}
				<div class="logo-text">
					<h1 class="text-lg font-bold text-gray-900 dark:text-white">AITM</h1>
					<p class="text-xs text-gray-500 dark:text-gray-400">AI Threat Modeler</p>
				</div>
			{/if}
		</div>
		
		<!-- Toggle Button -->
		<button 
			class="toggle-btn"
			on:click={toggleSidebar}
			title={$sidebarOpen ? 'Collapse sidebar' : 'Expand sidebar'}
		>
			<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				{#if $sidebarOpen}
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 19l-7-7 7-7m8 14l-7-7 7-7"/>
				{:else}
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 5l7 7-7 7M5 5l7 7-7 7"/>
				{/if}
			</svg>
		</button>
	</div>

	<!-- Backend Status Indicator -->
	<div class="status-indicator">
		<div class="flex items-center space-x-2">
			<div 
				class="status-dot"
				class:healthy={$isBackendHealthy}
				class:unhealthy={!$isBackendHealthy}
			></div>
			{#if $sidebarOpen}
				<span class="text-xs {$isBackendHealthy ? 'text-green-600' : 'text-red-600'}">
					{$isBackendHealthy ? 'Backend Online' : 'Backend Offline'}
				</span>
			{/if}
		</div>
	</div>

	<!-- Navigation -->
	<nav class="nav-menu">
		<ul class="nav-list">
			{#each navItems as item}
				<li>
					<a 
						href={item.href}
						class="nav-link"
						class:active={$page.url.pathname === item.href}
						on:click={() => navigateTo(item.page)}
						title={$sidebarOpen ? '' : item.name}
					>
						<div class="nav-icon">
							{@html item.icon}
						</div>
						{#if $sidebarOpen}
							<span class="nav-text">{item.name}</span>
						{/if}
					</a>
				</li>
			{/each}
		</ul>
	</nav>

	<!-- Sidebar Footer -->
	{#if $sidebarOpen}
		<div class="sidebar-footer">
			<div class="text-xs text-gray-500 dark:text-gray-400 text-center">
				Version 1.0.0
			</div>
		</div>
	{/if}
</aside>

<!-- Mobile Overlay -->
{#if $sidebarOpen}
	<button 
		class="mobile-overlay lg:hidden"
		on:click={toggleSidebar}
		aria-label="Close sidebar"
	>
		<span class="sr-only">Close sidebar</span>
	</button>
{/if}

<style>
	.sidebar {
		position: fixed;
		left: 0;
		top: 0;
		height: 100vh;
		background-color: white;
		border-right: 1px solid #e5e7eb;
		z-index: 1000;
		display: flex;
		flex-direction: column;
		transition: width 0.3s ease-in-out;
		width: 4rem; /* Collapsed width */
		overflow: hidden;
	}

	.sidebar.open {
		width: 16rem; /* Expanded width */
	}

	.sidebar-header {
		padding: 1rem;
		border-bottom: 1px solid #e5e7eb;
		display: flex;
		align-items: center;
		justify-content: space-between;
		min-height: 4rem;
	}

	.logo-container {
		flex-shrink: 0;
	}

	.logo-text {
		min-width: 0;
		opacity: 1;
		transition: opacity 0.2s ease-in-out;
	}

	.toggle-btn {
		background: transparent;
		border: none;
		cursor: pointer;
		padding: 0.5rem;
		border-radius: 0.375rem;
		color: #6b7280;
		transition: all 0.2s ease-in-out;
		flex-shrink: 0;
	}

	.toggle-btn:hover {
		background-color: #f3f4f6;
		color: #374151;
	}

	.status-indicator {
		padding: 0.75rem 1rem;
		border-bottom: 1px solid #e5e7eb;
	}

	.status-dot {
		width: 0.5rem;
		height: 0.5rem;
		border-radius: 50%;
		transition: background-color 0.2s ease-in-out;
	}

	.status-dot.healthy {
		background-color: #10b981;
	}

	.status-dot.unhealthy {
		background-color: #ef4444;
	}

	.nav-menu {
		flex: 1;
		padding: 1rem 0;
		overflow-y: auto;
	}

	.nav-list {
		list-style: none;
		margin: 0;
		padding: 0;
	}

	.nav-link {
		display: flex;
		align-items: center;
		padding: 0.75rem 1rem;
		color: #6b7280;
		text-decoration: none;
		transition: all 0.2s ease-in-out;
		margin: 0 0.5rem;
		border-radius: 0.5rem;
	}

	.nav-link:hover {
		background-color: #f3f4f6;
		color: #374151;
	}

	.nav-link.active {
		background-color: #dbeafe;
		color: #2563eb;
	}

	.nav-icon {
		flex-shrink: 0;
		width: 1.25rem;
		height: 1.25rem;
	}

	.nav-text {
		margin-left: 0.75rem;
		font-weight: 500;
		white-space: nowrap;
	}

	.sidebar-footer {
		padding: 1rem;
		border-top: 1px solid #e5e7eb;
	}

	.mobile-overlay {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background-color: rgba(0, 0, 0, 0.5);
		z-index: 999;
	}

	/* Dark theme adjustments */
	:global(.dark) .sidebar {
		background-color: #1f2937;
		border-right-color: #374151;
	}

	:global(.dark) .sidebar-header {
		border-bottom-color: #374151;
	}

	:global(.dark) .status-indicator {
		border-bottom-color: #374151;
	}

	:global(.dark) .nav-link {
		color: #d1d5db;
	}

	:global(.dark) .nav-link:hover {
		background-color: #374151;
		color: #f9fafb;
	}

	:global(.dark) .nav-link.active {
		background-color: #1e40af;
		color: #dbeafe;
	}

	:global(.dark) .toggle-btn {
		color: #d1d5db;
	}

	:global(.dark) .toggle-btn:hover {
		background-color: #374151;
		color: #f9fafb;
	}

	:global(.dark) .sidebar-footer {
		border-top-color: #374151;
	}

	/* Mobile responsiveness */
	@media (max-width: 1024px) {
		.sidebar {
			transform: translateX(-100%);
		}

		.sidebar.open {
			transform: translateX(0);
		}
	}
</style>
