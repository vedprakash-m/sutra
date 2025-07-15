"""
Coding Agent Optimizer module for the Forge implementation playbook generation.
Provides agent-specific prompt optimization and context-aware development workflow generation.
"""
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class CodingAgentOptimizer:
    """
    Optimizes prompts and workflows specifically for coding agent consumption
    with complete project context integration.
    """
    
    def __init__(self):
        self.optimization_report = {}
        self.agent_templates = self._load_agent_templates()
    
    def generate_context_optimized_prompts(
        self, 
        project_context: Dict, 
        focus_area: str = 'full-stack',
        optimization_level: str = 'production'
    ) -> Dict[str, Any]:
        """
        Generate coding-agent-optimized prompts using complete project context.
        
        Args:
            project_context: Complete context from all Forge stages
            focus_area: Area of focus (frontend, backend, full-stack, mobile)
            optimization_level: Level of optimization (development, staging, production)
        
        Returns:
            Dictionary of optimized coding prompts
        """
        try:
            # Extract key information from project context
            idea_data = project_context.get('idea_refinement', {})
            prd_data = project_context.get('prd_generation', {})
            ux_data = project_context.get('ux_requirements', {})
            tech_data = project_context.get('technical_analysis', {})
            
            # Generate context-aware prompts
            prompts = {
                "project_setup": self._generate_project_setup_prompt(tech_data, optimization_level),
                "architecture_implementation": self._generate_architecture_prompt(tech_data, prd_data),
                "frontend_development": self._generate_frontend_prompt(ux_data, tech_data),
                "backend_development": self._generate_backend_prompt(prd_data, tech_data),
                "api_development": self._generate_api_prompt(prd_data, tech_data),
                "database_implementation": self._generate_database_prompt(tech_data, prd_data),
                "testing_implementation": self._generate_testing_prompt(tech_data, prd_data),
                "deployment_automation": self._generate_deployment_prompt(tech_data),
                "security_implementation": self._generate_security_prompt(tech_data, prd_data),
                "performance_optimization": self._generate_performance_prompt(tech_data),
                "monitoring_setup": self._generate_monitoring_prompt(tech_data),
                "documentation_generation": self._generate_documentation_prompt(project_context)
            }
            
            # Apply focus area filtering
            if focus_area != 'full-stack':
                prompts = self._filter_by_focus_area(prompts, focus_area)
            
            # Apply agent-specific optimizations
            optimized_prompts = self._apply_agent_optimizations(prompts)
            
            return optimized_prompts
            
        except Exception as e:
            logger.error(f"Error generating context-optimized prompts: {str(e)}")
            return {}
    
    def create_systematic_workflow(
        self,
        technical_specs: Dict,
        ux_specs: Dict,
        requirements: Dict,
        workflow_methodology: str = 'agile_sprints'
    ) -> Dict[str, Any]:
        """
        Create step-by-step development workflow based on specifications.
        
        Args:
            technical_specs: Technical analysis results
            ux_specs: UX requirements data
            requirements: PRD requirements data
            workflow_methodology: Methodology (agile_sprints, waterfall, kanban)
        
        Returns:
            Systematic development workflow
        """
        try:
            workflow = {
                "methodology": workflow_methodology,
                "phases": self._generate_development_phases(technical_specs, requirements),
                "sprints": self._generate_sprint_breakdown(requirements, ux_specs),
                "dependencies": self._analyze_dependencies(technical_specs),
                "critical_path": self._identify_critical_path(technical_specs, requirements),
                "milestones": self._define_milestones(requirements),
                "quality_gates": self._define_quality_gates(technical_specs),
                "risk_mitigation": self._identify_risks_and_mitigation(technical_specs)
            }
            
            return workflow
            
        except Exception as e:
            logger.error(f"Error creating systematic workflow: {str(e)}")
            return {}
    
    def optimize_for_coding_agents(
        self, 
        prompts: Dict, 
        agent_type: str = 'general'
    ) -> Dict[str, Any]:
        """
        Optimize prompts specifically for coding agent consumption.
        
        Args:
            prompts: Raw prompts to optimize
            agent_type: Type of coding agent (general, cursor, copilot, custom)
        
        Returns:
            Agent-optimized prompts
        """
        try:
            optimized = {}
            
            for prompt_key, prompt_content in prompts.items():
                optimized[prompt_key] = {
                    "original": prompt_content,
                    "optimized": self._optimize_single_prompt(prompt_content, agent_type),
                    "agent_instructions": self._generate_agent_instructions(prompt_content, agent_type),
                    "context_awareness": self._add_context_awareness(prompt_content),
                    "validation_criteria": self._define_validation_criteria(prompt_content),
                    "output_format": self._define_output_format(prompt_content),
                    "error_handling": self._add_error_handling(prompt_content)
                }
            
            # Update optimization report
            self.optimization_report = {
                "agent_type": agent_type,
                "optimizations_applied": len(optimized),
                "optimization_timestamp": datetime.now().isoformat(),
                "agent_specific_features": self._get_agent_features(agent_type)
            }
            
            return optimized
            
        except Exception as e:
            logger.error(f"Error optimizing for coding agents: {str(e)}")
            return {}
    
    def get_optimization_report(self) -> Dict[str, Any]:
        """Get the latest optimization report."""
        return self.optimization_report
    
    # Private helper methods
    
    def _load_agent_templates(self) -> Dict[str, Any]:
        """Load agent-specific templates and configurations."""
        return {
            "general": {
                "instruction_format": "Step-by-step instructions with clear objectives",
                "code_style": "Clean, well-commented, production-ready",
                "validation": "Include test cases and validation steps"
            },
            "cursor": {
                "instruction_format": "Context-aware prompts with file references",
                "code_style": "TypeScript/Python focused with modern patterns",
                "validation": "Inline testing and immediate feedback"
            },
            "copilot": {
                "instruction_format": "Comment-driven development prompts",
                "code_style": "GitHub-style with comprehensive documentation",
                "validation": "Built-in testing suggestions"
            },
            "custom": {
                "instruction_format": "Flexible format based on agent capabilities",
                "code_style": "Adaptable to project requirements",
                "validation": "Custom validation based on project needs"
            }
        }
    
    def _generate_project_setup_prompt(self, tech_data: Dict, optimization_level: str) -> str:
        """Generate project setup prompt based on technical specifications."""
        stack = tech_data.get('recommended_stack', {})
        
        prompt = f"""
# Project Setup Instructions

## Objective
Set up a {stack.get('type', 'web')} application with the following technology stack:

## Technology Stack
- Frontend: {stack.get('frontend', 'React')}
- Backend: {stack.get('backend', 'Python')}
- Database: {stack.get('database', 'PostgreSQL')}
- Deployment: {stack.get('deployment', 'Azure')}

## Setup Steps
1. Initialize project structure with appropriate folder organization
2. Configure development environment with all necessary dependencies
3. Set up version control with appropriate .gitignore
4. Configure build and deployment pipelines
5. Implement basic health checks and monitoring

## Quality Requirements ({optimization_level})
- Code coverage: {'95%' if optimization_level == 'production' else '80%'}
- Security scanning: {'Required' if optimization_level == 'production' else 'Recommended'}
- Performance testing: {'Mandatory' if optimization_level == 'production' else 'Optional'}

## Validation
- All dependencies properly installed
- Build process working correctly
- Development server running without errors
- Basic tests passing
"""
        return prompt
    
    def _generate_architecture_prompt(self, tech_data: Dict, prd_data: Dict) -> str:
        """Generate architecture implementation prompt."""
        architecture = tech_data.get('architecture_recommendation', {})
        features = prd_data.get('features', [])
        
        prompt = f"""
# Architecture Implementation

## Architecture Pattern
Implement {architecture.get('pattern', 'microservices')} architecture with the following components:

## Core Components
{self._format_components(architecture.get('components', []))}

## Feature Implementation
{self._format_features(features)}

## Design Principles
- Separation of concerns
- Single responsibility principle
- Dependency injection
- Error handling and logging
- Performance optimization

## Implementation Guidelines
1. Start with core infrastructure components
2. Implement business logic layer by layer
3. Add cross-cutting concerns (logging, monitoring, security)
4. Implement feature-specific components
5. Add integration and testing

## Validation Criteria
- All components properly decoupled
- Clear interfaces between layers
- Comprehensive error handling
- Performance meets requirements
"""
        return prompt
    
    def _generate_frontend_prompt(self, ux_data: Dict, tech_data: Dict) -> str:
        """Generate frontend development prompt."""
        ui_framework = tech_data.get('recommended_stack', {}).get('frontend', 'React')
        design_system = ux_data.get('design_system', {})
        
        prompt = f"""
# Frontend Development Guide

## Framework
Implement using {ui_framework} with modern development practices

## Design System
{self._format_design_system(design_system)}

## Component Development
1. Create reusable UI components following design system
2. Implement responsive layouts for all screen sizes
3. Add accessibility features (WCAG 2.1 AA compliance)
4. Implement state management for complex interactions
5. Add performance optimizations (lazy loading, code splitting)

## User Experience Requirements
{self._format_ux_requirements(ux_data)}

## Testing Strategy
- Component testing with Jest/Testing Library
- Visual regression testing
- Accessibility testing with axe-core
- E2E testing for user journeys

## Performance Targets
- First Contentful Paint: < 1.5s
- Largest Contentful Paint: < 2.5s
- Cumulative Layout Shift: < 0.1
"""
        return prompt
    
    def _generate_backend_prompt(self, prd_data: Dict, tech_data: Dict) -> str:
        """Generate backend development prompt."""
        backend_framework = tech_data.get('recommended_stack', {}).get('backend', 'FastAPI')
        business_logic = prd_data.get('business_logic', [])
        
        prompt = f"""
# Backend Development Guide

## Framework
Implement using {backend_framework} with production-ready patterns

## Business Logic Implementation
{self._format_business_logic(business_logic)}

## API Development
1. Design RESTful APIs following OpenAPI specification
2. Implement proper authentication and authorization
3. Add comprehensive input validation
4. Implement proper error handling and logging
5. Add rate limiting and security measures

## Data Layer
1. Design efficient database schema
2. Implement repository pattern for data access
3. Add connection pooling and optimization
4. Implement caching strategies
5. Add backup and recovery procedures

## Security Implementation
- JWT token-based authentication
- Role-based access control
- Input sanitization and validation
- SQL injection prevention
- Cross-site scripting (XSS) protection
"""
        return prompt
    
    def _generate_api_prompt(self, prd_data: Dict, tech_data: Dict) -> str:
        """Generate API development prompt."""
        endpoints = prd_data.get('api_requirements', [])
        
        prompt = f"""
# API Development Guide

## API Endpoints
{self._format_api_endpoints(endpoints)}

## Implementation Standards
1. Follow RESTful conventions
2. Use appropriate HTTP status codes
3. Implement proper pagination for list endpoints
4. Add comprehensive documentation with OpenAPI/Swagger
5. Include request/response examples

## Security Requirements
- Authentication on all protected endpoints
- Input validation for all parameters
- Rate limiting per user/IP
- CORS configuration
- API versioning strategy

## Testing Requirements
- Unit tests for all business logic
- Integration tests for API endpoints
- Load testing for performance validation
- Security testing for vulnerabilities
"""
        return prompt
    
    def _generate_database_prompt(self, tech_data: Dict, prd_data: Dict) -> str:
        """Generate database implementation prompt."""
        database_type = tech_data.get('recommended_stack', {}).get('database', 'PostgreSQL')
        data_models = prd_data.get('data_models', [])
        
        prompt = f"""
# Database Implementation Guide

## Database System
Implement using {database_type} with proper schema design

## Data Models
{self._format_data_models(data_models)}

## Schema Design
1. Design normalized schema with appropriate relationships
2. Add proper indexes for query optimization
3. Implement constraints and validation rules
4. Add audit trails for data changes
5. Design backup and recovery strategies

## Performance Optimization
- Query optimization and indexing
- Connection pooling
- Caching strategies
- Partitioning for large tables
- Monitoring and alerting

## Security Measures
- Encrypted connections
- Principle of least privilege
- Data encryption at rest
- Regular security audits
"""
        return prompt
    
    def _generate_testing_prompt(self, tech_data: Dict, prd_data: Dict) -> str:
        """Generate testing implementation prompt."""
        testing_framework = tech_data.get('testing_framework', 'Jest/Pytest')
        
        prompt = f"""
# Testing Implementation Guide

## Testing Framework
Implement comprehensive testing using {testing_framework}

## Testing Strategy
1. Unit Tests - Test individual components and functions
2. Integration Tests - Test component interactions
3. API Tests - Test all endpoints and business logic
4. E2E Tests - Test complete user workflows
5. Performance Tests - Validate performance requirements
6. Security Tests - Test for vulnerabilities

## Coverage Requirements
- Unit test coverage: 90%+
- Integration test coverage: 80%+
- API test coverage: 100%
- Critical path E2E coverage: 100%

## Test Implementation
{self._format_test_requirements(prd_data)}

## Continuous Testing
- Automated test execution in CI/CD
- Test results reporting
- Performance regression testing
- Security vulnerability scanning
"""
        return prompt
    
    def _generate_deployment_prompt(self, tech_data: Dict) -> str:
        """Generate deployment automation prompt."""
        deployment_target = tech_data.get('deployment_target', 'Azure')
        
        prompt = f"""
# Deployment Automation Guide

## Deployment Target
Deploy to {deployment_target} with automated CI/CD pipeline

## Infrastructure as Code
1. Define infrastructure using Terraform/ARM templates
2. Implement environment-specific configurations
3. Add monitoring and alerting setup
4. Configure backup and disaster recovery
5. Implement security configurations

## CI/CD Pipeline
1. Automated testing on pull requests
2. Build and artifact creation
3. Automated deployment to staging
4. Manual approval for production deployment
5. Rollback procedures and monitoring

## Deployment Strategies
- Blue-green deployment for zero downtime
- Feature flags for controlled rollouts
- Health checks and smoke tests
- Automated rollback on failure

## Monitoring and Alerting
- Application performance monitoring
- Infrastructure monitoring
- Log aggregation and analysis
- Alert configuration for critical issues
"""
        return prompt
    
    def _generate_security_prompt(self, tech_data: Dict, prd_data: Dict) -> str:
        """Generate security implementation prompt."""
        security_requirements = prd_data.get('security_requirements', [])
        
        prompt = f"""
# Security Implementation Guide

## Security Requirements
{self._format_security_requirements(security_requirements)}

## Authentication and Authorization
1. Implement JWT-based authentication
2. Add role-based access control (RBAC)
3. Implement session management
4. Add multi-factor authentication (MFA)
5. Configure password policies

## Data Protection
1. Encrypt sensitive data at rest and in transit
2. Implement data classification and handling
3. Add audit logging for data access
4. Implement data retention policies
5. Add GDPR compliance measures

## Application Security
- Input validation and sanitization
- SQL injection prevention
- Cross-site scripting (XSS) protection
- Cross-site request forgery (CSRF) protection
- Security headers implementation

## Security Testing
- Static application security testing (SAST)
- Dynamic application security testing (DAST)
- Dependency vulnerability scanning
- Penetration testing
"""
        return prompt
    
    def _generate_performance_prompt(self, tech_data: Dict) -> str:
        """Generate performance optimization prompt."""
        performance_targets = tech_data.get('performance_targets', {})
        
        prompt = f"""
# Performance Optimization Guide

## Performance Targets
{self._format_performance_targets(performance_targets)}

## Frontend Optimization
1. Implement code splitting and lazy loading
2. Optimize images and static assets
3. Add service worker for caching
4. Minimize bundle size
5. Implement performance monitoring

## Backend Optimization
1. Optimize database queries and indexes
2. Implement caching strategies (Redis, CDN)
3. Add connection pooling
4. Optimize API response times
5. Implement async processing for heavy operations

## Infrastructure Optimization
- Auto-scaling configuration
- Load balancing setup
- CDN configuration for static assets
- Database optimization and monitoring
- Performance monitoring and alerting

## Monitoring and Analysis
- Real user monitoring (RUM)
- Application performance monitoring (APM)
- Database performance monitoring
- Infrastructure monitoring
- Performance regression testing
"""
        return prompt
    
    def _generate_monitoring_prompt(self, tech_data: Dict) -> str:
        """Generate monitoring setup prompt."""
        monitoring_stack = tech_data.get('monitoring_stack', 'Azure Monitor')
        
        prompt = f"""
# Monitoring and Observability Setup

## Monitoring Stack
Implement comprehensive monitoring using {monitoring_stack}

## Application Monitoring
1. Application performance monitoring (APM)
2. Real user monitoring (RUM)
3. Error tracking and alerting
4. Business metrics tracking
5. Custom metrics and dashboards

## Infrastructure Monitoring
1. Server and container monitoring
2. Database performance monitoring
3. Network and security monitoring
4. Resource utilization tracking
5. Capacity planning metrics

## Logging Strategy
1. Centralized log aggregation
2. Structured logging implementation
3. Log correlation and analysis
4. Security event logging
5. Compliance and audit logging

## Alerting and Incident Response
- Critical alert configuration
- Escalation procedures
- Incident response playbook
- Post-incident analysis
- Continuous improvement process
"""
        return prompt
    
    def _generate_documentation_prompt(self, project_context: Dict) -> str:
        """Generate documentation generation prompt."""
        prompt = f"""
# Documentation Generation Guide

## Technical Documentation
1. API documentation with OpenAPI/Swagger
2. Architecture documentation with diagrams
3. Database schema documentation
4. Deployment and operations guide
5. Security and compliance documentation

## User Documentation
1. User guides and tutorials
2. Feature documentation
3. Troubleshooting guides
4. FAQ and knowledge base
5. Video tutorials and demos

## Developer Documentation
1. Code documentation and comments
2. Contributing guidelines
3. Development setup guide
4. Testing guidelines
5. Code review standards

## Documentation Standards
- Clear and concise writing
- Up-to-date and accurate information
- Interactive examples and code samples
- Version control for documentation
- Regular review and updates

## Documentation Tools
- Automated API documentation generation
- Architecture diagram tools
- Documentation website generation
- Version control integration
- Collaborative editing capabilities
"""
        return prompt
    
    def _filter_by_focus_area(self, prompts: Dict, focus_area: str) -> Dict:
        """Filter prompts based on focus area."""
        focus_filters = {
            'frontend': ['project_setup', 'frontend_development', 'testing_implementation', 'deployment_automation'],
            'backend': ['project_setup', 'backend_development', 'api_development', 'database_implementation', 'testing_implementation', 'deployment_automation'],
            'mobile': ['project_setup', 'frontend_development', 'api_development', 'testing_implementation', 'deployment_automation'],
            'devops': ['project_setup', 'deployment_automation', 'monitoring_setup', 'security_implementation']
        }
        
        if focus_area in focus_filters:
            return {key: prompts[key] for key in focus_filters[focus_area] if key in prompts}
        
        return prompts
    
    def _apply_agent_optimizations(self, prompts: Dict) -> Dict:
        """Apply agent-specific optimizations to prompts."""
        optimized = {}
        
        for key, prompt in prompts.items():
            optimized[key] = {
                "content": prompt,
                "agent_instructions": self._generate_agent_instructions(prompt, 'general'),
                "validation_criteria": self._define_validation_criteria(prompt),
                "output_format": self._define_output_format(prompt),
                "context_requirements": self._add_context_awareness(prompt)
            }
        
        return optimized
    
    def _optimize_single_prompt(self, prompt: str, agent_type: str) -> str:
        """Optimize a single prompt for specific agent type."""
        template = self.agent_templates.get(agent_type, self.agent_templates['general'])
        
        # Add agent-specific optimizations
        optimized = f"""
{prompt}

## Agent Instructions ({agent_type})
- Instruction Format: {template['instruction_format']}
- Code Style: {template['code_style']}
- Validation: {template['validation']}

## Context Awareness
- Use project context from previous stages
- Maintain consistency with established patterns
- Consider performance and security implications

## Output Requirements
- Provide working, tested code
- Include comprehensive comments
- Add error handling and validation
- Include relevant tests
"""
        return optimized
    
    def _generate_agent_instructions(self, prompt: str, agent_type: str) -> List[str]:
        """Generate specific instructions for coding agents."""
        return [
            "Read and understand the complete project context",
            "Follow established coding patterns and conventions",
            "Implement comprehensive error handling",
            "Add appropriate tests for all functionality",
            "Include performance and security considerations",
            "Maintain code quality and documentation standards"
        ]
    
    def _add_context_awareness(self, prompt: str) -> Dict[str, str]:
        """Add context awareness requirements to prompts."""
        return {
            "project_context": "Use information from all previous Forge stages",
            "consistency": "Maintain consistency with established patterns",
            "dependencies": "Consider dependencies and integrations",
            "quality_standards": "Follow project quality standards"
        }
    
    def _define_validation_criteria(self, prompt: str) -> List[str]:
        """Define validation criteria for prompt outputs."""
        return [
            "Code compiles without errors",
            "All tests pass successfully",
            "Code follows project conventions",
            "Performance requirements met",
            "Security requirements satisfied"
        ]
    
    def _define_output_format(self, prompt: str) -> Dict[str, str]:
        """Define expected output format for prompts."""
        return {
            "code_files": "Complete, working code files",
            "tests": "Comprehensive test files",
            "documentation": "Clear documentation and comments",
            "configuration": "Necessary configuration files"
        }
    
    def _add_error_handling(self, prompt: str) -> List[str]:
        """Add error handling requirements to prompts."""
        return [
            "Implement try-catch blocks for error-prone operations",
            "Add appropriate logging for debugging",
            "Handle edge cases and invalid inputs",
            "Provide meaningful error messages",
            "Implement graceful degradation where appropriate"
        ]
    
    def _get_agent_features(self, agent_type: str) -> List[str]:
        """Get features specific to agent type."""
        features = {
            'general': ['Clear instructions', 'Comprehensive validation', 'Flexible format'],
            'cursor': ['Context awareness', 'File references', 'Real-time feedback'],
            'copilot': ['Comment-driven', 'GitHub integration', 'Code suggestions'],
            'custom': ['Adaptable format', 'Custom validation', 'Flexible requirements']
        }
        return features.get(agent_type, features['general'])
    
    # Formatting helper methods
    
    def _format_components(self, components: List) -> str:
        """Format architecture components for prompt."""
        return '\n'.join([f"- {comp}" for comp in components]) if components else "- Core application components"
    
    def _format_features(self, features: List) -> str:
        """Format features for prompt."""
        return '\n'.join([f"- {feature}" for feature in features]) if features else "- Core application features"
    
    def _format_design_system(self, design_system: Dict) -> str:
        """Format design system for prompt."""
        if not design_system:
            return "- Implement consistent design system with reusable components"
        return f"- Colors: {design_system.get('colors', 'Default')}\n- Typography: {design_system.get('typography', 'Default')}"
    
    def _format_ux_requirements(self, ux_data: Dict) -> str:
        """Format UX requirements for prompt."""
        return "- Responsive design for all devices\n- Accessibility compliance (WCAG 2.1 AA)\n- Intuitive user interface"
    
    def _format_business_logic(self, business_logic: List) -> str:
        """Format business logic for prompt."""
        return '\n'.join([f"- {logic}" for logic in business_logic]) if business_logic else "- Core business logic implementation"
    
    def _format_api_endpoints(self, endpoints: List) -> str:
        """Format API endpoints for prompt."""
        return '\n'.join([f"- {endpoint}" for endpoint in endpoints]) if endpoints else "- RESTful API endpoints"
    
    def _format_data_models(self, data_models: List) -> str:
        """Format data models for prompt."""
        return '\n'.join([f"- {model}" for model in data_models]) if data_models else "- Core data models"
    
    def _format_test_requirements(self, prd_data: Dict) -> str:
        """Format test requirements for prompt."""
        return "- Test all user stories and acceptance criteria\n- Test error handling and edge cases\n- Test performance requirements"
    
    def _format_security_requirements(self, security_requirements: List) -> str:
        """Format security requirements for prompt."""
        return '\n'.join([f"- {req}" for req in security_requirements]) if security_requirements else "- Standard security requirements"
    
    def _format_performance_targets(self, performance_targets: Dict) -> str:
        """Format performance targets for prompt."""
        if not performance_targets:
            return "- Response time: < 300ms\n- Throughput: High\n- Availability: 99.9%"
        return '\n'.join([f"- {key}: {value}" for key, value in performance_targets.items()])
    
    # Workflow generation methods
    
    def _generate_development_phases(self, technical_specs: Dict, requirements: Dict) -> List[Dict]:
        """Generate development phases for workflow."""
        return [
            {"phase": "Planning", "duration": "1 week", "activities": ["Requirements analysis", "Technical design"]},
            {"phase": "Development", "duration": "8 weeks", "activities": ["Core development", "Feature implementation"]},
            {"phase": "Testing", "duration": "2 weeks", "activities": ["Testing", "Bug fixes"]},
            {"phase": "Deployment", "duration": "1 week", "activities": ["Production deployment", "Monitoring setup"]}
        ]
    
    def _generate_sprint_breakdown(self, requirements: Dict, ux_specs: Dict) -> List[Dict]:
        """Generate sprint breakdown for agile workflow."""
        return [
            {"sprint": 1, "duration": "2 weeks", "focus": "Project setup and architecture"},
            {"sprint": 2, "duration": "2 weeks", "focus": "Core functionality implementation"},
            {"sprint": 3, "duration": "2 weeks", "focus": "User interface development"},
            {"sprint": 4, "duration": "2 weeks", "focus": "Integration and testing"}
        ]
    
    def _analyze_dependencies(self, technical_specs: Dict) -> List[Dict]:
        """Analyze project dependencies."""
        return [
            {"dependency": "Database setup", "blocks": ["Backend development"]},
            {"dependency": "API development", "blocks": ["Frontend integration"]},
            {"dependency": "Authentication", "blocks": ["Protected features"]}
        ]
    
    def _identify_critical_path(self, technical_specs: Dict, requirements: Dict) -> List[str]:
        """Identify critical path for project completion."""
        return [
            "Project setup",
            "Database implementation",
            "Core API development",
            "Authentication implementation",
            "Frontend development",
            "Integration testing",
            "Deployment"
        ]
    
    def _define_milestones(self, requirements: Dict) -> List[Dict]:
        """Define project milestones."""
        return [
            {"milestone": "MVP Ready", "date": "Week 6", "criteria": ["Core features working"]},
            {"milestone": "Beta Release", "date": "Week 10", "criteria": ["All features complete"]},
            {"milestone": "Production Ready", "date": "Week 12", "criteria": ["Testing complete"]}
        ]
    
    def _define_quality_gates(self, technical_specs: Dict) -> List[Dict]:
        """Define quality gates for workflow."""
        return [
            {"gate": "Code Review", "criteria": ["Code quality", "Security review"]},
            {"gate": "Testing", "criteria": ["Test coverage", "Performance testing"]},
            {"gate": "Security Scan", "criteria": ["Vulnerability scan", "Compliance check"]},
            {"gate": "Deployment", "criteria": ["All tests pass", "Security clear"]}
        ]
    
    def _identify_risks_and_mitigation(self, technical_specs: Dict) -> List[Dict]:
        """Identify risks and mitigation strategies."""
        return [
            {"risk": "Technical complexity", "mitigation": "Prototype critical components early"},
            {"risk": "Performance issues", "mitigation": "Regular performance testing"},
            {"risk": "Security vulnerabilities", "mitigation": "Security reviews and scanning"},
            {"risk": "Timeline delays", "mitigation": "Buffer time and priority management"}
        ]


def generate_coding_prompts(project_context: Dict, optimization_level: str = 'production') -> Dict[str, Any]:
    """
    Convenience function to generate coding prompts.
    
    Args:
        project_context: Complete project context from all Forge stages
        optimization_level: Level of optimization (development, staging, production)
    
    Returns:
        Dictionary of optimized coding prompts
    """
    optimizer = CodingAgentOptimizer()
    return optimizer.generate_context_optimized_prompts(project_context, optimization_level=optimization_level)
