#!/usr/bin/env python3
"""
ULTIMATE RECRUITING ENGINE v9.5 - EVIDENCE-FIRST SOURCING
Production Ready - Core v9 preserved + high-recall BIO OR REPOSITORY discovery
"""

import requests
import json
from datetime import datetime, timedelta, timezone
import re
from html import unescape
import sys
import os

# GitHub API Setup
# Token should be provided by user via environment variable or web interface
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')

github_headers = {
    "Accept": "application/vnd.github.v3+json"
}
if GITHUB_TOKEN:
    github_headers["Authorization"] = f"token {GITHUB_TOKEN}"
else:
    print("⚠️  GITHUB_TOKEN not set. Use Streamlit web interface to provide token.")

# ============================================================================
# v8.0: LOCATION DATABASE (FULLY PRESERVED)
# ============================================================================

LOCATION_DATABASE = {
    'amsterdam': {'country': 'Netherlands', 'region': 'Europe', 'nearby': ['rotterdam', 'utrecht', 'leiden', 'haarlem']},
    'berlin': {'country': 'Germany', 'region': 'Europe', 'nearby': ['potsdam', 'frankfurt', 'munich']},
    'london': {'country': 'UK', 'region': 'Europe', 'nearby': ['cambridge', 'oxford', 'reading']},
    'paris': {'country': 'France', 'region': 'Europe', 'nearby': ['lyon', 'versailles']},
    'barcelona': {'country': 'Spain', 'region': 'Europe', 'nearby': ['madrid', 'valencia']},
    'zurich': {'country': 'Switzerland', 'region': 'Europe', 'nearby': ['bern', 'basel', 'geneva']},
    'stockholm': {'country': 'Sweden', 'region': 'Europe', 'nearby': ['gothenburg', 'uppsala']},
    'dublin': {'country': 'Ireland', 'region': 'Europe', 'nearby': ['cork', 'belfast']},
    'san francisco': {'country': 'USA', 'region': 'Bay Area', 'nearby': ['oakland', 'san jose', 'palo alto', 'mountain view']},
    'seattle': {'country': 'USA', 'region': 'Seattle', 'nearby': ['tacoma', 'bellevue']},
    'new york': {'country': 'USA', 'region': 'NYC', 'nearby': ['brooklyn', 'jersey city']},
    'los angeles': {'country': 'USA', 'region': 'LA', 'nearby': ['santa monica', 'pasadena']},
    'austin': {'country': 'USA', 'region': 'Austin', 'nearby': ['round rock', 'cedar park']},
    'toronto': {'country': 'Canada', 'region': 'North America', 'nearby': ['mississauga', 'brampton']},
    'mexico city': {'country': 'Mexico', 'region': 'LatAm', 'nearby': ['guadalajara', 'monterrey']},
    'sao paulo': {'country': 'Brazil', 'region': 'LatAm', 'nearby': ['rio de janeiro', 'belo horizonte']},
    'buenos aires': {'country': 'Argentina', 'region': 'LatAm', 'nearby': ['la plata']},
    'bogota': {'country': 'Colombia', 'region': 'LatAm', 'nearby': ['medellin', 'cali']},
    'santiago': {'country': 'Chile', 'region': 'LatAm', 'nearby': ['valparaiso']},
    'bangalore': {'country': 'India', 'region': 'India', 'nearby': ['hyderabad', 'pune', 'mysore', 'coimbatore']},
    'mumbai': {'country': 'India', 'region': 'India', 'nearby': ['pune', 'nashik', 'aurangabad']},
    'delhi': {'country': 'India', 'region': 'India', 'nearby': ['noida', 'gurgaon', 'greater noida']},
    'hyderabad': {'country': 'India', 'region': 'India', 'nearby': ['secunderabad', 'vikarabad']},
    'pune': {'country': 'India', 'region': 'India', 'nearby': ['nashik', 'lonavala']},
    'singapore': {'country': 'Singapore', 'region': 'Southeast Asia', 'nearby': ['kuala lumpur', 'penang']},
    'shanghai': {'country': 'China', 'region': 'Asia', 'nearby': ['hangzhou', 'suzhou', 'nanjing']},
    'tokyo': {'country': 'Japan', 'region': 'Asia', 'nearby': ['osaka', 'yokohama', 'kawasaki']},
    'sydney': {'country': 'Australia', 'region': 'Oceania', 'nearby': ['melbourne', 'brisbane']},
}

REGION_MAPPINGS = {
    'india': ['bangalore', 'mumbai', 'delhi', 'hyderabad', 'pune', 'noida', 'gurgaon', 'nashik', 'coimbatore'],
    'europe': ['amsterdam', 'berlin', 'london', 'paris', 'barcelona', 'zurich', 'stockholm', 'dublin'],
    'latam': ['mexico city', 'sao paulo', 'buenos aires', 'bogota', 'santiago'],
    'asia': ['bangalore', 'mumbai', 'delhi', 'hyderabad', 'pune', 'singapore', 'shanghai', 'tokyo'],
    'southeast asia': ['singapore', 'kuala lumpur', 'penang', 'bangkok', 'jakarta'],
    'usa': ['san francisco', 'seattle', 'new york', 'los angeles', 'austin'],
    'north america': ['san francisco', 'seattle', 'new york', 'los angeles', 'austin', 'toronto'],
    'oceania': ['sydney', 'melbourne', 'brisbane'],
    'australia': ['sydney', 'melbourne', 'brisbane'],
    'middle east': ['dubai', 'tel aviv', 'istanbul'],
    'africa': ['johannesburg', 'cape town', 'cairo'],
}

# ============================================================================
# v8.0: LEVENSHTEIN DISTANCE (FULLY PRESERVED)
# ============================================================================

def levenshtein_distance(s1, s2):
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]

def fuzzy_match(keyword, text, max_distance=2):
    if keyword in text:
        return True
    if len(keyword) <= 2:
        return False
    words = text.split()
    for word in words:
        clean_word = re.sub(r'[^a-z0-9]', '', word.lower())
        distance = levenshtein_distance(keyword, clean_word)
        if distance <= max_distance:
            return True
    return False

# ============================================================================
# v8.0: LOCATION FILTERING (FULLY PRESERVED)
# ============================================================================

def parse_location_input(location_input):
    location_input = location_input.lower().strip()
    
    if location_input in ['global', 'remote', 'anywhere', 'distributed', 'worldwide', 'world', 'planet']:
        return {
            'type': 'GLOBAL',
            'locations': [None],
            'description': 'WORLDWIDE (All Locations)',
            'is_global': True
        }
    
    if location_input in LOCATION_DATABASE:
        loc_info = LOCATION_DATABASE[location_input]
        return {
            'type': 'SPECIFIC',
            'city': location_input,
            'country': loc_info['country'],
            'region': loc_info['region'],
            'nearby': loc_info['nearby'],
            'description': f"{location_input.upper()} • {loc_info['country']} • Nearby included",
            'is_global': False
        }
    
    matches = [k for k in LOCATION_DATABASE.keys() if location_input in k or k.startswith(location_input)]
    if matches:
        loc_info = LOCATION_DATABASE[matches[0]]
        return {
            'type': 'SPECIFIC',
            'city': matches[0],
            'country': loc_info['country'],
            'region': loc_info['region'],
            'nearby': loc_info['nearby'],
            'description': f"{matches[0].upper()} • {loc_info['country']} • Nearby included",
            'is_global': False
        }
    
    for region, cities in REGION_MAPPINGS.items():
        if location_input == region or location_input == region.replace(' ', ''):
            return {
                'type': 'REGION',
                'region': region.upper(),
                'cities': cities,
                'description': f"{region.upper()} • All major cities included",
                'is_global': False
            }
    
    if location_input.isalpha() or ' ' in location_input and all(c.isalpha() or c == ' ' for c in location_input):
        return {
            'type': 'RAW_LOCATION',
            'raw_input': location_input,
            'description': f"{location_input.upper()} • Raw location search (any global location accepted)",
            'is_global': False
        }
    
    print(f"\n⚠️  Location '{location_input}' not recognized in database.")
    print(f"   Proceeding with raw location search on GitHub...\n")
    
    return {
        'type': 'RAW_LOCATION',
        'raw_input': location_input,
        'description': f"{location_input.upper()} • Raw location search",
        'is_global': False
    }

def should_include_candidate(candidate_location, location_filter):
    if location_filter['is_global']:
        return True, 0
    
    candidate_loc = (candidate_location or '').lower().strip()
    
    if candidate_loc == '':
        return True, -10
    
    if location_filter['type'] == 'SPECIFIC':
        city = location_filter['city'].lower()
        country = location_filter['country'].lower()
        nearby = [n.lower() for n in location_filter['nearby']]
        
        if city in candidate_loc or country in candidate_loc:
            return True, 20
        if any(n in candidate_loc for n in nearby):
            return True, 15
        if country in candidate_loc:
            return True, 10
        return False, 0
    
    elif location_filter['type'] == 'REGION':
        region = location_filter['region'].lower()
        cities = [c.lower() for c in location_filter['cities']]
        
        if any(city in candidate_loc for city in cities):
            return True, 15
        return False, 0
    
    elif location_filter['type'] == 'RAW_LOCATION':
        raw_input = location_filter['raw_input'].lower()
        if raw_input in candidate_loc:
            return True, 15
        parts = raw_input.split()
        if any(part in candidate_loc for part in parts):
            return True, 10
        return True, -10
    
    return True, 0

# ============================================================================
# v8.0: OPEN TO WORK DETECTION (FULLY PRESERVED)
# ============================================================================

def detect_open_to_work(bio_text):
    if not bio_text:
        return False, 'NOT_MENTIONED'
    
    bio_lower = bio_text.lower()
    open_signals = ['open to work', 'open for', 'available for', 'hiring', 'looking for', 'seeking', 'available', 'open to', 'interested in', 'work opportunities', 'opportunity', 'actively looking', 'actively seeking']
    
    for signal in open_signals:
        if signal in bio_lower:
            return True, signal
    
    return False, 'NOT_MENTIONED'

# ============================================================================
# v8.0: 150+ SKILLS DATABASE (FULLY PRESERVED)
# ============================================================================

def build_skill_families_dynamically(skills_db):
    """
    DYNAMIC SKILL FAMILIES - Zero hardcoding.
    
    Builds skill relationships on-the-fly from the database itself.
    Handles infinite roles by understanding skill relationships.
    
    Algorithm:
    1. Group skills by domain (frontend, backend, ml, devops, etc.)
    2. Create relationship graph (if A relates to B, connect them)
    3. Find skill clusters (skills that relate to each other)
    4. Return dynamic families based on actual data
    
    Result: Infinite role coverage, zero hardcoded limits.
    """
    
    # Step 1: Group by domain
    domain_skills = {}
    for skill_name, skill_info in skills_db.items():
        domain = skill_info.get('domain', 'Other')
        if domain not in domain_skills:
            domain_skills[domain] = []
        domain_skills[domain].append(skill_name)
    
    # Step 2: Build relationship graph
    skill_relationships = {}
    for skill_name, skill_info in skills_db.items():
        related = set(skill_info.get('related_skills', []))
        # Also add skills from same domain as related
        domain = skill_info.get('domain', 'Other')
        related.update(domain_skills.get(domain, []))
        # Remove self-references
        related.discard(skill_name)
        skill_relationships[skill_name] = related
    
    # Step 3: Build dynamic families by domain
    families = {}
    
    # Create a family for each domain
    for domain, skills_in_domain in domain_skills.items():
        family_name = domain.lower().replace('/', '_').replace(' ', '_')
        families[family_name] = skills_in_domain
    
    # Step 4: Create cross-domain families from relationships
    # Find clusters of highly-related skills
    processed = set()
    cluster_num = 0
    
    for skill_name, related_skills in skill_relationships.items():
        if skill_name in processed:
            continue
        
        # Build a cluster around this skill
        cluster = {skill_name}
        cluster.update(related_skills)
        processed.update(cluster)
        
        # Create a cluster family
        if len(cluster) > 2:  # Only create if meaningful
            cluster_name = f"cluster_{cluster_num}_{'_'.join(list(cluster)[:3])}"
            families[cluster_name] = list(cluster)
            cluster_num += 1
    
    return families, skill_relationships, domain_skills

def find_related_skills_intelligent(mentioned_skills, skill_relationships, skills_db):
    """
    When user mentions ANY skill, find all related skills automatically.
    No hardcoding. Pure relationship inference.
    
    Example:
      User: "PyTorch and deep learning"
      System finds: tensorflow, keras, jax, neural networks, cnn, rnn, transformers
      (all related to pytorch or deep learning from the database)
    """
    
    related_to_mentioned = set(mentioned_skills)
    
    for skill in mentioned_skills:
        if skill in skill_relationships:
            # Add all skills that relate to this one
            related_to_mentioned.update(skill_relationships[skill])
            
            # Also add 2-hop relationships (friends of friends)
            for related_skill in skill_relationships.get(skill, []):
                related_to_mentioned.update(skill_relationships.get(related_skill, []))
    
    return related_to_mentioned

def get_skill_families():
    """Returns empty dict - families are now built dynamically"""
    return {}

def extract_skills_semantically(text_section, skills_db, all_skills_in_jd=None):
    """
    SMART EXTRACTION: Dynamically intelligent skill extraction.
    
    - Finds directly mentioned skills (exact + fuzzy match)
    - Uses relationship engine to find related skills (no hardcoding)
    - Filters by domain context (avoids irrelevant skills)
    - Handles infinite roles (works for any skill combination)
    - Zero hardcoded families
    """
    if not text_section:
        return []
    
    text_lower = text_section.lower()
    
    # Build dynamic relationships from skills database
    families, skill_relationships, domain_skills = build_skill_families_dynamically(skills_db)
    
    # Step 1: Find directly mentioned skills
    directly_mentioned = []
    for skill_name, skill_info in skills_db.items():
        keywords = skill_info.get('keywords', [])
        synonyms = skill_info.get('synonyms', [])
        all_terms = keywords + synonyms
        
        for term in all_terms:
            if fuzzy_match(term, text_lower, max_distance=2):
                directly_mentioned.append(skill_name)
                break
    
    # Step 2: Find related skills using relationship engine
    all_related = find_related_skills_intelligent(directly_mentioned, skill_relationships, skills_db)
    
    # Step 3: Deduplicate synonyms
    deduplicated = []
    for skill in all_related:
        if skill not in skills_db:
            continue
        is_parent = False
        for parent_name in all_related:
            if parent_name == skill:
                continue
            parent_synonyms = skills_db.get(parent_name, {}).get('synonyms', [])
            if skill in parent_synonyms:
                is_parent = True
                break
        
        if not is_parent and skill not in deduplicated:
            deduplicated.append(skill)
    
    # Step 4: Filter by domain context (keep skills from primary domain + related domains)
    domain_context = {}
    for skill in deduplicated:
        domain = skills_db.get(skill, {}).get('domain', 'Other')
        domain_context[domain] = domain_context.get(domain, 0) + 1
    
    if not domain_context:
        return deduplicated
    
    # Find primary domain
    primary_domain = max(domain_context.keys(), key=lambda x: domain_context[x])
    
    # Define domain conflicts (skills that don't belong together)
    domain_conflicts = {
        'Frontend': ['Backend', 'Infrastructure', 'Database', 'Mobile'],
        'Backend': ['Frontend', 'Mobile'],
        'Infrastructure': ['Frontend', 'Backend', 'Mobile'],
        'AI/ML': ['Frontend', 'Mobile'],
        'Mobile': ['Backend', 'Frontend', 'Infrastructure'],
    }
    
    # Filter conflicting skills
    rejected_domains = domain_conflicts.get(primary_domain, [])
    final_skills = [
        skill for skill in deduplicated
        if skills_db.get(skill, {}).get('domain', 'Other') not in rejected_domains
    ]
    
    return final_skills if final_skills else deduplicated

