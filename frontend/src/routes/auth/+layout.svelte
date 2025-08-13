<script>
	import '../../app.css';
</script>

<div class="auth-layout">
	<slot />
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

	.auth-layout {
		min-height: 100vh;
		background-color: #f9fafb;
	}

	/* Dark theme adjustments */
	:global(.dark) .auth-layout {
		background-color: #111827;
	}
</style>