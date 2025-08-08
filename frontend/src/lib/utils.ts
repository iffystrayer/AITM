/**
 * AITM Frontend Utility Functions
 * Common operations and helpers
 */

// Date and time utilities
export const formatDate = (dateString: string): string => {
	const date = new Date(dateString);
	return date.toLocaleDateString('en-US', {
		year: 'numeric',
		month: 'short',
		day: 'numeric',
	});
};

export const formatDateTime = (dateString: string): string => {
	const date = new Date(dateString);
	return date.toLocaleString('en-US', {
		year: 'numeric',
		month: 'short',
		day: 'numeric',
		hour: '2-digit',
		minute: '2-digit',
	});
};

export const formatTimeAgo = (dateString: string): string => {
	const date = new Date(dateString);
	const now = new Date();
	const diffMs = now.getTime() - date.getTime();
	
	const diffMinutes = Math.floor(diffMs / (1000 * 60));
	const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
	const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
	
	if (diffMinutes < 1) return 'Just now';
	if (diffMinutes < 60) return `${diffMinutes}m ago`;
	if (diffHours < 24) return `${diffHours}h ago`;
	if (diffDays < 7) return `${diffDays}d ago`;
	
	return formatDate(dateString);
};

// Text formatting utilities
export const truncateText = (text: string, maxLength: number = 100): string => {
	if (text.length <= maxLength) return text;
	return text.substring(0, maxLength - 3) + '...';
};

export const capitalizeFirst = (text: string): string => {
	return text.charAt(0).toUpperCase() + text.slice(1);
};

export const camelToTitle = (text: string): string => {
	return text
		.replace(/([A-Z])/g, ' $1')
		.replace(/^./, (str) => str.toUpperCase())
		.trim();
};

// Priority and status utilities
export const getPriorityColor = (priority: 'high' | 'medium' | 'low'): string => {
	switch (priority) {
		case 'high': return 'text-red-600 bg-red-50 border-red-200';
		case 'medium': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
		case 'low': return 'text-green-600 bg-green-50 border-green-200';
		default: return 'text-gray-600 bg-gray-50 border-gray-200';
	}
};

export const getStatusColor = (status: 'draft' | 'analyzing' | 'completed' | 'failed' | 'proposed' | 'accepted' | 'implemented'): string => {
	switch (status) {
		case 'completed':
		case 'implemented':
			return 'text-green-600 bg-green-50 border-green-200';
		case 'analyzing':
			return 'text-blue-600 bg-blue-50 border-blue-200';
		case 'accepted':
			return 'text-purple-600 bg-purple-50 border-purple-200';
		case 'proposed':
		case 'draft':
			return 'text-gray-600 bg-gray-50 border-gray-200';
		case 'failed':
			return 'text-red-600 bg-red-50 border-red-200';
		default:
			return 'text-gray-600 bg-gray-50 border-gray-200';
	}
};

export const getCriticalityColor = (criticality: 'high' | 'medium' | 'low'): string => {
	switch (criticality) {
		case 'high': return 'text-red-600 bg-red-50 border-red-200';
		case 'medium': return 'text-orange-600 bg-orange-50 border-orange-200';
		case 'low': return 'text-green-600 bg-green-50 border-green-200';
		default: return 'text-gray-600 bg-gray-50 border-gray-200';
	}
};

export const getPriorityScoreColor = (score: number): string => {
	if (score >= 8) return 'text-red-600 bg-red-50';
	if (score >= 6) return 'text-orange-600 bg-orange-50';
	if (score >= 4) return 'text-yellow-600 bg-yellow-50';
	return 'text-green-600 bg-green-50';
};

// Risk level utilities
export const getRiskLevelColor = (riskLevel: string): string => {
	const level = riskLevel.toLowerCase();
	if (level.includes('critical') || level.includes('high')) {
		return 'text-red-600 bg-red-50 border-red-200';
	}
	if (level.includes('medium') || level.includes('moderate')) {
		return 'text-orange-600 bg-orange-50 border-orange-200';
	}
	if (level.includes('low') || level.includes('minimal')) {
		return 'text-green-600 bg-green-50 border-green-200';
	}
	return 'text-gray-600 bg-gray-50 border-gray-200';
};

// Progress and percentage utilities
export const formatPercentage = (value: number, decimals: number = 1): string => {
	return `${(value * 100).toFixed(decimals)}%`;
};

export const formatScore = (score: number, maxScore: number = 10): string => {
	return `${score.toFixed(1)}/${maxScore}`;
};

// Validation utilities
export const isValidEmail = (email: string): boolean => {
	const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
	return emailRegex.test(email);
};

export const isValidUrl = (url: string): boolean => {
	try {
		new URL(url);
		return true;
	} catch {
		return false;
	}
};

// Array utilities
export const groupBy = <T>(array: T[], key: keyof T): Record<string, T[]> => {
	return array.reduce((groups, item) => {
		const groupKey = String(item[key]);
		if (!groups[groupKey]) {
			groups[groupKey] = [];
		}
		groups[groupKey].push(item);
		return groups;
	}, {} as Record<string, T[]>);
};

export const unique = <T>(array: T[]): T[] => {
	return [...new Set(array)];
};

export const sortBy = <T>(array: T[], key: keyof T, direction: 'asc' | 'desc' = 'asc'): T[] => {
	return [...array].sort((a, b) => {
		const aVal = a[key];
		const bVal = b[key];
		
		if (aVal < bVal) return direction === 'asc' ? -1 : 1;
		if (aVal > bVal) return direction === 'asc' ? 1 : -1;
		return 0;
	});
};

