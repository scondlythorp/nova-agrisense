export const GAMBIA_REGIONS = [
  { code: 'BJL', name: 'Banjul', headquarters: 'Banjul' },
  { code: 'KMC', name: 'Kanifing', headquarters: 'Kanifing' },
  { code: 'WCR', name: 'West Coast Region', headquarters: 'Brikama' },
  { code: 'LRR', name: 'Lower River Region', headquarters: 'Mansa Konko' },
  { code: 'NBR', name: 'North Bank Region', headquarters: 'Kerewan' },
  { code: 'CRR', name: 'Central River Region', headquarters: 'Janjanbureh' },
  { code: 'URR', name: 'Upper River Region', headquarters: 'Basse Santa Su' },
] as const;

export const API_V1_PREFIX = '/api/v1';

export const ORGANIZATION_TYPES = [
  { value: 'cooperative', label: 'Agricultural Cooperative' },
  { value: 'ngo', label: 'Agricultural NGO' },
  { value: 'government_department', label: 'Government Agricultural Department' },
  { value: 'research_institute', label: 'Research Organization' },
  { value: 'private_agribusiness', label: 'Private Agribusiness' },
] as const;

export const ORGANIZATION_ROLE_DEFINITIONS = [
  { key: 'ORGANIZATION_ADMIN', label: 'Organization Administrator', scope: 'tenant' },
  { key: 'AGRICULTURAL_OFFICER', label: 'Agricultural Officer', scope: 'tenant' },
  { key: 'DATA_MANAGER', label: 'Data Manager', scope: 'tenant' },
  { key: 'RESEARCHER', label: 'Researcher', scope: 'tenant' },
  { key: 'COOPERATIVE_MANAGER', label: 'Cooperative Manager', scope: 'tenant' },
  { key: 'FARMER', label: 'Farmer', scope: 'self' },
  { key: 'READ_ONLY_ANALYST', label: 'Read-Only Analyst', scope: 'tenant' },
] as const;

export const ROLE_DEFINITIONS = [
  { key: 'PLATFORM_ADMIN', label: 'Platform Administrator', scope: 'global' },
  ...ORGANIZATION_ROLE_DEFINITIONS,
] as const;
