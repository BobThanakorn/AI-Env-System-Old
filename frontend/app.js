const chat = document.getElementById("chat");
const chatContent = document.querySelector(".chat-content") || chat;
const input = document.getElementById("messageInput");
const sendButton = document.getElementById("sendButton");
const composer = document.getElementById("composer");
const sidebar = document.getElementById("sidebar");
const sidebarBackdrop = document.getElementById("sidebarBackdrop");
const toggleSidebarButton = document.getElementById("toggleSidebarButton");
const closeSidebarButton = document.getElementById("closeSidebarButton");
const serverStatus = document.getElementById("serverStatus");
const sessionInputTokens = document.getElementById("sessionInputTokens");
const sessionOutputTokens = document.getElementById("sessionOutputTokens");
const sessionTotalTokens = document.getElementById("sessionTotalTokens");
const lastRequestTokens = document.getElementById("lastRequestTokens");
const sessionFileInput = document.getElementById("sessionFileInput");
const attachFileButton = document.getElementById("attachFileButton");
const removeFileButton = document.getElementById("removeFileButton");
const attachmentBar = document.getElementById("attachmentBar");
const attachmentName = document.getElementById("attachmentName");
const attachmentSize = document.getElementById("attachmentSize");
const modeStatus = document.getElementById("modeStatus");
const modeChatButton = document.getElementById("modeChatButton");
const modeCoworkButton = document.getElementById("modeCoworkButton");
const topbarTitle = document.getElementById("topbarTitle");
const composerHint = document.getElementById("composerHint");
const workspaceMeta = document.getElementById("workspaceMeta");
const workspaceFileList = document.getElementById("workspaceFileList");

const SESSION_STORAGE_KEY = "tcc_session_id";
const MODE_STORAGE_KEY = "tcc_agent_mode";
const sessionId = localStorage.getItem(SESSION_STORAGE_KEY) || crypto.randomUUID();
localStorage.setItem(SESSION_STORAGE_KEY, sessionId);

const MAX_UPLOAD_BYTES = 100 * 1024 * 1024;
const MOBILE_BREAKPOINT = 900;
const TEXTAREA_MIN_HEIGHT = 44;

let agentMode = localStorage.getItem(MODE_STORAGE_KEY) || "chat";
let typingIndicator = null;
let isSending = false;
let activeCoworkPanel = null;

function getTextareaMaxHeight() {
  return Math.min(220, Math.floor(window.innerHeight * 0.35));
}

function setPrompt(text) {
  if (text.startsWith("cowork:")) {
    setAgentMode("cowork");
    text = text.slice("cowork:".length);
  }

  input.value = text;
  autoResizeTextarea();
  updateSendButtonState();
  input.focus();
  closeSidebar();
}

function setAgentMode(mode) {
  agentMode = mode === "cowork" ? "cowork" : "chat";
  localStorage.setItem(MODE_STORAGE_KEY, agentMode);

  modeChatButton.classList.toggle("active", agentMode === "chat");
  modeCoworkButton.classList.toggle("active", agentMode === "cowork");
  modeStatus.textContent = agentMode === "cowork" ? "Cowork" : "Chat";
  topbarTitle.textContent = agentMode === "cowork" ? "Cowork Task" : "Agent Chat";

  if (agentMode === "cowork") {
    input.placeholder = "Describe your goal — agent will plan and execute multiple steps...";
    composerHint.textContent =
      "Cowork mode: มอบหมายงานหลายขั้นตอน · agent จะแสดงความคืบหน้าแบบ real-time";
    sendButton.querySelector(".send-label").textContent = isSending ? "Working..." : "Run Task";
  } else {
    input.placeholder = "Ask the agent...";
    composerHint.textContent =
      "Enter ส่ง · Shift+Enter ขึ้นบรรทัดใหม่ · ลากไฟล์มาวางเพื่อแนบ";
    if (!isSending) {
      sendButton.querySelector(".send-label").textContent = "Send";
    }
  }
}

