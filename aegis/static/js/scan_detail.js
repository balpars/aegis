// Scan detail page JavaScript
const scanId = document.getElementById("scanId").textContent.trim();

document.addEventListener("DOMContentLoaded", function () {
  loadScanResults();
});

async function loadScanResults() {
  try {
    const response = await fetch(`/api/scan/${scanId}`);
    const data = await response.json();
    
    if (data.error) {
      alert("Error: " + data.error);
      return;
    }
    
    await renderScanResults(data);
  } catch (error) {
    console.error("Error loading scan results:", error);
    alert("Error loading scan results: " + error.message);
  }
}

async function renderScanResults(data) {
  document.getElementById("loading").style.display = "none";
  document.getElementById("scanContent").style.display = "block";
  
  // Render summary
  renderSummary(data);
  
  // Render consensus findings (async to load code snippets)
  await renderConsensusFindings(data.consensus_findings);
  
  // Render per-model findings (async to load code snippets)
  await renderPerModelFindings(data.per_model_findings);
}

function renderSummary(data) {
  const container = document.getElementById("summaryCards");
  const findings = data.consensus_findings || [];
  
  const critical = findings.filter(f => f.severity === "critical").length;
  const high = findings.filter(f => f.severity === "high").length;
  const medium = findings.filter(f => f.severity === "medium").length;
  const low = findings.filter(f => f.severity === "low").length;
  
  container.innerHTML = `
    <div class="col-md-3">
      <div class="card text-center">
        <div class="card-body">
          <i class="bi bi-exclamation-triangle fs-1 text-warning mb-2"></i>
          <h3 class="card-title">${findings.length}</h3>
          <p class="card-text text-muted">Total Issues</p>
        </div>
      </div>
    </div>
    <div class="col-md-3">
      <div class="card text-center">
        <div class="card-body">
          <i class="bi bi-exclamation-circle fs-1 text-danger mb-2"></i>
          <h3 class="card-title">${critical + high}</h3>
          <p class="card-text text-muted">High/Critical</p>
        </div>
      </div>
    </div>
    <div class="col-md-3">
      <div class="card text-center">
        <div class="card-body">
          <i class="bi bi-exclamation fs-1 text-warning mb-2"></i>
          <h3 class="card-title">${medium}</h3>
          <p class="card-text text-muted">Medium</p>
        </div>
      </div>
    </div>
    <div class="col-md-3">
      <div class="card text-center">
        <div class="card-body">
          <i class="bi bi-info-circle fs-1 text-success mb-2"></i>
          <h3 class="card-title">${low}</h3>
          <p class="card-text text-muted">Low</p>
        </div>
      </div>
    </div>
  `;
}

async function renderConsensusFindings(findings) {
  const container = document.getElementById("consensusFindings");
  
  if (findings.length === 0) {
    container.innerHTML = `
      <div class="card text-center">
        <div class="card-body py-5">
          <i class="bi bi-shield-check fs-1 text-success mb-3"></i>
          <h3 class="text-success">No Issues Found</h3>
          <p class="lead">No security vulnerabilities were detected.</p>
        </div>
      </div>
    `;
    return;
  }
  
  let html = "";
  for (const finding of findings) {
    const codeSnippet = await getCodeSnippet(finding.file, finding.start_line, finding.end_line, finding.severity);
    html += `
      <div class="card vulnerability-card severity-${finding.severity} mb-3">
        <div class="card-header d-flex justify-content-between align-items-center">
          <div>
            <h6 class="mb-0">
              ${getSeverityBadge(finding.severity)}
              ${escapeHtml(finding.name)}
            </h6>
          </div>
          <div>
            <span class="badge bg-secondary">${finding.cwe}</span>
            <span class="badge bg-info">Confidence: ${(finding.confidence * 100).toFixed(0)}%</span>
          </div>
        </div>
        <div class="card-body">
          <h6 class="text-primary">
            <i class="bi bi-file-code"></i> ${escapeHtml(finding.file)}
            <small class="text-muted">Lines ${finding.start_line}-${finding.end_line}</small>
          </h6>
          <p class="mb-2"><strong>Message:</strong> ${escapeHtml(finding.message)}</p>
          ${codeSnippet}
          <small class="text-muted d-block mt-2">Fingerprint: <code>${finding.fingerprint}</code></small>
        </div>
      </div>
    `;
  }
  container.innerHTML = html;
}