def get_skills_database():
    return {
        'python': {'keywords': ['python', 'py3', 'python3'], 'synonyms': ['py'], 'related_skills': ['data science', 'machine learning', 'devops'], 'domain': 'Language'},
        'java': {'keywords': ['java ', ' java', 'java programming'], 'synonyms': [], 'related_skills': ['spring', 'microservices', 'backend'], 'domain': 'Language'},
        'go': {'keywords': ['golang', 'go language'], 'synonyms': [], 'related_skills': ['kubernetes', 'devops', 'microservices'], 'domain': 'Language'},
        'rust': {'keywords': ['rust', 'rustlang'], 'synonyms': [], 'related_skills': ['systems', 'performance'], 'domain': 'Language'},
        'javascript': {'keywords': ['javascript', 'js ', 'node.js', 'nodejs'], 'synonyms': ['js'], 'related_skills': ['react', 'typescript', 'frontend'], 'domain': 'Language'},
        'typescript': {'keywords': ['typescript', 'ts '], 'synonyms': [], 'related_skills': ['javascript', 'react', 'angular'], 'domain': 'Language'},
        'c++': {'keywords': ['c++', 'cpp'], 'synonyms': [], 'related_skills': ['systems', 'performance'], 'domain': 'Language'},
        'c#': {'keywords': ['c#', 'csharp', 'c-sharp'], 'synonyms': [], 'related_skills': ['asp.net', 'dotnet'], 'domain': 'Language'},
        'sql': {'keywords': ['sql', 'tsql', 'plsql'], 'synonyms': [], 'related_skills': ['database', 'data engineering'], 'domain': 'Language'},
        'bash': {'keywords': ['bash', 'shell', 'sh '], 'synonyms': [], 'related_skills': ['devops', 'automation', 'linux'], 'domain': 'Language'},
        'swift': {'keywords': ['swift'], 'synonyms': [], 'related_skills': ['ios', 'mobile'], 'domain': 'Language'},
        'kotlin': {'keywords': ['kotlin'], 'synonyms': [], 'related_skills': ['android', 'java', 'mobile'], 'domain': 'Language'},
        'ruby': {'keywords': ['ruby'], 'synonyms': [], 'related_skills': ['rails', 'backend'], 'domain': 'Language'},
        'php': {'keywords': ['php'], 'synonyms': [], 'related_skills': ['laravel', 'backend'], 'domain': 'Language'},
        'react': {'keywords': ['react', 'reactjs', 'react.js'], 'synonyms': [], 'related_skills': ['javascript', 'typescript', 'frontend'], 'domain': 'Frontend'},
        'angular': {'keywords': ['angular', 'angularjs'], 'synonyms': [], 'related_skills': ['typescript', 'javascript', 'frontend'], 'domain': 'Frontend'},
        'vue': {'keywords': ['vue', 'vuejs', 'vue.js'], 'synonyms': [], 'related_skills': ['javascript', 'frontend'], 'domain': 'Frontend'},
        'html': {'keywords': ['html', 'html5'], 'synonyms': [], 'related_skills': ['css', 'frontend'], 'domain': 'Frontend'},
        'css': {'keywords': ['css', 'css3', 'scss', 'sass'], 'synonyms': [], 'related_skills': ['html', 'frontend'], 'domain': 'Frontend'},
        'webpack': {'keywords': ['webpack'], 'synonyms': [], 'related_skills': ['frontend', 'build tools'], 'domain': 'Frontend'},
        'tailwind': {'keywords': ['tailwind', 'tailwind css'], 'synonyms': [], 'related_skills': ['css', 'frontend'], 'domain': 'Frontend'},
        'spring': {'keywords': ['spring', 'spring boot'], 'synonyms': [], 'related_skills': ['java', 'microservices'], 'domain': 'Backend'},
        'django': {'keywords': ['django'], 'synonyms': [], 'related_skills': ['python', 'backend'], 'domain': 'Backend'},
        'flask': {'keywords': ['flask'], 'synonyms': [], 'related_skills': ['python', 'backend'], 'domain': 'Backend'},
        'fastapi': {'keywords': ['fastapi'], 'synonyms': [], 'related_skills': ['python', 'backend', 'api'], 'domain': 'Backend'},
        'express': {'keywords': ['express', 'express.js'], 'synonyms': [], 'related_skills': ['javascript', 'nodejs', 'backend'], 'domain': 'Backend'},
        'rails': {'keywords': ['rails', 'ruby on rails'], 'synonyms': [], 'related_skills': ['ruby', 'backend'], 'domain': 'Backend'},
        'asp.net': {'keywords': ['asp.net', 'asp net', '.net'], 'synonyms': [], 'related_skills': ['c#', 'backend'], 'domain': 'Backend'},
        'laravel': {'keywords': ['laravel'], 'synonyms': [], 'related_skills': ['php', 'backend'], 'domain': 'Backend'},
        'postgresql': {'keywords': ['postgresql', 'postgres', 'pg '], 'synonyms': [], 'related_skills': ['sql', 'database'], 'domain': 'Database'},
        'mysql': {'keywords': ['mysql'], 'synonyms': [], 'related_skills': ['sql', 'database'], 'domain': 'Database'},
        'mongodb': {'keywords': ['mongodb', 'mongo '], 'synonyms': [], 'related_skills': ['nosql', 'database'], 'domain': 'Database'},
        'redis': {'keywords': ['redis'], 'synonyms': [], 'related_skills': ['cache', 'database'], 'domain': 'Database'},
        'cassandra': {'keywords': ['cassandra'], 'synonyms': [], 'related_skills': ['distributed', 'database'], 'domain': 'Database'},
        'elasticsearch': {'keywords': ['elasticsearch', 'elastic'], 'synonyms': [], 'related_skills': ['search', 'database'], 'domain': 'Database'},
        'dynamodb': {'keywords': ['dynamodb'], 'synonyms': [], 'related_skills': ['aws', 'database'], 'domain': 'Database'},
        'kubernetes': {'keywords': ['kubernetes', 'k8s', 'kube'], 'synonyms': [], 'related_skills': ['docker', 'devops', 'microservices'], 'domain': 'Infrastructure'},
        'docker': {'keywords': ['docker'], 'synonyms': [], 'related_skills': ['kubernetes', 'containers', 'devops'], 'domain': 'Infrastructure'},
        'eks': {'keywords': ['eks'], 'synonyms': ['elastic kubernetes service'], 'related_skills': ['kubernetes', 'aws'], 'domain': 'Infrastructure'},
        'aks': {'keywords': ['aks'], 'synonyms': ['azure kubernetes'], 'related_skills': ['kubernetes', 'azure'], 'domain': 'Infrastructure'},
        'openshift': {'keywords': ['openshift', 'ocp'], 'synonyms': [], 'related_skills': ['kubernetes', 'rancher'], 'domain': 'Infrastructure'},
        'rancher': {'keywords': ['rancher'], 'synonyms': [], 'related_skills': ['kubernetes'], 'domain': 'Infrastructure'},
        'helm': {'keywords': ['helm'], 'synonyms': [], 'related_skills': ['kubernetes', 'devops'], 'domain': 'Infrastructure'},
        'docker compose': {'keywords': ['docker compose', 'docker-compose'], 'synonyms': [], 'related_skills': ['docker', 'containers'], 'domain': 'Infrastructure'},
        'vmware': {'keywords': ['vmware'], 'synonyms': [], 'related_skills': ['vsphere', 'vcf', 'sddc'], 'domain': 'Infrastructure'},
        'vsphere': {'keywords': ['vsphere'], 'synonyms': [], 'related_skills': ['vmware', 'vcf', 'sddc'], 'domain': 'Infrastructure'},
        'vks': {'keywords': ['vks', 'vsphere kubernetes service'], 'synonyms': [], 'related_skills': ['kubernetes', 'vmware', 'vsphere'], 'domain': 'Infrastructure'},
        'vcf': {'keywords': ['vcf', 'vmware cloud foundation'], 'synonyms': [], 'related_skills': ['vmware', 'vsphere', 'sddc'], 'domain': 'Infrastructure'},
        'nsx': {'keywords': ['nsx'], 'synonyms': [], 'related_skills': ['networking', 'vmware'], 'domain': 'Infrastructure'},
        'vsan': {'keywords': ['vsan'], 'synonyms': [], 'related_skills': ['storage', 'vmware'], 'domain': 'Infrastructure'},
        'sddc': {'keywords': ['sddc', 'software-defined'], 'synonyms': [], 'related_skills': ['vmware', 'datacenter'], 'domain': 'Infrastructure'},
        'terraform': {'keywords': ['terraform'], 'synonyms': [], 'related_skills': ['devops', 'infrastructure', 'iac'], 'domain': 'DevOps'},
        'ansible': {'keywords': ['ansible'], 'synonyms': [], 'related_skills': ['devops', 'automation'], 'domain': 'DevOps'},
        'jenkins': {'keywords': ['jenkins'], 'synonyms': [], 'related_skills': ['ci/cd', 'devops'], 'domain': 'DevOps'},
        'gitlab': {'keywords': ['gitlab', 'gitlab ci'], 'synonyms': [], 'related_skills': ['ci/cd', 'devops'], 'domain': 'DevOps'},
        'github actions': {'keywords': ['github actions'], 'synonyms': [], 'related_skills': ['ci/cd', 'devops'], 'domain': 'DevOps'},
        'ci/cd': {'keywords': ['ci/cd', 'continuous integration', 'continuous deployment'], 'synonyms': ['pipeline'], 'related_skills': ['devops'], 'domain': 'DevOps'},
        'devops': {'keywords': ['devops'], 'synonyms': [], 'related_skills': ['infrastructure', 'automation'], 'domain': 'DevOps'},
        'iac': {'keywords': ['iac', 'infrastructure as code'], 'synonyms': [], 'related_skills': ['terraform', 'devops'], 'domain': 'DevOps'},
        'prometheus': {'keywords': ['prometheus'], 'synonyms': [], 'related_skills': ['monitoring', 'observability'], 'domain': 'DevOps'},
        'grafana': {'keywords': ['grafana'], 'synonyms': [], 'related_skills': ['monitoring', 'observability'], 'domain': 'DevOps'},
        'elk': {'keywords': ['elk', 'elasticsearch', 'logstash', 'kibana'], 'synonyms': [], 'related_skills': ['logging', 'monitoring'], 'domain': 'DevOps'},
        'datadog': {'keywords': ['datadog'], 'synonyms': [], 'related_skills': ['monitoring', 'observability'], 'domain': 'DevOps'},
        'aws': {'keywords': ['aws', 'amazon web services'], 'synonyms': [], 'related_skills': ['cloud', 'devops'], 'domain': 'Cloud'},
        'azure': {'keywords': ['azure', 'microsoft azure'], 'synonyms': [], 'related_skills': ['cloud', 'devops'], 'domain': 'Cloud'},
        'gcp': {'keywords': ['gcp', 'google cloud'], 'synonyms': [], 'related_skills': ['cloud', 'devops'], 'domain': 'Cloud'},
        'cloud': {'keywords': ['cloud computing'], 'synonyms': [], 'related_skills': ['aws', 'azure', 'gcp'], 'domain': 'Cloud'},
        's3': {'keywords': ['s3'], 'synonyms': [], 'related_skills': ['aws', 'storage'], 'domain': 'Cloud'},
        'lambda': {'keywords': ['lambda', 'aws lambda'], 'synonyms': [], 'related_skills': ['aws', 'serverless'], 'domain': 'Cloud'},
        'linux': {'keywords': ['linux', 'ubuntu', 'centos'], 'synonyms': [], 'related_skills': ['bash', 'devops'], 'domain': 'Infrastructure'},
        'networking': {'keywords': ['networking', 'network architecture'], 'synonyms': ['network'], 'related_skills': ['devops', 'infrastructure'], 'domain': 'Infrastructure'},
        'cisco': {'keywords': ['cisco', 'ccnp', 'ccie'], 'synonyms': [], 'related_skills': ['networking'], 'domain': 'Infrastructure'},
        'nginx': {'keywords': ['nginx'], 'synonyms': [], 'related_skills': ['web server', 'devops'], 'domain': 'Infrastructure'},
        'apache': {'keywords': ['apache'], 'synonyms': [], 'related_skills': ['web server', 'devops'], 'domain': 'Infrastructure'},
        'rest api': {'keywords': ['rest', 'rest api', 'restful'], 'synonyms': ['api'], 'related_skills': ['backend'], 'domain': 'API'},
        'graphql': {'keywords': ['graphql'], 'synonyms': [], 'related_skills': ['api', 'backend'], 'domain': 'API'},
        'kafka': {'keywords': ['kafka'], 'synonyms': [], 'related_skills': ['event streaming', 'data engineering'], 'domain': 'API'},
        'microservices': {'keywords': ['microservices'], 'synonyms': [], 'related_skills': ['backend', 'kubernetes'], 'domain': 'Architecture'},
        'service mesh': {'keywords': ['service mesh', 'istio'], 'synonyms': [], 'related_skills': ['kubernetes', 'microservices'], 'domain': 'Architecture'},
        'machine learning': {'keywords': ['machine learning'], 'synonyms': ['ml'], 'related_skills': ['python', 'data science'], 'domain': 'AI/ML'},
        'deep learning': {'keywords': ['deep learning', 'neural network'], 'synonyms': [], 'related_skills': ['tensorflow', 'pytorch'], 'domain': 'AI/ML'},
        'pytorch': {'keywords': ['pytorch', 'torch'], 'synonyms': [], 'related_skills': ['tensorflow', 'keras', 'deep learning'], 'domain': 'AI/ML'},
        'tensorflow': {'keywords': ['tensorflow', 'tf.keras'], 'synonyms': [], 'related_skills': ['pytorch', 'keras', 'deep learning'], 'domain': 'AI/ML'},
        'keras': {'keywords': ['keras'], 'synonyms': [], 'related_skills': ['tensorflow', 'deep learning'], 'domain': 'AI/ML'},
        'scikit-learn': {'keywords': ['scikit-learn', 'sklearn'], 'synonyms': [], 'related_skills': ['machine learning', 'python'], 'domain': 'AI/ML'},
        'llm': {'keywords': ['llm', 'large language model'], 'synonyms': [], 'related_skills': ['nlp', 'deep learning'], 'domain': 'AI/ML'},
        'nlp': {'keywords': ['nlp', 'natural language processing'], 'synonyms': [], 'related_skills': ['deep learning', 'llm'], 'domain': 'AI/ML'},
        'computer vision': {'keywords': ['computer vision', 'cv ', 'image processing'], 'synonyms': [], 'related_skills': ['deep learning'], 'domain': 'AI/ML'},
        'reinforcement learning': {'keywords': ['reinforcement learning'], 'synonyms': [], 'related_skills': ['machine learning', 'deep learning'], 'domain': 'AI/ML'},
        'huggingface': {'keywords': ['huggingface', 'hugging face'], 'synonyms': [], 'related_skills': ['nlp', 'transformers'], 'domain': 'AI/ML'},
        'transformers': {'keywords': ['transformers'], 'synonyms': [], 'related_skills': ['nlp', 'deep learning'], 'domain': 'AI/ML'},
        'prompt engineering': {'keywords': ['prompt engineering', 'prompting'], 'synonyms': [], 'related_skills': ['llm'], 'domain': 'AI/ML'},
        'mlops': {'keywords': ['mlops'], 'synonyms': [], 'related_skills': ['devops', 'machine learning'], 'domain': 'AI/ML'},
        'data science': {'keywords': ['data science'], 'synonyms': [], 'related_skills': ['python', 'machine learning'], 'domain': 'AI/ML'},
        'spark': {'keywords': ['spark', 'apache spark', 'pyspark'], 'synonyms': [], 'related_skills': ['data engineering', 'python'], 'domain': 'Data'},
        'hadoop': {'keywords': ['hadoop'], 'synonyms': [], 'related_skills': ['distributed', 'data engineering'], 'domain': 'Data'},
        'airflow': {'keywords': ['airflow'], 'synonyms': [], 'related_skills': ['data engineering', 'devops'], 'domain': 'Data'},
        'dbt': {'keywords': ['dbt'], 'synonyms': [], 'related_skills': ['data engineering', 'sql'], 'domain': 'Data'},
        'etl': {'keywords': ['etl', 'extract transform load'], 'synonyms': [], 'related_skills': ['data engineering'], 'domain': 'Data'},
        'testing': {'keywords': ['testing', 'qa', 'test automation'], 'synonyms': [], 'related_skills': ['selenium'], 'domain': 'QA'},
        'selenium': {'keywords': ['selenium'], 'synonyms': [], 'related_skills': ['testing', 'automation'], 'domain': 'QA'},
        'jest': {'keywords': ['jest'], 'synonyms': [], 'related_skills': ['testing', 'javascript'], 'domain': 'QA'},
        'pytest': {'keywords': ['pytest'], 'synonyms': [], 'related_skills': ['testing', 'python'], 'domain': 'QA'},
        'ios': {'keywords': ['ios', 'iphone'], 'synonyms': [], 'related_skills': ['swift', 'mobile'], 'domain': 'Mobile'},
        'android': {'keywords': ['android'], 'synonyms': [], 'related_skills': ['kotlin', 'java', 'mobile'], 'domain': 'Mobile'},
        'react native': {'keywords': ['react native'], 'synonyms': [], 'related_skills': ['javascript', 'mobile'], 'domain': 'Mobile'},
        'flutter': {'keywords': ['flutter'], 'synonyms': [], 'related_skills': ['dart', 'mobile'], 'domain': 'Mobile'},
        'git': {'keywords': ['git'], 'synonyms': [], 'related_skills': ['devops', 'version control'], 'domain': 'Tools'},
        'next.js': {'keywords': ['next.js', 'next'], 'synonyms': [], 'related_skills': ['react', 'javascript'], 'domain': 'Frontend'},
        
        # ===== DATA ENGINEERING (Expanded) =====
        'snowflake': {'keywords': ['snowflake'], 'synonyms': [], 'related_skills': ['data engineering', 'sql', 'cloud'], 'domain': 'Data'},
        'bigquery': {'keywords': ['bigquery', 'big query'], 'synonyms': [], 'related_skills': ['data engineering', 'gcp', 'sql'], 'domain': 'Data'},
        'redshift': {'keywords': ['redshift'], 'synonyms': [], 'related_skills': ['data engineering', 'aws', 'sql'], 'domain': 'Data'},
        'delta lake': {'keywords': ['delta lake', 'delta'], 'synonyms': [], 'related_skills': ['spark', 'data engineering'], 'domain': 'Data'},
        'presto': {'keywords': ['presto'], 'synonyms': [], 'related_skills': ['sql', 'data engineering'], 'domain': 'Data'},
        'trino': {'keywords': ['trino'], 'synonyms': [], 'related_skills': ['presto', 'sql'], 'domain': 'Data'},
        
        # ===== AI/ML (Expanded) =====
        'jax': {'keywords': ['jax'], 'synonyms': [], 'related_skills': ['deep learning', 'python'], 'domain': 'AI/ML'},
        'xgboost': {'keywords': ['xgboost'], 'synonyms': [], 'related_skills': ['machine learning', 'python'], 'domain': 'AI/ML'},
        'lightgbm': {'keywords': ['lightgbm', 'light gbm'], 'synonyms': [], 'related_skills': ['machine learning', 'python'], 'domain': 'AI/ML'},
        'catboost': {'keywords': ['catboost'], 'synonyms': [], 'related_skills': ['machine learning', 'python'], 'domain': 'AI/ML'},
        'onnx': {'keywords': ['onnx'], 'synonyms': [], 'related_skills': ['machine learning', 'model deployment'], 'domain': 'AI/ML'},
        'mlflow': {'keywords': ['mlflow'], 'synonyms': [], 'related_skills': ['mlops', 'machine learning'], 'domain': 'AI/ML'},
        'kubeflow': {'keywords': ['kubeflow'], 'synonyms': [], 'related_skills': ['mlops', 'kubernetes', 'machine learning'], 'domain': 'AI/ML'},
        
        # ===== MOBILE (Expanded) =====
        'xcode': {'keywords': ['xcode'], 'synonyms': [], 'related_skills': ['ios', 'swift'], 'domain': 'Mobile'},
        'objective-c': {'keywords': ['objective-c', 'objc'], 'synonyms': [], 'related_skills': ['ios', 'macos'], 'domain': 'Mobile'},
        'dart': {'keywords': ['dart'], 'synonyms': [], 'related_skills': ['flutter', 'mobile'], 'domain': 'Mobile'},
        
        # ===== SECURITY (New) =====
        'encryption': {'keywords': ['encryption', 'cryptography'], 'synonyms': [], 'related_skills': ['security', 'ssl/tls'], 'domain': 'Security'},
        'ssl/tls': {'keywords': ['ssl', 'tls', 'https'], 'synonyms': [], 'related_skills': ['encryption', 'networking'], 'domain': 'Security'},
        'oauth': {'keywords': ['oauth'], 'synonyms': [], 'related_skills': ['authentication', 'security'], 'domain': 'Security'},
        'jwt': {'keywords': ['jwt', 'json web token'], 'synonyms': [], 'related_skills': ['authentication', 'security'], 'domain': 'Security'},
        'vault': {'keywords': ['vault', 'hashicorp vault'], 'synonyms': [], 'related_skills': ['secrets management', 'devops'], 'domain': 'Security'},
        'sonarqube': {'keywords': ['sonarqube', 'sonar'], 'synonyms': [], 'related_skills': ['code quality', 'devops'], 'domain': 'Security'},
        'snyk': {'keywords': ['snyk'], 'synonyms': [], 'related_skills': ['security scanning', 'devops'], 'domain': 'Security'},
        'trivy': {'keywords': ['trivy'], 'synonyms': [], 'related_skills': ['container security', 'devops'], 'domain': 'Security'},
        
        # ===== QA (Expanded) =====
        'cypress': {'keywords': ['cypress'], 'synonyms': [], 'related_skills': ['testing', 'javascript'], 'domain': 'QA'},
        'testng': {'keywords': ['testng'], 'synonyms': [], 'related_skills': ['testing', 'java'], 'domain': 'QA'},
        'junit': {'keywords': ['junit'], 'synonyms': [], 'related_skills': ['testing', 'java'], 'domain': 'QA'},
        'mocha': {'keywords': ['mocha'], 'synonyms': [], 'related_skills': ['testing', 'javascript'], 'domain': 'QA'},
        'cucumber': {'keywords': ['cucumber'], 'synonyms': [], 'related_skills': ['bdd', 'testing'], 'domain': 'QA'},
        'robotframework': {'keywords': ['robot framework', 'robotframework'], 'synonyms': [], 'related_skills': ['testing', 'automation'], 'domain': 'QA'},
        
        # ===== BLOCKCHAIN (New) =====
        'solidity': {'keywords': ['solidity'], 'synonyms': [], 'related_skills': ['ethereum', 'smart contracts'], 'domain': 'Blockchain'},
        'ethereum': {'keywords': ['ethereum', 'eth '], 'synonyms': [], 'related_skills': ['solidity', 'blockchain', 'web3'], 'domain': 'Blockchain'},
        'smart contracts': {'keywords': ['smart contracts', 'smart contract'], 'synonyms': [], 'related_skills': ['blockchain', 'solidity'], 'domain': 'Blockchain'},
        'web3': {'keywords': ['web3', 'web3.py', 'web3.js'], 'synonyms': [], 'related_skills': ['ethereum', 'blockchain'], 'domain': 'Blockchain'},
        'hardhat': {'keywords': ['hardhat'], 'synonyms': [], 'related_skills': ['solidity', 'ethereum'], 'domain': 'Blockchain'},
        'truffle': {'keywords': ['truffle'], 'synonyms': [], 'related_skills': ['solidity', 'ethereum'], 'domain': 'Blockchain'},
        'ethers.js': {'keywords': ['ethers.js', 'ethersjs'], 'synonyms': [], 'related_skills': ['ethereum', 'web3', 'javascript'], 'domain': 'Blockchain'},
        
        # ===== QUANTUM (New) =====
        'qiskit': {'keywords': ['qiskit'], 'synonyms': [], 'related_skills': ['quantum', 'python'], 'domain': 'Quantum'},
        'cirq': {'keywords': ['cirq'], 'synonyms': [], 'related_skills': ['quantum', 'python'], 'domain': 'Quantum'},
        'quantum algorithms': {'keywords': ['quantum algorithm'], 'synonyms': [], 'related_skills': ['quantum', 'algorithms'], 'domain': 'Quantum'},
        'quantum gates': {'keywords': ['quantum gate'], 'synonyms': [], 'related_skills': ['quantum', 'circuits'], 'domain': 'Quantum'},
        
        # ===== GAME DEVELOPMENT (New) =====
        'unity': {'keywords': ['unity', 'unity3d'], 'synonyms': [], 'related_skills': ['game development', 'c#'], 'domain': 'GameDev'},
        'unreal': {'keywords': ['unreal', 'unreal engine'], 'synonyms': [], 'related_skills': ['game development', 'c++'], 'domain': 'GameDev'},
        'godot': {'keywords': ['godot'], 'synonyms': [], 'related_skills': ['game development'], 'domain': 'GameDev'},
        'game physics': {'keywords': ['game physics', 'physics engine'], 'synonyms': [], 'related_skills': ['game development'], 'domain': 'GameDev'},
        
        # ===== ROBOTICS (New) =====
        'ros': {'keywords': ['ros', 'robotics operating system'], 'synonyms': [], 'related_skills': ['robotics', 'python', 'c++'], 'domain': 'Robotics'},
        'opencv': {'keywords': ['opencv'], 'synonyms': [], 'related_skills': ['computer vision', 'robotics'], 'domain': 'Robotics'},
        
        # ===== EMBEDDED (New) =====
        'embedded c': {'keywords': ['embedded c'], 'synonyms': [], 'related_skills': ['c', 'embedded systems'], 'domain': 'Embedded'},
        'assembly': {'keywords': ['assembly', 'asm '], 'synonyms': [], 'related_skills': ['embedded', 'microcontroller'], 'domain': 'Embedded'},
        'microcontroller': {'keywords': ['microcontroller'], 'synonyms': [], 'related_skills': ['embedded', 'assembly'], 'domain': 'Embedded'},
        'uart': {'keywords': ['uart'], 'synonyms': [], 'related_skills': ['embedded', 'communication'], 'domain': 'Embedded'},
        'gpio': {'keywords': ['gpio'], 'synonyms': [], 'related_skills': ['embedded', 'microcontroller'], 'domain': 'Embedded'},
        'stm32': {'keywords': ['stm32'], 'synonyms': [], 'related_skills': ['microcontroller', 'embedded'], 'domain': 'Embedded'},
        'arduino': {'keywords': ['arduino'], 'synonyms': [], 'related_skills': ['embedded', 'microcontroller'], 'domain': 'Embedded'},
        
        # ===== FIRMWARE (New) =====
        'verilog': {'keywords': ['verilog'], 'synonyms': [], 'related_skills': ['fpga', 'hdl'], 'domain': 'Firmware'},
        'systemverilog': {'keywords': ['systemverilog'], 'synonyms': [], 'related_skills': ['verilog', 'fpga'], 'domain': 'Firmware'},
        'vhdl': {'keywords': ['vhdl'], 'synonyms': [], 'related_skills': ['fpga', 'hdl'], 'domain': 'Firmware'},
        'fpga': {'keywords': ['fpga'], 'synonyms': [], 'related_skills': ['verilog', 'systemverilog'], 'domain': 'Firmware'},
        'vivado': {'keywords': ['vivado'], 'synonyms': [], 'related_skills': ['fpga', 'xilinx'], 'domain': 'Firmware'},
        'quartus': {'keywords': ['quartus'], 'synonyms': [], 'related_skills': ['fpga', 'altera'], 'domain': 'Firmware'},
        
        # ===== HARDWARE (New) =====
        'pcb design': {'keywords': ['pcb design', 'pcb'], 'synonyms': [], 'related_skills': ['circuit design', 'hardware'], 'domain': 'Hardware'},
        'circuit design': {'keywords': ['circuit design'], 'synonyms': [], 'related_skills': ['hardware', 'electronics'], 'domain': 'Hardware'},
        'eagle': {'keywords': ['eagle'], 'synonyms': [], 'related_skills': ['pcb design'], 'domain': 'Hardware'},
        'altium': {'keywords': ['altium'], 'synonyms': [], 'related_skills': ['pcb design'], 'domain': 'Hardware'},
        'kicad': {'keywords': ['kicad'], 'synonyms': [], 'related_skills': ['pcb design'], 'domain': 'Hardware'},
        
        # ===== AR/VR (New) =====
        'arkit': {'keywords': ['arkit'], 'synonyms': [], 'related_skills': ['ar/vr', 'ios'], 'domain': 'AR/VR'},
        'arcore': {'keywords': ['arcore'], 'synonyms': [], 'related_skills': ['ar/vr', 'android'], 'domain': 'AR/VR'},
        'opengl': {'keywords': ['opengl'], 'synonyms': [], 'related_skills': ['3d graphics', 'graphics'], 'domain': 'Graphics'},
        'vulkan': {'keywords': ['vulkan'], 'synonyms': [], 'related_skills': ['3d graphics', 'graphics'], 'domain': 'Graphics'},
        '3d graphics': {'keywords': ['3d graphics', '3d rendering'], 'synonyms': [], 'related_skills': ['graphics', 'ar/vr'], 'domain': 'Graphics'},
        
        # ===== IOT (New) =====
        'mqtt': {'keywords': ['mqtt'], 'synonyms': [], 'related_skills': ['iot', 'messaging'], 'domain': 'IoT'},
        'zigbee': {'keywords': ['zigbee'], 'synonyms': [], 'related_skills': ['iot', 'wireless'], 'domain': 'IoT'},
        'lora': {'keywords': ['lora'], 'synonyms': [], 'related_skills': ['iot', 'wireless'], 'domain': 'IoT'},
        'raspberry pi': {'keywords': ['raspberry pi'], 'synonyms': [], 'related_skills': ['iot', 'embedded'], 'domain': 'IoT'},
        
        # ===== FRONTEND (Expanded) =====
        'svelte': {'keywords': ['svelte'], 'synonyms': [], 'related_skills': ['javascript', 'frontend'], 'domain': 'Frontend'},
        'astro': {'keywords': ['astro'], 'synonyms': [], 'related_skills': ['javascript', 'frontend'], 'domain': 'Frontend'},
        'solid.js': {'keywords': ['solid.js', 'solidjs'], 'synonyms': [], 'related_skills': ['javascript', 'frontend'], 'domain': 'Frontend'},
        
        # ===== BACKEND (Expanded) =====
        'grpc': {'keywords': ['grpc'], 'synonyms': [], 'related_skills': ['api', 'backend', 'protobuf'], 'domain': 'API'},
        'protobuf': {'keywords': ['protobuf', 'protocol buffers'], 'synonyms': [], 'related_skills': ['grpc', 'serialization'], 'domain': 'API'},
        'nodejs': {'keywords': ['nodejs', 'node.js'], 'synonyms': [], 'related_skills': ['javascript', 'backend'], 'domain': 'Backend'},
        'coroutines': {'keywords': ['coroutines'], 'synonyms': [], 'related_skills': ['async', 'backend'], 'domain': 'Backend'},
        
        # ===== INFRASTRUCTURE (Expanded) =====
        'systemd': {'keywords': ['systemd'], 'synonyms': [], 'related_skills': ['linux', 'devops'], 'domain': 'Infrastructure'},
        'supervisord': {'keywords': ['supervisord'], 'synonyms': [], 'related_skills': ['process management', 'devops'], 'domain': 'Infrastructure'},
        'tcp/ip': {'keywords': ['tcp/ip', 'tcp', 'ip '], 'synonyms': [], 'related_skills': ['networking'], 'domain': 'Infrastructure'},
        'dns': {'keywords': ['dns'], 'synonyms': [], 'related_skills': ['networking'], 'domain': 'Infrastructure'},
        'bgp': {'keywords': ['bgp'], 'synonyms': [], 'related_skills': ['networking', 'routing'], 'domain': 'Infrastructure'},
        'ospf': {'keywords': ['ospf'], 'synonyms': [], 'related_skills': ['networking', 'routing'], 'domain': 'Infrastructure'},
        'mpls': {'keywords': ['mpls'], 'synonyms': [], 'related_skills': ['networking'], 'domain': 'Infrastructure'},
        
        # ===== MONITORING (Expanded) =====
        'observability': {'keywords': ['observability'], 'synonyms': [], 'related_skills': ['monitoring', 'devops'], 'domain': 'DevOps'},
        'newrelic': {'keywords': ['newrelic', 'new relic'], 'synonyms': [], 'related_skills': ['monitoring'], 'domain': 'DevOps'},
        'splunk': {'keywords': ['splunk'], 'synonyms': [], 'related_skills': ['logging', 'monitoring'], 'domain': 'DevOps'},
        
        # ===== ANALYTICS (New) =====
        'tableau': {'keywords': ['tableau'], 'synonyms': [], 'related_skills': ['analytics', 'data visualization'], 'domain': 'Analytics'},
        'looker': {'keywords': ['looker'], 'synonyms': [], 'related_skills': ['analytics', 'business intelligence'], 'domain': 'Analytics'},
        'power bi': {'keywords': ['power bi'], 'synonyms': [], 'related_skills': ['analytics', 'business intelligence'], 'domain': 'Analytics'},
        'qlik': {'keywords': ['qlik'], 'synonyms': [], 'related_skills': ['analytics', 'business intelligence'], 'domain': 'Analytics'},
        
        # ===== DATA VISUALIZATION (New) =====
        'matplotlib': {'keywords': ['matplotlib'], 'synonyms': [], 'related_skills': ['python', 'data science'], 'domain': 'Data'},
        'plotly': {'keywords': ['plotly'], 'synonyms': [], 'related_skills': ['data visualization', 'python'], 'domain': 'Data'},
        'd3.js': {'keywords': ['d3.js', 'd3'], 'synonyms': [], 'related_skills': ['javascript', 'data visualization'], 'domain': 'Frontend'},
        
        # ===== DATA PROCESSING (Expanded) =====
        'pandas': {'keywords': ['pandas'], 'synonyms': [], 'related_skills': ['python', 'data science'], 'domain': 'Data'},
        'numpy': {'keywords': ['numpy'], 'synonyms': [], 'related_skills': ['python', 'data science'], 'domain': 'Data'},
        'scipy': {'keywords': ['scipy'], 'synonyms': [], 'related_skills': ['python', 'data science'], 'domain': 'Data'},
    }


