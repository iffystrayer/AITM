import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import { resolve } from 'path';

export default defineConfig({
	plugins: [sveltekit()],
	server: {
		port: 41241,
		host: '127.0.0.1'
	},
	preview: {
		port: 41241,
		host: '127.0.0.1'
	},
	build: {
		// Production optimizations
		target: 'es2020',
		minify: 'esbuild',
		chunkSizeWarningLimit: 1000,
		ssrManifest: true,
		rollupOptions: {
			output: {
				// Optimize chunk splitting
				manualChunks: (id) => {
					// Separate vendor dependencies
					if (id.includes('node_modules')) {
						if (id.includes('svelte')) {
							return 'svelte-vendor';
						}
						if (id.includes('chart.js') || id.includes('chartjs')) {
							return 'charts-vendor';
						}
						if (id.includes('@playwright') || id.includes('playwright')) {
							return 'testing-vendor';
						}
						return 'vendor';
					}
					// Separate large component bundles
					if (id.includes('/components/project/')) {
						return 'project-components';
					}
					if (id.includes('/components/analytics/')) {
						return 'analytics-components';
					}
				},
				// Optimize asset naming
				assetFileNames: (assetInfo) => {
					const info = assetInfo.name.split('.');
					const ext = info[info.length - 1];
					if (/png|jpe?g|svg|gif|tiff|bmp|ico/i.test(ext)) {
						return `assets/images/[name]-[hash][extname]`;
					}
					if (/css/i.test(ext)) {
						return `assets/styles/[name]-[hash][extname]`;
					}
					return `assets/[name]-[hash][extname]`;
				},
				chunkFileNames: 'assets/js/[name]-[hash].js',
				entryFileNames: 'assets/js/[name]-[hash].js'
			}
		}
	},
	// Dependency optimization
	optimizeDeps: {
		include: [
			'chart.js/auto',
			'@sveltejs/kit',
			'svelte/store'
		],
		exclude: [
			'@playwright/test'
		]
	},
	// Performance optimizations
	define: {
		// Remove development-only code in production
		__DEV__: JSON.stringify(process.env.NODE_ENV !== 'production'),
		__PROD__: JSON.stringify(process.env.NODE_ENV === 'production')
	},
	resolve: {
		alias: {
			'$lib': resolve('./src/lib'),
			'$components': resolve('./src/lib/components'),
			'$stores': resolve('./src/lib/stores'),
			'$utils': resolve('./src/lib/utils')
		}
	},
	// CSS optimization
	css: {
		devSourcemap: true,
		preprocessor: {
			scss: {
				additionalData: '@use "sass:math";'
			}
		}
	}
});