async function getCodeSnippet(filePath, startLine, endLine, severity) {
  try {
    // Encode file path for URL
    const encodedPath = encodeURIComponent(filePath);
    const response = await fetch(`/api/scan/${scanId}/file/${encodedPath}`);
    
    if (!response.ok) {
      return '<p class="text-muted mt-3"><em>Source code not available</em></p>';
    }
    
    const data = await response.json();
    const content = data.content;
    const lines = content.split('\n');
    
    // Calculate context (5 lines before and after)
    const contextBefore = 5;
    const contextAfter = 5;
    const displayStart = Math.max(1, startLine - contextBefore);
    const displayEnd = Math.min(lines.length, endLine + contextAfter);
    
    let snippetHtml = `
      <div class="code-snippet-container mt-3">
        <div class="code-snippet-header">
          <i class="bi bi-code-square"></i> Code Context (Lines ${displayStart}-${displayEnd})
        </div>
        <div class="code-snippet-content">
    `;
    
    for (let i = displayStart; i <= displayEnd; i++) {
      const lineContent = lines[i - 1] || '';
      const isVulnerable = i >= startLine && i <= endLine;
      const lineClass = isVulnerable ? `severity-${severity}` : 'context';
      
      snippetHtml += `
        <div class="code-snippet-line ${lineClass}">
          <span class="code-snippet-line-number">${i}</span>
          <span class="code-snippet-code">${escapeHtml(lineContent)}</span>
        </div>
      `;
    }
    
    snippetHtml += `
        </div>
      </div>
    `;
    
    return snippetHtml;
  } catch (error) {
    console.error('Error fetching code snippet:', error);
    return '<p class="text-muted mt-3"><em>Unable to load source code</em></p>';
  }
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

async function renderPerModelFindings(perModelFindings) {
  const container = document.getElementById("perModelFindings");
  
  if (Object.keys(perModelFindings).length === 0) {
    container.innerHTML = '<p class="text-muted">No per-model findings available.</p>';
    return;
  }
  
  let html = "";
  for (const [modelId, findings] of Object.entries(perModelFindings)) {
    html += `
      <div class="card mb-4">
        <div class="card-header">
          <h6 class="mb-0">${modelId}</h6>
        </div>
        <div class="card-body">
          <p class="text-muted">${findings.length} findings</p>
    `;
    
    // Render each finding with code snippet
    for (const finding of findings) {
      const codeSnippet = await getCodeSnippet(finding.file, finding.start_line, finding.end_line, finding.severity);
      html += `
        <div class="card vulnerability-card severity-${finding.severity} mb-3">
          <div class="card-header d-flex justify-content-between align-items-center">
            <div>
              <h6 class="mb-0">
                ${getSeverityBadge(finding.severity)}
                ${escapeHtml(finding.name)}
              </h6>
            </div>
            <div>
              <span class="badge bg-secondary">${finding.cwe}</span>
              <span class="badge bg-info">Confidence: ${(finding.confidence * 100).toFixed(0)}%</span>
            </div>
          </div>
          <div class="card-body">
            <h6 class="text-primary">
              <i class="bi bi-file-code"></i> ${escapeHtml(finding.file)}
              <small class="text-muted">Lines ${finding.start_line}-${finding.end_line}</small>
            </h6>
            <p class="mb-2"><strong>Message:</strong> ${escapeHtml(finding.message)}</p>
            ${codeSnippet}
            <small class="text-muted d-block mt-2">Fingerprint: <code>${finding.fingerprint}</code></small>
          </div>
        </div>
      `;
    }
    
    html += `
        </div>
      </div>
    `;
  }
  container.innerHTML = html;
}

function getSeverityBadge(severity) {
  const badges = {
    critical: '<span class="badge bg-dark me-2">CRITICAL</span>',
    high: '<span class="badge bg-danger me-2">HIGH</span>',
    medium: '<span class="badge bg-warning me-2">MEDIUM</span>',
    low: '<span class="badge bg-success me-2">LOW</span>',
  };
  return badges[severity] || '<span class="badge bg-secondary me-2">UNKNOWN</span>';
}

function getSeverityColor(severity) {
  const colors = {
    critical: "dark",
    high: "danger",
    medium: "warning",
    low: "success",
  };
  return colors[severity] || "secondary";
}

function exportSARIF() {
  window.location.href = `/api/scan/${scanId}/sarif`;
}

function exportCSV() {
  window.location.href = `/api/scan/${scanId}/csv`;
}

async function exportJSON() {
  try {
    const response = await fetch(`/api/scan/${scanId}`);
    const data = await response.json();
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `scan_${scanId}.json`;
    a.click();
    URL.revokeObjectURL(url);
  } catch (error) {
    alert("Error exporting JSON: " + error.message);
  }
}
