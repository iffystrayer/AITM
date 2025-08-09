# AITM User Guide

## Table of Contents
- [Getting Started](#getting-started)
- [Dashboard Overview](#dashboard-overview)
- [Project Management](#project-management)
- [Threat Analysis Workflow](#threat-analysis-workflow)
- [Asset Management](#asset-management)
- [MITRE ATT&CK Framework](#mitre-attck-framework)
- [Analysis & Results](#analysis--results)
- [Reports & Documentation](#reports--documentation)
- [User Interface Features](#user-interface-features)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Getting Started

### What is AITM?
AITM (AI-Powered Threat Modeler) is a comprehensive cybersecurity platform that helps organizations identify, analyze, and mitigate potential security threats in their systems and applications. Using artificial intelligence and the MITRE ATT&CK framework, AITM provides intelligent threat modeling capabilities.

### Accessing AITM
1. **Web Browser**: Navigate to your organization's AITM URL (e.g., https://aitm.yourcompany.com)
2. **Supported Browsers**: Chrome, Firefox, Safari, Edge (latest versions)
3. **Account**: Contact your system administrator for login credentials
4. **Login**: Use your email address and password to access the platform

### User Roles
- **Administrator**: Full system access and configuration
- **Security Analyst**: Complete threat modeling and analysis capabilities
- **Viewer**: Read-only access to view existing threat models and reports

## Dashboard Overview

### Main Dashboard Elements

#### System Status Section
- **Backend Status**: Displays API server health (✅ Backend Online)
- **AI Services**: Shows availability of LLM providers
- **Database Status**: Indicates database connectivity

#### Quick Actions
- **🚀 New Project**: Start a new threat modeling project
- **📊 View Reports**: Access existing analysis reports
- **🔍 API Documentation**: View API documentation
- **💊 Health Check**: Check system health status

#### Recent Activity
- **Recent Projects**: List of your recently accessed projects
- **System Statistics**: Overall platform usage metrics
- **Notifications**: Important system updates and alerts

#### Feature Highlights
- **Multi-Agent System**: AI-powered threat analysis
- **LLM Integration**: Support for multiple AI providers
- **MITRE ATT&CK**: Comprehensive attack technique database
- **REST API**: Programmatic access to platform features

### Navigation Menu
- **🏠 Dashboard**: Main overview page
- **📁 Projects**: Manage threat modeling projects
- **🔍 Analysis**: Threat analysis tools and workflows
- **💎 Assets**: Organizational asset inventory
- **🎯 MITRE ATT&CK**: Attack technique analysis
- **📊 Reports**: Generated reports and documentation

## Project Management

### Creating a New Project

#### Step 1: Initialize Project
1. Click **"+ New Project"** button on dashboard
2. Enter **Project Name** (descriptive and unique)
3. Add **Project Description** (purpose and scope)
4. Select **Project Type** if applicable
5. Click **"Create Project"** to initialize

#### Step 2: Project Configuration
- **Team Members**: Invite team members to collaborate
- **Security Scope**: Define what systems/applications to analyze
- **Compliance Requirements**: Specify relevant compliance frameworks
- **Timeline**: Set project milestones and deadlines

### Project Dashboard

#### Project Information Panel
```
Project: E-Commerce Platform Security Assessment
Status: In Progress
Created: August 9, 2025
Last Modified: Today, 2:30 PM
Team Members: 3
Completion: 65%
```

#### Quick Stats
- **Assets Identified**: Number of system components
- **Threats Detected**: Security threats found
- **Mitigations Planned**: Recommended security controls
- **Risk Level**: Overall risk assessment

#### Project Actions
- **📝 Edit Project**: Modify project details
- **👥 Manage Team**: Add/remove team members  
- **🔄 Sync Data**: Refresh project information
- **📋 Export**: Export project data
- **🗑️ Archive**: Archive completed projects

### Project Lifecycle

#### 1. Planning Phase
- Define project scope and objectives
- Identify stakeholders and team members
- Establish security requirements and constraints

#### 2. Information Gathering
- Document system architecture
- Identify critical assets and data flows
- Collect existing security documentation

#### 3. Threat Analysis
- Use AI-powered analysis tools
- Map threats to MITRE ATT&CK framework
- Assess risk levels and impact

#### 4. Mitigation Planning
- Develop security controls and countermeasures
- Prioritize mitigations based on risk
- Create implementation roadmap

#### 5. Documentation & Reporting
- Generate comprehensive threat model documentation
- Create executive summaries and technical reports
- Export results in various formats

## Threat Analysis Workflow

### System Input and Description

#### Adding System Information
1. **Navigation**: Go to Projects → Select Project → Analysis
2. **System Description**: Provide detailed system overview
   ```
   Example:
   "Web-based e-commerce platform with React frontend, 
   Node.js API backend, PostgreSQL database, and 
   third-party payment processing integration."
   ```
3. **Architecture Details**: Include:
   - Technology stack
   - Network topology
   - Data flows
   - External integrations
   - User types and access levels

#### Input Types Supported
- **Text Description**: Free-form system description
- **Architecture Diagrams**: Upload system diagrams
- **Configuration Files**: Import relevant config files
- **Existing Documentation**: Link to current documentation

### AI-Powered Analysis

#### Starting Analysis
1. **Configure Analysis Settings**:
   - **LLM Provider**: Choose AI provider (OpenAI, Anthropic, Google)
   - **Analysis Depth**: Standard, Comprehensive, or Quick
   - **MITRE Mapping**: Enable/disable ATT&CK framework mapping
   - **Focus Areas**: Specify particular security domains

2. **Initiate Analysis**:
   - Click **"Start Analysis"** button
   - Monitor progress in real-time
   - Review preliminary findings as they appear

#### Analysis Process
```
Phase 1: System Understanding (2-3 minutes)
├─ Parse system description
├─ Identify key components
├─ Map data flows
└─ Classify asset types

Phase 2: Threat Identification (5-8 minutes)
├─ Generate potential attack vectors
├─ Map to MITRE ATT&CK techniques
├─ Assess threat likelihood
└─ Calculate impact scores

Phase 3: Risk Assessment (3-5 minutes)
├─ Evaluate threat-asset combinations
├─ Calculate risk scores
├─ Prioritize findings
└─ Generate recommendations

Phase 4: Report Generation (2-3 minutes)
├─ Compile analysis results
├─ Create executive summary
├─ Generate technical details
└─ Format final report
```

### Review and Refinement

#### Analysis Results Review
- **Threat Overview**: High-level summary of identified threats
- **Risk Matrix**: Visual representation of risk levels
- **MITRE Mapping**: Threats mapped to ATT&CK techniques
- **Recommendations**: AI-generated mitigation strategies

#### Manual Refinement Options
- **Add Custom Threats**: Include organization-specific threats
- **Modify Risk Scores**: Adjust based on organizational context
- **Update Mitigations**: Add custom security controls
- **Annotate Findings**: Add contextual notes and comments

## Asset Management

### Asset Inventory

#### Viewing Assets
1. Navigate to **"💎 Assets"** section
2. View comprehensive asset inventory table
3. Use search and filtering options to find specific assets

#### Asset Categories
- **Server**: Web servers, application servers, database servers
- **Database**: SQL databases, NoSQL databases, data warehouses
- **Service**: APIs, microservices, third-party integrations
- **Infrastructure**: Load balancers, firewalls, network equipment

#### Asset Information
- **Asset Name**: Descriptive name for the component
- **Type**: Category classification
- **Criticality**: Business impact level (Critical, High, Medium, Low)
- **Technology**: Underlying technology or platform
- **Status**: Current operational status

### Adding New Assets

#### Asset Creation Process
1. Click **"💎 Add Asset"** button
2. Fill out asset information:
   - **Asset Name**: Enter descriptive name
   - **Type**: Select from dropdown (Server, Database, Service, Infrastructure)
   - **Criticality Level**: Choose business impact level
   - **Technology/Platform**: Specify underlying technology
   - **Description**: Add detailed description (optional)

3. Review and save the asset entry

#### Criticality Levels
- **🔴 Critical**: Business-critical systems, revenue-generating assets
- **🟠 High**: Important systems with significant business impact
- **🟡 Medium**: Standard systems with moderate business impact
- **🟢 Low**: Non-critical systems with minimal business impact

### Asset Relationships

#### Dependency Mapping
- Map relationships between assets
- Identify critical dependencies
- Understand cascade failure scenarios
- Plan security controls accordingly

#### Integration Points
- Document external integrations
- Map data flows between assets
- Identify trust boundaries
- Assess security implications

## MITRE ATT&CK Framework

### Framework Overview

The MITRE ATT&CK framework provides a comprehensive knowledge base of adversary tactics and techniques based on real-world observations. AITM integrates this framework to provide structured threat analysis.

### Navigation Modes

#### 1. Matrix View
- **Overview**: Visual representation of all tactics
- **Tactic Cards**: Color-coded tactic categories
- **Technique Count**: Number of techniques per tactic
- **Interactive Navigation**: Click tactics to drill down

#### 2. Techniques View
- **Technique List**: Tabular view of all techniques
- **Search Functionality**: Find techniques by ID or name
- **Filtering Options**: Filter by tactic, risk level, or other criteria
- **Sorting Options**: Sort by various attributes

#### 3. Details View
- **Comprehensive Information**: Full technique documentation
- **Detection Methods**: How to detect the technique
- **Mitigation Strategies**: How to defend against the technique
- **Risk Assessment**: Threat level and impact analysis

### MITRE ATT&CK Tactics

#### Initial Access (TA0001)
- **Purpose**: Adversary is trying to get into your network
- **Common Techniques**: Phishing, Valid Accounts, Exploit Public-Facing Application
- **Color Code**: 🔴 Red

#### Execution (TA0002)
- **Purpose**: Adversary is trying to run malicious code
- **Common Techniques**: Command and Scripting Interpreter, User Execution
- **Color Code**: 🟠 Orange

#### Persistence (TA0003)
- **Purpose**: Adversary is trying to maintain their foothold
- **Common Techniques**: Scheduled Task/Job, Registry Run Keys
- **Color Code**: 🟡 Yellow

#### Privilege Escalation (TA0004)
- **Purpose**: Adversary is trying to gain higher-level permissions
- **Common Techniques**: Process Injection, Valid Accounts
- **Color Code**: 🟢 Green

#### Defense Evasion (TA0005)
- **Purpose**: Adversary is trying to avoid being detected
- **Common Techniques**: Obfuscated Files, Process Injection
- **Color Code**: 🔵 Blue

#### Credential Access (TA0006)
- **Purpose**: Adversary is trying to steal account names and passwords
- **Common Techniques**: OS Credential Dumping, Brute Force
- **Color Code**: 🟣 Indigo

### Technique Analysis

#### Technique Details
When you select a specific technique, you'll see:

**Example: T1566 - Phishing**
- **Description**: How adversaries use phishing in attacks
- **Sub-techniques**: Spearphishing Attachment, Spearphishing Link, etc.
- **Detection Methods**: 
  - Monitor for suspicious email patterns
  - Analyze network traffic for malicious domains
  - Review authentication logs for unusual access
  - Implement behavioral analysis for user activities

- **Mitigation Strategies**:
  - Implement email security gateways and filtering
  - Conduct regular security awareness training
  - Deploy multi-factor authentication
  - Maintain updated endpoint protection
  - Implement application sandboxing

- **Risk Level**: Calculated based on technique prevalence and impact
- **Threat Level**: Visual indicator of severity

### Using MITRE Data in Threat Modeling

#### 1. Threat Identification
- Map system vulnerabilities to MITRE techniques
- Identify applicable attack vectors
- Assess technique likelihood for your environment

#### 2. Risk Assessment
- Use MITRE data to inform risk calculations
- Consider technique sophistication and detection difficulty
- Factor in organizational-specific risk factors

#### 3. Mitigation Planning
- Use MITRE mitigation guidance
- Prioritize controls based on technique coverage
- Plan defense-in-depth strategies

## Analysis & Results

### Analysis Dashboard

#### Results Overview
- **Executive Summary**: High-level findings and recommendations
- **Risk Distribution**: Visual breakdown of risk levels
- **Threat Categories**: Types of threats identified
- **Mitigation Priority**: Recommended action priorities

#### Key Metrics
```
Total Threats Identified: 23
High Risk Threats: 8
Medium Risk Threats: 12
Low Risk Threats: 3

MITRE Techniques Mapped: 15
Critical Assets at Risk: 5
Mitigation Strategies: 31
```

### Detailed Findings

#### Threat Details
Each identified threat includes:
- **Threat Name**: Descriptive threat title
- **Risk Level**: Color-coded risk assessment
- **MITRE Technique**: Associated ATT&CK technique
- **Affected Assets**: Which systems are at risk
- **Attack Vector**: How the threat could be exploited
- **Business Impact**: Potential consequences
- **Likelihood**: Probability of occurrence
- **Detection Methods**: How to identify the threat
- **Mitigation Strategies**: How to address the threat

#### Risk Assessment Matrix
```
         Likelihood
         Low  Med  High
Impact   ┌────┬────┬────┐
High     │🟡  │🟠  │🔴  │
         ├────┼────┼────┤
Medium   │🟢  │🟡  │🟠  │
         ├────┼────┼────┤
Low      │🟢  │🟢  │🟡  │
         └────┴────┴────┘

🟢 Low Risk    🟡 Medium Risk    🟠 High Risk    🔴 Critical Risk
```

### Mitigation Recommendations

#### Security Control Categories
- **Preventive Controls**: Stop attacks before they occur
- **Detective Controls**: Identify attacks in progress
- **Corrective Controls**: Respond to and recover from attacks
- **Administrative Controls**: Policies and procedures
- **Technical Controls**: Technology-based security measures

#### Implementation Priorities
1. **Critical**: Address immediately (0-30 days)
2. **High**: Address soon (30-90 days)
3. **Medium**: Address within planning cycle (90-180 days)
4. **Low**: Address as resources allow (180+ days)

### Results Export and Sharing

#### Export Options
- **PDF Report**: Comprehensive document suitable for sharing
- **Excel Spreadsheet**: Data in tabular format for analysis
- **JSON Data**: Machine-readable format for integration
- **Word Document**: Editable format for customization

#### Sharing Features
- **Team Sharing**: Share results with project team members
- **Stakeholder Reports**: Generate executive summaries
- **API Access**: Programmatic access to results data
- **Email Integration**: Send reports via email

## Reports & Documentation

### Report Types

#### Executive Summary
- **Audience**: Senior management and executives
- **Length**: 1-2 pages
- **Content**:
  - Overall risk posture
  - Key findings and recommendations
  - Business impact assessment
  - Resource requirements for mitigation

#### Technical Report
- **Audience**: IT and security teams
- **Length**: 10-50 pages
- **Content**:
  - Detailed threat analysis
  - Technical mitigation strategies
  - Implementation guidance
  - Testing and validation procedures

#### Compliance Report
- **Audience**: Compliance and audit teams
- **Length**: 5-20 pages
- **Content**:
  - Regulatory requirement mapping
  - Control effectiveness assessment
  - Gap analysis and recommendations
  - Compliance status summary

### Report Generation

#### Automatic Report Creation
1. Navigate to project results
2. Click **"Generate Report"** button
3. Select report type and format
4. Configure report options:
   - Include/exclude sections
   - Risk level filtering
   - Audience-specific content
   - Branding and formatting options
5. Generate and download report

#### Custom Report Builder
- **Template Selection**: Choose from pre-built templates
- **Content Customization**: Add/remove sections as needed
- **Formatting Options**: Adjust styling and layout
- **Data Filtering**: Include specific findings or categories
- **Executive Summary**: Auto-generated or custom written

### Documentation Best Practices

#### Report Organization
1. **Executive Summary**: Key findings and recommendations
2. **Methodology**: How the analysis was conducted
3. **Scope and Assumptions**: What was included/excluded
4. **Findings**: Detailed threat analysis results
5. **Risk Assessment**: Risk ratings and justifications
6. **Recommendations**: Mitigation strategies and priorities
7. **Appendices**: Supporting data and references

#### Writing Guidelines
- **Clear Language**: Avoid technical jargon in executive sections
- **Actionable Recommendations**: Specific, measurable, and achievable
- **Risk Context**: Explain risk in business terms
- **Timeline**: Provide realistic implementation timelines
- **Resource Requirements**: Specify personnel and budget needs

## User Interface Features

### Theme and Display Options

#### Dark/Light Mode Toggle
- **Access**: Click theme toggle button in navigation
- **Automatic**: Follows system preference by default
- **Manual Override**: Set specific theme preference
- **Accessibility**: High contrast options available

#### Responsive Design
- **Desktop**: Full-featured interface with all capabilities
- **Tablet**: Touch-optimized interface with adapted navigation
- **Mobile**: Essential features accessible on mobile devices

### Search and Filtering

#### Global Search
- **Access**: Search bar in main navigation
- **Scope**: Searches across all projects, assets, and findings
- **Filters**: Filter by project, type, date, or status
- **Results**: Organized by category with quick navigation

#### Advanced Filtering
- **Risk Level**: Filter by Low, Medium, High, Critical
- **MITRE Techniques**: Filter by specific ATT&CK techniques
- **Asset Types**: Filter by asset categories
- **Date Range**: Filter by creation or modification date
- **Team Member**: Filter by assigned team member

### Keyboard Shortcuts

#### Navigation
- `Ctrl/Cmd + 1`: Dashboard
- `Ctrl/Cmd + 2`: Projects
- `Ctrl/Cmd + 3`: Analysis
- `Ctrl/Cmd + 4`: Assets
- `Ctrl/Cmd + 5`: MITRE ATT&CK
- `Ctrl/Cmd + 6`: Reports

#### Actions
- `Ctrl/Cmd + N`: New Project
- `Ctrl/Cmd + S`: Save current work
- `Ctrl/Cmd + F`: Search
- `Escape`: Close modal/dialog
- `Tab`: Navigate between form fields

### Accessibility Features

#### Screen Reader Support
- **ARIA Labels**: All interactive elements properly labeled
- **Semantic HTML**: Proper heading structure and landmarks
- **Alt Text**: All images include descriptive alt text
- **Focus Management**: Logical tab order and focus indicators

#### Visual Accessibility
- **High Contrast Mode**: Enhanced color contrast options
- **Font Size**: Adjustable text size settings
- **Color Independence**: Information not conveyed by color alone
- **Motion Control**: Reduced motion options for animations

## Best Practices

### Project Planning

#### 1. Define Clear Scope
- **System Boundaries**: Clearly define what's included/excluded
- **Security Objectives**: Specify security goals and requirements
- **Stakeholder Involvement**: Include relevant team members
- **Timeline Planning**: Set realistic milestones and deadlines

#### 2. Gather Comprehensive Information
- **System Documentation**: Collect existing architecture docs
- **Data Flow Diagrams**: Understand how data moves through systems
- **Security Controls**: Document existing security measures
- **Compliance Requirements**: Identify regulatory obligations

#### 3. Iterative Approach
- **Start Simple**: Begin with high-level analysis
- **Refine Gradually**: Add detail through iterations
- **Regular Reviews**: Schedule periodic review sessions
- **Continuous Updates**: Keep threat model current with system changes

### Effective Threat Analysis

#### 1. Leverage AI Capabilities
- **Detailed Descriptions**: Provide comprehensive system information
- **Multiple Perspectives**: Consider different attack scenarios
- **Validation**: Review AI-generated findings for accuracy
- **Customization**: Adapt findings to organizational context

#### 2. Use MITRE ATT&CK Effectively
- **Technique Research**: Study relevant ATT&CK techniques in detail
- **Environmental Context**: Consider your specific environment
- **Defense Gaps**: Identify uncovered attack vectors
- **Mitigation Planning**: Use MITRE mitigation guidance

#### 3. Risk-Based Prioritization
- **Business Impact**: Align with business priorities and assets
- **Threat Landscape**: Consider current threat intelligence
- **Resource Constraints**: Prioritize based on available resources
- **Quick Wins**: Identify low-effort, high-impact mitigations

### Documentation Standards

#### 1. Consistent Formatting
- **Templates**: Use standardized report templates
- **Naming Conventions**: Follow consistent naming patterns
- **Version Control**: Track document versions and changes
- **Review Process**: Implement peer review procedures

#### 2. Audience-Appropriate Content
- **Executive Summary**: Business-focused, non-technical language
- **Technical Details**: Detailed implementation guidance
- **Action Items**: Clear, specific, and measurable tasks
- **Timelines**: Realistic implementation schedules

#### 3. Maintenance and Updates
- **Regular Reviews**: Schedule periodic threat model reviews
- **Change Management**: Update models when systems change
- **Lessons Learned**: Incorporate feedback and improvements
- **Archive Management**: Properly archive completed projects

## Troubleshooting

### Common Issues

#### Login Problems
**Issue**: Cannot access AITM platform
**Solutions**:
1. Verify correct URL and credentials
2. Check browser compatibility (latest Chrome, Firefox, Safari, Edge)
3. Clear browser cache and cookies
4. Try incognito/private browsing mode
5. Contact administrator if issues persist

#### Performance Issues
**Issue**: Slow loading or unresponsive interface
**Solutions**:
1. Check internet connection stability
2. Close unnecessary browser tabs
3. Disable browser extensions temporarily
4. Try different browser
5. Contact support if problems continue

#### Analysis Not Starting
**Issue**: AI analysis fails to initiate
**Solutions**:
1. Verify system description is comprehensive (minimum 50 words)
2. Check AI service availability in dashboard
3. Try different LLM provider if available
4. Wait and retry if services are temporarily unavailable
5. Contact administrator for service status

#### Missing Data or Features
**Issue**: Expected data or features not visible
**Solutions**:
1. Check user role permissions
2. Verify project access rights
3. Refresh page or logout/login again
4. Check if features require specific user roles
5. Contact administrator for access issues

### Getting Help

#### Self-Service Resources
- **User Guide**: This comprehensive documentation
- **FAQ Section**: Common questions and answers
- **Video Tutorials**: Step-by-step guidance for key features
- **Knowledge Base**: Searchable help articles

#### Support Channels
- **Help Desk**: Submit support tickets for technical issues
- **Administrator**: Contact your system administrator
- **Training**: Request additional training sessions
- **Community Forum**: Connect with other users (if available)

#### Reporting Issues
When reporting issues, include:
1. **Browser and Version**: e.g., Chrome 91.0.4472.124
2. **Operating System**: e.g., Windows 10, macOS 12.4
3. **Error Messages**: Exact text of any error messages
4. **Steps to Reproduce**: Detailed steps that led to the issue
5. **Screenshots**: Visual documentation of the problem
6. **Expected Behavior**: What you expected to happen
7. **Actual Behavior**: What actually happened

---

## Support and Resources

### Additional Learning
- **Security Training**: Cybersecurity fundamentals and threat modeling concepts
- **MITRE ATT&CK Training**: Framework-specific training and certification
- **Platform Updates**: Stay informed about new features and capabilities

### Community
- **User Forums**: Connect with other AITM users
- **Best Practices Sharing**: Learn from community experiences
- **Feature Requests**: Suggest improvements and new features

---

*This user guide is regularly updated to reflect the latest platform features and capabilities. For the most current information, always refer to the online documentation.*

*Last Updated: August 9, 2025*
*Document Version: 1.0*