async function loadWorkspaceFiles() {
  try {
    const response = await fetch("/workspace/files");
    const data = await response.json();

    if (!response.ok) {
      workspaceMeta.textContent = "Unable to load workspace";
      return;
    }

    workspaceMeta.textContent = data.count + " file(s)";
    workspaceFileList.innerHTML = "";

    (data.files || []).slice(0, 40).forEach(function(file) {
      const item = document.createElement("li");
      const button = document.createElement("button");
      button.type = "button";
      button.className = "workspace-file-btn";
      button.textContent = file.path;
      button.title = file.path + " (" + formatFileSize(file.size_bytes || 0) + ")";
      button.addEventListener("click", function() {
        const prefix = agentMode === "cowork" ? "cowork:" : "";
        setPrompt(prefix + "อ่านไฟล์ " + file.path + " แล้วสรุปให้หน่อย");
      });
      item.appendChild(button);
      workspaceFileList.appendChild(item);
    });

    if ((data.files || []).length > 40) {
      const more = document.createElement("li");
      more.className = "workspace-more";
      more.textContent = "+" + (data.count - 40) + " more files";
      workspaceFileList.appendChild(more);
    }
  } catch (error) {
    workspaceMeta.textContent = "Workspace offline";
    console.error("Failed to load workspace files:", error);
  }
}

function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
  return (bytes / (1024 * 1024)).toFixed(1) + " MB";
}

function isMobileLayout() {
  return window.innerWidth <= MOBILE_BREAKPOINT;
}

function openSidebar() {
  document.body.classList.add("sidebar-open");
  sidebarBackdrop.hidden = false;
  toggleSidebarButton.setAttribute("aria-expanded", "true");
}

function closeSidebar() {
  document.body.classList.remove("sidebar-open");
  sidebarBackdrop.hidden = true;
  toggleSidebarButton.setAttribute("aria-expanded", "false");
}

function toggleSidebar() {
  if (document.body.classList.contains("sidebar-open")) {
    closeSidebar();
  } else {
    openSidebar();
  }
}

function autoResizeTextarea() {
  input.style.height = "0px";
  input.classList.remove("is-scrollable");

  const maxHeight = getTextareaMaxHeight();
  const scrollHeight = input.scrollHeight;
  const nextHeight = Math.min(
    Math.max(scrollHeight, TEXTAREA_MIN_HEIGHT),
    maxHeight
  );

  input.style.height = nextHeight + "px";

  if (scrollHeight > maxHeight) {
    input.classList.add("is-scrollable");
  }
}

function updateSendButtonState() {
  const hasText = input.value.trim().length > 0;
  sendButton.disabled = isSending || !hasText;
}

function scrollChatToBottom(behavior = "smooth") {
  chat.scrollTo({
    top: chat.scrollHeight,
    behavior,
  });
}

function updateTokenDisplay(usage) {
  if (!usage) return;

  const session = usage.session || {};
  const request = usage.request || {};

  sessionInputTokens.textContent = session.input_tokens ?? 0;
  sessionOutputTokens.textContent = session.output_tokens ?? 0;
  sessionTotalTokens.textContent = session.total_tokens ?? 0;
  lastRequestTokens.textContent = request.total_tokens ?? 0;
}

function updateUploadDisplay(fileInfo) {
  if (!fileInfo) {
    attachmentBar.hidden = true;
    attachmentName.textContent = "";
    attachmentSize.textContent = "";
    removeFileButton.hidden = true;
    composer.classList.remove("has-attachment");
    return;
  }

  attachmentBar.hidden = false;
  attachmentName.textContent = fileInfo.filename;
  attachmentSize.textContent = fileInfo.size_label || formatFileSize(fileInfo.size_bytes || 0);
  removeFileButton.hidden = false;
  composer.classList.add("has-attachment");
}