# ============================================================================
# v8.0: README SCANNING (FULLY PRESERVED)
# ============================================================================

def fetch_and_scan_readme(username, repo_name):
    try:
        url = f"https://api.github.com/repos/{username}/{repo_name}/readme"
        response = requests.get(url, headers=github_headers, timeout=5)
        
        if response.status_code == 200:
            readme_data = response.json()
            if 'content' in readme_data:
                import base64
                content = base64.b64decode(readme_data['content']).decode('utf-8', errors='ignore')
                return content.lower()
    except:
        pass
    
    return ""

# ============================================================================
# v9.0 FEATURE 1: RECENCY CHECK
# ============================================================================

def check_recency(last_activity_date_str):
    try:
        last_activity = datetime.fromisoformat(last_activity_date_str.replace('Z', '+00:00'))
        days_since = (datetime.now(timezone.utc) - last_activity).days
    except:
        return "⏸️ UNKNOWN", 999, "UNKNOWN", -5
    
    if days_since < 7:
        return "🔥 ACTIVE (last 7 days)", days_since, "VERY_ACTIVE", 15
    elif days_since < 30:
        return "🔥 ACTIVE (last 30 days)", days_since, "ACTIVE", 12
    elif days_since < 90:
        return "⭐ SEMI-ACTIVE (1-3 months)", days_since, "SEMI_ACTIVE", 5
    elif days_since < 180:
        return "📅 SEMI-DORMANT (3-6 months)", days_since, "SEMI_DORMANT", 0
    elif days_since < 365:
        return "⏸️ DORMANT (6-12 months)", days_since, "DORMANT", -5
    else:
        return "🔴 VERY DORMANT (12+ months)", days_since, "VERY_DORMANT", -10

