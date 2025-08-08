<script>
	import { onMount } from 'svelte';

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
			const response = await fetch('http://localhost:38527/api/v1/projects/');
			if (response.ok) {
				const data = await response.json();
				// API returns direct array, not wrapped in data property
				projects = Array.isArray(data) ? data : [];
				error = null;
			} else {
				error = 'Failed to load projects';
			}
		} catch (err) {
			error = 'Connection error: ' + err.message;
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
			const response = await fetch('http://localhost:38527/api/v1/projects/', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
				},
				body: JSON.stringify(newProject)
			});

			if (response.ok) {
				newProject = { name: '', description: '' };
				showCreateForm = false;
				await loadProjects();
			} else {
				const errorData = await response.json();
				alert('Failed to create project: ' + (errorData.detail || 'Unknown error'));
			}
		} catch (err) {
			alert('Connection error: ' + err.message);
		}
	}

	async function deleteProject(projectId) {
		if (!confirm('Are you sure you want to delete this project?')) {
			return;
		}

	try {
			const response = await fetch(`http://localhost:38527/api/v1/projects/${projectId}`, {
				method: 'DELETE'
			});

			if (response.ok) {
				await loadProjects();
			} else {
				alert('Failed to delete project');
			}
		} catch (err) {
			alert('Connection error: ' + err.message);
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

<div class="space-y-6">
	<!-- Header -->
	<div class="bg-white shadow rounded-lg p-6">
		<div class="flex justify-between items-center mb-4">
			<div>
				<h2 class="text-2xl font-bold text-gray-900">Threat Modeling Projects</h2>
				<p class="text-gray-600 mt-1">
					Manage and organize your security analysis projects
				</p>
			</div>
			<button
				class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium"
				on:click={() => showCreateForm = true}
			>
				+ New Project
			</button>
		</div>

		{#if error}
			<div class="p-4 bg-red-50 border border-red-200 rounded-lg">
				<div class="flex">
					<div class="flex-shrink-0">
						<svg class="w-5 h-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
							<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
						</svg>
					</div>
					<div class="ml-3">
						<h3 class="text-sm font-medium text-red-800">Error Loading Projects</h3>
						<div class="mt-2 text-sm text-red-700">
							<p>{error}</p>
						</div>
						<div class="mt-3">
							<button
								class="bg-red-100 hover:bg-red-200 text-red-800 px-3 py-1 rounded text-sm"
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
		<div class="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
			<div class="bg-white rounded-lg shadow-xl p-6 max-w-md w-full mx-4">
				<h3 class="text-lg font-semibold text-gray-900 mb-4">Create New Project</h3>
				<form on:submit|preventDefault={createProject}>
					<div class="space-y-4">
						<div>
							<label class="block text-sm font-medium text-gray-700 mb-1">Project Name *</label>
							<input
								type="text"
								bind:value={newProject.name}
								class="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
								placeholder="Enter project name"
								required
							>
						</div>
						<div>
							<label class="block text-sm font-medium text-gray-700 mb-1">Description</label>
							<textarea
								bind:value={newProject.description}
								class="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
								rows="3"
								placeholder="Optional project description"
							></textarea>
						</div>
					</div>
					<div class="flex justify-end space-x-3 mt-6">
						<button
							type="button"
							class="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg"
							on:click={() => showCreateForm = false}
						>
							Cancel
						</button>
						<button
							type="submit"
							class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
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
		<div class="bg-white shadow rounded-lg p-8">
			<div class="text-center">
				<div class="animate-spin inline-block w-6 h-6 border-2 border-gray-300 border-t-blue-600 rounded-full"></div>
				<p class="mt-2 text-gray-500">Loading projects...</p>
			</div>
		</div>
	{:else if projects.length === 0}
		<div class="bg-white shadow rounded-lg p-8 text-center">
			<div class="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-gray-100">
				<svg class="h-6 w-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/>
				</svg>
			</div>
			<h3 class="mt-2 text-sm font-medium text-gray-900">No projects yet</h3>
			<p class="mt-1 text-sm text-gray-500">Get started by creating your first threat modeling project.</p>
			<div class="mt-6">
				<button
					class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
					on:click={() => showCreateForm = true}
				>
					Create First Project
				</button>
			</div>
		</div>
	{:else}
		<div class="bg-white shadow overflow-hidden sm:rounded-lg">
			<div class="px-4 py-5 sm:p-6">
				<div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
					{#each projects as project (project.id)}
						<div class="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
							<div class="flex justify-between items-start mb-3">
								<h3 class="text-lg font-medium text-gray-900 truncate">{project.name}</h3>
								<span class="px-2 py-1 text-xs font-semibold rounded-full {getStatusColor(project.status)}">
									{project.status}
								</span>
							</div>
							{#if project.description}
								<p class="text-sm text-gray-600 mb-3 line-clamp-2">{project.description}</p>
							{/if}
							<div class="text-xs text-gray-500 mb-3">
								Created: {formatDate(project.created_at)}
							</div>
							<div class="flex justify-between items-center">
								<a
									href="/projects/{project.id}"
									class="text-blue-600 hover:text-blue-800 text-sm font-medium"
								>
									View Details →
								</a>
								<button
									class="text-red-600 hover:text-red-800 text-sm"
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