function showTypingIndicator() {
  if (typingIndicator) return;

  typingIndicator = document.createElement("div");
  typingIndicator.className = "message-row assistant typing-indicator message-enter";
  typingIndicator.innerHTML =
    '<div class="message-stack">' +
    '<div class="meta">Agent</div>' +
    '<div class="message-bubble">' +
    '<div class="typing-dots" aria-label="Agent is thinking">' +
    '<span></span><span></span><span></span>' +
    "</div></div></div>";

  chatContent.appendChild(typingIndicator);
  scrollChatToBottom();
}

function hideTypingIndicator() {
  if (!typingIndicator) return;
  typingIndicator.remove();
  typingIndicator = null;
}

async function loadSessionUpload() {
  try {
    const response = await fetch("/sessions/" + sessionId + "/upload");
    const data = await response.json();
    updateUploadDisplay(data.file || null);
  } catch (error) {
    console.error("Failed to load session upload:", error);
  }
}

async function checkServerHealth() {
  try {
    const response = await fetch("/health");
    if (!response.ok) throw new Error("offline");
    serverStatus.textContent = "Online";
    serverStatus.className = "status-online";
  } catch (error) {
    serverStatus.textContent = "Offline";
    serverStatus.className = "status-offline";
  }
}

async function uploadSessionFile(file) {
  if (!file) return;

  if (file.size > MAX_UPLOAD_BYTES) {
    addMessage("assistant", "Upload failed: file exceeds 100 MB limit.");
    return;
  }

  attachFileButton.disabled = true;
  attachFileButton.classList.add("loading");

  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch("/sessions/" + sessionId + "/upload", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();

    if (!response.ok) {
      const detail = data.detail || JSON.stringify(data);
      addMessage("assistant", "Upload failed: " + detail);
      return;
    }

    updateUploadDisplay(data.file || null);
  } catch (error) {
    addMessage("assistant", "Upload failed: " + error.message);
  } finally {
    attachFileButton.disabled = false;
    attachFileButton.classList.remove("loading");
    sessionFileInput.value = "";
  }
}

async function removeSessionFile() {
  removeFileButton.disabled = true;

  try {
    const response = await fetch("/sessions/" + sessionId + "/upload", {
      method: "DELETE",
    });

    const data = await response.json();

    if (!response.ok) {
      addMessage("assistant", "Remove failed: " + JSON.stringify(data));
      return;
    }

    updateUploadDisplay(null);
  } catch (error) {
    addMessage("assistant", "Remove failed: " + error.message);
  } finally {
    removeFileButton.disabled = false;
  }
}

function addMessage(role, content, raw = null) {
  const row = document.createElement("div");
  row.className = "message-row " + role + " message-enter";

  const stack = document.createElement("div");
  stack.className = "message-stack";

  const meta = document.createElement("div");
  meta.className = "meta";
  meta.textContent = role === "user" ? "You" : "Agent";

  const bubble = document.createElement("div");
  bubble.className = "message-bubble";

  const body = document.createElement("div");
  body.className = "message-body";
  body.textContent = content;

  bubble.appendChild(body);
  stack.appendChild(meta);
  stack.appendChild(bubble);

  if (raw && raw.pending_confirmation) {
    stack.appendChild(renderConfirmationPanel(raw.pending_confirmation));
  }

  if (raw && raw.run_canvas) {
    stack.appendChild(renderRunCanvas(raw.run_canvas));
    showRunCanvasPanel(raw.run_canvas);
  }

  if (raw && raw.steps && raw.steps.length > 0) {
    stack.appendChild(renderCoworkSteps(raw.steps));
  }

  if (raw && raw.usage) {
    const usageLine = document.createElement("div");
    usageLine.className = "message-usage";
    const requestUsage = raw.usage.request || {};
    usageLine.textContent =
      "Tokens — in: " + (requestUsage.input_tokens ?? 0) +
      ", out: " + (requestUsage.output_tokens ?? 0) +
      ", total: " + (requestUsage.total_tokens ?? 0);
    stack.appendChild(usageLine);
  }

  if (raw) {
    const details = document.createElement("details");
    const summary = document.createElement("summary");
    summary.textContent = "View agent details";

    const pre = document.createElement("pre");
    pre.textContent = JSON.stringify(raw, null, 2);

    details.appendChild(summary);
    details.appendChild(pre);
    stack.appendChild(details);
  }

  row.appendChild(stack);
  chatContent.appendChild(row);
  scrollChatToBottom();
}