// Search and filtering utilities
export const fuzzySearch = (items: any[], query: string, keys: string[]): any[] => {
	if (!query.trim()) return items;
	
	const searchTerm = query.toLowerCase();
	
	return items.filter(item => {
		return keys.some(key => {
			const value = getNestedValue(item, key);
			return String(value).toLowerCase().includes(searchTerm);
		});
	});
};

export const getNestedValue = (obj: any, path: string): any => {
	return path.split('.').reduce((current, key) => current?.[key], obj);
};

// File utilities
export const downloadJson = (data: any, filename: string): void => {
	const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
	const url = URL.createObjectURL(blob);
	const link = document.createElement('a');
	link.href = url;
	link.download = filename;
	document.body.appendChild(link);
	link.click();
	document.body.removeChild(link);
	URL.revokeObjectURL(url);
};

export const downloadCsv = (data: any[], filename: string): void => {
	if (data.length === 0) return;
	
	const headers = Object.keys(data[0]);
	const csvContent = [
		headers.join(','),
		...data.map(row => headers.map(header => JSON.stringify(row[header] || '')).join(','))
	].join('\n');
	
	const blob = new Blob([csvContent], { type: 'text/csv' });
	const url = URL.createObjectURL(blob);
	const link = document.createElement('a');
	link.href = url;
	link.download = filename;
	document.body.appendChild(link);
	link.click();
	document.body.removeChild(link);
	URL.revokeObjectURL(url);
};

export const readFileAsText = (file: File): Promise<string> => {
	return new Promise((resolve, reject) => {
		const reader = new FileReader();
		reader.onload = (e) => resolve(e.target?.result as string);
		reader.onerror = (e) => reject(e);
		reader.readAsText(file);
	});
};

// Copy to clipboard
export const copyToClipboard = async (text: string): Promise<boolean> => {
	try {
		if (navigator.clipboard && window.isSecureContext) {
			await navigator.clipboard.writeText(text);
			return true;
		} else {
			// Fallback for older browsers
			const textArea = document.createElement('textarea');
			textArea.value = text;
			textArea.style.position = 'fixed';
			textArea.style.left = '-999999px';
			textArea.style.top = '-999999px';
			document.body.appendChild(textArea);
			textArea.focus();
			textArea.select();
			const success = document.execCommand('copy');
			document.body.removeChild(textArea);
			return success;
		}
	} catch (error) {
		console.error('Failed to copy to clipboard:', error);
		return false;
	}
};

// URL utilities
export const buildQueryString = (params: Record<string, any>): string => {
	const filteredParams = Object.entries(params)
		.filter(([_, value]) => value !== null && value !== undefined && value !== '')
		.map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`);
	
	return filteredParams.length > 0 ? `?${filteredParams.join('&')}` : '';
};

export const parseQueryString = (search: string): Record<string, string> => {
	const params = new URLSearchParams(search);
	const result: Record<string, string> = {};
	
	for (const [key, value] of params) {
		result[key] = value;
	}
	
	return result;
};

// Local storage utilities with error handling (browser-only)
export const getFromStorage = <T>(key: string, defaultValue: T): T => {
	if (typeof window === 'undefined') return defaultValue;
	try {
		const item = localStorage.getItem(key);
		return item ? JSON.parse(item) : defaultValue;
	} catch (error) {
		console.warn(`Failed to get ${key} from localStorage:`, error);
		return defaultValue;
	}
};

export const setInStorage = (key: string, value: any): boolean => {
	if (typeof window === 'undefined') return false;
	try {
		localStorage.setItem(key, JSON.stringify(value));
		return true;
	} catch (error) {
		console.warn(`Failed to set ${key} in localStorage:`, error);
		return false;
	}
};

export const removeFromStorage = (key: string): boolean => {
	if (typeof window === 'undefined') return false;
	try {
		localStorage.removeItem(key);
		return true;
	} catch (error) {
		console.warn(`Failed to remove ${key} from localStorage:`, error);
		return false;
	}
};

// Theme utilities
export const getThemePreference = (): 'light' | 'dark' | 'system' => {
	return getFromStorage('theme-preference', 'system');
};

export const setThemePreference = (theme: 'light' | 'dark' | 'system'): void => {
	setInStorage('theme-preference', theme);
};

export const applyTheme = (theme: 'light' | 'dark' | 'system' = 'system'): void => {
	if (typeof window === 'undefined') return;
	const root = document.documentElement;
	
	if (theme === 'system') {
		const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
		root.classList.toggle('dark', prefersDark);
	} else {
		root.classList.toggle('dark', theme === 'dark');
	}
};

// Error handling utilities
export const extractErrorMessage = (error: any): string => {
	if (typeof error === 'string') return error;
	if (error?.response?.data?.detail) return error.response.data.detail;
	if (error?.response?.data?.message) return error.response.data.message;
	if (error?.message) return error.message;
	return 'An unexpected error occurred';
};

export const isNetworkError = (error: any): boolean => {
	return error?.code === 'NETWORK_ERROR' || 
		   error?.message?.includes('Network Error') ||
		   error?.code === 'ECONNREFUSED';
};

// Debounce utility
export const debounce = <T extends (...args: any[]) => any>(
	func: T,
	wait: number
): (...args: Parameters<T>) => void => {
	let timeout: NodeJS.Timeout;
	
	return (...args: Parameters<T>) => {
		clearTimeout(timeout);
		timeout = setTimeout(() => func(...args), wait);
	};
};

// Throttle utility
export const throttle = <T extends (...args: any[]) => any>(
	func: T,
	wait: number
): (...args: Parameters<T>) => void => {
	let inThrottle: boolean;
	
	return (...args: Parameters<T>) => {
		if (!inThrottle) {
			func(...args);
			inThrottle = true;
			setTimeout(() => inThrottle = false, wait);
		}
	};
};
