<script>
	import { onMount } from 'svelte';
	import { sidebarOpen, currentProject, isAnalyzing, analysisProgress, currentPage } from '$lib/stores';
	import { applyTheme, getThemePreference, setThemePreference } from '$lib/utils';
	
	let theme = 'system';

	onMount(() => {
		if (typeof window !== 'undefined') {
			theme = getThemePreference();
		}
	});

	function toggleSidebar() {
		sidebarOpen.update(open => !open);
	}

	function toggleTheme() {
		if (typeof window !== 'undefined') {
			theme = theme === 'light' ? 'dark' : 'light';
			setThemePreference(theme);
			applyTheme(theme);
		}
	}

	// Get page title based on current page
	$: pageTitle = getPageTitle($currentPage);

	function getPageTitle(page) {
		switch (page) {
			case 'dashboard': return 'Dashboard';
			case 'projects': return 'Projects';
			case 'analysis': return 'Threat Analysis';
			case 'assets': return 'Asset Management';
			case 'reports': return 'Reports';
			case 'mitre': return 'MITRE ATT&CK';
			default: return 'AITM';
		}
	}
</script>

<header class="header">
	<div class="header-left">
		<!-- Mobile Menu Button -->
		<button 
			class="mobile-menu-btn lg:hidden"
			on:click={toggleSidebar}
		>
			<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/>
			</svg>
		</button>

		<!-- Page Title -->
		<div class="page-title">
			<h1 class="text-2xl font-bold text-gray-900 dark:text-white">
				{pageTitle}
			</h1>
			{#if $currentProject}
				<p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
					Project: {$currentProject.name}
				</p>
			{/if}
		</div>
	</div>

	<div class="header-right">
		<!-- Analysis Progress Indicator -->
		{#if $isAnalyzing}
			<div class="analysis-indicator">
				<div class="flex items-center space-x-2">
					<div class="animate-spin w-4 h-4 border-2 border-blue-200 border-t-blue-600 rounded-full"></div>
					<span class="text-sm text-blue-600 font-medium">
						Analyzing... {Math.round($analysisProgress)}%
					</span>
				</div>
				<div class="progress-bar">
					<div 
						class="progress-fill"
						style="width: {$analysisProgress}%"
					></div>
				</div>
			</div>
		{/if}

		<!-- Theme Toggle -->
		<button 
			class="theme-toggle"
			on:click={toggleTheme}
			title="Toggle theme"
		>
			{#if theme === 'light'}
				<!-- Moon icon for dark mode -->
				<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"/>
				</svg>
			{:else}
				<!-- Sun icon for light mode -->
				<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"/>
				</svg>
			{/if}
		</button>

		<!-- User Menu (placeholder for future auth) -->
		<div class="user-menu">
			<button class="user-button">
				<div class="user-avatar">
					<svg class="w-6 h-6 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
						<path fill-rule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clip-rule="evenodd"/>
					</svg>
				</div>
				<span class="user-name hidden sm:block">User</span>
				<svg class="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
				</svg>
			</button>
		</div>

		<!-- Quick Actions (future) -->
		<div class="quick-actions hidden lg:flex">
			<!-- Placeholder for quick action buttons -->
		</div>
	</div>
</header>

<style>
	.header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 1rem 1.5rem;
		background-color: white;
		border-bottom: 1px solid #e5e7eb;
		min-height: 4rem;
	}

	.header-left {
		display: flex;
		align-items: center;
		space-x: 1rem;
	}

	.header-right {
		display: flex;
		align-items: center;
		space-x: 1rem;
	}

	.mobile-menu-btn {
		background: transparent;
		border: none;
		cursor: pointer;
		padding: 0.5rem;
		border-radius: 0.375rem;
		color: #6b7280;
		transition: all 0.2s ease-in-out;
		margin-right: 1rem;
	}

	.mobile-menu-btn:hover {
		background-color: #f3f4f6;
		color: #374151;
	}

	.page-title {
		min-width: 0;
	}

	.analysis-indicator {
		display: flex;
		flex-direction: column;
		align-items: flex-end;
		min-width: 12rem;
	}

	.progress-bar {
		width: 12rem;
		height: 0.25rem;
		background-color: #e5e7eb;
		border-radius: 0.125rem;
		overflow: hidden;
		margin-top: 0.25rem;
	}

	.progress-fill {
		height: 100%;
		background-color: #2563eb;
		border-radius: 0.125rem;
		transition: width 0.3s ease-in-out;
	}

	.theme-toggle {
		background: transparent;
		border: none;
		cursor: pointer;
		padding: 0.5rem;
		border-radius: 0.375rem;
		color: #6b7280;
		transition: all 0.2s ease-in-out;
	}

	.theme-toggle:hover {
		background-color: #f3f4f6;
		color: #374151;
	}

	.user-menu {
		position: relative;
	}

	.user-button {
		display: flex;
		align-items: center;
		padding: 0.5rem;
		border-radius: 0.375rem;
		color: #6b7280;
		background: transparent;
		border: none;
		cursor: pointer;
		transition: all 0.2s ease-in-out;
	}

	.user-button:hover {
		background-color: #f3f4f6;
		color: #374151;
	}

	.user-avatar {
		width: 2rem;
		height: 2rem;
		border-radius: 50%;
		background-color: #f3f4f6;
		display: flex;
		align-items: center;
		justify-content: center;
		margin-right: 0.5rem;
	}

	.user-name {
		font-weight: 500;
		font-size: 0.875rem;
	}

	.quick-actions {
		display: flex;
		align-items: center;
		space-x: 0.5rem;
	}

	/* Dark theme adjustments */
	:global(.dark) .header {
		background-color: #1f2937;
		border-bottom-color: #374151;
	}

	:global(.dark) .mobile-menu-btn {
		color: #d1d5db;
	}

	:global(.dark) .mobile-menu-btn:hover {
		background-color: #374151;
		color: #f9fafb;
	}

	:global(.dark) .theme-toggle {
		color: #d1d5db;
	}

	:global(.dark) .theme-toggle:hover {
		background-color: #374151;
		color: #f9fafb;
	}

	:global(.dark) .user-button {
		color: #d1d5db;
	}

	:global(.dark) .user-button:hover {
		background-color: #374151;
		color: #f9fafb;
	}

	:global(.dark) .user-avatar {
		background-color: #374151;
	}

	:global(.dark) .progress-bar {
		background-color: #374151;
	}

	/* Mobile responsiveness */
	@media (max-width: 640px) {
		.header {
			padding: 1rem;
		}

		.analysis-indicator {
			min-width: 8rem;
		}

		.progress-bar {
			width: 8rem;
		}

		.user-name {
			display: none;
		}
	}
</style>
