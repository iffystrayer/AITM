/**
 * AITM Frontend API Service
 * Handles all communication with the FastAPI backend
 */

import axios, { type AxiosInstance, type AxiosResponse } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:38527/api/v1';

class ApiService {
	private client: AxiosInstance;

	constructor() {
		this.client = axios.create({
			baseURL: API_BASE_URL,
			timeout: 60000, // 60 seconds for analysis operations
			headers: {
				'Content-Type': 'application/json',
			},
		});

		// Request interceptor
		this.client.interceptors.request.use(
			(config) => {
				// Add any auth headers here if needed
				return config;
			},
			(error) => Promise.reject(error)
		);

		// Response interceptor
		this.client.interceptors.response.use(
			(response) => response,
			(error) => {
				console.error('API Error:', error.response?.data || error.message);
				return Promise.reject(error);
			}
		);
	}

	// Health check
	async healthCheck(): Promise<ApiResponse<HealthStatus>> {
		const response = await this.client.get('/health');
		return response.data;
	}

	// Project Management
	async getProjects(): Promise<ApiResponse<Project[]>> {
		const response = await this.client.get('/projects');
		return response.data;
	}

	async getProject(projectId: number): Promise<ApiResponse<Project>> {
		const response = await this.client.get(`/projects/${projectId}`);
		return response.data;
	}

	async createProject(projectData: CreateProjectRequest): Promise<ApiResponse<Project>> {
		const response = await this.client.post('/projects', projectData);
		return response.data;
	}

	async updateProject(projectId: number, projectData: Partial<CreateProjectRequest>): Promise<ApiResponse<Project>> {
		const response = await this.client.put(`/projects/${projectId}`, projectData);
		return response.data;
	}

	async deleteProject(projectId: number): Promise<ApiResponse<null>> {
		const response = await this.client.delete(`/projects/${projectId}`);
		return response.data;
	}

	// System Input Management
	async addSystemInput(projectId: number, inputData: SystemInputRequest): Promise<ApiResponse<SystemInput>> {
		const response = await this.client.post(`/projects/${projectId}/system-inputs`, inputData);
		return response.data;
	}

	async getSystemInputs(projectId: number): Promise<ApiResponse<SystemInput[]>> {
		const response = await this.client.get(`/projects/${projectId}/system-inputs`);
		return response.data;
	}

	async deleteSystemInput(projectId: number, inputId: number): Promise<ApiResponse<null>> {
		const response = await this.client.delete(`/projects/${projectId}/system-inputs/${inputId}`);
		return response.data;
	}

	// Threat Modeling Analysis
	async startThreatModeling(
		projectId: number, 
		analysisConfig: ThreatModelingConfig
	): Promise<ApiResponse<ThreatModelingResponse>> {
		const response = await this.client.post(`/projects/${projectId}/analyze`, analysisConfig);
		return response.data;
	}


	// Attack Paths
	async getAttackPaths(projectId: number): Promise<ApiResponse<AttackPath[]>> {
		const response = await this.client.get(`/projects/${projectId}/attack-paths`);
		return response.data;
	}

	async getAttackPath(projectId: number, pathId: number): Promise<ApiResponse<AttackPath>> {
		const response = await this.client.get(`/projects/${projectId}/attack-paths/${pathId}`);
		return response.data;
	}

	// Recommendations
	async getRecommendations(projectId: number): Promise<ApiResponse<Recommendation[]>> {
		const response = await this.client.get(`/projects/${projectId}/recommendations`);
		return response.data;
	}

	async updateRecommendationStatus(
		projectId: number,
		recommendationId: number,
		status: 'proposed' | 'accepted' | 'implemented'
	): Promise<ApiResponse<Recommendation>> {
		const response = await this.client.patch(
			`/projects/${projectId}/recommendations/${recommendationId}`,
			{ status }
		);
		return response.data;
	}

	// MITRE ATT&CK Integration
	async searchMitreTechniques(query: string, limit: number = 10): Promise<ApiResponse<MitreTechnique[]>> {
		const response = await this.client.get(`/mitre/techniques/search`, {
			params: { query, limit }
		});
		return response.data;
	}

	async getMitreTechnique(techniqueId: string): Promise<ApiResponse<MitreTechnique>> {
		const response = await this.client.get(`/mitre/techniques/${techniqueId}`);
		return response.data;
	}

	async getMitreTactics(): Promise<ApiResponse<string[]>> {
		const response = await this.client.get('/mitre/tactics');
		return response.data;
	}

	async getTechniquesByTactic(tactic: string): Promise<ApiResponse<MitreTechnique[]>> {
		const response = await this.client.get(`/mitre/tactics/${tactic}/techniques`);
		return response.data;
	}

	// Asset Management
	async getAssets(projectId: number): Promise<ApiResponse<Asset[]>> {
		const response = await this.client.get(`/projects/${projectId}/assets`);
		return response.data;
	}

	async createAsset(projectId: number, assetData: CreateAssetRequest): Promise<ApiResponse<Asset>> {
		const response = await this.client.post(`/projects/${projectId}/assets`, assetData);
		return response.data;
	}

