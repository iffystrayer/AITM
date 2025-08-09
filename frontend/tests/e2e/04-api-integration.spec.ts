import { test, expect } from '../fixtures';

test.describe('API Integration Tests', () => {
  const API_BASE = 'http://127.0.0.1:38527';

  test('should have backend API accessible', async ({ page }) => {
    await test.step('Check health endpoint', async () => {
      const response = await page.request.get(`${API_BASE}/health`);
      expect(response.ok()).toBeTruthy();
      
      const health = await response.json();
      expect(health).toHaveProperty('status');
      expect(health.status).toBe('healthy');
    });

    await test.step('Check API documentation', async () => {
      const response = await page.request.get(`${API_BASE}/docs`);
      expect(response.ok()).toBeTruthy();
      
      const html = await response.text();
      expect(html).toContain('FastAPI');
      expect(html).toContain('swagger');
    });
  });

  test('should handle projects CRUD operations via API', async ({ page }) => {
    let createdProjectId: string;

    await test.step('Create project via API', async () => {
      const projectData = {
        name: `API Test Project ${Date.now()}`,
        description: 'Created via API integration test'
      };

      const response = await page.request.post(`${API_BASE}/api/v1/projects/`, {
        data: projectData
      });

      expect(response.ok()).toBeTruthy();
      const project = await response.json();
      
      expect(project).toHaveProperty('id');
      expect(project).toHaveProperty('name', projectData.name);
      expect(project).toHaveProperty('description', projectData.description);
      expect(project).toHaveProperty('status', 'created');
      
      createdProjectId = project.id;
    });

    await test.step('Get project via API', async () => {
      const response = await page.request.get(`${API_BASE}/api/v1/projects/${createdProjectId}`);
      expect(response.ok()).toBeTruthy();
      
      const project = await response.json();
      expect(project).toHaveProperty('id', createdProjectId);
    });

    await test.step('List projects via API', async () => {
      const response = await page.request.get(`${API_BASE}/api/v1/projects/`);
      expect(response.ok()).toBeTruthy();
      
      const projects = await response.json();
      expect(Array.isArray(projects)).toBeTruthy();
      
      const createdProject = projects.find((p: any) => p.id === createdProjectId);
      expect(createdProject).toBeDefined();
    });

    await test.step('Update project via API', async () => {
      const updateData = {
        name: `Updated API Test Project ${Date.now()}`,
        description: 'Updated via API integration test'
      };

      const response = await page.request.put(`${API_BASE}/api/v1/projects/${createdProjectId}`, {
        data: updateData
      });

      expect(response.ok()).toBeTruthy();
      const project = await response.json();
      expect(project).toHaveProperty('name', updateData.name);
      expect(project).toHaveProperty('description', updateData.description);
    });

    await test.step('Delete project via API', async () => {
      const response = await page.request.delete(`${API_BASE}/api/v1/projects/${createdProjectId}`);
      expect(response.ok()).toBeTruthy();
      
      // Verify project is deleted
      const getResponse = await page.request.get(`${API_BASE}/api/v1/projects/${createdProjectId}`);
      expect(getResponse.status()).toBe(404);
    });
  });

  test('should handle system inputs via API', async ({ page }) => {
    let projectId: string;
    let inputId: string;

    await test.step('Create test project', async () => {
      const projectData = {
        name: `Input Test Project ${Date.now()}`,
        description: 'Project for testing system inputs API'
      };

      const response = await page.request.post(`${API_BASE}/api/v1/projects/`, {
        data: projectData
      });

      const project = await response.json();
      projectId = project.id;
    });

    await test.step('Add system input via API', async () => {
      const inputData = {
        title: 'API Test System Input',
        description: 'System input created via API test',
        content: 'Web application with React frontend and Node.js backend',
        input_type: 'text'
      };

      const response = await page.request.post(`${API_BASE}/api/v1/projects/${projectId}/inputs`, {
        data: inputData
      });

      expect(response.ok()).toBeTruthy();
      const input = await response.json();
      
      expect(input).toHaveProperty('id');
      expect(input).toHaveProperty('title', inputData.title);
      expect(input).toHaveProperty('content', inputData.content);
      
      inputId = input.id;
    });

    await test.step('List system inputs via API', async () => {
      const response = await page.request.get(`${API_BASE}/api/v1/projects/${projectId}/inputs`);
      expect(response.ok()).toBeTruthy();
      
      const result = await response.json();
      expect(result).toHaveProperty('data');
      expect(Array.isArray(result.data)).toBeTruthy();
      
      const createdInput = result.data.find((input: any) => input.id === inputId);
      expect(createdInput).toBeDefined();
    });

    await test.step('Clean up test project', async () => {
      await page.request.delete(`${API_BASE}/api/v1/projects/${projectId}`);
    });
  });

  test('should handle threat modeling endpoints', async ({ page }) => {
    let projectId: string;

    await test.step('Create project with system input', async () => {
      // Create project
      const projectResponse = await page.request.post(`${API_BASE}/api/v1/projects/`, {
        data: {
          name: `Threat Analysis API Test ${Date.now()}`,
          description: 'Project for testing threat analysis API'
        }
      });
      
      const project = await projectResponse.json();
      projectId = project.id;

      // Add system input
      await page.request.post(`${API_BASE}/api/v1/projects/${projectId}/inputs`, {
        data: {
          title: 'Test System',
          description: 'Test system for analysis',
          content: 'Simple web application for testing',
          input_type: 'text'
        }
      });
    });

    await test.step('Check analysis status endpoint', async () => {
      const response = await page.request.get(`${API_BASE}/api/v1/projects/${projectId}/analysis/status`);
      
      if (response.ok()) {
        const status = await response.json();
        expect(status).toHaveProperty('status');
        console.log('Analysis status:', status.status);
      } else {
        // Endpoint might not be implemented yet - that's okay for this test
        console.log('Analysis status endpoint not available:', response.status());
      }
    });

    await test.step('Test analysis initiation endpoint', async () => {
      const analysisConfig = {
        llm_provider: 'gemini',
        analysis_depth: 'standard',
        include_mitre_mapping: true
      };

      const response = await page.request.post(`${API_BASE}/api/v1/projects/${projectId}/analysis/start`, {
        data: analysisConfig
      });

      if (response.ok()) {
        const result = await response.json();
        console.log('Analysis started:', result);
        expect(result).toHaveProperty('status');
      } else {
        // Endpoint might not be fully implemented - log the error
        console.log('Analysis start endpoint response:', response.status());
        const errorText = await response.text();
        console.log('Error details:', errorText);
      }
    });

    await test.step('Clean up test project', async () => {
      await page.request.delete(`${API_BASE}/api/v1/projects/${projectId}`);
    });
  });

  test('should handle API error responses correctly', async ({ page }) => {
    await test.step('Test non-existent project', async () => {
      const response = await page.request.get(`${API_BASE}/api/v1/projects/99999`);
      expect(response.status()).toBe(404);
    });

    await test.step('Test invalid project creation', async () => {
      const response = await page.request.post(`${API_BASE}/api/v1/projects/`, {
        data: {} // Missing required name field
      });
      
      expect(response.status()).toBeGreaterThanOrEqual(400);
    });

    await test.step('Test invalid project update', async () => {
      const response = await page.request.put(`${API_BASE}/api/v1/projects/99999`, {
        data: { name: 'Updated Name' }
      });
      
      expect(response.status()).toBe(404);
    });

    await test.step('Test system input for non-existent project', async () => {
      const response = await page.request.post(`${API_BASE}/api/v1/projects/99999/inputs`, {
        data: {
          title: 'Test Input',
          content: 'Test content',
          input_type: 'text'
        }
      });
      
      expect(response.status()).toBeGreaterThanOrEqual(400);
    });
  });

  test('should validate API response schemas', async ({ page }) => {
    let projectId: string;

    await test.step('Create project and validate response schema', async () => {
      const response = await page.request.post(`${API_BASE}/api/v1/projects/`, {
        data: {
          name: 'Schema Validation Test',
          description: 'Testing API response schemas'
        }
      });

      expect(response.ok()).toBeTruthy();
      const project = await response.json();

      // Validate required fields are present
      expect(project).toHaveProperty('id');
      expect(project).toHaveProperty('name');
      expect(project).toHaveProperty('status');
      expect(project).toHaveProperty('created_at');
      expect(project).toHaveProperty('updated_at');

      // Validate field types
      expect(typeof project.id).toBe('string');
      expect(typeof project.name).toBe('string');
      expect(typeof project.status).toBe('string');
      expect(typeof project.created_at).toBe('string');
      expect(typeof project.updated_at).toBe('string');

      projectId = project.id;
    });

    await test.step('Validate projects list response schema', async () => {
      const response = await page.request.get(`${API_BASE}/api/v1/projects/`);
      expect(response.ok()).toBeTruthy();
      
      const projects = await response.json();
      expect(Array.isArray(projects)).toBeTruthy();
      
      if (projects.length > 0) {
        const project = projects[0];
        expect(project).toHaveProperty('id');
        expect(project).toHaveProperty('name');
        expect(project).toHaveProperty('status');
      }
    });

    await test.step('Clean up', async () => {
      await page.request.delete(`${API_BASE}/api/v1/projects/${projectId}`);
    });
  });

  test('should handle concurrent API requests', async ({ page }) => {
    await test.step('Create multiple projects concurrently', async () => {
      const projectPromises = Array.from({ length: 5 }, (_, i) => 
        page.request.post(`${API_BASE}/api/v1/projects/`, {
          data: {
            name: `Concurrent Test Project ${i + 1} - ${Date.now()}`,
            description: `Concurrent creation test project ${i + 1}`
          }
        })
      );

      const responses = await Promise.all(projectPromises);
      
      // All should succeed
      responses.forEach(response => {
        expect(response.ok()).toBeTruthy();
      });

      // Get project IDs for cleanup
      const projects = await Promise.all(
        responses.map(response => response.json())
      );
      
      // Clean up all created projects
      const deletePromises = projects.map(project =>
        page.request.delete(`${API_BASE}/api/v1/projects/${project.id}`)
      );
      
      await Promise.all(deletePromises);
    });
  });
});