# ============================================================================
# v9.0 FEATURE 2: RED FLAGS
# ============================================================================

def detect_red_flags(candidate, account_age_days):
    flags = []
    
    followers = candidate.get('followers', 0)
    repos = candidate.get('repos', 0)
    stars = candidate.get('stars', 0)
    days_since_activity = candidate.get('days_since_activity', 999)
    bio = candidate.get('bio', '')
    
    if account_age_days < 7 and followers > 100:
        flags.append("🚩 NEW ACCOUNT (< 7 days) with HIGH FOLLOWERS (>100) - likely auto-generated profile")
    
    if followers >= 1000 and repos == 0:
        flags.append("🚩 HIGH FOLLOWERS (1000+) but ZERO REPOS - probably Twitter influencer, not engineer")
    
    if days_since_activity >= 730:
        flags.append("🚩 NO ACTIVITY FOR 2+ YEARS - probably left tech or inactive")
    
    if candidate.get('rare_skill_count', 0) >= 7 and account_age_days < 180:
        flags.append("🚩 PERFECT PROFILE (all rare skills + new account) - verify authenticity")
    
    if days_since_activity > 365 and (not bio or bio == 'N/A'):
        flags.append("🚩 INACTIVE + NO BIO - low credibility profile")
    
    return flags

# ============================================================================
# v9.0 FEATURE 3: OPPORTUNITY SIGNALS
# ============================================================================

def detect_opportunity_signals(candidate, previous_last_activity=None):
    """Return factual public GitHub availability/activity signals only.
    These are context for a recruiter, not predictions of response likelihood or job-search intent.
    """
    signals = []
    days_since = candidate.get('days_since_activity', 999)
    bio = (candidate.get('bio') or '').lower()
    open_to_work = candidate.get('open_to_work_detected', False)

    if open_to_work:
        signals.append("🔓 Public bio contains an availability/opportunity keyword - recruiter verification recommended")
    if days_since < 30:
        signals.append("🟢 Public GitHub activity detected within the last 30 days")

    learning_keywords = ['learning', 'studying', 'exploring', 'diving into', 'new to']
    if any(kw in bio for kw in learning_keywords):
        signals.append("📚 Public bio mentions learning/exploring a technology")

    return signals

# ============================================================================
# v9.0 FEATURE 4: SPECIALIZATION LEVEL
# ============================================================================

def detect_specialization_level(tier1_skills, all_languages):
    """Describe only the breadth/depth of GitHub evidence detected for the target skills.
    Avoid inferring career level or professional identity from public GitHub alone.
    """
    domain_map = {
        'python': 'Backend', 'java': 'Backend', 'go': 'Backend/Infra', 'react': 'Frontend',
        'angular': 'Frontend', 'vue': 'Frontend', 'kubernetes': 'Infrastructure', 'docker': 'Infrastructure',
        'aws': 'Cloud', 'azure': 'Cloud', 'tensorflow': 'AI/ML', 'pytorch': 'AI/ML',
        'django': 'Backend', 'spring': 'Backend', 'spark': 'Data', 'airflow': 'Data',
    }
    domains = {domain_map.get(skill, 'Other') for skill in tier1_skills}
    depth_score = len(set(tier1_skills))
    breadth_score = len(domains)

    if depth_score >= 5 and breadth_score >= 3:
        label, desc = "BROAD + DEEP GITHUB EVIDENCE", "Target-skill evidence spans several technical domains"
    elif depth_score >= 5:
        label, desc = "DEEP GITHUB EVIDENCE", "Many target skills detected in a narrower domain set"
    elif depth_score >= 3 and breadth_score >= 3:
        label, desc = "BROAD GITHUB EVIDENCE", "Target-skill evidence spans multiple domains"
    elif depth_score >= 3:
        label, desc = "FOCUSED GITHUB EVIDENCE", "Several target skills detected in a focused domain set"
    else:
        label, desc = "LIMITED GITHUB EVIDENCE", "Not enough public GitHub evidence to infer breadth or depth"
    return label, depth_score, breadth_score, desc

# ============================================================================
# v9.0 FEATURE 5: COMMUNICATION SCORE
# ============================================================================

def score_communication_quality(bio, readme_scans, username):
    """Compatibility function: scores public profile/documentation completeness, NOT human communication ability."""
    score = 0
    signals = []
    bio_text = (bio or '').strip()
    readme_text = (readme_scans or '').strip()
    if bio_text:
        score += 3
        signals.append("Public bio present")
    if len(bio_text) >= 80:
        score += 2
        signals.append("Detailed public bio")
    if readme_text and readme_text != bio_text:
        score += 3
        signals.append("Repository documentation evidence available")
    if any(term in bio_text.lower() for term in ['blog', 'portfolio', 'article', 'book']):
        score += 1
        signals.append("Public writing/portfolio reference")
    score = min(10, score)
    return score, signals, f"Public profile/documentation signal: {score}/10 (not a communication assessment)"

# ============================================================================
# v9.0 FEATURE 6: UNICORN DETECTION
# ============================================================================

def detect_unicorn_profile(tier1_matches, core_skills_required, account_age_days):
    if not core_skills_required:
        return False, 0, "No skills to match against"
    
    match_ratio = len(tier1_matches) / len(core_skills_required)
    
    rare_skill_combos = {
        'kubernetes': True, 'terraform': True, 'llm': True, 'mlops': True,
        'gcp': True, 'aks': True, 'eks': True,
    }
    
    rare_matches = sum(1 for match in tier1_matches if any(rare in match.lower() for rare in rare_skill_combos.keys()))
    rarity_multiplier = 1 + (rare_matches * 0.15)
    
    rarity_score = min(100, int(match_ratio * 100 * rarity_multiplier))
    
    is_unicorn = match_ratio >= 0.9 and len(tier1_matches) >= 5
    
    if is_unicorn:
        explanation = f"🦄 UNICORN PROFILE - Matches {match_ratio*100:.0f}% of rare skills ({len(tier1_matches)}/{len(core_skills_required)}). Verify authenticity or bid aggressively!"
    elif match_ratio >= 0.8:
        explanation = f"⭐ HIGH MATCH - Covers {match_ratio*100:.0f}% of required skills. Strong candidate."
    elif match_ratio >= 0.6:
        explanation = f"✅ GOOD MATCH - Covers {match_ratio*100:.0f}% of required skills. Worth reaching out."
    else:
        explanation = f"📊 PARTIAL MATCH - Covers {match_ratio*100:.0f}% of required skills."
    
    return is_unicorn, rarity_score, explanation

# ============================================================================
# v8.0: JD PARSING (FULLY PRESERVED)
# ============================================================================

def extract_jd_sections(jd_text):
    """IMPROVED: Smart section extraction - handles ANY case/format"""
    jd_lower = jd_text.lower()
    
    must_have_section = ""
    nice_to_have_section = ""
    
    # Pattern 1: Find "MUST HAVE:" or "Required:" section (case-insensitive)
    must_match = re.search(
        r'(?:must\s+have|required\s+skills?|requirements?)\s*:?\s*(.+?)(?=(?:nice|preferred|bonus|what\s|qualifications|technical|$))',
        jd_lower,
        re.IGNORECASE | re.DOTALL
    )
    
    if must_match:
        must_have_section = must_match.group(1).strip()
    
    # Pattern 2: Find "NICE TO HAVE:" or "Preferred:" section (case-insensitive)
    nice_match = re.search(
        r'(?:nice\s+to\s+have|preferred|bonus\s+skills?)\s*:?\s*(.+?)(?=(?:must|required|technical|what|responsibilities|$))',
        jd_lower,
        re.IGNORECASE | re.DOTALL
    )
    
    if nice_match:
        nice_to_have_section = nice_match.group(1).strip()
    
    # If we found sections, clean them up (remove bullets, dashes, etc.)
    if must_have_section:
        must_have_section = re.sub(r'[\n\r•-]\s*', ' ', must_have_section)
        must_have_section = ' '.join(must_have_section.split())
    
    if nice_to_have_section:
        nice_to_have_section = re.sub(r'[\n\r•-]\s*', ' ', nice_to_have_section)
        nice_to_have_section = ' '.join(nice_to_have_section.split())
    
    return {
        'must_have': must_have_section,
        'nice_to_have': nice_to_have_section,
        'full_text': jd_lower
    }

def get_role_skill_relevance_map():
    """Maps roles to CORE, SUPPORTING, and IRRELEVANT skills"""
    return {
        'ML_ENGINEER': {
            'CORE': ['python', 'pytorch', 'tensorflow', 'keras', 'jax', 'deep learning', 'neural networks', 
                     'scikit-learn', 'xgboost', 'machine learning', 'nlp', 'llm', 'transformers', 
                     'numpy', 'pandas', 'data science', 'cnn', 'rnn'],
            'SUPPORTING': ['docker', 'kubernetes', 'aws', 'gcp', 'azure', 'git', 'mlops', 'airflow', 'mlflow', 'sql'],
            'IRRELEVANT': ['react', 'angular', 'vue', 'html', 'css', 'javascript', 'swift', 'android'],
        },
        'DATA_ENGINEER': {
            'CORE': ['python', 'sql', 'spark', 'kafka', 'airflow', 'etl', 'hadoop', 'dbt', 'bigquery', 'snowflake'],
            'SUPPORTING': ['docker', 'kubernetes', 'aws', 'gcp', 'git', 'scala', 'java'],
            'IRRELEVANT': ['react', 'swift', 'ios', 'pytorch', 'tensorflow'],
        },
        'FRONTEND_ENGINEER': {
            'CORE': ['react', 'angular', 'vue', 'html', 'css', 'javascript', 'typescript', 'webpack'],
            'SUPPORTING': ['git', 'docker', 'nodejs', 'npm', 'jest', 'cypress', 'graphql'],
            'IRRELEVANT': ['kubernetes', 'spark', 'tensorflow', 'python backend', 'java backend'],
        },
        'BACKEND_ENGINEER': {
            'CORE': ['python', 'java', 'go', 'nodejs', 'django', 'flask', 'spring', 'express', 'sql'],
            'SUPPORTING': ['docker', 'kubernetes', 'aws', 'git', 'microservices', 'graphql'],
            'IRRELEVANT': ['react', 'angular', 'swift', 'ios', 'html', 'css'],
        },
        'DEVOPS_ENGINEER': {
            'CORE': ['kubernetes', 'docker', 'terraform', 'ansible', 'aws', 'gcp', 'azure', 'ci/cd', 'jenkins'],
            'SUPPORTING': ['python', 'bash', 'git', 'networking', 'linux', 'monitoring'],
            'IRRELEVANT': ['react', 'typescript', 'pytorch', 'swift', 'ios'],
        },
    }

