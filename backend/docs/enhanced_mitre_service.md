# Enhanced MITRE ATT&CK Service

## Overview

The Enhanced MITRE ATT&CK Service provides comprehensive integration with the MITRE ATT&CK framework for advanced threat modeling capabilities. It offers intelligent technique mapping, component-based analysis, attack path generation, and robust search functionality.

## Features

### Core Capabilities
- **Comprehensive ATT&CK Data Management**: Downloads, caches, and manages the complete MITRE ATT&CK knowledge base
- **Intelligent Search**: Advanced technique search with relevance scoring and fuzzy matching
- **Component Mapping**: Maps system components to relevant ATT&CK techniques based on technology stack and component type
- **Entry Point Analysis**: Identifies potential attack techniques based on system entry points and their exposure levels
- **Attack Path Generation**: Creates realistic attack scenarios from entry points to critical assets
- **Performance Optimized**: Caches data in memory with fast search indexes for sub-millisecond queries

### Data Sources
- **Primary**: Official MITRE ATT&CK STIX data from GitHub
- **Fallback**: Local cached files
- **Testing**: Comprehensive sample dataset for development and testing

## Architecture

### Service Components

```python
class EnhancedMitreService:
    # Data Caches
    techniques_cache: Dict[str, Dict[str, Any]]      # Technique ID -> Details
    tactics_cache: Dict[str, List[Dict[str, Any]]]   # Tactic -> Techniques
    platforms_cache: Dict[str, List[Dict[str, Any]]] # Platform -> Techniques
    
    # Search Indexes
    technique_search_index: Dict[str, Set[str]]      # Word -> Technique IDs
    tactic_search_index: Dict[str, Set[str]]         # Word -> Tactic names
    
    # Relationship Mappings
    technique_to_mitigation: Dict[str, List[str]]    # Technique -> Mitigations
    mitigation_to_technique: Dict[str, List[str]]    # Mitigation -> Techniques
```

### Initialization Flow

1. **Check for existing data** (cached file or database)
2. **Download fresh data** if needed from MITRE's official repository
3. **Parse STIX format** and extract techniques, tactics, platforms, and relationships
4. **Build search indexes** for fast text-based queries
5. **Store in database** for persistence across restarts
6. **Fallback to sample data** if download fails (for MVP development)

## API Reference

### Core Data Access

#### `get_technique(technique_id: str) -> Optional[Dict]`
Retrieve a specific technique by its MITRE ATT&CK ID.

```python
technique = mitre_service.get_technique('T1190')
# Returns: {
#     'id': 'T1190',
#     'name': 'Exploit Public-Facing Application',
#     'description': '...',
#     'tactics': ['initial-access'],
#     'platforms': ['Windows', 'Linux', 'macOS'],
#     'mitigations': ['M1048', 'M1050', 'M1051']
# }
```

#### `get_techniques_by_tactic(tactic: str) -> List[Dict]`
Get all techniques associated with a specific tactic.

```python
initial_access = mitre_service.get_techniques_by_tactic('initial-access')
# Returns list of all initial access techniques
```

#### `get_techniques_by_platform(platform: str) -> List[Dict]`
Get all techniques that target a specific platform.

```python
windows_techniques = mitre_service.get_techniques_by_platform('Windows')
# Returns list of Windows-specific techniques
```

### Search and Discovery

#### `search_techniques(query: str) -> List[Dict]`
Search techniques using keywords with relevance scoring.

```python
results = mitre_service.search_techniques('web application exploit')
# Returns ranked list of relevant techniques
```

**Relevance Scoring Features:**
- Exact name matches get highest priority
- Partial name matches get medium priority
- Description matches get lower priority
- Results are automatically sorted by relevance

### Component Analysis

#### `get_techniques_for_system_components(components, entry_points=None, limit_per_component=10)`
Map system components to relevant ATT&CK techniques.

```python
components = [
    {
        'name': 'web-server',
        'type': 'web application',
        'technologies': ['nginx', 'linux']
    }
]

results = mitre_service.get_techniques_for_system_components(components)
# Returns: {
#     'web-server': [
#         {
#             'id': 'T1190',
#             'name': 'Exploit Public-Facing Application',
#             'component_relevance': 2.5,
#             ...
#         }
#     ]
# }
```

**Component Type Mapping:**
- `web` / `application` → Web exploitation techniques
- `database` → Database-specific attacks
- `api` → API security techniques
- `server` / `host` → System-level techniques
- `network` → Network-based attacks

#### `get_techniques_for_entry_points(entry_points, limit=20)`
Identify attack techniques relevant to system entry points.

```python
entry_points = [
    {
        'name': 'public-api',
        'type': 'api',
        'exposure': 'external',
        'authentication_required': False
    }
]

techniques = mitre_service.get_techniques_for_entry_points(entry_points)
# Returns techniques prioritized for external entry points
```

### Attack Path Generation

