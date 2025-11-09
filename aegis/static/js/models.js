// Models page JavaScript
document.addEventListener("DOMContentLoaded", function () {
  loadOllamaModels();
  loadRegisteredModels();
});

async function loadOllamaModels() {
  try {
    const response = await fetch("/api/models/ollama");
    const data = await response.json();
    const container = document.getElementById("ollamaModelsList");
    
    if (data.models.length === 0) {
      container.innerHTML = '<p class="text-muted">No Ollama models installed. Pull a model to get started.</p>';
      return;
    }
    
    let html = '<div class="list-group">';
    data.models.forEach(model => {
      html += `
        <div class="list-group-item d-flex justify-content-between align-items-center">
          <div>
            <strong>${model.name}</strong>
            <br>
            <small class="text-muted">${formatBytes(model.size)}</small>
          </div>
          <div>
            <button class="btn btn-sm btn-primary" onclick="registerOllamaModel('${model.name}')">
              <i class="bi bi-plus-circle"></i> Register
            </button>
          </div>
        </div>
      `;
    });
    html += '</div>';
    container.innerHTML = html;
  } catch (error) {
    console.error("Error loading Ollama models:", error);
  }
}

async function loadRegisteredModels() {
  try {
    const response = await fetch("/api/models");
    const data = await response.json();
    
    // Group by provider
    const byProvider = {};
    data.models.forEach(model => {
      if (!byProvider[model.provider]) {
        byProvider[model.provider] = [];
      }
      byProvider[model.provider].push(model);
    });
    
    // Update each tab
    updateModelList("cloud", byProvider["openai"] || byProvider["anthropic"] || byProvider["azure"] || []);
    updateModelList("hf", byProvider["hf"] || []);
    updateModelList("classic", byProvider["classic"] || []);
  } catch (error) {
    console.error("Error loading registered models:", error);
  }
}

function updateModelList(provider, models) {
  const container = document.getElementById(`${provider}ModelsList`);
  if (models.length === 0) {
    container.innerHTML = '<p class="text-muted">No models registered. Add a model to get started.</p>';
    return;
  }
  
  let html = '<div class="list-group">';
  models.forEach(model => {
    html += `
      <div class="list-group-item d-flex justify-content-between align-items-center">
        <div>
          <strong>${model.display_name}</strong>
          <br>
          <small class="text-muted">${model.id}</small>
        </div>
        <button class="btn btn-sm btn-danger" onclick="removeModel('${model.id}')">
          <i class="bi bi-trash"></i> Remove
        </button>
      </div>
    `;
  });
  html += '</div>';
  container.innerHTML = html;
}

async function pullOllamaModel() {
  const modelName = document.getElementById("ollamaModelName").value;
  if (!modelName) {
    alert("Please enter a model name");
    return;
  }
  
  const progressDiv = document.getElementById("pullProgress");
  const progressBar = progressDiv.querySelector(".progress-bar");
  progressDiv.style.display = "block";
  progressBar.style.width = "0%";
  
  try {
    const response = await fetch("/api/models/ollama/pull", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: modelName }),
    });
    
    const data = await response.json();
    if (data.success) {
      progressBar.style.width = "100%";
      
      // Auto-register the model after pulling
      try {
        const registerResponse = await fetch("/api/models/ollama/register", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name: modelName }),
        });
        const registerData = await registerResponse.json();
        if (registerData.adapter) {
          alert(`Model "${modelName}" pulled and registered successfully!`);
        } else {
          alert(`Model "${modelName}" pulled successfully! Please register it manually.`);
        }
      } catch (regError) {
        alert(`Model "${modelName}" pulled successfully! Please register it manually.`);
      }
      
      bootstrap.Modal.getInstance(document.getElementById("pullOllamaModal")).hide();
      document.getElementById("ollamaModelName").value = "";
      loadOllamaModels();
      loadRegisteredModels();
    } else {
      alert("Error: " + (data.error || "Unknown error"));
    }
  } catch (error) {
    alert("Error pulling model: " + error.message);
  } finally {
    progressDiv.style.display = "none";
  }
}

async function registerOllamaModel(modelName) {
  try {
    const response = await fetch("/api/models/ollama/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: modelName }),
    });
    
    const data = await response.json();
    if (data.adapter) {
      alert("Model registered successfully!");
      loadRegisteredModels();
    } else {
      alert("Error registering model");
    }
  } catch (error) {
    alert("Error: " + error.message);
  }
}

async function addCloudModel() {
  const provider = document.getElementById("cloudProvider").value;
  const modelName = document.getElementById("cloudModelName").value;
  const apiKey = document.getElementById("cloudApiKey").value;
  const apiBase = document.getElementById("cloudApiBase").value;
  
  try {
    const response = await fetch("/api/models/llm/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        provider: provider,
        model_name: modelName,
        api_key: apiKey,
        api_base: apiBase || null,
      }),
    });
    
    const data = await response.json();
    if (data.adapter) {
      alert("Model added successfully!");
      bootstrap.Modal.getInstance(document.getElementById("addCloudModal")).hide();
      document.getElementById("addCloudForm").reset();
      loadRegisteredModels();
    } else {
      alert("Error adding model");
    }
  } catch (error) {
    alert("Error: " + error.message);
  }
}

async function addHFModel() {
  const modelId = document.getElementById("hfModelId").value;
  const task = document.getElementById("hfTask").value;
  const cacheDir = document.getElementById("hfCacheDir").value;
  
  try {
    const response = await fetch("/api/models/hf/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model_id: modelId,
        task: task,
        cache_dir: cacheDir || null,
      }),
    });
    
    const data = await response.json();
    if (data.adapter) {
      alert("Model added successfully!");
      bootstrap.Modal.getInstance(document.getElementById("addHFModal")).hide();
      document.getElementById("addHFForm").reset();
      loadRegisteredModels();
    } else {
      alert("Error adding model");
    }
  } catch (error) {
    alert("Error: " + error.message);
  }
}

async function addClassicModel() {
  const modelPath = document.getElementById("classicModelPath").value;
  const modelType = document.getElementById("classicModelType").value;
  
  try {
    const response = await fetch("/api/models/classic/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model_path: modelPath,
        model_type: modelType,
      }),
    });
    
    const data = await response.json();
    if (data.adapter) {
      alert("Model added successfully!");
      bootstrap.Modal.getInstance(document.getElementById("addClassicModal")).hide();
      document.getElementById("addClassicForm").reset();
      loadRegisteredModels();
    } else {
      alert("Error adding model");
    }
  } catch (error) {
    alert("Error: " + error.message);
  }
}

async function removeModel(adapterId) {
  if (!confirm("Are you sure you want to remove this model?")) {
    return;
  }
  
  try {
    const response = await fetch(`/api/models/${adapterId}`, {
      method: "DELETE",
    });
    
    const data = await response.json();
    if (data.success) {
      alert("Model removed successfully!");
      loadRegisteredModels();
    } else {
      alert("Error removing model");
    }
  } catch (error) {
    alert("Error: " + error.message);
  }
}

function formatBytes(bytes) {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
}