def infer_role_from_skills_dynamically(explicitly_mentioned_skills, skills_db):
    """
    TRULY UNIVERSAL: Infer role from the SKILLS MENTIONED, not hardcoded role lists.
    
    Algorithm:
    1. Extract domains of all mentioned skills
    2. Whichever domain dominates = primary role
    3. Group all other skills relative to that domain
    
    This works for ANY role (ML, Quantum, Blockchain, Robotics, etc.)
    because it's based on the skills themselves, not hardcoded lists.
    """
    
    if not explicitly_mentioned_skills:
        return None, {}
    
    # Step 1: Count domain frequency
    domain_counts = {}
    skill_domains = {}
    
    for skill_name in explicitly_mentioned_skills:
        skill_info = skills_db.get(skill_name, {})
        domain = skill_info.get('domain', 'Other')
        
        skill_domains[skill_name] = domain
        domain_counts[domain] = domain_counts.get(domain, 0) + 1
    
    # Step 2: Find primary domain
    if not domain_counts:
        return None, skill_domains
    
    primary_domain = max(domain_counts.items(), key=lambda x: x[1])[0]
    
    # Step 3: Build relevance map based on primary domain
    # Skills from primary domain = CORE
    # Related skills (from same family) = SUPPORTING
    # Everything else = OTHER
    relevance_map = {}
    
    for skill_name in explicitly_mentioned_skills:
        domain = skill_domains.get(skill_name, 'Other')
        
        if domain == primary_domain:
            relevance_map[skill_name] = 'CORE'
        else:
            # Check if this skill relates to any CORE skill
            skill_info = skills_db.get(skill_name, {})
            related_skills = skill_info.get('related_skills', [])
            
            # Check if any CORE skill is in this skill's relationships
            has_core_relation = any(
                s in explicitly_mentioned_skills and 
                skill_domains.get(s) == primary_domain 
                for s in related_skills
            )
            
            if has_core_relation:
                relevance_map[skill_name] = 'SUPPORTING'
            else:
                relevance_map[skill_name] = 'OTHER'
    
    return primary_domain, relevance_map

def get_skill_relevance(skill_name, role_domain):
    """Fallback: if no dynamic role detected, default to SUPPORTING"""
    return 'SUPPORTING'

def detect_role_domain(jd_text):
    """DEPRECATED - kept for backward compatibility only"""
    return None

def group_skills_semantically(skills_list, skills_db):
    """Group related skills together intelligently"""
    groups = {
        'ML Frameworks': ['pytorch', 'tensorflow', 'keras', 'jax', 'scikit-learn', 'xgboost'],
        'Deep Learning': ['deep learning', 'neural networks', 'cnn', 'rnn', 'transformers', 'bert'],
        'Data Processing': ['numpy', 'pandas', 'scipy', 'matplotlib', 'seaborn'],
        'Infrastructure': ['docker', 'kubernetes', 'terraform', 'ansible'],
        'Cloud Platforms': ['aws', 'gcp', 'azure'],
        'Languages': ['python', 'java', 'go', 'javascript', 'typescript'],
    }
    
    skill_to_group = {}
    for group, skills in groups.items():
        for skill in skills:
            skill_to_group[skill] = group
    
    grouped = {}
    for skill in skills_list:
        group = skill_to_group.get(skill, 'Other')
        if group not in grouped:
            grouped[group] = []
        grouped[group].append(skill)
    
    return grouped

def extract_explicitly_mentioned_skills(text, skills_db):
    """
    Extract skills DIRECTLY MENTIONED - handles both known and unknown skills.
    
    UNIVERSAL: Works with skills not in database by treating them as valid mentions.
    """
    text_lower = text.lower()
    mentioned_skills = []
    unknown_skills = set()  # Use set to avoid duplicates
    
    # Step 1: Match skills in database
    for skill_name, skill_info in skills_db.items():
        keywords = skill_info.get('keywords', [])
        
        for keyword in keywords:
            if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower):
                mentioned_skills.append(skill_name)
                break
    
    # Step 2: Try to catch unknown skills by looking for capitalized tech terms
    # Only consider words that LOOK like tech names, not generic English words
    words = text.split()
    known_keywords = set()
    for skill_name, skill_info in skills_db.items():
        keywords = skill_info.get('keywords', [])
        known_keywords.update([k.lower() for k in keywords])
    
    # Common English words that aren't tech skills
    exclude_words = {
        'senior', 'junior', 'engineer', 'developer', 'architect', 'lead', 'must', 'have', 
        'nice', 'to', 'with', 'and', 'or', 'position', 'requirement', 'engineer', 'years',
        'experience', 'skills', 'required', 'preferred', 'bonus', 'location', 'full',
        'responsibilities', 'qualifications', 'technical', 'experience', 'years',
        'new', 'the', 'our', 'your', 'for', 'is', 'be', 'an', 'a', 'be', 'by', 'in',
    }
    
    for word in words:
        # Remove trailing punctuation
        clean_word = word.rstrip('.,;:!?-()[]{}')
        
        # Check if word looks like a tech term
        if (len(clean_word) >= 3 and  # At least 3 chars
            clean_word[0].isupper() and  # Starts with capital
            clean_word.lower() not in known_keywords and  # Not already known
            clean_word.lower() not in exclude_words and  # Not a common word
            not clean_word.endswith(':') and  # Not a section header
            '/' not in clean_word):  # Not a path
            unknown_skills.add(clean_word)
    
    # Combine: known skills + unknown skills (unknown skills treated as valid)
    return mentioned_skills + sorted(list(unknown_skills))

def infer_skill_criticality(skill_name, skill_info, jd_sections, jd_lower, skills_db):
    """SMART: Context-aware skill criticality with semantic understanding"""
    keywords = skill_info.get('keywords', [])
    synonyms = skill_info.get('synonyms', [])
    all_terms = keywords + synonyms
    
    must_have = jd_sections.get('must_have', '').strip()
    nice_to_have = jd_sections.get('nice_to_have', '').strip()
    full_text = jd_sections.get('full_text', '')
    
    # RULE 1: If explicit sections exist, ONLY use them
    has_explicit_sections = bool(must_have or nice_to_have)
    
    if has_explicit_sections:
        # RULE 1: Check MUST HAVE section - EXACT SUBSTRING ONLY (NO fuzzy matching!)
        # Fuzzy matching can cause false positives (e.g., 'aws' matching 'apis')
        if must_have:
            for term in all_terms:
                # Use EXACT substring matching, case-insensitive
                if term.lower() in must_have:
                    return 'MUST_HAVE', 0.95
        
        # RULE 2: Check NICE TO HAVE section - EXACT SUBSTRING ONLY (NO fuzzy matching!)
        if nice_to_have:
            for term in all_terms:
                # Use EXACT substring matching, case-insensitive
                if term.lower() in nice_to_have:
                    return 'NICE_TO_HAVE', 0.90
        
        # RULE 3: Not found in any explicit section - return BONUS (don't infer from related skills)
        # This respects user's explicit categorization ABSOLUTELY
        return 'BONUS', 0.0
    
    # RULE 2: No explicit sections? Use context patterns (but be smart)
    tier1_patterns = [
        r'must\s+have.*?{term}',
        r'required.*?{term}',
        r'{term}.*?non-negotiable',
        r'strong.*?{term}',
        r'expert.*?{term}',
        r'{term}.*?essential',
        r'{term}.*?mandatory',
        r'core\s+skill.*?{term}',
        r'hands-on.*?{term}',
        r'{term}.*?\d+\+\s*years',
        r'\d+\+\s*years.*?{term}',
    ]
    
    tier2_patterns = [
        r'preferred.*?{term}',
        r'nice\s+to\s+have.*?{term}',
        r'exposure\s+to.*?{term}',
        r'familiarity\s+with.*?{term}',
        r'would\s+be\s+nice.*?{term}',
        r'{term}.*?beneficial',
        r'{term}.*?plus',
        r'{term}.*?bonus',
    ]
    
    # Check TIER 1 patterns
    for term in all_terms:
        for pattern_template in tier1_patterns:
            pattern = pattern_template.format(term=term)
            if re.search(pattern, full_text, re.IGNORECASE):
                return 'MUST_HAVE', 0.85
    
    # Check TIER 2 patterns
    for term in all_terms:
        for pattern_template in tier2_patterns:
            pattern = pattern_template.format(term=term)
            if re.search(pattern, full_text, re.IGNORECASE):
                return 'NICE_TO_HAVE', 0.75
    
    # Check for mentions with context
    for term in all_terms:
        if fuzzy_match(term, full_text, max_distance=2):
            return 'MUST_HAVE', 0.70
    
    # Semantic fallback: if related skills are explicitly mentioned, include this skill
    related_skills = skill_info.get('related_skills', [])
    for related in related_skills:
        if fuzzy_match(related, full_text, max_distance=2):
            return 'NICE_TO_HAVE', 0.60  # Lower confidence for semantic inference
    
    return 'BONUS', 0.0

def detect_role_type(jd_text):
    """NEW v9.2: Universal role detection - works with ANY role on the planet"""
    jd_lower = jd_text.lower()
    
    # Extract likely job title from first 3 lines
    first_lines = ' '.join(jd_lower.split('\n')[:3])
    
    # Try to extract role title directly (most reliable)
    # Common patterns: "Software Engineer", "Senior Backend", "Lead Platform Engineer", etc.
    role_title_patterns = [
        r'^(.*?engineer)(?:\s|$)',  # Any "... engineer"
        r'^(.*?architect)(?:\s|$)',  # Any "... architect"
        r'^(.*?manager)(?:\s|$)',  # Any "... manager"
        r'^(.*?lead)(?:\s|$)',  # Any "... lead"
        r'^(.*?specialist)(?:\s|$)',  # Any "... specialist"
        r'^(.*?developer)(?:\s|$)',  # Any "... developer"
        r'^(.*?scientist)(?:\s|$)',  # Any "... scientist"
        r'^(.*?administrator)(?:\s|$)',  # Any "... administrator"
    ]
    
    inferred_title = None
    for pattern in role_title_patterns:
        match = re.search(pattern, first_lines, re.IGNORECASE)
        if match:
            inferred_title = match.group(1).strip()
            break
    
    # If no title found, try to extract from common position formats
    if not inferred_title:
        # Look for patterns like "Senior Software Engineer" or "Principal Architect"
        title_match = re.search(r'((?:senior|junior|lead|principal|staff|staff-level|director|head)?\s*\w+\s+(?:engineer|architect|manager|developer|scientist|specialist|administrator|officer))', first_lines, re.IGNORECASE)
        if title_match:
            inferred_title = title_match.group(1).strip()
    
    # Fallback: if still no title, use first 100 chars
    if not inferred_title:
        inferred_title = first_lines.split('\n')[0][:80].strip()
    
    # Now map to category for ranking purposes (but keep original title for display)
    category_mapping = {
        'ML_ENGINEER': ['machine learning', 'ml engineer', 'deep learning', 'nlp', 'llm', 'ai engineer', 'ai platform', 'data scientist'],
        'BACKEND_ENGINEER': ['backend', 'backend engineer', 'server-side', 'api', 'microservices', 'platform engineer'],
        'FRONTEND_ENGINEER': ['frontend', 'frontend engineer', 'ui developer', 'react developer', 'angular developer'],
        'DEVOPS_ENGINEER': ['devops', 'infrastructure', 'kubernetes', 'cloud engineer', 'sre', 'site reliability', 'platform architect'],
        'DATA_ENGINEER': ['data engineer', 'data pipeline', 'etl', 'data infrastructure'],
        'SECURITY_ENGINEER': ['security engineer', 'security architect', 'appsec'],
        'QA_ENGINEER': ['qa engineer', 'quality assurance', 'test automation'],
    }
    
    detected_category = 'GENERAL_ENGINEER'
    confidence = 50
    
    for category, keywords in category_mapping.items():
        matches = sum(1 for kw in keywords if kw in jd_lower)
        if matches > 0:
            detected_category = category
            confidence = min(90, 60 + (matches * 10))
            break
    
    # Return both the inferred title (for display) and category (for ranking)
    return inferred_title, detected_category, confidence

def deconstruct_jd_intelligent(jd_text):
    jd_text = re.sub(r'<[^>]+>', '', jd_text)
    jd_text = unescape(jd_text)
    jd_text = ' '.join(jd_text.split())
    jd_lower = jd_text.lower()
    jd_sections = extract_jd_sections(jd_text)
    
    skills_db = get_skills_database()
    
    # SMART 1: Extract ALL skills - known AND unknown
    explicitly_mentioned = extract_explicitly_mentioned_skills(jd_text, skills_db)
    
    # SMART 2: Separate known and unknown skills
    known_skills = [s for s in explicitly_mentioned if s in skills_db]
    unknown_skills = [s for s in explicitly_mentioned if s not in skills_db]
    
    # SMART 3: Infer role DYNAMICALLY from known skills
    primary_domain, dynamic_relevance_map = infer_role_from_skills_dynamically(known_skills, skills_db)
    
    # SMART 4: Categorize skills using both explicit sections AND dynamic relevance
    core_skills = []
    nice_to_have = []
    
    # Process known skills
    for skill_name in known_skills:
        skill_info = skills_db.get(skill_name, {})
        
        # PRIMARY (CRITICAL): Check explicit MUST/NICE sections - ALWAYS respect these!
        section_criticality, section_conf = infer_skill_criticality(skill_name, skill_info, jd_sections, jd_lower, skills_db)
        
        # SECONDARY: Use dynamic role inference ONLY if skill was NOT explicitly mentioned in sections
        # (i.e., found in job description but not in MUST HAVE or NICE TO HAVE sections)
        if section_criticality == 'BONUS':
            # Skill is mentioned but not in explicit sections - use dynamic inference
            dynamic_relevance = dynamic_relevance_map.get(skill_name, 'SUPPORTING')
            
            if dynamic_relevance == 'CORE':
                section_criticality = 'MUST_HAVE'
                section_conf = 0.85
            elif dynamic_relevance == 'SUPPORTING':
                section_criticality = 'NICE_TO_HAVE'
                section_conf = 0.75
        
        # NEVER override explicit sections - RULE: Explicit > Dynamic
        if section_criticality == 'MUST_HAVE':
            core_skills.append({'skill': skill_name, 'confidence': section_conf})
        elif section_criticality == 'NICE_TO_HAVE':
            nice_to_have.append({'skill': skill_name, 'confidence': section_conf})
    
    # Process unknown skills - still treat them intelligently
    must_have_lower = jd_sections.get('must_have', '').lower()
    nice_to_have_lower = jd_sections.get('nice_to_have', '').lower()
    
    for unknown_skill in unknown_skills:
        unknown_lower = unknown_skill.lower()
        
        # Check if unknown skill appears in MUST HAVE section
        if must_have_lower and unknown_lower in must_have_lower:
            core_skills.append({'skill': unknown_skill, 'confidence': 0.90})
        # Check if unknown skill appears in NICE TO HAVE section  
        elif nice_to_have_lower and unknown_lower in nice_to_have_lower:
            nice_to_have.append({'skill': unknown_skill, 'confidence': 0.80})
        # Otherwise treat as supporting (probably mentioned but not explicitly required)
        else:
            nice_to_have.append({'skill': unknown_skill, 'confidence': 0.70})
    
    seniority_level = 'MID'
    seniority_conf = 0
    
    if re.search(r'principal|staff|lead', jd_lower):
        seniority_level = 'SENIOR'
        seniority_conf = 90
    elif re.search(r'senior|8\+|10\+|expert', jd_lower):
        seniority_level = 'SENIOR'
        seniority_conf = 85
    elif re.search(r'junior|entry|0-3|entry-level', jd_lower):
        seniority_level = 'JUNIOR'
        seniority_conf = 85
    
    years = None
    years_match = re.search(r'(\d+)\+?\s*(?:years?|yrs?)', jd_lower)
    if years_match:
        years = int(years_match.group(1))
    
    remote_status = 'UNKNOWN'
    if re.search(r'remote|distributed|anywhere|work from home', jd_lower):
        remote_status = 'FULLY_REMOTE'
    elif re.search(r'hybrid', jd_lower):
        remote_status = 'HYBRID'
    elif re.search(r'on-site|on site|onsite', jd_lower):
        remote_status = 'ON_SITE'
    
    role_title, role_category, role_conf = detect_role_type(jd_text)
    
    # Determine specialization based on primary domain (smarter than regex)
    specialization = 'General'
    if primary_domain:
        # Map domain to specialization name
        domain_to_spec = {
            'Language': 'General',
            'Frontend': 'Frontend',
            'Backend': 'Backend',
            'Database': 'Data',
            'Infrastructure': 'Infrastructure',
            'AI/ML': 'AI/ML',
            'Cloud': 'Cloud',
            'Mobile': 'Mobile',
        }
        specialization = domain_to_spec.get(primary_domain, 'General')
    else:
        # Fallback to text-based detection if no primary domain detected
        if 'machine learning' in jd_lower or 'ai' in jd_lower or 'pytorch' in jd_lower or 'tensorflow' in jd_lower:
            specialization = 'AI/ML'
        elif 'data' in jd_lower:
            specialization = 'Data'
        elif 'devops' in jd_lower or 'infrastructure' in jd_lower or 'kubernetes' in jd_lower:
            specialization = 'Infrastructure'
        elif 'frontend' in jd_lower:
            specialization = 'Frontend'
        elif 'backend' in jd_lower:
            specialization = 'Backend'
    
    return {
        'core_skills': core_skills,
        'nice_to_have': nice_to_have,
        'seniority_level': seniority_level,
        'seniority_confidence': seniority_conf,
        'years': years,
        'remote_status': remote_status,
        'role_type': role_category,  # Category for ranking
        'role_title': role_title,  # Actual inferred title
        'role_confidence': role_conf,
        'specialization': specialization,
        'jd_sections': jd_sections,
        'primary_domain': primary_domain,  # Inferred from skills domains
        'dynamic_relevance_map': dynamic_relevance_map  # Skills categorized by relevance
    }

