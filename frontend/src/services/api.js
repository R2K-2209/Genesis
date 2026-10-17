/**
 * API Service for communicating with the FastAPI backend.
 */

const API_BASE_URL = 'http://localhost:8000';

export async function fetchHealth() {
  const res = await fetch(`${API_BASE_URL}/api/health`);
  if (!res.ok) throw new Error('Backend offline');
  return res.json();
}

export async function fetchDatabaseOverview() {
  const res = await fetch(`${API_BASE_URL}/api/database/overview`);
  if (!res.ok) throw new Error('Failed to fetch database overview');
  return res.json();
}

export async function fetchDatabaseTables() {
  const res = await fetch(`${API_BASE_URL}/api/database/tables`);
  if (!res.ok) throw new Error('Failed to fetch database tables');
  return res.json();
}

export async function fetchTableData(tableName, { page = 1, limit = 25, search = '', sortBy = '', sortOrder = 'ASC' } = {}) {
  const params = new URLSearchParams({
    page: page.toString(),
    limit: limit.toString(),
    sort_order: sortOrder,
  });
  if (search) params.append('search', search);
  if (sortBy) params.append('sort_by', sortBy);

  const res = await fetch(`${API_BASE_URL}/api/database/tables/${encodeURIComponent(tableName)}?${params}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to fetch table data' }));
    throw new Error(err.detail || 'Failed to fetch table data');
  }
  return res.json();
}

export async function insertTableRow(tableName, payload) {
  const res = await fetch(`${API_BASE_URL}/api/database/tables/${encodeURIComponent(tableName)}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Insert failed' }));
    throw new Error(err.detail || 'Insert failed');
  }
  return res.json();
}

export async function updateTableRow(tableName, recordId, payload) {
  const res = await fetch(`${API_BASE_URL}/api/database/tables/${encodeURIComponent(tableName)}/${recordId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Update failed' }));
    throw new Error(err.detail || 'Update failed');
  }
  return res.json();
}

export async function deleteTableRow(tableName, recordId) {
  const res = await fetch(`${API_BASE_URL}/api/database/tables/${encodeURIComponent(tableName)}/${recordId}`, {
    method: 'DELETE',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Delete failed' }));
    throw new Error(err.detail || 'Delete failed');
  }
  return res.json();
}

export async function resetDatabase() {
  const res = await fetch(`${API_BASE_URL}/api/database/reset`, {
    method: 'POST',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Reset failed' }));
    throw new Error(err.detail || 'Reset failed');
  }
  return res.json();
}

export async function fetchApiCatalog() {
  const res = await fetch(`${API_BASE_URL}/api/v1/catalog`);
  if (!res.ok) throw new Error('Failed to load API catalog');
  return res.json();
}

export async function executeApiEndpoint(method, pathTemplate, params = {}, body = null) {
  let resolvedPath = pathTemplate;
  const queryParams = new URLSearchParams();

  // Substitute {param} in path
  Object.entries(params).forEach(([key, val]) => {
    const placeholder = `{${key}}`;
    if (resolvedPath.includes(placeholder)) {
      resolvedPath = resolvedPath.replace(placeholder, encodeURIComponent(String(val)));
    } else if (method === 'GET' && val !== undefined && val !== '') {
      queryParams.append(key, String(val));
    }
  });

  const queryString = queryParams.toString();
  const url = `${API_BASE_URL}${resolvedPath}${queryString ? `?${queryString}` : ''}`;

  const startTime = performance.now();
  const options = {
    method,
    headers: { 'Content-Type': 'application/json' }
  };
  if (method === 'POST' && body) {
    options.body = typeof body === 'string' ? body : JSON.stringify(body);
  }

  const res = await fetch(url, options);
  const latency = Math.round(performance.now() - startTime);
  const data = await res.json().catch(() => null);

  return {
    status: res.status,
    statusText: res.statusText || (res.status === 200 ? 'OK' : 'Error'),
    ok: res.ok,
    latency,
    url,
    data
  };
}

export async function fetchDriftState() {
  const res = await fetch(`${API_BASE_URL}/api/v1/drift-state`);
  if (!res.ok) throw new Error('Failed to fetch drift state');
  return res.json();
}

export async function updateDriftState(endpointId, driftMode = 'healthy', customParams = null, customPath = null) {
  const res = await fetch(`${API_BASE_URL}/api/v1/drift-state`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      endpoint_id: endpointId,
      drift_mode: driftMode,
      custom_params: customParams,
      custom_path: customPath
    })
  });
  if (!res.ok) throw new Error('Failed to update drift state');
  return res.json();
}

export async function resetDriftState() {
  const res = await fetch(`${API_BASE_URL}/api/v1/drift-state/reset`, {
    method: 'POST'
  });
  if (!res.ok) throw new Error('Failed to reset drift state');
  return res.json();
}

export async function sendChatMessage(message, { groqApiKey = '', model = 'llama-3.3-70b-versatile', history = [], useLangChain = false, engineMode = 'baseline', activeDrifts = null } = {}) {
  const res = await fetch(`${API_BASE_URL}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      groq_api_key: groqApiKey || undefined,
      model,
      history,
      use_langchain: useLangChain,
      engine_mode: engineMode,
      active_drifts: activeDrifts || undefined
    })
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Chat service error' }));
    throw new Error(err.detail || 'Chat service error');
  }
  return res.json();
}