	async updateAsset(
		projectId: number,
		assetId: number,
		assetData: Partial<CreateAssetRequest>
	): Promise<ApiResponse<Asset>> {
		const response = await this.client.put(`/projects/${projectId}/assets/${assetId}`, assetData);
		return response.data;
	}

	async deleteAsset(projectId: number, assetId: number): Promise<ApiResponse<null>> {
		const response = await this.client.delete(`/projects/${projectId}/assets/${assetId}`);
		return response.data;
	}

	// Report Generation
	async generateReport(projectId: number, format: 'json' | 'pdf' = 'json'): Promise<ApiResponse<ThreatModelReport>> {
		const response = await this.client.post(`/projects/${projectId}/report`, { format });
		return response.data;
	}

	// New Analysis Endpoints
	async startAnalysis(projectId: number, analysisConfig: AnalysisStartRequest): Promise<ApiResponse<AnalysisStartResponse>> {
		const response = await this.client.post(`/projects/${projectId}/analysis/start`, analysisConfig);
		return response.data;
	}

	async getAnalysisStatus(projectId: number): Promise<ApiResponse<AnalysisStatusResponse>> {
		const response = await this.client.get(`/projects/${projectId}/analysis/status`);
		return response.data;
	}

	async getAnalysisResults(projectId: number): Promise<ApiResponse<AnalysisResultsResponse>> {
		const response = await this.client.get(`/projects/${projectId}/analysis/results`);
		return response.data;
	}

	// System Input Management (updated endpoint)
	async getProjectInputs(projectId: number): Promise<ApiResponse<SystemInput[]>> {
		const response = await this.client.get(`/projects/${projectId}/inputs`);
		return response.data;
	}

	async addProjectInput(projectId: number, inputData: SystemInputRequest): Promise<ApiResponse<{ message: string; input_id: number }>> {
		const response = await this.client.post(`/projects/${projectId}/inputs`, inputData);
		return response.data;
	}

	// Analysis polling with new endpoints
	async pollAnalysisStatus(projectId: number, onUpdate?: (status: AnalysisStatusResponse) => void): Promise<AnalysisStatusResponse> {
		return new Promise((resolve, reject) => {
			const pollInterval = setInterval(async () => {
				try {
					const statusResponse = await this.getAnalysisStatus(projectId);
					const status = statusResponse.data;
					
					if (onUpdate) {
						onUpdate(status);
					}
					
					if (status.status === 'completed' || status.status === 'failed') {
						clearInterval(pollInterval);
						resolve(status);
					}
				} catch (error) {
					clearInterval(pollInterval);
					reject(error);
				}
			}, 2000); // Poll every 2 seconds
		});
	}


    predictRisk(historicalData: any[]): Promise<ApiResponse<any>> {
        return this.client.post('/predictions/predict-risk', historicalData);
    }

    // Legacy threat modeling methods for backwards compatibility
	async getThreatModelingStatus(projectId: number): Promise<ApiResponse<ThreatModelingStatus>> {
		// Map new analysis status to old format
		const statusResponse = await this.getAnalysisStatus(projectId);
		const newStatus = statusResponse.data;
		
		return {
			data: {
				project_id: newStatus.project_id,
				status: newStatus.status as any,
				attack_paths_count: 0, // Would need to fetch from results
				recommendations_count: 0, // Would need to fetch from results
				last_updated: newStatus.started_at || '',
				progress: newStatus.progress?.percentage || 0,
				current_step: newStatus.progress?.message || ''
			},
			success: true
		};
	}
}

// Type Definitions
export interface ApiResponse<T> {
	data: T;
	message?: string;
	success: boolean;
}

export interface HealthStatus {
	status: string;
	timestamp: string;
	version: string;
}

export interface Project {
	id: number;
	name: string;
	description: string | null;
	status: 'draft' | 'analyzing' | 'completed' | 'failed';
	created_at: string;
	updated_at: string;
}

export interface CreateProjectRequest {
	name: string;
	description?: string;
}

export interface SystemInput {
	id: number;
	project_id: number;
	input_type: 'text' | 'json' | 'file';
	content: string;
	filename: string | null;
	created_at: string;
}

export interface SystemInputRequest {
	input_type: 'text' | 'json' | 'file';
	content: string;
	filename?: string;
}

export interface ThreatModelingConfig {
	llm_provider?: 'openai' | 'google' | 'ollama' | 'litellm';
	analysis_depth?: 'quick' | 'standard' | 'deep';
	include_mitigations?: boolean;
	include_executive_summary?: boolean;
	include_technical_details?: boolean;
	existing_controls?: string[];
	control_documentation?: string;
}

export interface ThreatModelingResponse {
	project_id: number;
	status: string;
	message: string;
}

export interface ThreatModelingStatus {
	project_id: number;
	status: 'draft' | 'analyzing' | 'completed' | 'failed';
	attack_paths_count: number;
	recommendations_count: number;
	last_updated: string;
	progress?: number;
	current_step?: string;
}

