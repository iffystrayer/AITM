import { test as base, expect, Page } from '@playwright/test';

// Test data factory
export const TestData = {
  project: {
    name: 'E2E Test Project',
    description: 'Automated test project for end-to-end testing'
  },
  systemInput: {
    title: 'Web Application System',
    description: 'E2E test system description',
    content: `Test Web Application Architecture:
    
Frontend:
- React.js application hosted on Nginx
- Communicates with backend via REST APIs
- User authentication with JWT tokens
- File uploads for document management

Backend:
- Node.js with Express framework
- PostgreSQL database for data storage
- Redis cache for session management
- RESTful API endpoints for CRUD operations

Infrastructure:
- AWS EC2 instances for application hosting
- RDS for managed database
- S3 for file storage
- CloudFront CDN for static assets

Security Controls:
- HTTPS encryption for all traffic
- Input validation and sanitization
- Rate limiting on API endpoints
- Regular security updates and patches`
  }
};

// Page Object Models
export class DashboardPage {
  constructor(private page: Page) {}

  async goto() {
    await this.page.goto('/');
    await this.page.waitForLoadState('networkidle');
  }

  async waitForBackendStatus() {
    await this.page.waitForSelector('text=Backend Online', { timeout: 10000 });
  }

  async getBackendStatus() {
    return await this.page.textContent('[data-testid="backend-status"] dd');
  }

  async clickAPIDocumentation() {
    await this.page.click('text=📚 API Documentation');
  }

  async clickHealthCheck() {
    await this.page.click('text=🔍 Health Check');
  }
}

export class ProjectsPage {
  constructor(private page: Page) {}

  async goto() {
    await this.page.goto('/projects');
    await this.page.waitForLoadState('networkidle');
  }

  async createProject(projectData = TestData.project) {
    await this.page.click('text=+ New Project');
    await this.page.fill('input[placeholder="Enter project name"]', projectData.name);
    await this.page.fill('textarea[placeholder="Optional project description"]', projectData.description);
    await this.page.click('button:has-text("Create Project")');
    await this.page.waitForLoadState('networkidle');
  }

  async getProjectCount() {
    const projects = await this.page.locator('[data-testid="project-card"]').count();
    return projects;
  }

  async clickProject(projectName: string) {
    await this.page.click(`text=${projectName}`);
  }

  async deleteProject(projectName: string) {
    const projectCard = this.page.locator(`text=${projectName}`).locator('..');
    await projectCard.locator('button:has-text("Delete")').click();
    await this.page.click('button:has-text("OK")'); // Confirm deletion
  }

  async waitForProjectsLoad() {
    await this.page.waitForSelector('text=Threat Modeling Projects', { timeout: 10000 });
  }
}

export class ProjectDetailPage {
  constructor(private page: Page) {}

  async goto(projectId: string) {
    await this.page.goto(`/projects/${projectId}`);
    await this.page.waitForLoadState('networkidle');
  }

  async clickTab(tabName: 'overview' | 'inputs' | 'analysis' | 'results') {
    await this.page.click(`button:has-text("${tabName.charAt(0).toUpperCase() + tabName.slice(1)}")`);
  }

  async addSystemInput(inputData = TestData.systemInput) {
    await this.clickTab('inputs');
    await this.page.click('button:has-text("+ Add Input")');
    
    await this.page.fill('input[placeholder="System description title"]', inputData.title);
    await this.page.fill('textarea[placeholder="Brief description"]', inputData.description);
    await this.page.fill('textarea[placeholder="Enter system description"]', inputData.content);
    
    await this.page.click('button:has-text("Add System Input")');
    await this.page.waitForLoadState('networkidle');
  }

  async getSystemInputCount() {
    await this.clickTab('inputs');
    const inputs = await this.page.locator('[data-testid="system-input"]').count();
    return inputs;
  }

  async startAnalysis() {
    await this.clickTab('analysis');
    await this.page.click('button:has-text("Start Threat Analysis")');
    
    // Analysis configuration modal
    await this.page.selectOption('select[name="llm_provider"]', 'gemini');
    await this.page.selectOption('select[name="analysis_depth"]', 'standard');
    await this.page.click('button:has-text("Start Analysis")');
    
    await this.page.waitForLoadState('networkidle');
  }

  async waitForAnalysisComplete() {
    // Wait for analysis to complete (up to 2 minutes)
    await this.page.waitForSelector('button:has-text("View Results")', { timeout: 120000 });
  }

  async viewResults() {
    await this.clickTab('results');
  }

  async getAnalysisStatus() {
    await this.clickTab('overview');
    return await this.page.textContent('[data-testid="analysis-status"]');
  }
}

export class NavigationHelper {
  constructor(private page: Page) {}

  async navigateToProjects() {
    await this.page.click('a:has-text("Projects")');
    await this.page.waitForLoadState('networkidle');
  }

  async navigateToAnalysis() {
    await this.page.click('a:has-text("Analysis")');
    await this.page.waitForLoadState('networkidle');
  }

  async navigateToAssets() {
    await this.page.click('a:has-text("Assets")');
    await this.page.waitForLoadState('networkidle');
  }

  async navigateToReports() {
    await this.page.click('a:has-text("Reports")');
    await this.page.waitForLoadState('networkidle');
  }

  async navigateToDashboard() {
    await this.page.click('a:has-text("Dashboard")');
    await this.page.waitForLoadState('networkidle');
  }
}

// Extended test with fixtures
export const test = base.extend<{
  dashboardPage: DashboardPage;
  projectsPage: ProjectsPage;
  projectDetailPage: ProjectDetailPage;
  navigation: NavigationHelper;
}>({
  dashboardPage: async ({ page }, use) => {
    await use(new DashboardPage(page));
  },
  projectsPage: async ({ page }, use) => {
    await use(new ProjectsPage(page));
  },
  projectDetailPage: async ({ page }, use) => {
    await use(new ProjectDetailPage(page));
  },
  navigation: async ({ page }, use) => {
    await use(new NavigationHelper(page));
  },
});

export { expect };
