<script>
	import { createEventDispatcher } from 'svelte';

	export let projectId;
	export let show = false;

	const dispatch = createEventDispatcher();

	let inputType = 'text'; // 'text' or 'file'
	let inputTitle = '';
	let inputDescription = '';
	let systemDescription = '';
	let fileInput;
	let uploading = false;
	let error = null;

	async function handleSubmit() {
		if (!inputTitle.trim()) {
			error = 'Input title is required';
			return;
		}

		if (inputType === 'text' && !systemDescription.trim()) {
			error = 'System description is required';
			return;
		}

		try {
			uploading = true;
			error = null;

			const inputData = {
				title: inputTitle.trim(),
				description: inputDescription.trim(),
				input_type: inputType,
				content: inputType === 'text' ? systemDescription.trim() : null
			};

			// If it's a file upload, handle that separately
			let response;
			if (inputType === 'file' && fileInput?.files?.[0]) {
				const formData = new FormData();
				formData.append('file', fileInput.files[0]);
				formData.append('title', inputTitle.trim());
				formData.append('description', inputDescription.trim());
				
				response = await fetch(`http://localhost:38527/api/v1/projects/${projectId}/inputs/upload`, {
					method: 'POST',
					body: formData
				});
			} else {
				// Text input
				response = await fetch(`http://localhost:38527/api/v1/projects/${projectId}/inputs`, {
					method: 'POST',
					headers: {
						'Content-Type': 'application/json',
					},
					body: JSON.stringify(inputData)
				});
			}

			if (response.ok) {
				// Reset form
				inputTitle = '';
				inputDescription = '';
				systemDescription = '';
				if (fileInput) fileInput.value = '';
				
				dispatch('inputAdded');
				show = false;
			} else {
				const errorData = await response.json();
				error = errorData.detail || 'Failed to add system input';
			}
		} catch (err) {
			error = 'Connection error: ' + err.message;
		} finally {
			uploading = false;
		}
	}

	function handleCancel() {
		// Reset form
		inputTitle = '';
		inputDescription = '';
		systemDescription = '';
		if (fileInput) fileInput.value = '';
		error = null;
		show = false;
	}

	function handleFileChange(event) {
		const file = event.target.files?.[0];
		if (file && !inputTitle) {
			// Auto-fill title with filename
			inputTitle = file.name.replace(/\.[^/.]+$/, ""); // Remove extension
		}
	}
</script>

{#if show}
	<!-- Modal Backdrop -->
	<div class="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
		<div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
			<div class="flex justify-between items-center mb-6">
				<h3 class="text-lg font-semibold text-gray-900 dark:text-white">Add System Input</h3>
				<button
					on:click={handleCancel}
					class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
				>
					<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
					</svg>
				</button>
			</div>

			{#if error}
				<div class="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
					<p class="text-sm text-red-800 dark:text-red-200">{error}</p>
				</div>
			{/if}

			<form on:submit|preventDefault={handleSubmit} class="space-y-6">
				<!-- Input Type Selection -->
				<div>
					<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">Input Type</label>
					<div class="flex space-x-4">
						<label class="flex items-center">
							<input
								type="radio"
								bind:group={inputType}
								value="text"
								class="mr-2 text-blue-600"
							>
							<span class="text-sm text-gray-700 dark:text-gray-300">Text Description</span>
						</label>
						<label class="flex items-center">
							<input
								type="radio"
								bind:group={inputType}
								value="file"
								class="mr-2 text-blue-600"
							>
							<span class="text-sm text-gray-700 dark:text-gray-300">File Upload</span>
						</label>
					</div>
				</div>

				<!-- Basic Information -->
				<div>
					<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
						Title *
					</label>
					<input
						type="text"
						bind:value={inputTitle}
						class="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
						placeholder="e.g., Web Application Architecture, Database Schema"
						required
					>
				</div>

				<div>
					<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
						Description
					</label>
					<textarea
						bind:value={inputDescription}
						class="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
						rows="2"
						placeholder="Optional description of this input"
					></textarea>
				</div>

				{#if inputType === 'text'}
					<!-- Text Input -->
					<div>
						<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
							System Description *
						</label>
						<textarea
							bind:value={systemDescription}
							class="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
							rows="8"
							placeholder="Describe your system architecture, components, data flows, trust boundaries, and security controls. The more detail you provide, the better the threat analysis will be."
							required
						></textarea>
						<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
							Include information about: technologies used, network architecture, data storage, user access patterns, external integrations, and existing security measures.
						</p>
					</div>
				{:else}
					<!-- File Upload -->
					<div>
						<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
							Upload File *
						</label>
						<input
							type="file"
							bind:this={fileInput}
							on:change={handleFileChange}
							accept=".txt,.md,.json,.yaml,.yml,.xml,.csv"
							class="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
							required
						>
						<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
							Supported formats: TXT, MD, JSON, YAML, XML, CSV. Max size: 10MB
						</p>
					</div>
				{/if}

				<!-- Form Actions -->
				<div class="flex justify-end space-x-3 pt-4 border-t border-gray-200 dark:border-gray-600">
					<button
						type="button"
						on:click={handleCancel}
						class="px-4 py-2 text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg"
						disabled={uploading}
					>
						Cancel
					</button>
					<button
						type="submit"
						class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed"
						disabled={uploading}
					>
						{#if uploading}
							<div class="flex items-center space-x-2">
								<div class="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
								<span>Adding...</span>
							</div>
						{:else}
							Add Input
						{/if}
					</button>
				</div>
			</form>
		</div>
	</div>
{/if}
