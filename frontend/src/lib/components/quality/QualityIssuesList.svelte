<script>
	import { createEventDispatcher } from 'svelte';
	
	export let issues = [];
	export let showFilters = true;
	export let showActions = true;
	export let pageSize = 10;

	const dispatch = createEventDispatcher();

	let currentPage = 1;
	let selectedIssues = new Set();
	let filters = {
		severity: 'all',
		type: 'all',
		status: 'all',
		autoFixable: 'all'
	};
	let sortBy = 'createdAt';
	let sortOrder = 'desc';

	const severityColors = {
		critical: 'bg-red-500/20 text-red-300 border-red-400/30',
		high: 'bg-orange-500/20 text-orange-300 border-orange-400/30',
		medium: 'bg-yellow-500/20 text-yellow-300 border-yellow-400/30',
		low: 'bg-blue-500/20 text-blue-300 border-blue-400/30'
	};

	const typeIcons = {
		complexity: 'M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z',
		coverage: 'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z',
		style: 'M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zM7 21h10a2 2 0 002-2v-5a2 2 0 00-2-2H9a2 2 0 00-2 2v5a4 4 0 004 4z',
		security: 'M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z',
		performance: 'M13 10V3L4 14h7v7l9-11h-7z'
	};

	$: filteredIssues = filterAndSortIssues(issues, filters, sortBy, sortOrder);
	$: paginatedIssues = paginateIssues(filteredIssues, currentPage, pageSize);
	$: totalPages = Math.ceil(filteredIssues.length / pageSize);

	function filterAndSortIssues(issues, filters, sortBy, sortOrder) {
		let filtered = issues.filter(issue => {
			if (filters.severity !== 'all' && issue.severity !== filters.severity) return false;
			if (filters.type !== 'all' && issue.type !== filters.type) return false;
			if (filters.status !== 'all' && issue.status !== filters.status) return false;
			if (filters.autoFixable !== 'all') {
				const isAutoFixable = issue.autoFixable === true;
				if (filters.autoFixable === 'yes' && !isAutoFixable) return false;
				if (filters.autoFixable === 'no' && isAutoFixable) return false;
			}
			return true;
		});

		// Sort issues
		filtered.sort((a, b) => {
			let aVal = a[sortBy];
			let bVal = b[sortBy];

			if (sortBy === 'createdAt') {
				aVal = new Date(aVal);
				bVal = new Date(bVal);
			}

			if (sortOrder === 'asc') {
				return aVal > bVal ? 1 : -1;
			} else {
				return aVal < bVal ? 1 : -1;
			}
		});

		return filtered;
	}

	function paginateIssues(issues, page, size) {
		const start = (page - 1) * size;
		return issues.slice(start, start + size);
	}

	function handleIssueSelect(issueId, selected) {
		if (selected) {
			selectedIssues.add(issueId);
		} else {
			selectedIssues.delete(issueId);
		}
		selectedIssues = selectedIssues; // Trigger reactivity
	}

	function handleSelectAll(selected) {
		if (selected) {
			paginatedIssues.forEach(issue => selectedIssues.add(issue.id));
		} else {
			selectedIssues.clear();
		}
		selectedIssues = selectedIssues; // Trigger reactivity
	}

	function handleBulkAction(action) {
		const issueIds = Array.from(selectedIssues);
		dispatch('bulkAction', { action, issueIds });
		selectedIssues.clear();
		selectedIssues = selectedIssues;
	}

	function handleIssueAction(issue, action) {
		dispatch('issueAction', { issue, action });
	}

	function formatDate(dateString) {
		return new Date(dateString).toLocaleDateString('en-US', {
			month: 'short',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	}

	function changePage(newPage) {
		if (newPage >= 1 && newPage <= totalPages) {
			currentPage = newPage;
		}
	}
</script>

<div class="space-y-6">
	<!-- Header -->
	<div class="flex justify-between items-center">
		<h2 class="text-xl font-bold text-white">Quality Issues</h2>
		<div class="text-sm text-gray-400">
			{filteredIssues.length} issues found
		</div>
	</div>

	<!-- Filters -->
	{#if showFilters}
		<div class="grid grid-cols-1 md:grid-cols-4 gap-4 p-4 bg-white/5 rounded-xl border border-white/10">
			<div>
				<label class="block text-sm font-medium text-gray-300 mb-2">Severity</label>
				<select bind:value={filters.severity} class="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-400">
					<option value="all" class="bg-gray-800">All Severities</option>
					<option value="critical" class="bg-gray-800">Critical</option>
					<option value="high" class="bg-gray-800">High</option>
					<option value="medium" class="bg-gray-800">Medium</option>
					<option value="low" class="bg-gray-800">Low</option>
				</select>
			</div>
			<div>
				<label class="block text-sm font-medium text-gray-300 mb-2">Type</label>
				<select bind:value={filters.type} class="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-400">
					<option value="all" class="bg-gray-800">All Types</option>
					<option value="complexity" class="bg-gray-800">Complexity</option>
					<option value="coverage" class="bg-gray-800">Coverage</option>
					<option value="style" class="bg-gray-800">Style</option>
					<option value="security" class="bg-gray-800">Security</option>
					<option value="performance" class="bg-gray-800">Performance</option>
				</select>
			</div>
			<div>
				<label class="block text-sm font-medium text-gray-300 mb-2">Status</label>
				<select bind:value={filters.status} class="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-400">
					<option value="all" class="bg-gray-800">All Statuses</option>
					<option value="open" class="bg-gray-800">Open</option>
					<option value="in_progress" class="bg-gray-800">In Progress</option>
					<option value="resolved" class="bg-gray-800">Resolved</option>
				</select>
			</div>
			<div>
				<label class="block text-sm font-medium text-gray-300 mb-2">Auto-fixable</label>
				<select bind:value={filters.autoFixable} class="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-400">
					<option value="all" class="bg-gray-800">All Issues</option>
					<option value="yes" class="bg-gray-800">Auto-fixable</option>
					<option value="no" class="bg-gray-800">Manual Fix</option>
				</select>
			</div>
		</div>
	{/if}

	<!-- Bulk Actions -->
	{#if showActions && selectedIssues.size > 0}
		<div class="flex items-center space-x-4 p-4 bg-blue-500/10 border border-blue-400/30 rounded-xl">
			<span class="text-blue-300 text-sm">{selectedIssues.size} issues selected</span>
			<div class="flex space-x-2">
				<button 
					on:click={() => handleBulkAction('resolve')}
					class="px-3 py-1 bg-green-500/20 hover:bg-green-500/30 text-green-300 rounded-lg text-sm transition-colors"
				>
					Resolve
				</button>
				<button 
					on:click={() => handleBulkAction('autofix')}
					class="px-3 py-1 bg-purple-500/20 hover:bg-purple-500/30 text-purple-300 rounded-lg text-sm transition-colors"
				>
					Auto-fix
				</button>
				<button 
					on:click={() => handleBulkAction('assign')}
					class="px-3 py-1 bg-blue-500/20 hover:bg-blue-500/30 text-blue-300 rounded-lg text-sm transition-colors"
				>
					Assign
				</button>
			</div>
		</div>
	{/if}

	<!-- Issues Table -->
	<div class="bg-white/5 rounded-xl border border-white/10 overflow-hidden">
		<div class="overflow-x-auto">
			<table class="w-full">
				<thead class="bg-white/5">
					<tr>
						{#if showActions}
							<th class="px-4 py-3 text-left">
								<input 
									type="checkbox" 
									checked={selectedIssues.size === paginatedIssues.length && paginatedIssues.length > 0}
									on:change={(e) => handleSelectAll(e.target.checked)}
									class="rounded border-gray-600 bg-gray-700 text-blue-500 focus:ring-blue-400"
								/>
							</th>
						{/if}
						<th class="px-4 py-3 text-left text-sm font-medium text-gray-300">Issue</th>
						<th class="px-4 py-3 text-left text-sm font-medium text-gray-300">Severity</th>
						<th class="px-4 py-3 text-left text-sm font-medium text-gray-300">Type</th>
						<th class="px-4 py-3 text-left text-sm font-medium text-gray-300">Status</th>
						<th class="px-4 py-3 text-left text-sm font-medium text-gray-300">File</th>
						<th class="px-4 py-3 text-left text-sm font-medium text-gray-300">Created</th>
						{#if showActions}
							<th class="px-4 py-3 text-left text-sm font-medium text-gray-300">Actions</th>
						{/if}
					</tr>
				</thead>
				<tbody class="divide-y divide-white/10">
					{#each paginatedIssues as issue}
						<tr class="hover:bg-white/5 transition-colors">
							{#if showActions}
								<td class="px-4 py-3">
									<input 
										type="checkbox" 
										checked={selectedIssues.has(issue.id)}
										on:change={(e) => handleIssueSelect(issue.id, e.target.checked)}
										class="rounded border-gray-600 bg-gray-700 text-blue-500 focus:ring-blue-400"
									/>
								</td>
							{/if}
							<td class="px-4 py-3">
								<div class="flex items-start space-x-3">
									<div class="w-8 h-8 bg-white/10 rounded-lg flex items-center justify-center flex-shrink-0">
										<svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d={typeIcons[issue.type] || typeIcons.complexity}/>
										</svg>
									</div>
									<div>
										<p class="text-white font-medium text-sm">{issue.title}</p>
										{#if issue.lineNumber}
											<p class="text-gray-400 text-xs">Line {issue.lineNumber}</p>
										{/if}
									</div>
								</div>
							</td>
							<td class="px-4 py-3">
								<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border {severityColors[issue.severity] || severityColors.low}">
									{issue.severity}
								</span>
							</td>
							<td class="px-4 py-3">
								<span class="text-gray-300 text-sm capitalize">{issue.type}</span>
							</td>
							<td class="px-4 py-3">
								<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {
									issue.status === 'open' ? 'bg-red-500/20 text-red-300' :
									issue.status === 'in_progress' ? 'bg-yellow-500/20 text-yellow-300' :
									'bg-green-500/20 text-green-300'
								}">
									{issue.status.replace('_', ' ')}
								</span>
							</td>
							<td class="px-4 py-3">
								<span class="text-gray-400 text-sm font-mono">{issue.filePath}</span>
							</td>
							<td class="px-4 py-3">
								<span class="text-gray-400 text-sm">{formatDate(issue.createdAt)}</span>
							</td>
							{#if showActions}
								<td class="px-4 py-3">
									<div class="flex items-center space-x-2">
										{#if issue.autoFixable}
											<button 
												on:click={() => handleIssueAction(issue, 'autofix')}
												class="p-1 text-purple-400 hover:text-purple-300 hover:bg-purple-500/20 rounded transition-colors"
												title="Auto-fix"
											>
												<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
													<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
												</svg>
											</button>
										{/if}
										<button 
											on:click={() => handleIssueAction(issue, 'view')}
											class="p-1 text-blue-400 hover:text-blue-300 hover:bg-blue-500/20 rounded transition-colors"
											title="View details"
										>
											<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
											</svg>
										</button>
										<button 
											on:click={() => handleIssueAction(issue, 'resolve')}
											class="p-1 text-green-400 hover:text-green-300 hover:bg-green-500/20 rounded transition-colors"
											title="Mark as resolved"
										>
											<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
											</svg>
										</button>
									</div>
								</td>
							{/if}
						</tr>
					{/each}
				</tbody>
			</table>
		</div>

		<!-- Pagination -->
		{#if totalPages > 1}
			<div class="px-4 py-3 bg-white/5 border-t border-white/10 flex items-center justify-between">
				<div class="text-sm text-gray-400">
					Showing {(currentPage - 1) * pageSize + 1} to {Math.min(currentPage * pageSize, filteredIssues.length)} of {filteredIssues.length} issues
				</div>
				<div class="flex items-center space-x-2">
					<button 
						on:click={() => changePage(currentPage - 1)}
						disabled={currentPage === 1}
						class="px-3 py-1 bg-white/10 hover:bg-white/20 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg text-sm transition-colors"
					>
						Previous
					</button>
					{#each Array.from({length: Math.min(5, totalPages)}, (_, i) => i + Math.max(1, currentPage - 2)) as page}
						{#if page <= totalPages}
							<button 
								on:click={() => changePage(page)}
								class="px-3 py-1 {page === currentPage ? 'bg-blue-500 text-white' : 'bg-white/10 hover:bg-white/20 text-gray-300'} rounded-lg text-sm transition-colors"
							>
								{page}
							</button>
						{/if}
					{/each}
					<button 
						on:click={() => changePage(currentPage + 1)}
						disabled={currentPage === totalPages}
						class="px-3 py-1 bg-white/10 hover:bg-white/20 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg text-sm transition-colors"
					>
						Next
					</button>
				</div>
			</div>
		{/if}
	</div>
</div>