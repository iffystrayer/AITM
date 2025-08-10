<script>
	import { createEventDispatcher } from 'svelte';
	import LoadingSpinner from '../ui/LoadingSpinner.svelte';
	import { MessageCircleIcon, BrainIcon, SendIcon, LightbulbIcon } from 'lucide-svelte';
	
	const dispatch = createEventDispatcher();
	
	export let context = null;
	export let placeholder = "Ask me anything about cybersecurity, threat analysis, or security best practices...";
	
	let query = '';
	let loading = false;
	let response = null;
	let error = null;
	let conversationHistory = [];
	
	// Example queries to help users get started
	const exampleQueries = [
		"What are the most critical security risks for a cloud-based e-commerce application?",
		"How can I protect my API endpoints from common attacks?",
		"What are the key indicators of a supply chain attack?",
		"How do I implement zero trust security architecture?",
		"What security controls should I prioritize for container deployments?",
		"How can I detect and prevent SQL injection attacks?",
		"What are the requirements for SOC 2 compliance?",
		"How do I create an effective incident response plan?"
	];
	
	async function submitQuery() {
		if (!query.trim()) {
			error = 'Please enter a security question';
			return;
		}
		
		loading = true;
		error = null;
		response = null;
		
		try {
			const apiResponse = await fetch('/api/v1/enhanced-ai/query/natural-language', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
				},
				body: JSON.stringify({
					query: query,
					context: context,
					include_recommendations: true
				})
			});
			
			if (!apiResponse.ok) {
				const errorData = await apiResponse.json();
				throw new Error(errorData.detail || `Query failed with status ${apiResponse.status}`);
			}
			
			response = await apiResponse.json();
			
			// Add to conversation history
			conversationHistory = [
				...conversationHistory,
				{
					type: 'question',
					content: query,
					timestamp: new Date().toISOString()
				},
				{
					type: 'answer',
					content: response,
					timestamp: new Date().toISOString()
				}
			];
			
			// Dispatch event for parent components
			dispatch('queryComplete', {
				query: query,
				response: response
			});
			
			// Clear the query
			query = '';
			
		} catch (err) {
			error = err.message;
			console.error('Natural language query failed:', err);
		} finally {
			loading = false;
		}
	}
	
	function handleKeyPress(event) {
		if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) {
			event.preventDefault();
			submitQuery();
		}
	}
	
	function useExampleQuery(exampleQuery) {
		query = exampleQuery;
	}
	
	function clearConversation() {
		conversationHistory = [];
		response = null;
		error = null;
	}
	
	function formatConfidence(confidence) {
		return `${(confidence * 100).toFixed(1)}%`;
	}
</script>