function renderConfirmationPanel(pending) {
  const panel = document.createElement("div");
  panel.className = "confirmation-panel";

  const path = pending.args && pending.args.path ? pending.args.path : "unknown";
  const info = document.createElement("div");
  info.className = "confirmation-info";
  info.textContent = "รอยืนยันการลบ: " + path;
  panel.appendChild(info);

  const actions = document.createElement("div");
  actions.className = "confirmation-actions";

  const confirmButton = document.createElement("button");
  confirmButton.type = "button";
  confirmButton.className = "confirm-btn";
  confirmButton.textContent = "ยืนยัน";
  confirmButton.addEventListener("click", function() {
    submitConfirmation(pending.confirmation_id, true);
  });

  const cancelButton = document.createElement("button");
  cancelButton.type = "button";
  cancelButton.className = "cancel-btn";
  cancelButton.textContent = "ยกเลิก";
  cancelButton.addEventListener("click", function() {
    submitConfirmation(pending.confirmation_id, false);
  });

  actions.appendChild(confirmButton);
  actions.appendChild(cancelButton);
  panel.appendChild(actions);

  return panel;
}

function renderCoworkSteps(steps) {
  const panel = document.createElement("div");
  panel.className = "cowork-steps-panel";

  const title = document.createElement("div");
  title.className = "cowork-steps-title";
  title.textContent = "Cowork steps (" + steps.length + ")";
  panel.appendChild(title);

  const list = document.createElement("ol");
  list.className = "cowork-steps-list";

  steps.forEach(function(step) {
    const item = document.createElement("li");
    item.className = "cowork-step-item";

    const action = step.plan && step.plan.action ? step.plan.action : "step";
    const reason = step.plan && step.plan.reason ? step.plan.reason : "";
    const summary = step.summary || "";

    const header = document.createElement("div");
    header.className = "cowork-step-header";
    header.textContent = "Step " + (step.step || "?") + ": " + action;
    item.appendChild(header);

    if (reason) {
      const reasonEl = document.createElement("div");
      reasonEl.className = "cowork-step-reason";
      reasonEl.textContent = reason;
      item.appendChild(reasonEl);
    }

    if (summary) {
      const summaryEl = document.createElement("div");
      summaryEl.className = "cowork-step-summary";
      summaryEl.textContent = summary;
      item.appendChild(summaryEl);
    }

    if (step.tool_result && step.tool_result.error) {
      const errorEl = document.createElement("div");
      errorEl.className = "cowork-step-error";
      errorEl.textContent = step.tool_result.error;
      item.appendChild(errorEl);
    }

    list.appendChild(item);
  });

  panel.appendChild(list);
  return panel;
}

function createCoworkProgressPanel(goal) {
  const row = document.createElement("div");
  row.className = "message-row assistant cowork-progress message-enter";

  const stack = document.createElement("div");
  stack.className = "message-stack";

  const meta = document.createElement("div");
  meta.className = "meta";
  meta.textContent = "Cowork";

  const bubble = document.createElement("div");
  bubble.className = "message-bubble cowork-progress-bubble";

  const goalEl = document.createElement("div");
  goalEl.className = "cowork-goal";
  goalEl.textContent = "Goal: " + goal;
  bubble.appendChild(goalEl);

  const statusEl = document.createElement("div");
  statusEl.className = "cowork-live-status";
  statusEl.textContent = "Starting task...";
  bubble.appendChild(statusEl);

  const stepsList = document.createElement("ol");
  stepsList.className = "cowork-live-steps";
  bubble.appendChild(stepsList);

  stack.appendChild(meta);
  stack.appendChild(bubble);
  row.appendChild(stack);
  chatContent.appendChild(row);
  scrollChatToBottom();

  return {
    row: row,
    statusEl: statusEl,
    stepsList: stepsList,
    steps: [],
  };
}

