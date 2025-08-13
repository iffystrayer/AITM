<script>
	import { goto } from '$app/navigation';
	import { apiService } from '$lib/api';
	import { onMount } from 'svelte';

	let email = '';
	let password = '';
	let loading = false;
	let error = '';

	const handleLogin = async (e) => {
		e.preventDefault();
		loading = true;
		error = '';

		try {
			const formData = new FormData();
			formData.append('username', email);
			formData.append('password', password);

			const response = await fetch('http://localhost:38527/api/v1/auth/login', {
				method: 'POST',
				body: formData
			});

			if (response.ok) {
				const data = await response.json();
				// Store the token in localStorage
				localStorage.setItem('access_token', data.access_token);
				localStorage.setItem('refresh_token', data.refresh_token);
				
				// Redirect to dashboard
				goto('/');
			} else {
				const errorData = await response.json();
				error = errorData.detail || 'Login failed';
			}
		} catch (err) {
			error = 'Network error. Please try again.';
			console.error('Login error:', err);
		} finally {
			loading = false;
		}
	};

	onMount(() => {
		// Check if user is already logged in
		const token = localStorage.getItem('access_token');
		if (token) {
			goto('/');
		}
	});
</script>

<svelte:head>
	<title>Login - AITM</title>
</svelte:head>

<div class="min-h-screen bg-gradient-to-br from-indigo-900 via-purple-900 to-pink-800 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
	<!-- Background decoration -->
	<div class="absolute inset-0 bg-black opacity-50"></div>
	<div class="absolute inset-0">
		<div class="absolute top-0 left-0 w-72 h-72 bg-purple-300 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-blob"></div>
		<div class="absolute top-0 right-0 w-72 h-72 bg-yellow-300 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-blob animation-delay-2000"></div>
		<div class="absolute -bottom-8 left-20 w-72 h-72 bg-pink-300 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-blob animation-delay-4000"></div>
	</div>
	
	<div class="relative max-w-md w-full">
		<!-- Login Card -->
		<div class="bg-white/10 backdrop-blur-lg rounded-2xl shadow-2xl border border-white/20 p-8 space-y-8">
			<div class="text-center">
				<div class="mx-auto h-16 w-16 flex items-center justify-center bg-gradient-to-r from-cyan-400 to-blue-500 rounded-2xl shadow-lg">
					<svg class="w-10 h-10 text-white" fill="currentColor" viewBox="0 0 24 24">
						<path d="M12 2L2 7v10c0 5.55 3.84 9.74 9 11 5.16-1.26 9-5.45 9-11V7l-10-5z"></path>
					</svg>
				</div>
				<h2 class="mt-6 text-center text-3xl font-bold text-white">
					Welcome to AITM
				</h2>
				<p class="mt-2 text-center text-sm text-gray-200">
					AI-Powered Threat Modeler
				</p>
			</div>
			
			<form class="space-y-6" on:submit={handleLogin}>
				<div class="space-y-4">
					<div>
						<label for="email" class="block text-sm font-medium text-gray-200 mb-2">Email address</label>
						<input
							id="email"
							name="email"
							type="email"
							autocomplete="email"
							required
							bind:value={email}
							class="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-gray-300 focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:border-transparent backdrop-blur-sm transition-all duration-200"
							placeholder="Enter your email"
						/>
					</div>
					<div>
						<label for="password" class="block text-sm font-medium text-gray-200 mb-2">Password</label>
						<input
							id="password"
							name="password"
							type="password"
							autocomplete="current-password"
							required
							bind:value={password}
							class="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-gray-300 focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:border-transparent backdrop-blur-sm transition-all duration-200"
							placeholder="Enter your password"
						/>
					</div>
				</div>

				{#if error}
					<div class="bg-red-500/20 border border-red-400/30 text-red-200 px-4 py-3 rounded-xl backdrop-blur-sm">
						{error}
					</div>
				{/if}

				<button
					type="submit"
					disabled={loading}
					class="w-full flex justify-center py-3 px-4 border border-transparent text-sm font-semibold rounded-xl text-white bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:ring-offset-2 focus:ring-offset-transparent disabled:opacity-50 disabled:cursor-not-allowed transform transition-all duration-200 hover:scale-105 shadow-lg hover:shadow-xl"
				>
					{#if loading}
						<svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
							<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
							<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
						</svg>
						Signing in...
					{:else}
						<span class="flex items-center">
							<svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1"/>
							</svg>
							Sign in
						</span>
					{/if}
				</button>

				<div class="text-center">
					<p class="text-sm text-gray-300">
						Don't have an account? 
						<a href="/auth/register" class="font-semibold text-cyan-400 hover:text-cyan-300 transition-colors duration-200">
							Sign up
						</a>
					</p>
				</div>
			</form>
		</div>
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