export async function fetchAegisLedger(limit = 50) {
  const res = await fetch(`${API_BASE_URL}/api/v1/aegis/ledger?limit=${limit}`);
  if (!res.ok) throw new Error('Failed to fetch Aegis ledger');
  return res.json();
}

export async function resetAegisState() {
  const res = await fetch(`${API_BASE_URL}/api/v1/aegis/reset`, {
    method: 'POST'
  });
  if (!res.ok) throw new Error('Failed to reset Aegis state');
  return res.json();
}

export async function executeBlastRadiusTest({
  scenario = 'comparison',
  endpoint = null,
  httpMethod = null,
  fieldRenames = null,
  typeCasts = null,
  nestedWraps = null,
  injectedHeaders = null,
  modifiedKeys = null
} = {}) {
  const res = await fetch(`${API_BASE_URL}/api/aegis/test/blast-radius`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      scenario,
      endpoint: endpoint || undefined,
      http_method: httpMethod || undefined,
      field_renames: fieldRenames || undefined,
      type_casts: typeCasts || undefined,
      nested_wraps: nestedWraps || undefined,
      injected_headers: injectedHeaders || undefined,
      modified_keys: modifiedKeys || undefined
    })
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Blast-radius test failed' }));
    throw new Error(err.detail || 'Blast-radius test failed');
  }
  return res.json();
}

export async function executeSingleFlightTest() {
  const res = await fetch(`${API_BASE_URL}/api/aegis/test/single-flight`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Single-flight test failed' }));
    throw new Error(err.detail || 'Single-flight test failed');
  }
  return res.json();
}

export async function executeSqlUndoTest() {
  const res = await fetch(`${API_BASE_URL}/api/aegis/test/sql-undo`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'SQL Undo test failed' }));
    throw new Error(err.detail || 'SQL Undo test failed');
  }
  return res.json();
}

export async function executeGitOpsPrTest({
  githubToken = '',
  githubRepo = 'R2K-2209/Genesis',
  baseBranch = 'main',
  toolName = 'get_student',
  endpoint = '/api/v1/students/{student_id}/graduation-eligibility',
  driftType = null,
  fieldRenames = null,
  typeCasts = null,
  nestedWraps = null,
  routeRedirect = null
} = {}) {
  const res = await fetch(`${API_BASE_URL}/api/aegis/test/gitops-pr`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      github_token: githubToken || undefined,
      github_repo: githubRepo,
      base_branch: baseBranch,
      tool_name: toolName,
      endpoint: endpoint,
      drift_type: driftType || undefined,
      field_renames: fieldRenames || undefined,
      type_casts: typeCasts || undefined,
      nested_wraps: nestedWraps || undefined,
      route_redirect: routeRedirect || undefined
    })
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'GitOps Auto-PR test failed' }));
    throw new Error(err.detail || 'GitOps Auto-PR test failed');
  }
  return res.json();
}