function updateCoworkProgress(panel, event) {
  if (!panel) return;

  if (event.type === "task_started") {
    panel.statusEl.textContent = "Planning steps (max " + (event.max_steps || 8) + ")...";
  }

  if (event.type === "step_planned") {
    panel.statusEl.textContent = "Step " + event.step + ": planning " + (event.plan.action || "...");
  }

  if (event.type === "step_executed") {
    panel.steps.push(event);
    panel.statusEl.textContent = "Completed step " + event.step + " of task";

    const item = document.createElement("li");
    item.className = "cowork-live-step done";
    item.textContent =
      (event.plan && event.plan.action ? event.plan.action : "step") +
      " — " +
      (event.summary || "done");
    panel.stepsList.appendChild(item);
    scrollChatToBottom();
  }

  if (event.type === "step_error") {
    const item = document.createElement("li");
    item.className = "cowork-live-step error";
    item.textContent = "Error at step " + event.step + ": " + event.error;
    panel.stepsList.appendChild(item);
  }

  if (event.type === "confirmation_required") {
    panel.statusEl.textContent = "Waiting for your confirmation...";
  }

  if (event.type === "task_completed") {
    panel.statusEl.textContent = "Task completed";
    panel.row.classList.add("cowork-done");
  }
}

function renderRunCanvas(canvas) {
  const panel = document.createElement("div");
  panel.className = "run-canvas-inline";

  const header = document.createElement("div");
  header.className = "run-canvas-header";
  header.textContent =
    "Python Run — " + (canvas.file || "script") +
    " · exit " + (canvas.exit_code ?? "?") +
    " · " + (canvas.duration_ms ?? 0) + " ms";
  panel.appendChild(header);

  if (canvas.source_preview) {
    const sourceBlock = document.createElement("pre");
    sourceBlock.className = "run-canvas-source";
    sourceBlock.textContent = canvas.source_preview;
    panel.appendChild(sourceBlock);
  }

  if (canvas.stdout) {
    const stdoutLabel = document.createElement("div");
    stdoutLabel.className = "run-canvas-label stdout-label";
    stdoutLabel.textContent = "stdout";
    panel.appendChild(stdoutLabel);

    const stdoutBlock = document.createElement("pre");
    stdoutBlock.className = "run-canvas-output stdout-output";
    stdoutBlock.textContent = canvas.stdout;
    panel.appendChild(stdoutBlock);
  }

  if (canvas.stderr) {
    const stderrLabel = document.createElement("div");
    stderrLabel.className = "run-canvas-label stderr-label";
    stderrLabel.textContent = "stderr";
    panel.appendChild(stderrLabel);

    const stderrBlock = document.createElement("pre");
    stderrBlock.className = "run-canvas-output stderr-output";
    stderrBlock.textContent = canvas.stderr;
    panel.appendChild(stderrBlock);
  }

  if (!canvas.stdout && !canvas.stderr) {
    const empty = document.createElement("div");
    empty.className = "run-canvas-empty";
    empty.textContent = canvas.timed_out
      ? "Execution timed out with no output."
      : "No output produced.";
    panel.appendChild(empty);
  }

  return panel;
}

function showRunCanvasPanel(canvas) {
  let panel = document.getElementById("runCanvasPanel");
  if (!panel) {
    panel = document.createElement("aside");
    panel.id = "runCanvasPanel";
    panel.className = "run-canvas-panel";
    panel.innerHTML =
      '<div class="run-canvas-panel-header">' +
      '<div class="run-canvas-panel-title">Python Output</div>' +
      '<button type="button" id="closeRunCanvasButton" class="icon-btn run-canvas-close" aria-label="Close output panel">×</button>' +
      "</div>" +
      '<div id="runCanvasPanelBody" class="run-canvas-panel-body"></div>';

    document.body.appendChild(panel);
    document.getElementById("closeRunCanvasButton").addEventListener("click", hideRunCanvasPanel);
  }

  const body = document.getElementById("runCanvasPanelBody");
  body.innerHTML = "";
  body.appendChild(renderRunCanvas(canvas));
  panel.classList.add("open");
  document.body.classList.add("run-canvas-open");
}