export interface AttackPath {
	id: number;
	project_id: number;
	name: string;
	techniques: string[];
	priority_score: number;
	explanation: string;
	created_at: string;
}

export interface Recommendation {
	id: number;
	project_id: number;
	title: string;
	description: string;
	priority: 'high' | 'medium' | 'low';
	attack_technique: string | null;
	status: 'proposed' | 'accepted' | 'implemented';
	created_at: string;
}

export interface MitreTechnique {
	technique_id: string;
	name: string;
	tactic: string;
	description: string;
	platforms: string[];
	data_sources: string[];
	mitigations: string[];
}

export interface Asset {
	id: number;
	project_id: number;
	name: string;
	asset_type: string;
	criticality: 'high' | 'medium' | 'low';
	description: string | null;
	technologies: string[] | null;
	created_at: string;
}

export interface CreateAssetRequest {
	name: string;
	asset_type: string;
	criticality: 'high' | 'medium' | 'low';
	description?: string;
	technologies?: string[];
}

// New Analysis API Types
export interface AnalysisStartRequest {
	project_id: number;
	input_ids: number[];
	config: {
		analysis_depth?: 'quick' | 'standard' | 'deep';
		include_threat_modeling?: boolean;
		include_mitigations?: boolean;
		include_compliance_check?: boolean;
		priority_level?: 'low' | 'medium' | 'high';
	};
}

export interface AnalysisStartResponse {
	project_id: number;
	status: string;
	message: string;
	started_at: string;
}

export interface AnalysisProgress {
	current_phase?: string;
	percentage: number;
	message?: string;
}

export interface AnalysisStatusResponse {
	project_id: number;
	status: 'idle' | 'running' | 'completed' | 'failed';
	progress?: AnalysisProgress;
	started_at?: string;
	completed_at?: string;
	error_message?: string;
}

export interface ExecutiveSummary {
	overview: string;
	key_findings: string[];
	priority_actions: string[];
	risk_level: string;
	business_impact?: string;
}

export interface AttackPathStep {
	step: number;
	technique_id: string;
	technique_name: string;
	tactic: string;
	target_component: string;
	description?: string;
}

export interface AttackPathResult {
	name: string;
	description: string;
	impact: 'low' | 'medium' | 'high' | 'critical';
	likelihood: 'low' | 'medium' | 'high' | 'critical';
	techniques: AttackPathStep[];
}

export interface IdentifiedTechnique {
	technique_id: string;
	technique_name: string;
	tactic: string;
	applicability_score: number;
	system_component?: string;
	rationale?: string;
	prerequisites: string[];
}

export interface SecurityRecommendation {
	title: string;
	description: string;
	priority: 'low' | 'medium' | 'high' | 'urgent';
	attack_technique?: string;
	affected_assets: string[];
	implementation_effort?: string;
	cost_estimate?: string;
	timeline?: string;
}

export interface AnalysisResultsResponse {
	project_id: number;
	overall_risk_score: number;
	confidence_score: number;
	executive_summary?: ExecutiveSummary;
	attack_paths: AttackPathResult[];
	identified_techniques: IdentifiedTechnique[];
	recommendations: SecurityRecommendation[];
	system_analysis_results: Record<string, any>[];
	control_evaluation_results: Record<string, any>[];
	full_report?: Record<string, any>;
	created_at: string;
	updated_at: string;
}

export interface ThreatModelReport {
	executive_summary: {
		overview: string;
		key_findings: string[];
		risk_level: string;
		priority_actions: string[];
		business_impact: string;
	};
	technical_analysis: {
		system_overview: string;
		attack_surface: {
			entry_points: number;
			critical_assets: number;
			identified_threats: number;
		};
		threat_landscape: Array<{
			threat_category: string;
			techniques_count: number;
			risk_level: string;
			description: string;
		}>;
		attack_paths: Array<{
			path_name: string;
			likelihood: string;
			impact: string;
			techniques: string[];
			description: string;
		}>;
	};
	control_assessment: {
		current_controls: string;
		effectiveness_score: number;
		control_gaps: Array<{
			gap: string;
			severity: string;
			affected_techniques: string[];
			recommendation: string;
		}>;
	};
	recommendations: {
		immediate_actions: Array<{
			priority: number;
			action: string;
			justification: string;
			timeline: string;
			effort: string;
		}>;
		strategic_improvements: Array<{
			improvement: string;
			benefits: string;
			timeline: string;
			investment: string;
		}>;
	};
	metrics: {
		threat_coverage: number;
		control_maturity: number;
		residual_risk: number;
		techniques_analyzed: number;
		paths_identified: number;
	};
	mitre_analysis: {
		framework_version: string;
		coverage_analysis: {
			percentage: number;
			techniques_covered: number;
			total_techniques: number;
		};
		top_tactics_covered: Array<{
			tactic: string;
			coverage_percentage: number;
			techniques_covered: number;
			total_techniques: number;
		}>;
	};
	report_metadata: {
		generated_at: string;
		analysis_scope: string;
		framework: string;
		version: string;
	};
}

// Export singleton instance
export const apiService = new ApiService();
export default apiService;
