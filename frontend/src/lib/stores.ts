/**
 * AITM Frontend Svelte Stores
 * Global state management for the application
 */

import { writable, derived, type Readable } from 'svelte/store';
import type { 
	Project, 
	ThreatModelingStatus, 
	AttackPath, 
	Recommendation, 
	Asset,
	SystemInput,
	HealthStatus 
} from './api';

// Application state
export const isLoading = writable<boolean>(false);
export const error = writable<string | null>(null);
export const notification = writable<{
	type: 'success' | 'error' | 'warning' | 'info';
	message: string;
	duration?: number;
} | null>(null);

// Backend health status
export const healthStatus = writable<HealthStatus | null>(null);
export const isBackendHealthy = derived(
	healthStatus,
	($healthStatus) => $healthStatus?.status === 'healthy'
);

// Current project and related data
export const currentProject = writable<Project | null>(null);
export const projects = writable<Project[]>([]);

// Project-specific data
export const systemInputs = writable<SystemInput[]>([]);
export const assets = writable<Asset[]>([]);
export const attackPaths = writable<AttackPath[]>([]);
export const recommendations = writable<Recommendation[]>([]);

// Threat modeling analysis state
export const analysisStatus = writable<ThreatModelingStatus | null>(null);
export const isAnalyzing = derived(
	analysisStatus,
	($status) => $status?.status === 'analyzing'
);

export const analysisProgress = derived(
	analysisStatus,
	($status) => $status?.progress || 0
);

export const analysisCurrentStep = derived(
	analysisStatus,
	($status) => $status?.current_step || ''
);

// UI state
export const sidebarOpen = writable<boolean>(true);
export const currentPage = writable<'dashboard' | 'projects' | 'analysis' | 'assets' | 'reports' | 'mitre'>('dashboard');

// Selected items
export const selectedProject = writable<number | null>(null);
export const selectedAttackPath = writable<AttackPath | null>(null);
export const selectedRecommendation = writable<Recommendation | null>(null);

// Search and filtering
export const searchQuery = writable<string>('');
export const filterCriteria = writable<{
	priority?: 'high' | 'medium' | 'low';
	status?: 'proposed' | 'accepted' | 'implemented';
	tactic?: string;
}>({});

// Analysis configuration
export const analysisConfig = writable<{
	llm_provider: 'openai' | 'google' | 'ollama' | 'litellm';
	analysis_depth: 'quick' | 'standard' | 'deep';
	include_mitigations: boolean;
	include_executive_summary: boolean;
	include_technical_details: boolean;
	existing_controls: string[];
	control_documentation: string;
}>({
	llm_provider: 'openai',
	analysis_depth: 'standard',
	include_mitigations: true,
	include_executive_summary: true,
	include_technical_details: true,
	existing_controls: [],
	control_documentation: ''
});

// MITRE ATT&CK data
export const mitreTactics = writable<string[]>([]);
export const selectedTactic = writable<string>('');