function hideRunCanvasPanel() {
  const panel = document.getElementById("runCanvasPanel");
  if (panel) {
    panel.classList.remove("open");
  }
  document.body.classList.remove("run-canvas-open");
}

async function submitConfirmation(confirmationId, confirmed) {
  if (isSending) return;

  isSending = true;
  sendButton.disabled = true;
  showTypingIndicator();

  const label = confirmed ? "ยืนยัน" : "ยกเลิก";
  addMessage("user", label);

  try {
    const response = await fetch("/agent/confirm", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        session_id: sessionId,
        confirmation_id: confirmationId,
        confirmed: confirmed,
      }),
    });

    const data = await response.json();
    handleAgentResponse(data);
  } catch (error) {
    addMessage("assistant", "Confirmation failed: " + error.message);
  } finally {
    hideTypingIndicator();
    isSending = false;
    updateSendButtonState();
  }
}

function handleAgentResponse(data) {
  updateTokenDisplay(data.usage);
  updateUploadDisplay(data.uploaded_file || null);
  addMessage("assistant", data.answer || "No answer returned.", data);
  loadWorkspaceFiles();
}

function clearSession() {
  // Keep session alive for Cowork-style continuity across reloads.
}

async function sendCoworkMessage(goal) {
  activeCoworkPanel = createCoworkProgressPanel(goal);

  let finalData = null;

  try {
    const response = await fetch("/agent/cowork", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        goal: goal,
        session_id: sessionId,
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      addMessage("assistant", "Cowork error: " + errorText);
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const chunk = await reader.read();
      if (chunk.done) break;

      buffer += decoder.decode(chunk.value, { stream: true });
      const parts = buffer.split("\n\n");
      buffer = parts.pop() || "";

      parts.forEach(function(part) {
        const line = part.trim();
        if (!line.startsWith("data: ")) return;

        const payload = line.slice(6);
        if (payload === "[DONE]") return;

        try {
          const event = JSON.parse(payload);
          updateCoworkProgress(activeCoworkPanel, event);

          if (event.type === "task_completed") {
            finalData = {
              type: "cowork_completed",
              answer: event.answer,
              steps: event.steps || activeCoworkPanel.steps.map(function(s) {
                return {
                  step: s.step,
                  plan: s.plan,
                  tool_result: s.tool_result,
                  summary: s.summary,
                };
              }),
              usage: {
                request: event.usage || {},
                session: {},
              },
              run_canvas: event.run_canvas || null,
            };
          }

          if (event.type === "confirmation_required") {
            finalData = {
              type: "confirmation_required",
              answer: event.answer,
              steps: event.steps || [],
              pending_confirmation: event.pending_confirmation,
              usage: {
                request: event.usage || {},
                session: {},
              },
            };
          }
        } catch (parseError) {
          console.error("SSE parse error:", parseError);
        }
      });
    }

    if (finalData) {
      const usageResponse = await fetch("/sessions/" + sessionId + "/usage");
      if (usageResponse.ok) {
        const usageData = await usageResponse.json();
        finalData.usage.session = usageData.usage || {};
        updateTokenDisplay(finalData.usage);
      }

      if (finalData.run_canvas) {
        showRunCanvasPanel(finalData.run_canvas);
      }

      if (finalData.pending_confirmation) {
        activeCoworkPanel.row.querySelector(".message-stack").appendChild(
          renderConfirmationPanel(finalData.pending_confirmation)
        );
      }

      if (finalData.steps && finalData.steps.length > 0) {
        activeCoworkPanel.row.querySelector(".message-stack").appendChild(
          renderCoworkSteps(finalData.steps)
        );
      }

      const answerBubble = document.createElement("div");
      answerBubble.className = "cowork-final-answer";
      answerBubble.textContent = finalData.answer || "Task finished.";
      activeCoworkPanel.row.querySelector(".cowork-progress-bubble").appendChild(answerBubble);

      const details = document.createElement("details");
      const summary = document.createElement("summary");
      summary.textContent = "View agent details";
      const pre = document.createElement("pre");
      pre.textContent = JSON.stringify(finalData, null, 2);
      details.appendChild(summary);
      details.appendChild(pre);
      activeCoworkPanel.row.querySelector(".message-stack").appendChild(details);
    } else {
      addMessage("assistant", "Cowork ended without a final result.");
    }

    loadWorkspaceFiles();
  } catch (error) {
    addMessage("assistant", "Cowork request failed: " + error.message);
  }
}