<div class="natural-language-query">
	<!-- Header -->
	<div class="bg-gradient-to-r from-green-600 to-blue-600 text-white p-6 rounded-t-lg">
		<div class="flex items-center gap-3">
			<MessageCircleIcon size={24} />
			<div>
				<h2 class="text-xl font-bold">AI Security Analyst</h2>
				<p class="text-green-100">Ask natural language questions about cybersecurity and threat modeling</p>
			</div>
		</div>
	</div>
	
	<div class="bg-white border-x border-b border-gray-200 rounded-b-lg">
		<!-- Query Input Section -->
		<div class="p-6 border-b border-gray-200">
			<div class="space-y-4">
				<!-- Query Input -->
				<div>
					<label for="securityQuery" class="block text-sm font-medium text-gray-700 mb-2">
						Ask Your Security Question
					</label>
					<div class="relative">
						<textarea
							id="securityQuery"
							bind:value={query}
							{placeholder}
							rows="3"
							class="w-full px-3 py-2 pr-12 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 resize-none"
							disabled={loading}
							on:keypress={handleKeyPress}
						></textarea>
						<button
							on:click={submitQuery}
							disabled={loading || !query.trim()}
							class="absolute bottom-2 right-2 p-2 bg-green-500 text-white rounded-md hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
							title="Send query (Ctrl+Enter)"
						>
							{#if loading}
								<LoadingSpinner size={16} />
							{:else}
								<SendIcon size={16} />
							{/if}
						</button>
					</div>
					<p class="text-xs text-gray-500 mt-1">Press Ctrl+Enter to send your question</p>
				</div>
				
				<!-- Example Queries -->
				{#if conversationHistory.length === 0}
					<div>
						<label class="block text-sm font-medium text-gray-700 mb-2">
							<LightbulbIcon size={16} class="inline mr-1" />
							Example Questions
						</label>
						<div class="grid grid-cols-1 md:grid-cols-2 gap-2">
							{#each exampleQueries.slice(0, 6) as example}
								<button
									on:click={() => useExampleQuery(example)}
									class="text-left p-3 text-sm text-gray-600 border border-gray-200 rounded-lg hover:border-green-300 hover:bg-green-50 transition-colors"
									disabled={loading}
								>
									"{example}"
								</button>
							{/each}
						</div>
					</div>
				{/if}
			</div>
		</div>
		
		<!-- Conversation History -->
		{#if conversationHistory.length > 0}
			<div class="p-6">
				<div class="flex items-center justify-between mb-4">
					<h3 class="text-lg font-semibold text-gray-900">Conversation</h3>
					<button
						on:click={clearConversation}
						class="text-sm text-gray-500 hover:text-red-500 transition-colors"
					>
						Clear History
					</button>
				</div>
				
				<div class="space-y-6 max-h-96 overflow-y-auto">
					{#each conversationHistory as message}
						{#if message.type === 'question'}
							<div class="flex justify-end">
								<div class="bg-blue-500 text-white rounded-lg px-4 py-2 max-w-3xl">
									<p class="text-sm">{message.content}</p>
									<p class="text-xs text-blue-200 mt-1">
										{new Date(message.timestamp).toLocaleTimeString()}
									</p>
								</div>
							</div>
						{:else if message.type === 'answer'}
							<div class="flex justify-start">
								<div class="bg-gray-100 rounded-lg px-4 py-3 max-w-4xl">
									<div class="flex items-start gap-3">
										<BrainIcon size={16} class="text-green-500 mt-1 flex-shrink-0" />
										<div class="flex-1">
											<p class="text-sm text-gray-800 mb-2">{message.content.answer}</p>
											
											{#if message.content.recommendations && message.content.recommendations.length > 0}
												<div class="mt-3">
													<h4 class="font-medium text-gray-800 text-sm mb-2">Recommendations:</h4>
													<ul class="space-y-1">
														{#each message.content.recommendations as recommendation}
															<li class="flex items-start gap-2 text-sm text-gray-600">
																<span class="text-green-500 mt-0.5 flex-shrink-0">•</span>
																<span>{recommendation}</span>
															</li>
														{/each}
													</ul>
												</div>
											{/if}
											
											{#if message.content.related_topics && message.content.related_topics.length > 0}
												<div class="mt-3">
													<h4 class="font-medium text-gray-800 text-sm mb-2">Related Topics:</h4>
													<div class="flex flex-wrap gap-2">
														{#each message.content.related_topics as topic}
															<span class="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">{topic}</span>
														{/each}
													</div>
												</div>
											{/if}
											
											<div class="flex items-center justify-between mt-3 pt-2 border-t border-gray-200 text-xs text-gray-500">
												<span>
													Confidence: {formatConfidence(message.content.confidence)}
													{#if message.content.context_used}• Context Applied{/if}
												</span>
												<span>{new Date(message.timestamp).toLocaleTimeString()}</span>
											</div>
										</div>
									</div>
								</div>
							</div>
						{/if}
					{/each}
				</div>
			</div>
		{/if}
		
		<!-- Current Response -->
		{#if loading}
			<div class="p-6 border-t border-gray-200">
				<div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
					<div class="flex items-center gap-3">
						<LoadingSpinner size={20} />
						<div>
							<h3 class="font-semibold text-blue-800">AI Analyst Thinking...</h3>
							<p class="text-blue-700 text-sm">Processing your security question and generating insights</p>
						</div>
					</div>
				</div>
			</div>
		{/if}
		
		{#if error}
			<div class="p-6 border-t border-gray-200">
				<div class="bg-red-50 border border-red-200 rounded-lg p-4">
					<div class="flex items-start gap-3">
						<MessageCircleIcon size={20} class="text-red-500 mt-0.5" />
						<div>
							<h3 class="font-semibold text-red-800">Query Failed</h3>
							<p class="text-red-700 mt-1">{error}</p>
							<button
								on:click={() => error = null}
								class="text-sm text-red-600 hover:text-red-800 mt-2 underline"
							>
								Try Again
							</button>
						</div>
					</div>
				</div>
			</div>
		{/if}
	</div>
</div>

<!-- Floating Action Button for Mobile -->
<div class="fixed bottom-6 right-6 md:hidden">
	<button
		on:click={() => document.getElementById('securityQuery')?.focus()}
		class="bg-green-500 hover:bg-green-600 text-white rounded-full p-4 shadow-lg transition-colors"
	>
		<MessageCircleIcon size={24} />
	</button>
</div>

<style>
	.natural-language-query {
		@apply max-w-6xl mx-auto;
	}
	
	/* Custom scrollbar for conversation history */
	.natural-language-query :global(.overflow-y-auto) {
		scrollbar-width: thin;
		scrollbar-color: #cbd5e1 #f1f5f9;
	}
	
	.natural-language-query :global(.overflow-y-auto)::-webkit-scrollbar {
		width: 6px;
	}
	
	.natural-language-query :global(.overflow-y-auto)::-webkit-scrollbar-track {
		background: #f1f5f9;
	}
	
	.natural-language-query :global(.overflow-y-auto)::-webkit-scrollbar-thumb {
		background: #cbd5e1;
		border-radius: 3px;
	}
	
	.natural-language-query :global(.overflow-y-auto)::-webkit-scrollbar-thumb:hover {
		background: #94a3b8;
	}
	
	/* Smooth animations */
	.natural-language-query :global(.space-y-6 > *) {
		animation: fadeInUp 0.3s ease-out;
	}
	
	@keyframes fadeInUp {
		from {
			opacity: 0;
			transform: translateY(10px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}
	
	/* Mobile responsiveness */
	@media (max-width: 768px) {
		.natural-language-query :global(.max-w-3xl),
		.natural-language-query :global(.max-w-4xl) {
			max-width: calc(100vw - 4rem);
		}
	}
</style>
