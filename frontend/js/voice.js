let recognition = null;
let isRecording = false;

function initVoice() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        showToast('Speech Recognition not supported in this browser.', 'error');
        return;
    }

    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = 'en-US'; // Can be changed based on settings

    recognition.onstart = () => {
        isRecording = true;
        updateVoiceUI(true);
        document.getElementById('voiceStatus').textContent = 'Listening... Speak now.';
        document.getElementById('voiceTranscript').textContent = '';
        document.getElementById('voiceResponse').textContent = '...';
        document.getElementById('voiceIntentBar').style.display = 'none';
    };

    recognition.onresult = (event) => {
        let interimTranscript = '';
        let finalTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; ++i) {
            if (event.results[i].isFinal) {
                finalTranscript += event.results[i][0].transcript;
            } else {
                interimTranscript += event.results[i][0].transcript;
            }
        }

        const displayTranscript = finalTranscript || interimTranscript;
        document.getElementById('voiceTranscript').textContent = displayTranscript;

        if (finalTranscript) {
            processCommand(finalTranscript);
        }
    };

    recognition.onerror = (event) => {
        console.error('Speech recognition error', event.error);
        isRecording = false;
        updateVoiceUI(false);
        document.getElementById('voiceStatus').textContent = 'Error: ' + event.error;
        showToast('Voice recognition error: ' + event.error, 'error');
    };

    recognition.onend = () => {
        isRecording = false;
        updateVoiceUI(false);
        if (document.getElementById('voiceStatus').textContent === 'Listening... Speak now.') {
            document.getElementById('voiceStatus').textContent = 'Processing...';
        }
    };

    // Attach to UI elements
    const orb = document.getElementById('voiceOrb');
    if (orb) orb.addEventListener('click', toggleRecording);

    const fabTopbar = document.getElementById('voiceFabTopbar');
    if (fabTopbar) fabTopbar.addEventListener('click', () => {
        navigateTo('voice');
        toggleRecording();
    });

    const fabFixed = document.getElementById('voiceFabFixed');
    if (fabFixed) fabFixed.addEventListener('click', () => {
        navigateTo('voice');
        toggleRecording();
    });

    const manualBtn = document.getElementById('voiceTextSendBtn');
    const manualInput = document.getElementById('voiceTextInput');
    
    if (manualBtn && manualInput) {
        manualBtn.addEventListener('click', () => {
            const text = manualInput.value.trim();
            if (text) {
                document.getElementById('voiceTranscript').textContent = text;
                processCommand(text);
                manualInput.value = '';
            }
        });
        manualInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') manualBtn.click();
        });
    }
}

function toggleRecording() {
    if (!recognition) return;
    
    if (isRecording) {
        recognition.stop();
    } else {
        recognition.start();
    }
}

function updateVoiceUI(recording) {
    const orb = document.getElementById('voiceOrb');
    const fabTopbar = document.getElementById('voiceFabTopbar');
    const fabFixed = document.getElementById('voiceFabFixed');
    
    if (recording) {
        if(orb) orb.classList.add('listening');
        if(fabTopbar) fabTopbar.classList.add('recording');
        if(fabFixed) fabFixed.classList.add('recording');
    } else {
        if(orb) orb.classList.remove('listening');
        if(fabTopbar) fabTopbar.classList.remove('recording');
        if(fabFixed) fabFixed.classList.remove('recording');
    }
}

async function processCommand(text) {
    document.getElementById('voiceStatus').textContent = 'Processing command...';
    document.getElementById('voiceResponse').textContent = 'Thinking...';
    
    const res = await api.processVoice(text);
    
    if (res.ok) {
        const d = res.data;
        document.getElementById('voiceStatus').textContent = 'Command processed';
        document.getElementById('voiceResponse').textContent = d.response_text;
        
        document.getElementById('voiceIntentBar').style.display = 'flex';
        document.getElementById('vib-intent').textContent = d.detected_intent;
        document.getElementById('vib-lang').textContent = d.language.toUpperCase();
        document.getElementById('vib-conf').textContent = (d.confidence * 100).toFixed(0) + '%';
        
        showToast(`Intent: ${d.detected_intent}`, 'success');
        
        // Execute UI Action based on intent
        executeIntentAction(d.detected_intent, d.entities);
        
        // Refresh history
        loadVoiceHistory();
    } else {
        document.getElementById('voiceStatus').textContent = 'Failed';
        document.getElementById('voiceResponse').textContent = res.message;
        showToast(res.message, 'error');
    }
}

function executeIntentAction(intent, entities) {
    switch (intent) {
        case 'upload':
            navigateTo('upload');
            if (entities.category) {
                const catSelect = document.getElementById('uploadCategory');
                if (catSelect) {
                    for (let i=0; i<catSelect.options.length; i++) {
                        if (catSelect.options[i].value.toLowerCase() === entities.category.toLowerCase()) {
                            catSelect.selectedIndex = i;
                            break;
                        }
                    }
                }
            }
            break;
            
        case 'search':
        case 'filter':
            navigateTo('media');
            if (entities.file_type) {
                const tSelect = document.getElementById('filterType');
                if (tSelect) tSelect.value = entities.file_type;
            }
            if (entities.category) {
                const cSelect = document.getElementById('filterCategory');
                if (cSelect) {
                    // Title case
                    const cat = entities.category.charAt(0).toUpperCase() + entities.category.slice(1);
                    cSelect.value = cat;
                }
            }
            // Trigger search
            const sBtn = document.getElementById('mediaSearchBtn');
            if (sBtn) sBtn.click();
            break;
            
        case 'analytics':
            navigateTo('analytics');
            break;
            
        case 'schedule':
            navigateTo('schedule');
            break;
    }
}

async function loadVoiceCommandsRef() {
    const res = await api.getVoiceCommands();
    if (res.ok) {
        const grid = document.getElementById('commandsGrid');
        if (!grid) return;
        
        grid.innerHTML = '';
        res.data.forEach(cmd => {
            const card = document.createElement('div');
            card.className = 'cmd-card';
            card.innerHTML = `
                <div class="cmd-intent">${cmd.intent}</div>
                ${cmd.examples.map(ex => `<div class="cmd-ex">"${ex}"</div>`).join('')}
                <div class="cmd-kw">Keywords: ${cmd.keywords.join(', ')}</div>
            `;
            grid.appendChild(card);
        });
    }
}

async function loadVoiceHistory() {
    const res = await api.getVoiceHistory(5);
    if (res.ok) {
        const list = document.getElementById('voiceHistoryList');
        if (!list) return;
        
        if (res.data.length === 0) {
            list.innerHTML = '<div class="vh-item">No recent commands.</div>';
            return;
        }
        
        list.innerHTML = '';
        res.data.forEach(h => {
            const item = document.createElement('div');
            item.className = 'vh-item';
            item.style.borderLeftColor = h.success ? 'var(--success)' : 'var(--danger)';
            item.innerHTML = `
                <div class="vh-text">"${h.text}"</div>
                <div class="vh-meta">
                    <span>Intent: ${h.intent}</span>
                    <span>${h.executed_at.split(' ')[1]}</span>
                </div>
            `;
            list.appendChild(item);
        });
    }
}
