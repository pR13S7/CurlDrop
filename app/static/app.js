let MAX_SIZE = 200 * 1024 * 1024;

fetch('/api/config').then(r => r.json()).then(cfg => {
  MAX_SIZE = cfg.max_file_size;
  document.getElementById('ttl-hours').textContent = cfg.ttl_hours;
}).catch(() => {
  document.getElementById('ttl-hours').textContent = '24';
});

const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const fileInfo = document.getElementById('file-info');
const fileName = document.getElementById('file-name');
const fileSize = document.getElementById('file-size');
const uploadBtn = document.getElementById('upload-btn');
const progressContainer = document.getElementById('progress-container');
const progressBar = document.getElementById('progress-bar');
const progressText = document.getElementById('progress-text');
const errorMsg = document.getElementById('error-msg');
const uploadSection = document.getElementById('upload-section');
const successSection = document.getElementById('success-section');
const resetBtn = document.getElementById('reset-btn');

let selectedFile = null;

function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function showError(msg) {
  errorMsg.textContent = msg;
  errorMsg.classList.remove('hidden');
}

function hideError() {
  errorMsg.classList.add('hidden');
}

function selectFile(file) {
  hideError();
  if (file.size > MAX_SIZE) {
    showError('File is too large. Maximum size is 200 MB.');
    return;
  }
  selectedFile = file;
  fileName.textContent = file.name;
  fileSize.textContent = formatSize(file.size);
  fileInfo.classList.remove('hidden');
  progressContainer.classList.add('hidden');
  uploadBtn.disabled = false;
  uploadBtn.textContent = 'Upload';
}

dropZone.addEventListener('click', () => fileInput.click());

dropZone.addEventListener('dragover', (e) => {
  e.preventDefault();
  dropZone.classList.add('drop-active');
});

dropZone.addEventListener('dragleave', () => {
  dropZone.classList.remove('drop-active');
});

dropZone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropZone.classList.remove('drop-active');
  if (e.dataTransfer.files.length) selectFile(e.dataTransfer.files[0]);
});

fileInput.addEventListener('change', () => {
  if (fileInput.files.length) selectFile(fileInput.files[0]);
});

uploadBtn.addEventListener('click', () => {
  if (!selectedFile) return;
  hideError();
  uploadBtn.disabled = true;
  uploadBtn.textContent = 'Uploading...';
  progressContainer.classList.remove('hidden');

  const formData = new FormData();
  formData.append('file', selectedFile);

  const xhr = new XMLHttpRequest();
  xhr.open('POST', '/api/upload');

  xhr.upload.addEventListener('progress', (e) => {
    if (e.lengthComputable) {
      const pct = Math.round((e.loaded / e.total) * 100);
      progressBar.style.width = pct + '%';
      progressText.textContent = pct + '%';
    }
  });

  xhr.addEventListener('load', () => {
    if (xhr.status === 200) {
      const data = JSON.parse(xhr.responseText);
      showSuccess(data);
    } else {
      let msg = 'Upload failed.';
      try { msg = JSON.parse(xhr.responseText).detail; } catch {}
      showError(msg);
      uploadBtn.disabled = false;
      uploadBtn.textContent = 'Upload';
    }
  });

  xhr.addEventListener('error', () => {
    showError('Network error. Please try again.');
    uploadBtn.disabled = false;
    uploadBtn.textContent = 'Upload';
  });

  xhr.send(formData);
});

function showSuccess(data) {
  uploadSection.classList.add('hidden');
  successSection.classList.remove('hidden');

  document.getElementById('result-filename').textContent = data.filename;
  document.getElementById('result-size').textContent = formatSize(data.size);

  const expires = new Date(data.expires_at);
  const diff = expires - new Date();
  const hours = Math.floor(diff / 3600000);
  const mins = Math.floor((diff % 3600000) / 60000);
  document.getElementById('result-expires').textContent = `in ${hours}h ${mins}m`;

  document.getElementById('result-url').value = data.download_url;
  document.getElementById('result-curl').value = data.curl_command;
  document.getElementById('result-wget').value = data.wget_command;
}

function copyText(inputId) {
  const input = document.getElementById(inputId);
  const text = input.value;
  const btn = input.nextElementSibling;

  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard.writeText(text);
  } else {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
  }

  btn.textContent = 'Copied!';
  setTimeout(() => { btn.textContent = 'Copy'; }, 1500);
}

resetBtn.addEventListener('click', () => {
  successSection.classList.add('hidden');
  uploadSection.classList.remove('hidden');
  fileInfo.classList.add('hidden');
  progressContainer.classList.add('hidden');
  progressBar.style.width = '0%';
  progressText.textContent = '0%';
  selectedFile = null;
  fileInput.value = '';
});
