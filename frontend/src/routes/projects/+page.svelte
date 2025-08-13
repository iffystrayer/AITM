<script>
	import { onMount } from 'svelte';
	import { apiService } from '$lib/api';

	let projects = [];
	let loading = true;
	let error = null;
	let showCreateForm = false;
	let newProject = { name: '', description: '' };

	onMount(async () => {
		await loadProjects();
	});

	async function loadProjects() {
		try {
			loading = true;
			const response = await apiService.getProjects();
			projects = response.data || response || [];
			error = null;
		} catch (err) {
			error = 'Failed to load projects: ' + err.message;
			console.error('Error loading projects:', err);
		} finally {
			loading = false;
		}
	}

	async function createProject() {
		if (!newProject.name.trim()) {
			alert('Project name is required');
			return;
		}

		try {
			await apiService.createProject(newProject);
			newProject = { name: '', description: '' };
			showCreateForm = false;
			await loadProjects();
		} catch (err) {
			alert('Failed to create project: ' + err.message);
			console.error('Error creating project:', err);
		}
	}

	async function deleteProject(projectId) {
		if (!confirm('Are you sure you want to delete this project?')) {
			return;
		}

		try {
			await apiService.deleteProject(projectId);
			await loadProjects();
		} catch (err) {
			alert('Failed to delete project: ' + err.message);
			console.error('Error deleting project:', err);
		}
	}

	function formatDate(dateString) {
		return new Date(dateString).toLocaleDateString('en-US', {
			year: 'numeric',
			month: 'short',
			day: 'numeric'
		});
	}

	function getStatusColor(status) {
		switch (status) {
			case 'completed': return 'bg-green-100 text-green-800';
			case 'analyzing': return 'bg-blue-100 text-blue-800';
			case 'failed': return 'bg-red-100 text-red-800';
			default: return 'bg-gray-100 text-gray-800';
		}
	}
</script>

<svelte:head>
	<title>Projects - AITM</title>
</svelte:head>