// Utility functions for store management
export const storeUtils = {
	// Clear all project-specific data
	clearProjectData: () => {
		systemInputs.set([]);
		assets.set([]);
		attackPaths.set([]);
		recommendations.set([]);
		analysisStatus.set(null);
		selectedAttackPath.set(null);
		selectedRecommendation.set(null);
	},

	// Show notification
	showNotification: (
		type: 'success' | 'error' | 'warning' | 'info',
		message: string,
		duration: number = 5000
	) => {
		notification.set({ type, message, duration });
		
		if (duration > 0) {
			setTimeout(() => {
				notification.set(null);
			}, duration);
		}
	},

	// Set loading state with optional error clearing
	setLoading: (loading: boolean, clearError: boolean = true) => {
		isLoading.set(loading);
		if (clearError) {
			error.set(null);
		}
	},

	// Set error state
	setError: (errorMessage: string | null) => {
		error.set(errorMessage);
		isLoading.set(false);
		
		if (errorMessage) {
			storeUtils.showNotification('error', errorMessage);
		}
	},

	// Update current project and load related data
	setCurrentProject: (project: Project | null) => {
		currentProject.set(project);
		selectedProject.set(project?.id || null);
		
		if (!project) {
			storeUtils.clearProjectData();
		}
	},

	// Filter recommendations by criteria
	getFilteredRecommendations: (
		allRecommendations: Recommendation[],
		criteria: { priority?: string; status?: string; search?: string }
	): Recommendation[] => {
		return allRecommendations.filter(rec => {
			if (criteria.priority && rec.priority !== criteria.priority) return false;
			if (criteria.status && rec.status !== criteria.status) return false;
			if (criteria.search) {
				const search = criteria.search.toLowerCase();
				return rec.title.toLowerCase().includes(search) ||
					   rec.description.toLowerCase().includes(search);
			}
			return true;
		});
	},

	// Sort attack paths by priority score
	sortAttackPathsByPriority: (paths: AttackPath[]): AttackPath[] => {
		return [...paths].sort((a, b) => b.priority_score - a.priority_score);
	},

	// Get recommendation count by status
	getRecommendationStats: (recommendations: Recommendation[]) => {
		return {
			total: recommendations.length,
			proposed: recommendations.filter(r => r.status === 'proposed').length,
			accepted: recommendations.filter(r => r.status === 'accepted').length,
			implemented: recommendations.filter(r => r.status === 'implemented').length,
			high_priority: recommendations.filter(r => r.priority === 'high').length,
			medium_priority: recommendations.filter(r => r.priority === 'medium').length,
			low_priority: recommendations.filter(r => r.priority === 'low').length,
		};
	},

	// Get asset count by criticality
	getAssetStats: (allAssets: Asset[]) => {
		return {
			total: allAssets.length,
			high: allAssets.filter(a => a.criticality === 'high').length,
			medium: allAssets.filter(a => a.criticality === 'medium').length,
			low: allAssets.filter(a => a.criticality === 'low').length,
		};
	}
};

// Derived stores for computed values
export const projectStats = derived(
	[projects, currentProject, attackPaths, recommendations, assets],
	([$projects, $currentProject, $attackPaths, $recommendations, $assets]) => {
		if (!$currentProject) {
			return {
				totalProjects: $projects.length,
				completedProjects: $projects.filter(p => p.status === 'completed').length,
				analyzingProjects: $projects.filter(p => p.status === 'analyzing').length,
				draftProjects: $projects.filter(p => p.status === 'draft').length,
			};
		}

		const recStats = storeUtils.getRecommendationStats($recommendations);
		const assetStats = storeUtils.getAssetStats($assets);

		return {
			totalProjects: $projects.length,
			completedProjects: $projects.filter(p => p.status === 'completed').length,
			analyzingProjects: $projects.filter(p => p.status === 'analyzing').length,
			draftProjects: $projects.filter(p => p.status === 'draft').length,
			currentProjectStats: {
				attackPaths: $attackPaths.length,
				highPriorityPaths: $attackPaths.filter(p => p.priority_score > 7).length,
				...recStats,
				...assetStats
			}
		};
	}
);

export const filteredRecommendations = derived(
	[recommendations, filterCriteria, searchQuery],
	([$recommendations, $filterCriteria, $searchQuery]) => {
		return storeUtils.getFilteredRecommendations($recommendations, {
			...$filterCriteria,
			search: $searchQuery
		});
	}
);

export const sortedAttackPaths = derived(
	attackPaths,
	($attackPaths) => storeUtils.sortAttackPathsByPriority($attackPaths)
);

// Reset function for clearing all state
export const resetStores = () => {
	isLoading.set(false);
	error.set(null);
	notification.set(null);
	healthStatus.set(null);
	currentProject.set(null);
	projects.set([]);
	storeUtils.clearProjectData();
	currentPage.set('dashboard');
	selectedProject.set(null);
	searchQuery.set('');
	filterCriteria.set({});
	mitreTactics.set([]);
	selectedTactic.set('');
};