#### `generate_attack_paths(critical_assets, entry_points, components, paths_per_entry=3, max_path_length=5)`
Generate realistic attack paths from entry points to critical assets.

```python
paths = mitre_service.generate_attack_paths(
    critical_assets=[{'name': 'customer-db', 'criticality': 'critical'}],
    entry_points=[{'name': 'web-app', 'exposure': 'external'}],
    components=[{'name': 'api-server', 'type': 'api'}]
)

# Returns: [
#     {
#         'path_id': 'AP-1',
#         'name': 'Attack via web-app',
#         'techniques': [
#             {
#                 'step': 1,
#                 'technique_id': 'T1190',
#                 'technique_name': 'Exploit Public-Facing Application',
#                 'tactic': 'initial-access',
#                 'target_component': 'web-app'
#             },
#             # ... additional steps
#         ],
#         'likelihood': 'high',
#         'impact': 'critical'
#     }
# ]
```

**Attack Path Features:**
- Follows realistic attack progression through MITRE tactics
- Considers system topology and component relationships
- Provides likelihood and impact assessments
- Generates multiple alternative paths per entry point

## Configuration

### Required Settings

```python
# app/core/config.py
class Settings:
    mitre_attack_data_url: str = "https://github.com/mitre/cti/raw/master/enterprise-attack/enterprise-attack.json"
```

### Data Storage

- **Cache Directory**: `/app/data/mitre/`
- **Database Table**: `mitre_attack`
- **File Format**: JSON (STIX 2.0 format)

### Performance Tuning

- **Memory Usage**: ~10-20MB for full ATT&CK dataset
- **Search Index**: ~5MB additional memory
- **Query Performance**: Sub-millisecond for most operations
- **Initialization Time**: 2-5 seconds (first run with download)

## Usage Examples

### Basic Usage

```python
from app.services.enhanced_mitre_service import get_enhanced_mitre_service

# Get service instance (singleton)
mitre_service = get_enhanced_mitre_service()

# Initialize data (call once at startup)
await mitre_service.initialize()

# Search for techniques
results = mitre_service.search_techniques('credential access')

# Get techniques for a web application
web_techniques = mitre_service.get_techniques_by_platform('Windows')
```

### Integration with Threat Modeling

```python
# Analyze system components
system_components = [
    {'name': 'frontend', 'type': 'web application', 'technologies': ['react', 'nginx']},
    {'name': 'api', 'type': 'api service', 'technologies': ['nodejs', 'docker']},
    {'name': 'database', 'type': 'database', 'technologies': ['postgresql']}
]

# Map to ATT&CK techniques
component_threats = mitre_service.get_techniques_for_system_components(system_components)

# Generate attack scenarios
entry_points = [{'name': 'web-interface', 'exposure': 'external', 'type': 'web'}]
critical_assets = [{'name': 'user-data', 'criticality': 'high'}]

attack_paths = mitre_service.generate_attack_paths(
    critical_assets=critical_assets,
    entry_points=entry_points, 
    components=system_components
)
```

## Testing

### Sample Data

The service includes comprehensive sample data for testing:
- 8 representative ATT&CK techniques
- Coverage of all major tactics
- Multiple platforms (Windows, Linux, macOS)
- Realistic mitigation mappings

### Test Coverage

```bash
# Run tests
pytest backend/tests/test_enhanced_mitre_service.py -v

# Key test areas:
# - Data initialization and caching
# - Search functionality and relevance scoring
# - Component mapping and relevance calculation
# - Attack path generation
# - Error handling and fallback mechanisms
```

## Error Handling

### Graceful Degradation
1. **Network failures**: Falls back to cached data or sample data
2. **Data corruption**: Re-downloads and rebuilds cache
3. **Missing techniques**: Returns empty results without crashing
4. **Invalid queries**: Handles gracefully with empty results

### Logging
- Comprehensive logging at INFO, WARNING, and ERROR levels
- Performance metrics for initialization and search operations
- Error details for troubleshooting data issues

## Performance Considerations

### Memory Management
- Lazy loading of data (only loads when needed)
- Efficient data structures (sets for fast lookups)
- Periodic cleanup of unused cache entries

### Scalability
- Singleton pattern prevents duplicate data loading
- Search indexes enable fast queries on large datasets
- Async/await support for non-blocking operations

## Future Enhancements

### Planned Features
- **Real-time updates**: Monitor MITRE repository for updates
- **Custom techniques**: Support for organization-specific techniques
- **Advanced analytics**: Technique frequency analysis and trending
- **Machine learning**: AI-powered technique recommendation
- **Visualization**: Graph-based attack path visualization

### Integration Points
- **SIEM integration**: Export techniques for security monitoring
- **Vulnerability management**: Map CVEs to ATT&CK techniques  
- **Red team tools**: Export attack paths for penetration testing
- **Compliance mapping**: Map techniques to regulatory frameworks
