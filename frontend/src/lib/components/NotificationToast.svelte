<script>
	import { notification } from '$lib/stores';
	import { fade, fly } from 'svelte/transition';
	
	// Icon components for different notification types
	const icons = {
		success: `<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
			<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
		</svg>`,
		error: `<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
			<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
		</svg>`,
		warning: `<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
			<path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
		</svg>`,
		info: `<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
			<path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/>
		</svg>`
	};

	const typeClasses = {
		success: 'bg-green-50 border-green-200 text-green-800',
		error: 'bg-red-50 border-red-200 text-red-800',
		warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
		info: 'bg-blue-50 border-blue-200 text-blue-800'
	};

	const iconClasses = {
		success: 'text-green-400',
		error: 'text-red-400',
		warning: 'text-yellow-400',
		info: 'text-blue-400'
	};

	function closeNotification() {
		notification.set(null);
	}
</script>

{#if $notification}
	<div 
		class="notification-container"
		transition:fly="{{ y: -50, duration: 300 }}"
	>
		<div class="notification-toast {typeClasses[$notification.type]}">
			<div class="flex">
				<div class="flex-shrink-0">
					<div class="icon {iconClasses[$notification.type]}">
						{@html icons[$notification.type]}
					</div>
				</div>
				<div class="ml-3">
					<p class="text-sm font-medium">
						{$notification.message}
					</p>
				</div>
				<div class="ml-auto pl-3">
					<div class="-mx-1.5 -my-1.5">
						<button
							type="button"
							class="close-button"
							on:click={closeNotification}
						>
							<span class="sr-only">Dismiss</span>
							<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
								<path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
							</svg>
						</button>
					</div>
				</div>
			</div>
		</div>
	</div>
{/if}

<style>
	.notification-container {
		position: fixed;
		top: 1rem;
		right: 1rem;
		z-index: 10000;
		max-width: 24rem;
	}

	.notification-toast {
		border: 1px solid;
		border-radius: 0.5rem;
		padding: 1rem;
		box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
	}

	.icon {
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.close-button {
		display: inline-flex;
		border-radius: 0.375rem;
		color: currentColor;
		background-color: transparent;
		padding: 0.375rem;
		opacity: 0.7;
		transition: opacity 0.15s ease-in-out;
	}

	.close-button:hover {
		opacity: 1;
	}

	.close-button:focus {
		outline: none;
		ring: 2px solid;
		ring-offset: 2px;
	}

	/* Dark theme adjustments */
	:global(.dark) .notification-toast {
		background-color: rgba(55, 65, 81, 0.9);
		border-color: rgba(75, 85, 99, 0.5);
		color: #f3f4f6;
	}
</style>