async function sendMessage() {
  const message = input.value.trim();

  if (!message || isSending) return;

  addMessage("user", message);
  input.value = "";
  autoResizeTextarea();
  updateSendButtonState();

  isSending = true;
  sendButton.classList.add("loading");
  const busyLabel = agentMode === "cowork" ? "Working..." : "Thinking...";
  sendButton.querySelector(".send-label").textContent = busyLabel;
  updateSendButtonState();
  showTypingIndicator();

  try {
    if (agentMode === "cowork") {
      hideTypingIndicator();
      await sendCoworkMessage(message);
      return;
    }

    const response = await fetch("/agent/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message,
        session_id: sessionId,
        mode: "chat",
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      addMessage("assistant", "Error: " + JSON.stringify(data));
      return;
    }

    handleAgentResponse(data);
  } catch (error) {
    addMessage("assistant", "Request failed: " + error.message);
  } finally {
    hideTypingIndicator();
    isSending = false;
    sendButton.classList.remove("loading");
    sendButton.querySelector(".send-label").textContent =
      agentMode === "cowork" ? "Run Task" : "Send";
    updateSendButtonState();
    input.focus();
  }
}

function initQuickActions() {
  document.querySelectorAll(".quick-actions button[data-prompt]").forEach(function(button) {
    button.addEventListener("click", function() {
      setPrompt(button.dataset.prompt || "");
    });
  });
}

function initSidebar() {
  toggleSidebarButton.addEventListener("click", toggleSidebar);
  closeSidebarButton.addEventListener("click", closeSidebar);
  sidebarBackdrop.addEventListener("click", closeSidebar);

  window.addEventListener("resize", function() {
    if (!isMobileLayout()) {
      closeSidebar();
    }
    autoResizeTextarea();
  });
}

function initComposer() {
  attachFileButton.addEventListener("click", function() {
    sessionFileInput.click();
  });

  sessionFileInput.addEventListener("change", function() {
    const file = sessionFileInput.files[0];
    if (file) {
      uploadSessionFile(file);
    }
  });

  removeFileButton.addEventListener("click", removeSessionFile);

  input.addEventListener("input", function() {
    autoResizeTextarea();
    updateSendButtonState();
  });

  input.addEventListener("keydown", function(event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  });

  sendButton.addEventListener("click", sendMessage);

  composer.addEventListener("dragover", function(event) {
    event.preventDefault();
    composer.classList.add("drag-over");
  });

  composer.addEventListener("dragleave", function(event) {
    if (!composer.contains(event.relatedTarget)) {
      composer.classList.remove("drag-over");
    }
  });

  composer.addEventListener("drop", function(event) {
    event.preventDefault();
    composer.classList.remove("drag-over");

    const file = event.dataTransfer && event.dataTransfer.files[0];
    if (file) {
      uploadSessionFile(file);
    }
  });
}

function initModeToggle() {
  modeChatButton.addEventListener("click", function() {
    setAgentMode("chat");
  });
  modeCoworkButton.addEventListener("click", function() {
    setAgentMode("cowork");
  });
  setAgentMode(agentMode);
}

function initApp() {
  initQuickActions();
  initSidebar();
  initComposer();
  initModeToggle();
  autoResizeTextarea();
  updateSendButtonState();
  checkServerHealth();
  loadSessionUpload();
  loadWorkspaceFiles();

  setInterval(checkServerHealth, 30000);
}

window.setPrompt = setPrompt;
initApp();