<!-- Background with gradient and animated elements -->
<div class="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
	<!-- Animated background elements -->
	<div class="absolute inset-0 overflow-hidden">
		<div class="absolute -top-40 -right-40 w-80 h-80 bg-purple-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob"></div>
		<div class="absolute -bottom-40 -left-40 w-80 h-80 bg-cyan-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob animation-delay-2000"></div>
		<div class="absolute top-40 left-40 w-80 h-80 bg-pink-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob animation-delay-4000"></div>
	</div>

	<div class="relative space-y-8 p-6">
		<!-- Header -->
		<div class="bg-white/10 backdrop-blur-sm border border-white/20 rounded-2xl shadow-2xl p-8">
			<div class="flex justify-between items-center mb-4">
				<div>
					<h2 class="text-3xl font-bold bg-gradient-to-r from-cyan-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
						Threat Modeling Projects
					</h2>
					<p class="text-gray-300 mt-2 text-lg">
						Manage and organize your security analysis projects
					</p>
				</div>
				<button
					class="bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 text-white px-6 py-3 rounded-xl font-semibold transform transition-all duration-200 hover:scale-105 shadow-lg hover:shadow-xl flex items-center space-x-2"
					on:click={() => showCreateForm = true}
				>
					<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/>
					</svg>
					<span>New Project</span>
				</button>
			</div>

			{#if error}
				<div class="p-6 bg-red-500/10 backdrop-blur-sm border border-red-400/30 rounded-xl">
					<div class="flex">
						<div class="flex-shrink-0">
							<div class="w-10 h-10 bg-red-500/20 rounded-full flex items-center justify-center">
								<svg class="w-6 h-6 text-red-400" fill="currentColor" viewBox="0 0 20 20">
									<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
								</svg>
							</div>
						</div>
						<div class="ml-4">
							<h3 class="text-lg font-semibold text-red-200">Error Loading Projects</h3>
							<div class="mt-2 text-red-300">
								<p>{error}</p>
							</div>
							<div class="mt-4">
								<button
									class="bg-red-500/20 hover:bg-red-500/30 text-red-200 px-4 py-2 rounded-xl transition-colors duration-200"
									on:click={loadProjects}
								>
									Retry
								</button>
							</div>
						</div>
					</div>
				</div>
			{/if}
		</div>

		<!-- Create Project Modal -->
		{#if showCreateForm}
			<div class="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
				<div class="bg-white/10 backdrop-blur-lg border border-white/20 rounded-2xl shadow-2xl p-8 max-w-md w-full mx-4">
					<h3 class="text-2xl font-bold text-white mb-6">Create New Project</h3>
					<form on:submit|preventDefault={createProject}>
						<div class="space-y-6">
							<div>
								<label class="block text-sm font-medium text-gray-200 mb-2">Project Name *</label>
								<input
									type="text"
									bind:value={newProject.name}
									class="w-full bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white placeholder-gray-300 focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:border-transparent backdrop-blur-sm transition-all duration-200"
									placeholder="Enter project name"
									required
								>
							</div>
							<div>
								<label class="block text-sm font-medium text-gray-200 mb-2">Description</label>
								<textarea
									bind:value={newProject.description}
									class="w-full bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white placeholder-gray-300 focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:border-transparent backdrop-blur-sm transition-all duration-200"
									rows="3"
									placeholder="Optional project description"
								></textarea>
							</div>
						</div>
						<div class="flex justify-end space-x-4 mt-8">
							<button
								type="button"
								class="px-6 py-3 text-gray-300 bg-white/10 hover:bg-white/20 rounded-xl transition-colors duration-200"
								on:click={() => showCreateForm = false}
							>
								Cancel
							</button>
							<button
								type="submit"
								class="px-6 py-3 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 text-white rounded-xl font-semibold transform transition-all duration-200 hover:scale-105 shadow-lg"
							>
								Create Project
							</button>
						</div>
					</form>
				</div>
			</div>
		{/if}

		<!-- Projects List -->
		{#if loading}
			<div class="bg-white/10 backdrop-blur-sm border border-white/20 rounded-2xl shadow-2xl p-12">
				<div class="text-center">
					<div class="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-cyan-500 to-blue-600 rounded-full mb-4">
						<svg class="animate-spin w-8 h-8 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
							<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
							<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
						</svg>
					</div>
					<p class="text-gray-300 text-lg">Loading projects...</p>
				</div>
			</div>
		{:else if projects.length === 0}
			<div class="bg-white/10 backdrop-blur-sm border border-white/20 rounded-2xl shadow-2xl p-12 text-center">
				<div class="mx-auto flex items-center justify-center h-16 w-16 rounded-2xl bg-gradient-to-r from-purple-500/20 to-pink-500/20 mb-6">
					<svg class="h-8 w-8 text-purple-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/>
					</svg>
				</div>
				<h3 class="text-xl font-semibold text-white mb-2">No projects yet</h3>
				<p class="text-gray-300 mb-8">Get started by creating your first threat modeling project.</p>
				<button
					class="bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 text-white px-6 py-3 rounded-xl font-semibold transform transition-all duration-200 hover:scale-105 shadow-lg"
					on:click={() => showCreateForm = true}
				>
					Create First Project
				</button>
			</div>
		{:else}
			<div class="bg-white/10 backdrop-blur-sm border border-white/20 rounded-2xl shadow-2xl overflow-hidden">
				<div class="p-8">
					<div class="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
						{#each projects as project (project.id)}
							<div class="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-6 hover:bg-white/10 hover:scale-105 transition-all duration-300 shadow-lg">
								<div class="flex justify-between items-start mb-4">
									<h3 class="text-lg font-semibold text-white truncate">{project.name}</h3>
									<span class="px-3 py-1 text-xs font-semibold rounded-full {project.status === 'completed' ? 'bg-green-500/20 text-green-300' : project.status === 'analyzing' ? 'bg-blue-500/20 text-blue-300' : project.status === 'failed' ? 'bg-red-500/20 text-red-300' : 'bg-gray-500/20 text-gray-300'}">
										{project.status}
									</span>
								</div>
								{#if project.description}
									<p class="text-sm text-gray-300 mb-4 line-clamp-2">{project.description}</p>
								{/if}
								<div class="text-xs text-gray-400 mb-4">
									Created: {formatDate(project.created_at)}
								</div>
								<div class="flex justify-between items-center">
									<a
										href="/projects/{project.id}"
										class="text-cyan-400 hover:text-cyan-300 text-sm font-medium flex items-center space-x-1 transition-colors duration-200"
									>
										<span>View Details</span>
										<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
										</svg>
									</a>
									<button
										class="text-red-400 hover:text-red-300 text-sm transition-colors duration-200"
										on:click={() => deleteProject(project.id)}
										title="Delete project"
									>
										Delete
									</button>
								</div>
							</div>
						{/each}
					</div>
				</div>
			</div>
		{/if}
	</div>
</div>

<style>
	@keyframes blob {
		0% {
			transform: translate(0px, 0px) scale(1);
		}
		33% {
			transform: translate(30px, -50px) scale(1.1);
		}
		66% {
			transform: translate(-20px, 20px) scale(0.9);
		}
		100% {
			transform: translate(0px, 0px) scale(1);
		}
	}
	
	.animate-blob {
		animation: blob 7s infinite;
	}
	
	.animation-delay-2000 {
		animation-delay: 2s;
	}
	
	.animation-delay-4000 {
		animation-delay: 4s;
	}
</style>