# ============================================================================
# v8.0: GITHUB PROFILE ANALYSIS (FULLY PRESERVED)
# ============================================================================

def analyze_github_profile_intelligent(username):
    try:
        response = requests.get(f"https://api.github.com/users/{username}", headers=github_headers, timeout=5)
        user_data = response.json()
        
        if isinstance(user_data, dict) and 'message' in user_data:
            return None
        
        bio = (user_data.get('bio') or '').lower()
        name = (user_data.get('name') or '').lower()
        company = (user_data.get('company') or '').lower()
        location = user_data.get('location') or ''
        followers = user_data.get('followers', 0)
        public_repos = user_data.get('public_repos', 0)
        created_at = user_data.get('created_at') or ''
        
        try:
            created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            account_age_days = (datetime.now(timezone.utc) - created_date).days
        except:
            account_age_days = 999
        
        profile_text = f"{bio} {name} {company}"
        
        open_to_work, signal = detect_open_to_work(bio)
        
        top_languages = {}
        all_languages = {}
        last_activity_date = None
        
        try:
            repos_resp = requests.get(f"https://api.github.com/users/{username}/repos", 
                                     headers=github_headers, 
                                     params={"per_page": 50, "sort": "stars", "direction": "desc"}, 
                                     timeout=5)
            repos = repos_resp.json() if isinstance(repos_resp.json(), list) else []
            repos = sorted(repos, key=lambda r: r.get('stargazers_count', 0), reverse=True)
            
            if repos:
                last_activity_date = repos[0].get('updated_at')
            
            top_repo_text = ""
            
            # SMARTER: Only analyze top 5 repos by stars (avoid noise from random projects)
            for repo in repos[:5]:
                stars = repo.get('stargazers_count', 0)
                repo_name = (repo.get('name') or '').lower()
                repo_desc = (repo.get('description') or '').lower()
                repo_lang = (repo.get('language') or '').lower()
                
                # SMARTER: Only count languages from repos with 100+ stars (main projects)
                if stars > 100 and repo_lang:
                    top_languages[repo_lang] = top_languages.get(repo_lang, 0) + 1
                    all_languages[repo_lang] = all_languages.get(repo_lang, 0) + 1
                
                if stars > 100:
                    top_repo_text += f" {repo_name} {repo_desc} {repo_lang}"
                    readme_content = fetch_and_scan_readme(username, repo.get('name', ''))
                    if readme_content:
                        top_repo_text += f" {readme_content[:500]}"
            
            profile_text += f" {top_repo_text}"
        except:
            pass
        
        skills_db = get_skills_database()
        tier1_skills = []
        tier2_skills = []
        
        language_skills = ['python', 'java', 'go', 'rust', 'javascript', 'typescript', 'c++', 'c#', 'sql', 'bash', 'swift', 'kotlin', 'ruby', 'php']
        for lang_skill in language_skills:
            skill_info = skills_db.get(lang_skill, {})
            keywords = skill_info.get('keywords', [])
            for kw in keywords:
                if kw in top_languages or kw in all_languages:
                    tier1_skills.append(lang_skill)
                    break
        
        framework_skills = ['react', 'angular', 'vue', 'spring', 'django', 'flask', 'express', 'rails', 'fastapi', 'docker', 'kubernetes', 'aws', 'azure', 'tensorflow', 'pytorch']
        
        # SMARTER: Only include frameworks relevant to detected languages
        # E.g., if JavaScript/TypeScript is primary, prioritize JS frameworks (React, Angular, Vue, Express)
        # Don't add infrastructure skills (AWS, Kubernetes) unless they're explicitly in the profile
        for framework_skill in framework_skills:
            skill_info = skills_db.get(framework_skill, {})
            keywords = skill_info.get('keywords', [])
            keywords.append(framework_skill)
            
            # Check if mentioned in profile text (from top repos only)
            mentioned = any(kw in profile_text for kw in keywords)
            
            if mentioned:
                # FILTER: Avoid including random infrastructure tools
                # Only include if: it's a frontend framework, or explicitly in top repo text
                if framework_skill in ['react', 'angular', 'vue', 'express', 'django', 'flask', 'spring', 'rails', 'fastapi']:
                    tier1_skills.append(framework_skill)
                elif framework_skill in ['docker', 'kubernetes', 'aws', 'azure', 'tensorflow', 'pytorch']:
                    # Only add infra skills if explicitly mentioned in READMEs/descriptions
                    if any(kw in top_repo_text for kw in keywords):
                        tier1_skills.append(framework_skill)

        
        bio_skills = ['machine learning', 'devops', 'cloud', 'frontend', 'backend', 'data science', 'ai', 'nlp', 'llm', 'architecture']
        for bio_skill in bio_skills:
            skill_info = skills_db.get(bio_skill, {})
            keywords = skill_info.get('keywords', [])
            for kw in keywords:
                if fuzzy_match(kw, bio, max_distance=2):
                    tier2_skills.append(bio_skill)
                    break
        
        if any(s in tier1_skills for s in ['react', 'angular', 'vue', 'javascript', 'typescript']):
            for skill in ['html', 'css', 'webpack', 'next.js']:
                if skill in skills_db:
                    tier2_skills.append(skill)
        
        if any(s in tier1_skills for s in ['python', 'tensorflow', 'pytorch']):
            for skill in ['numpy', 'pandas', 'scikit-learn', 'deep learning']:
                if skill in skills_db:
                    tier2_skills.append(skill)
        
        if any(s in tier1_skills for s in ['kubernetes', 'docker', 'go', 'devops']):
            for skill in ['terraform', 'ansible', 'linux', 'ci/cd']:
                if skill in skills_db:
                    tier2_skills.append(skill)
        
        role_type = 'GENERAL_ENGINEER'
        role_score = {}
        
        role_indicators = {
            'FRONTEND_ENGINEER': ['react', 'angular', 'vue', 'javascript', 'typescript', 'html', 'css', 'webpack'],
            'BACKEND_ENGINEER': ['spring', 'django', 'flask', 'fastapi', 'express', 'java', 'python', 'sql'],
            'DEVOPS_ENGINEER': ['kubernetes', 'docker', 'terraform', 'linux', 'devops', 'ci/cd', 'aws'],
            'ML_ENGINEER': ['pytorch', 'tensorflow', 'machine learning', 'python', 'data science', 'nlp'],
            'DATA_ENGINEER': ['spark', 'airflow', 'dbt', 'python', 'sql', 'kafka'],
            'FULL_STACK': ['react', 'django', 'python', 'javascript', 'sql', 'docker'],
        }
        
        all_detected_skills = tier1_skills + tier2_skills
        for role, indicators in role_indicators.items():
            matches = sum(1 for ind in indicators if ind in all_detected_skills)
            if matches > 0:
                role_score[role] = matches
        
        if role_score:
            role_type = max(role_score, key=role_score.get)
        
        stars = sum(repo.get('stargazers_count', 0) for repo in repos[:30] if isinstance(repo, dict))
        
        if followers >= 1000 and stars >= 1000:
            seniority = 'SENIOR'
            seniority_conf = 95
        elif followers >= 1000 or stars >= 1000:
            seniority = 'SENIOR'
            seniority_conf = 85
        elif followers >= 500 or stars >= 500:
            seniority = 'MID'
            seniority_conf = 80
        elif followers >= 100 or stars >= 100:
            seniority = 'MID'
            seniority_conf = 70
        elif followers >= 50 or public_repos >= 20:
            seniority = 'MID'
            seniority_conf = 60
        else:
            seniority = 'JUNIOR'
            seniority_conf = 65
        
        return {
            'username': username,
            'tier1_skills': list(set(tier1_skills)),
            'tier2_skills': list(set(tier2_skills)),
            'role_type': role_type,
            'seniority': seniority,
            'seniority_conf': seniority_conf,
            'followers': followers,
            'public_repos': public_repos,
            'bio': user_data.get('bio', '') or 'N/A',
            'location': location or 'Not specified',
            'profile_text': profile_text,
            'top_languages': top_languages,
            'all_languages': all_languages,
            'total_stars': stars,
            'open_to_work': open_to_work,
            'open_to_work_signal': signal,
            'last_activity_date': last_activity_date,
            'account_age_days': account_age_days,
        }
    
    except:
        return None

# ============================================================================
# v8.0: GITHUB SEARCH (FULLY PRESERVED)
# ============================================================================

def calculate_evidence_confidence(bio_keywords_found, repo_keywords_found, evidence_sources, total_keywords):
    """
    Calculate confidence score (HIGH/MEDIUM/LOW) based on evidence quality.
    
    HIGH: Found in both BIO + REPOSITORY, or multiple keyword matches
    MEDIUM: Found in one source with multiple keywords
    LOW: Found in one source with single keyword
    """
    total_found = len(bio_keywords_found) + len(repo_keywords_found)
    
    # Both sources = HIGH
    if 'BIO' in evidence_sources and 'REPOSITORY' in evidence_sources:
        return 'HIGH', '(appears in BIO + REPOSITORY code)'
    
    # Multiple keyword matches = HIGH
    if total_found >= 3:
        return 'HIGH', f'(found {total_found} keyword variants)'
    
    # Single source with 2+ keywords = MEDIUM
    if total_found >= 2:
        return 'MEDIUM', f'(found {total_found} keyword variants)'
    
    # Single source, single keyword = MEDIUM (still solid)
    if total_found == 1:
        return 'MEDIUM', '(found in public evidence)'
    
    return 'LOW', '(limited evidence)'

def _enrich_github_user(username, discovery_source=None, discovery_evidence=None):
    """Fetch a public user plus repository evidence used for transparent matching."""
    try:
        user_resp = requests.get(f"https://api.github.com/users/{username}", headers=github_headers, timeout=7)
        user_data = user_resp.json()
        if not isinstance(user_data, dict) or 'message' in user_data or user_data.get('type') != 'User':
            return None

        repos = []
        try:
            repos_resp = requests.get(
                f"https://api.github.com/users/{username}/repos",
                headers=github_headers,
                params={"per_page": 100, "sort": "updated", "direction": "desc"},
                timeout=8
            )
            repo_json = repos_resp.json()
            repos = repo_json if isinstance(repo_json, list) else []
        except Exception:
            repos = []

        total_stars = sum(r.get('stargazers_count', 0) or 0 for r in repos)
        updated_dates = [r.get('updated_at') for r in repos if r.get('updated_at')]
        last_activity = max(updated_dates) if updated_dates else None

        evidence_parts = []
        repo_evidence = []
        for repo in repos[:40]:
            name = repo.get('name') or ''
            desc = repo.get('description') or ''
            language = repo.get('language') or ''
            topics = repo.get('topics') or []
            evidence = ' '.join([name, desc, language, ' '.join(topics)]).strip()
            if evidence:
                evidence_parts.append(evidence)
                repo_evidence.append({
                    'name': name,
                    'url': repo.get('html_url', ''),
                    'description': desc,
                    'language': language,
                    'topics': topics,
                    'stars': repo.get('stargazers_count', 0) or 0,
                    'updated_at': repo.get('updated_at')
                })

        return {
            'username': user_data.get('login'),
            'url': user_data.get('html_url', ''),
            'bio': user_data.get('bio') or 'N/A',
            'location': user_data.get('location') or 'Not specified',
            'repos': user_data.get('public_repos', 0),
            'followers': user_data.get('followers', 0),
            'stars': total_stars,
            'last_activity': last_activity,
            'created_at': user_data.get('created_at'),
            'repo_evidence': repo_evidence,
            'repo_evidence_text': ' '.join(evidence_parts).lower(),
            'discovery_sources': [discovery_source] if discovery_source else [],
            'discovery_evidence': [discovery_evidence] if discovery_evidence else [],
        }
    except Exception:
        return None


def search_github_typo_proof(keyword, location_filter, min_followers=0):
    """High-recall candidate discovery.

    Inclusion rule: BIO evidence OR REPOSITORY evidence.
    A candidate never needs evidence from both channels to enter the pool.
    Results from both independent channels are unioned and deduplicated by username.
    """
    results_by_user = {}
    location_keywords = []
    if location_filter['type'] == 'GLOBAL':
        location_keywords = [None]
    elif location_filter['type'] == 'SPECIFIC':
        location_keywords = [location_filter['city']] + location_filter['nearby']
    elif location_filter['type'] == 'REGION':
        location_keywords = location_filter['cities']
    elif location_filter['type'] == 'RAW_LOCATION':
        location_keywords = [location_filter['raw_input']]

    # 1) BIO DISCOVERY - precise, location-aware.
    for loc_keyword in location_keywords:
        query = f'"{keyword}" in:bio'
        if loc_keyword:
            query += f' location:"{loc_keyword}"'
        try:
            print(f"\n   🔎 BIO Search Query: {query}")
            response = requests.get("https://api.github.com/search/users", headers=github_headers,
                                    params={"q": query, "sort": "followers", "order": "desc", "per_page": 10}, timeout=10)
            data = response.json()
            print(f"   📊 BIO Response: {data.get('total_count', 0)} total results")
            for user in data.get('items', []):
                username = user.get('login')
                if not username or username in results_by_user:
                    continue
                cand = _enrich_github_user(username, 'BIO', f'{keyword} found through GitHub bio search')
                if cand:
                    include, _ = should_include_candidate(cand.get('location'), location_filter)
                    if include:
                        results_by_user[username] = cand
        except Exception as e:
            print(f"   ❌ BIO Search Error: {e}")

    # 2) REPOSITORY DISCOVERY - evidence-first recall.
    # GitHub repository search supports name/description/readme indexing. We then verify owner location.
    repo_query = f'"{keyword}" in:name,description,readme fork:false archived:false'
    try:
        print(f"\n   🔎 REPO Search Query: {repo_query}")
        response = requests.get("https://api.github.com/search/repositories", headers=github_headers,
                                params={"q": repo_query, "sort": "updated", "order": "desc", "per_page": 20}, timeout=10)
        data = response.json()
        print(f"   📊 REPO Response: {data.get('total_count', 0)} total results")
        for repo in data.get('items', []):
            owner = repo.get('owner') or {}
            username = owner.get('login')
            if not username or owner.get('type') != 'User':
                continue
            evidence = f"{repo.get('full_name','')} | {repo.get('description') or ''}"
            if username in results_by_user:
                if 'REPOSITORY' not in results_by_user[username]['discovery_sources']:
                    results_by_user[username]['discovery_sources'].append('REPOSITORY')
                    results_by_user[username]['discovery_evidence'].append(evidence)
                continue
            cand = _enrich_github_user(username, 'REPOSITORY', evidence)
            if cand:
                include, _ = should_include_candidate(cand.get('location'), location_filter)
                if include:
                    results_by_user[username] = cand
    except Exception as e:
        print(f"   ❌ REPO Search Error: {e}")

    return list(results_by_user.values())

# ============================================================================
# v9.0: ELITE SCORING (FULLY PRESERVED v8.0 + ALL 6 v9.0 FEATURES)
# ============================================================================

def score_candidates_elite(candidates, jd_analysis, skills_db, location_filter):
    for candidate in candidates:
        score = 0
        bio = candidate.get('bio') or ''
        bio_lower = bio.lower() if bio and bio != 'N/A' else ''
        repo_evidence_text = candidate.get('repo_evidence_text', '') or ''
        evidence_text = f"{bio_lower} {repo_evidence_text}".strip()
        location = candidate.get('location') or ''
        followers = candidate.get('followers', 0)
        stars = candidate.get('stars', 0)
        repos = candidate.get('repos', 0)
        last_activity = candidate.get('last_activity')
        created_at = candidate.get('created_at')
        
        tier1_detailed = []
        tier2_detailed = []
        
        # ===== TIER 1: MUST-HAVE SKILLS (40 points) =====
        tier1_matches = 0
        for skill_obj in jd_analysis.get('core_skills', [])[:10]:
            skill_name = skill_obj.get('skill')
            skill_info = skills_db.get(skill_name, {})
            keywords = skill_info.get('keywords', [])
            
            bio_keywords_found = []
            repo_keywords_found = []
            for kw in keywords:
                if fuzzy_match(kw, bio_lower, max_distance=2):
                    bio_keywords_found.append(kw)
                if fuzzy_match(kw, repo_evidence_text, max_distance=2):
                    repo_keywords_found.append(kw)

            # HIGH-RECALL OR RULE: either source is sufficient.
            keywords_found = list(dict.fromkeys(bio_keywords_found + repo_keywords_found))
            if bio_keywords_found or repo_keywords_found:
                evidence_sources = []
                if bio_keywords_found:
                    evidence_sources.append('BIO')
                if repo_keywords_found:
                    evidence_sources.append('REPOSITORY')
                
                # Calculate confidence
                confidence_level, confidence_reason = calculate_evidence_confidence(
                    bio_keywords_found, repo_keywords_found, evidence_sources, len(keywords)
                )
                
                tier1_matches += 1
                tier1_detailed.append({
                    'skill': skill_name,
                    'keywords_found': keywords_found,
                    'bio_keywords_found': bio_keywords_found,
                    'repo_keywords_found': repo_keywords_found,
                    'evidence_sources': evidence_sources,
                    'match_type': 'CORE_SKILL',
                    'confidence': confidence_level,
                    'confidence_reason': confidence_reason
                })
        
        max_core = max(1, len(jd_analysis.get('core_skills', [])))
        tier1_score = (tier1_matches / max_core) * 40 if max_core > 0 else 0
        score += tier1_score
        candidate['tier1_matches'] = tier1_matches
        candidate['tier1_detailed'] = tier1_detailed
        
        # ===== TIER 2: BONUS SKILLS (20 points) =====
        tier2_matches = 0
        for skill_obj in jd_analysis.get('nice_to_have', [])[:10]:
            skill_name = skill_obj.get('skill')
            skill_info = skills_db.get(skill_name, {})
            keywords = skill_info.get('keywords', [])
            
            bio_keywords_found = []
            repo_keywords_found = []
            for kw in keywords:
                if fuzzy_match(kw, bio_lower, max_distance=2):
                    bio_keywords_found.append(kw)
                if fuzzy_match(kw, repo_evidence_text, max_distance=2):
                    repo_keywords_found.append(kw)

            # HIGH-RECALL OR RULE: either source is sufficient.
            keywords_found = list(dict.fromkeys(bio_keywords_found + repo_keywords_found))
            if bio_keywords_found or repo_keywords_found:
                evidence_sources = []
                if bio_keywords_found:
                    evidence_sources.append('BIO')
                if repo_keywords_found:
                    evidence_sources.append('REPOSITORY')
                
                # Calculate confidence
                confidence_level, confidence_reason = calculate_evidence_confidence(
                    bio_keywords_found, repo_keywords_found, evidence_sources, len(keywords)
                )
                
                tier2_matches += 1
                tier2_detailed.append({
                    'skill': skill_name,
                    'keywords_found': keywords_found,
                    'bio_keywords_found': bio_keywords_found,
                    'repo_keywords_found': repo_keywords_found,
                    'evidence_sources': evidence_sources,
                    'match_type': 'BONUS_SKILL',
                    'confidence': confidence_level,
                    'confidence_reason': confidence_reason
                })
        
        max_nice = max(1, len(jd_analysis.get('nice_to_have', [])))
        tier2_score = (tier2_matches / max_nice) * 20 if max_nice > 0 and jd_analysis.get('nice_to_have') else 0
        score += tier2_score
        candidate['tier2_matches'] = tier2_matches
        candidate['tier2_detailed'] = tier2_detailed
        
        # ===== BIO MATCHING (10 points) =====
        bio_score = 0
        bio_signals_detailed = []
        
        if tier1_matches >= 1:
            bio_score += 5
            bio_signals_detailed.append(f"Core skill match: {tier1_matches} TIER 1 skills")
        
        if tier2_matches >= 1:
            bio_score += 5
            bio_signals_detailed.append(f"Bonus skills: {tier2_matches} TIER 2 skills")
        
        score += bio_score
        candidate['bio_signals'] = bio_signals_detailed
        
        # ===== BONUS: OPEN TO WORK (+10) =====
        candidate['open_to_work_detected'] = False
        open_keywords = ['open to work', 'open for work', 'open to opportunities', 'seeking opportunities', 'available for work']
        for kw in open_keywords:
            if kw in bio_lower:
                candidate['open_to_work_detected'] = True
                break
        
        # ===== BONUS: PROFILE COMPLETENESS (+5) =====
        if bio != 'N/A' and bio.strip() != '':
            score += 2
        if location != 'Not specified' and location.strip() != '':
            score += 3
        
        # ===== v9.0: RECENCY CHECK (+15 bonus) =====
        recency_signal, days_since, activity_status, recency_bonus = check_recency(last_activity or '')
        score += recency_bonus
        candidate['recency_signal'] = recency_signal
        candidate['days_since_activity'] = days_since
        candidate['activity_status'] = activity_status
        candidate['was_dormant_before'] = False  # Historical dormancy cannot be established from a single current snapshot
        
        # ===== v9.0: RED FLAGS =====
        account_age_days = 999
        if created_at:
            try:
                created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                account_age_days = (datetime.now(timezone.utc) - created_date).days
            except:
                pass
        
        candidate['rare_skill_count'] = len(tier1_detailed)
        red_flags = detect_red_flags(candidate, account_age_days)
        candidate['red_flags'] = red_flags
        if red_flags:
            score -= 5
        
        # ===== v9.0: OPPORTUNITY SIGNALS (+10 bonus) =====
        opportunity_signals = detect_opportunity_signals(candidate)
        candidate['opportunity_signals'] = opportunity_signals
        # Informational only: do not boost ranking based on inferred availability/activity.
        
        # ===== v9.0: SPECIALIZATION LEVEL =====
        spec_type, depth, breadth, spec_desc = detect_specialization_level(
            [m['skill'] for m in tier1_detailed], 
            {}
        )
        candidate['specialization_type'] = spec_type
        candidate['specialization_depth'] = depth
        candidate['specialization_breadth'] = breadth
        candidate['specialization_desc'] = spec_desc
        
        # ===== v9.0: COMMUNICATION SCORE (+5 bonus) =====
        readme_scans = candidate.get('repo_evidence_text', '')
        comm_score, comm_signals, comm_explanation = score_communication_quality(bio, readme_scans, candidate.get('username', ''))
        candidate['communication_score'] = comm_score
        candidate['communication_signals'] = comm_signals
        candidate['communication_explanation'] = comm_explanation
        # Informational only: profile/documentation completeness does not change candidate ranking.
        
        # ===== v9.0: UNICORN DETECTION =====
        is_unicorn, rarity_score, unicorn_explanation = detect_unicorn_profile(
            [m['skill'] for m in tier1_detailed],
            [s['skill'] for s in jd_analysis.get('core_skills', [])],
            account_age_days
        )
        candidate['is_unicorn'] = is_unicorn
        candidate['rarity_score'] = rarity_score
        candidate['unicorn_explanation'] = unicorn_explanation
        
        # ===== BONUS: ACTIVITY CONFIDENCE (+5) =====
        activity_conf = 0
        activity_signals = []
        
        if followers >= 1000:
            activity_conf = 95
            activity_signals.append('High visibility (1000+ followers)')
        elif followers >= 500:
            activity_conf = 85
            activity_signals.append('Well-known (500-999 followers)')
        elif followers >= 100:
            activity_conf = 70
            activity_signals.append('Active contributor (100+ followers)')
        elif followers >= 50:
            activity_conf = 55
            activity_signals.append('Growing (50+ followers)')
        else:
            activity_conf = 40
            activity_signals.append('💡 Early-stage/Lurker - low visibility but skills may match!')
        
        if stars >= 1000:
            activity_conf = min(100, activity_conf + 10)
            activity_signals.append('Popular projects (1000+ stars)')
        elif stars >= 500:
            activity_conf = min(100, activity_conf + 5)
            activity_signals.append('Well-starred repos (500+ stars)')
        
        if repos >= 100:
            activity_conf = min(100, activity_conf + 5)
            activity_signals.append('Very active (100+ repos)')
        elif repos >= 50:
            activity_conf = min(100, activity_conf + 3)
            activity_signals.append('Active (50+ repos)')
        
        activity_bonus = (activity_conf / 100) * 5
        score += activity_bonus
        
        candidate['activity_confidence'] = min(100, activity_conf)
        candidate['activity_signals'] = activity_signals
        candidate['is_high_visibility'] = followers >= 100 or stars >= 100
        candidate['is_low_visibility'] = followers < 50 or (followers < 100 and stars < 100)
        
        # ===== BONUS: LOCATION MATCH (+10) =====
        location_priority = should_include_candidate(location, location_filter)[1]
        if location_priority > 0:
            score += location_priority / 2
        candidate['location_priority'] = location_priority
        
        candidate['match_score'] = min(100, score)
        candidate['account_age_days'] = account_age_days
    
    return candidates

# ============================================================================
# MAIN EXECUTION (ALL v8.0 + ALL v9.0)
# ============================================================================

print("\n" + "="*100)
print("ULTIMATE RECRUITING ENGINE v9.6 - TRULY UNIVERSAL")
print("="*100)
print("""
🎯 WORKS WITH ANY ROLE, ANY SKILL, ANY JD

✅ FULLY OPTIMIZED ROLES (150+ skills mapped):
   • ML/AI Engineer      • Data Engineer        • Frontend Engineer
   • Backend Engineer    • DevOps/SRE/Platform • Mobile (iOS/Android)
   • Cloud Architect     • Security Engineer   • Database Admin
   • QA/Test Engineer    • Solutions Architect • And more...

✅ ALSO WORKS FOR (Add skills first time if needed):
   • Blockchain Engineer • Quantum Engineer    • Game Developer
   • Robotics Engineer   • Embedded Systems    • Network Engineer
   • AR/VR Developer     • Hardware Engineer   • Any future role

💡 HOW IT WORKS: Paste ANY job description.
   • System auto-detects role from skills
   • Intelligently groups CORE vs SUPPORTING
   • Handles unknown skills with semantic understanding
   • No role is rejected - we'll learn and search smartly

📝 FORMAT: Can be:
   - Single line: "Senior ML Engineer with PyTorch and TensorFlow"
   - Multi-line with MUST HAVE / NICE TO HAVE sections
   - Any domain, any tech stack, any language

🔧 If a skill isn't recognized: System adds it to learning and searches anyway

""")
print("="*100 + "\n")

print("STEP 1: Choose Input Method:\n")
print("1. GitHub Profile Link (Ideal candidate as reference)")
print("2. Brief Requirement (One-liner with MUST HAVE / NICE TO HAVE - SMART & CONTROLLED recruiting)")
choice = input("Enter 1 or 2: ").strip()

if choice == "1":
    print("\nPaste GitHub Profile Link (e.g., https://github.com/username):\n")
    github_link = input().strip()
    
    if not github_link.startswith('https://github.com/'):
        print("\n❌ Invalid link. Must be: https://github.com/username\n")
        exit()
    
    github_username = github_link.replace('https://github.com/', '').strip('/')
    
    print(f"\n🔍 Analyzing GitHub profile: {github_username}...\n")
    
    profile_analysis = analyze_github_profile_intelligent(github_username)
    
    if not profile_analysis:
        print(f"\n❌ Could not fetch profile for {github_username}.")
        print("\n   Possible reasons:")
        print("   • GitHub API rate limit exceeded (60/hour without token)")
        print("   • Invalid GitHub username")
        print("   • Network timeout\n")
        print("   Recommendation: Use OPTION 2 (paste job description instead)\n")
        exit()
    
    jd_analysis = {
        'core_skills': [{'skill': s, 'confidence': 0.95} for s in profile_analysis['tier1_skills'][:10]],
        'nice_to_have': [{'skill': s, 'confidence': 0.85} for s in profile_analysis['tier2_skills'][:5]],
        'seniority_level': 'UNKNOWN',  # GitHub visibility is not reliable evidence of professional seniority
        'seniority_confidence': 0,
        'role_type': profile_analysis['role_type'],
        'role_confidence': 85,
        'remote_status': 'UNKNOWN',
        'location': 'GLOBAL',
        'specialization': profile_analysis['role_type'].replace('_', ' ')
    }
    
    reference_input = profile_analysis['username']

elif choice == "2":
    print("\n🎯 FOR BEST RESULTS: Use MUST HAVE / NICE TO HAVE structure (100% precise control)")
    print("   This format ensures the system respects YOUR exact priorities.\n")
    print("Enter requirement (one-liner or multi-line with MUST/NICE sections):")
    print("\nEXAMPLES:\n")
    print("ONE-LINER:")
    print("  - Senior Backend Engineer with 6+ years, Python, Django, PostgreSQL, Docker.")
    print("\nWITH SECTIONS (RECOMMENDED - Most Control):")
    print("  - Senior Backend Engineer, 6+ years.")
    print("  - MUST HAVE: Python, Django, PostgreSQL, REST APIs, Docker.")
    print("  - NICE TO HAVE: Kubernetes, Redis, AWS, GraphQL.")
    print("\n💡 Tip: For multi-line input, paste all text then press Ctrl+D (Mac/Linux) or Ctrl+Z (Windows):\n")
    
    # Read multi-line input
    lines = []
    try:
        while True:
            line = input()
            if line.strip() == "":  # Empty line = end of input
                if lines:
                    break
            else:
                lines.append(line)
    except EOFError:
        # Ctrl+D pressed
        pass
    
    brief_requirement = "\n".join(lines).strip()
    
    if len(brief_requirement) < 10:
        print("\n❌ Requirement too short. Please be more specific.\n")
        exit()
    
    print(f"\n🔍 Parsing requirement...\n")
    
    # Create synthetic JD with full multi-line requirement
    synthetic_jd = f"Position: {brief_requirement}\n\nFull Requirement:\n{brief_requirement}"
    jd_analysis = deconstruct_jd_intelligent(synthetic_jd)
    reference_input = brief_requirement


else:
    print("\n❌ Invalid choice. Enter 1 or 2.\n")
    exit()

if not jd_analysis.get('core_skills'):
    print("\n⚠️  No core skills detected. This might return broad results.\n")

print("="*100)
print("REQUIREMENT ANALYSIS")
print("="*100 + "\n")

# Display actual role title + category for context
role_title = jd_analysis.get('role_title', 'Unknown Position')
role_category = jd_analysis.get('role_type', 'GENERAL_ENGINEER')
print(f"🎯 ROLE: {role_title.title()}")
print(f"   └─ Category: {role_category.replace('_', ' ')} (Conf: {jd_analysis.get('role_confidence', 0)}%)")
print(f"📊 SPECIALIZATION: {jd_analysis.get('specialization', 'General')}\n")

print(f"✅ MUST-HAVE ({len(jd_analysis.get('core_skills', []))}): {', '.join([s['skill'] for s in jd_analysis.get('core_skills', [])][:10]) or 'None'}")

# Display NICE-TO-HAVE
nice_skills = jd_analysis.get('nice_to_have', [])
if nice_skills:
    nice_skill_names = [s['skill'] for s in nice_skills[:10]]
    print(f"✅ NICE-TO-HAVE ({len(nice_skills)}): {', '.join(nice_skill_names)}")
else:
    print(f"✅ NICE-TO-HAVE (0): None")

print(f"✅ SENIORITY: {jd_analysis.get('seniority_level')} (Conf: {jd_analysis.get('seniority_confidence', 0)}%)")
if jd_analysis.get('years'):
    print(f"✅ YEARS: {jd_analysis['years']}+")
print(f"✅ REMOTE: {jd_analysis.get('remote_status')}\n")

print("="*100)
print("LOCATION & TRAVEL PREFERENCES")
print("="*100 + "\n")

print("Enter location(s) - ANY city/region/country on planet accepted!")
print("Examples:")
print("  Cities: amsterdam, berlin, london, paris, bangalore, mumbai, tokyo, sydney")
print("  Regions: india, europe, latam, asia, southeast asia, usa, australia, middle east, africa")
print("  Global: global, remote, anywhere, worldwide\n")
location_input = input().strip() or "global"
location_filter = parse_location_input(location_input)
print(f"\n✅ Searching: {location_filter['description']}\n")

print("="*100)
print("EXECUTING 3-LAYER SEARCH (TIGHT → SMART EXPANSION → FALLBACK)")
print("="*100 + "\n")

all_candidates = {}
skills_db = get_skills_database()

print("🔍 LAYER 1: CORE SKILLS (TIGHT - NO EXPANSION)\n")

layer1_results = 0
for skill_obj in jd_analysis.get('core_skills', [])[:6]:
    skill_name = skill_obj.get('skill')
    print(f"   {skill_name}...", end=" ", flush=True)
    candidates = search_github_typo_proof(skill_name, location_filter)
    
    for candidate in candidates:
        if candidate['username'] not in all_candidates:
            all_candidates[candidate['username']] = candidate
    
    layer1_results += len(candidates)
    print(f"✅ ({len(candidates)})")

print(f"\nLayer 1 Total: {layer1_results} candidates\n")

if layer1_results < 8:
    print("🔍 LAYER 2: SEMANTIC EXPANSION (INTELLIGENT FALLBACK)\n")
    
    for skill_obj in jd_analysis.get('core_skills', [])[:4]:
        skill_name = skill_obj.get('skill')
        skill_info = skills_db.get(skill_name, {})
        related = skill_info.get('related_skills', [])[:2]
        
        for expanded_skill in related:
            print(f"   {expanded_skill} (related to {skill_name})...", end=" ", flush=True)
            candidates = search_github_typo_proof(expanded_skill, location_filter)
            
            for candidate in candidates:
                if candidate['username'] not in all_candidates:
                    all_candidates[candidate['username']] = candidate
            
            print(f"✅ ({len(candidates)})")

if len(all_candidates) < 5:
    print("\n🔍 LAYER 3: NICE-TO-HAVE (EXPAND PREFERENCES)\n")
    
    for skill_obj in jd_analysis.get('nice_to_have', [])[:3]:
        skill_name = skill_obj.get('skill')
        print(f"   {skill_name}...", end=" ", flush=True)
        candidates = search_github_typo_proof(skill_name, location_filter)
        
        for candidate in candidates:
            if candidate['username'] not in all_candidates:
                all_candidates[candidate['username']] = candidate
        
        print(f"✅ ({len(candidates)})")

if not all_candidates:
    print("\n❌ No candidates found.\n")
    exit()

all_candidates_list = list(all_candidates.values())
all_candidates_list = score_candidates_elite(all_candidates_list, jd_analysis, skills_db, location_filter)
sorted_candidates = sorted(all_candidates_list, key=lambda x: x['match_score'], reverse=True)

print(f"\n{'='*100}")
print(f"RESULTS: {len(all_candidates)} CANDIDATES (ELITE v9.0 SCORING)")
print(f"{'='*100}\n")

results_per_batch = 10
batch_num = 1
start_idx = 0
end_idx = min(results_per_batch, len(sorted_candidates))

while start_idx < len(sorted_candidates):
    print(f"\n{'='*100}")
    print(f"BATCH {batch_num} ({start_idx+1}-{end_idx} of {len(all_candidates)})")
    print(f"{'='*100}\n")
    
    for i, candidate in enumerate(sorted_candidates[start_idx:end_idx], start_idx+1):
        followers = candidate['followers']
        
        if followers >= 1000:
            follower_tier = "🔥 INFLUENCER (>1000)"
        elif followers >= 500:
            follower_tier = "⭐ SENIOR (500-999)"
        elif followers >= 100:
            follower_tier = "📈 MID-LEVEL (100-499)"
        elif followers >= 50:
            follower_tier = "👤 GROWING (50-99)"
        else:
            follower_tier = "🌱 EMERGING (0-49)"
        
        relevance = candidate['match_score']
        if followers >= 500:
            relevance += 5
        if candidate.get('bio') and candidate['bio'] != 'N/A':
            relevance += 3
        if candidate.get('stars', 0) > 100:
            relevance += 4
        
        relevance = min(100, relevance)
        
        if relevance >= 85:
            relevance_ind = "🟢 HIGHLY RELEVANT"
        elif relevance >= 70:
            relevance_ind = "🟡 RELEVANT"
        elif relevance >= 50:
            relevance_ind = "🟠 MODERATE"
        else:
            relevance_ind = "🔴 LOW MATCH"
        
        print(f"{i}. {candidate['username']} | Score: {candidate['match_score']:.0f}/100 | {relevance_ind}")
        print(f"   {candidate['url']}")
        print(f"   {follower_tier} | 📍 {candidate['location']} | Stars: {candidate['stars']} | Repos: {candidate['repos']}")
        
        if candidate.get('recency_signal'):
            print(f"   {candidate['recency_signal']}")
        
        if candidate.get('is_unicorn'):
            print(f"   🎯 HIGH TARGET-SKILL COVERAGE - verify evidence before outreach")
        
        if candidate.get('red_flags'):
            for flag in candidate['red_flags'][:1]:
                print(f"   {flag}")
        
        if candidate.get('opportunity_signals'):
            print(f"   📌 PUBLIC SIGNAL: {candidate['opportunity_signals'][0]}")
        
        if candidate.get('specialization_type'):
            print(f"   {candidate['specialization_type']} ({candidate['specialization_depth']} skills, {candidate['specialization_breadth']} domains)")
        
        if candidate.get('communication_score'):
            comm_emoji = "⭐" if candidate['communication_score'] >= 7 else "📝"
            print(f"   {comm_emoji} Profile/docs: {candidate['communication_score']}/10")
        
        if candidate['open_to_work_detected']:
            print(f"   🔓 OPEN TO WORK")
        
        if candidate.get('tier1_detailed'):
            print(f"\n   ✅ TIER 1 MATCH ({len(candidate['tier1_detailed'])} skills):")
            for match in candidate['tier1_detailed'][:5]:
                keywords_str = ", ".join([f'"{kw}"' for kw in match['keywords_found']])
                sources_str = " OR ".join(match.get('evidence_sources', [])) or "PUBLIC GITHUB"
                confidence = match.get('confidence', 'MEDIUM')
                confidence_emoji = '🟢' if confidence == 'HIGH' else '🟡' if confidence == 'MEDIUM' else '🔴'
                confidence_reason = match.get('confidence_reason', '')
                print(f"      • {match['skill']} [{sources_str}] {confidence_emoji} {confidence}")
                print(f"        {confidence_reason} | found: {keywords_str}")
        
        if candidate.get('tier2_detailed'):
            print(f"\n   🎁 TIER 2 MATCH ({len(candidate['tier2_detailed'])} skills):")
            for match in candidate['tier2_detailed'][:3]:
                keywords_str = ", ".join([f'"{kw}"' for kw in match['keywords_found']])
                sources_str = " OR ".join(match.get('evidence_sources', [])) or "PUBLIC GITHUB"
                confidence = match.get('confidence', 'MEDIUM')
                confidence_emoji = '🟢' if confidence == 'HIGH' else '🟡' if confidence == 'MEDIUM' else '🔴'
                confidence_reason = match.get('confidence_reason', '')
                print(f"      • {match['skill']} [{sources_str}] {confidence_emoji} {confidence}")
                print(f"        {confidence_reason} | found: {keywords_str}")
        
        if candidate.get('bio_signals'):
            print(f"\n   🎯 BIO SIGNALS: {', '.join(candidate['bio_signals'])}")
        
        if candidate.get('is_low_visibility'):
            print(f"\n   💡 LOW VISIBILITY: {', '.join(candidate.get('activity_signals', []))} - BUT SKILLS MATCH!")
        elif candidate.get('activity_signals'):
            print(f"\n   ⭐ ACTIVITY: {', '.join(candidate.get('activity_signals', [])[:2])}")
        
        print()
    
    if end_idx < len(sorted_candidates):
        print(f"{'='*100}")
        user_input = input(f"\n✅ Showing {end_idx - start_idx} candidates. Load next batch? (yes/no/save): ").strip().lower()
        
        if user_input in ['yes', 'y']:
            batch_num += 1
            start_idx = end_idx
            end_idx = min(start_idx + results_per_batch, len(sorted_candidates))
            continue
        elif user_input in ['save', 's']:
            break
        else:
            break
    else:
        print(f"{'='*100}")
        print(f"\n✅ All {len(sorted_candidates)} candidates shown.\n")
        break

save_name = input("Save results as: ").strip() or f"recruiting_results_v9_{int(datetime.now().timestamp())}"
txt_file = os.path.expanduser(f'~/{save_name}.txt')

try:
    with open(txt_file, 'w') as f:
        f.write("="*100 + "\n")
        f.write(f"ULTIMATE RECRUITING ENGINE v9.0 - ELITE SOURCER RESULTS\n")
        f.write(f"Core v9 features + BIO OR REPOSITORY high-recall discovery\n")
        f.write("="*100 + "\n\n")
        
        f.write(f"REFERENCE: {reference_input}\n")
        f.write(f"Role: {jd_analysis.get('role_title', 'Unknown')} (Category: {jd_analysis.get('role_type')})\n")
        f.write(f"Location Filter: {location_filter['description']}\n")
        f.write(f"TIER 1 (Non-Negotiable): {', '.join([s['skill'] for s in jd_analysis.get('core_skills', [])])}\n")
        f.write(f"TIER 2 (Bonus): {', '.join([s['skill'] for s in jd_analysis.get('nice_to_have', [])])}\n")
        f.write(f"Total Candidates Found: {len(all_candidates)}\n")
        f.write("="*100 + "\n\n")
        
        f.write("TOP 50 ELITE-SCORED CANDIDATES (v9.0)\n")
        f.write("="*100 + "\n\n")
        
        for i, candidate in enumerate(sorted_candidates[:50], 1):
            relevance = candidate['match_score']
            if candidate['followers'] >= 500:
                relevance += 5
            if candidate.get('bio') and candidate['bio'] != 'N/A':
                relevance += 3
            if candidate.get('stars', 0) > 100:
                relevance += 4
            relevance = min(100, relevance)
            
            f.write(f"{i}. {candidate['username']} ({relevance:.0f}/100 Relevance)\n")
            f.write(f"   {candidate['url']}\n")
            f.write(f"   Location: {candidate['location']} | Followers: {candidate['followers']} | Stars: {candidate['stars']} | Repos: {candidate['repos']}\n")
            
            if candidate.get('recency_signal'):
                f.write(f"   Recency: {candidate['recency_signal']}\n")
            
            if candidate.get('is_unicorn'):
                f.write(f"   🎯 HIGH TARGET-SKILL COVERAGE - {candidate['unicorn_explanation']}\n")
            
            if candidate.get('red_flags'):
                for flag in candidate['red_flags'][:1]:
                    f.write(f"   {flag}\n")
            
            if candidate.get('opportunity_signals'):
                for opp in candidate['opportunity_signals'][:2]:
                    f.write(f"   🚀 {opp}\n")
            
            if candidate.get('specialization_type'):
                f.write(f"   {candidate['specialization_type']}: {candidate['specialization_desc']}\n")
            
            if candidate.get('communication_score'):
                f.write(f"   Profile/docs: {candidate['communication_score']}/10 - {', '.join(candidate.get('communication_signals', [])[:2])}\n")
            
            open_status = "🔓 OPEN TO WORK" if candidate.get('open_to_work_detected') else "Not mentioned"
            f.write(f"   Status: {open_status}\n")
            
            if candidate.get('tier1_detailed'):
                f.write(f"\n   ✅ TIER 1 MATCHES ({len(candidate['tier1_detailed'])} skills):\n")
                for match in candidate['tier1_detailed'][:5]:
                    keywords_str = ", ".join([f'"{kw}"' for kw in match['keywords_found']])
                    sources_str = " OR ".join(match.get('evidence_sources', [])) or "PUBLIC GITHUB"
                    confidence = match.get('confidence', 'MEDIUM')
                    confidence_reason = match.get('confidence_reason', '')
                    f.write(f"      • {match['skill']} [{sources_str}] - {confidence}\n")
                    f.write(f"        {confidence_reason} | found: {keywords_str}\n")
            
            if candidate.get('tier2_detailed'):
                f.write(f"\n   🎁 TIER 2 MATCHES ({len(candidate['tier2_detailed'])} skills):\n")
                for match in candidate['tier2_detailed'][:3]:
                    keywords_str = ", ".join([f'"{kw}"' for kw in match['keywords_found']])
                    sources_str = " OR ".join(match.get('evidence_sources', [])) or "PUBLIC GITHUB"
                    confidence = match.get('confidence', 'MEDIUM')
                    confidence_reason = match.get('confidence_reason', '')
                    f.write(f"      • {match['skill']} [{sources_str}] - {confidence}\n")
                    f.write(f"        {confidence_reason} | found: {keywords_str}\n")
            
            if candidate.get('bio_signals'):
                f.write(f"\n   🎯 BIO SIGNALS: {', '.join(candidate['bio_signals'])}\n")
            
            f.write("\n")
    
    print(f"\n✅ Saved: {txt_file}\n")
except Exception as e:
    print(f"\n⚠️  Could not save file: {e}\n")

print("="*100)
print("ENGINE v9.0 COMPLETE - ELITE SOURCER INTELLIGENCE ACTIVATED")
print("="*100)
