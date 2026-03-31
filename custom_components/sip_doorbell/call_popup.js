/**
 * SIP Doorbell Call Popup with WebRTC Support
 * 
 * Автоматически открывает карточку звонка при входящем вызове.
 * Поддерживает WebRTC для аудио-звонков.
 * Установите как "Dashboard Card" или добавьте в resources.
 */

class SIPDoorbellCallPopup extends HTMLElement {
    constructor() {
        super();
        this._hass = null;
        this._config = null;
        this._activeCall = null;
        this._dialog = null;
        this._webrtcClient = null;
        this._remoteAudio = null;
        this._localStream = null;
        this._isMuted = false;
        this._isConnected = false;
    }

    setConfig(config) {
        this._config = {
            title: '🔔 Входящий звонок',
            auto_open: true,
            auto_close: false,
            timeout: 30,
            // Позиция окна: 'center', 'top', 'bottom-right', 'bottom-left', 'top-right', 'top-left'
            position: 'center',
            // Тема: 'light', 'dark', 'auto'
            theme: 'auto',
            // Camera entity для показа видео
            camera_entity: null,
            // Включить WebRTC аудио
            enable_webrtc: true,
            // Показывать ли аудио индикатор
            show_audio_indicator: true,
            // Кастомные кнопки действий
            custom_actions: [],
            // Звуковое уведомление
            play_sound: true,
            sound_url: '/local/sounds/doorbell.mp3',
            // Цвета кнопок (CSS цвета)
            colors: {
                answer: '#4caf50',
                decline: '#f44336',
                dtmf: '#2196f3',
                mute: '#ff9800'
            },
            // Размеры окна
            width: '400px',
            height: 'auto',
            ...config
        };
    }

    set hass(hass) {
        this._hass = hass;
        
        // Подписка на события SIP Doorbell
        if (!this._subscription) {
            this._subscribeToCalls();
        }
    }

    async _subscribeToCalls() {
        try {
            this._subscription = await this._hass.connection.subscribeMessage(
                (message) => this._handleCallEvent(message),
                {
                    type: 'sip_doorbell/subscribe_calls',
                }
            );
        } catch (err) {
            console.error('Failed to subscribe to SIP calls:', err);
        }
    }

    _handleCallEvent(message) {
        const event = message.event;
        
        if (event.event_type === 'sip_doorbell_incoming_call') {
            this._showCallPopup(event.data);
        } else if (event.event_type === 'sip_doorbell_call_ended') {
            this._endWebRTCCall();
            this._closeCallPopup();
        }
    }

    _getTheme() {
        if (this._config.theme === 'auto') {
            // Определяем тему Home Assistant
            const hass = this._hass;
            if (hass && hass.themes && hass.themes.darkMode) {
                return 'dark';
            }
            return 'light';
        }
        return this._config.theme;
    }

    _getPositionStyles() {
        const positions = {
            'center': 'align-items: center; justify-content: center;',
            'top': 'align-items: flex-start; justify-content: center; padding-top: 50px;',
            'bottom-right': 'align-items: flex-end; justify-content: flex-end; padding: 20px;',
            'bottom-left': 'align-items: flex-end; justify-content: flex-start; padding: 20px;',
            'top-right': 'align-items: flex-start; justify-content: flex-end; padding: 20px;',
            'top-left': 'align-items: flex-start; justify-content: flex-start; padding: 20px;'
        };
        return positions[this._config.position] || positions['center'];
    }

    _playNotificationSound() {
        if (!this._config.play_sound) return;
        
        try {
            const audio = new Audio(this._config.sound_url);
            audio.volume = 0.7;
            audio.play().catch(e => {
                console.warn('Failed to play notification sound:', e);
            });
        } catch (e) {
            console.warn('Error playing sound:', e);
        }
    }

    _sendVibration() {
        // Вибрация на мобильных устройствах
        if (navigator.vibrate) {
            navigator.vibrate([200, 100, 200, 100, 400]);
        }
    }

    /**
     * Initialize WebRTC client if available
     */
    async _initWebRTC(extension) {
        if (!this._config.enable_webrtc) return false;
        
        // Check if SIPWebRTCClient is available
        if (typeof SIPWebRTCClient === 'undefined') {
            console.warn('SIPWebRTCClient not loaded. Please add webrtc-client.js to your resources.');
            return false;
        }

        try {
            this._webrtcClient = new SIPWebRTCClient({
                extension: extension,
                hass: this._hass,
                onRemoteStream: (stream) => {
                    this._handleRemoteStream(stream);
                },
                onLocalStream: (stream) => {
                    this._localStream = stream;
                },
                onConnectionStateChange: (state) => {
                    this._updateConnectionState(state);
                },
                onError: (error) => {
                    console.error('WebRTC error:', error);
                    this._showNotification('WebRTC Error: ' + error, 'error');
                }
            });

            return true;
        } catch (error) {
            console.error('Failed to initialize WebRTC:', error);
            return false;
        }
    }

    /**
     * Handle incoming audio stream
     */
    _handleRemoteStream(stream) {
        if (!this._remoteAudio) return;

        this._remoteAudio.srcObject = stream;
        this._remoteAudio.play().catch(e => {
            console.warn('Auto-play prevented:', e);
            // Show manual play button if needed
        });

        this._isConnected = true;
        this._updateAudioIndicator(true);
    }

    /**
     * Update connection state UI
     */
    _updateConnectionState(state) {
        const statusEl = this._dialog?.querySelector('.connection-status');
        if (!statusEl) return;

        const stateLabels = {
            'connecting': 'Подключение...',
            'connected': 'Соединено',
            'disconnected': 'Отключено',
            'failed': 'Ошибка соединения',
            'closed': 'Закрыто'
        };

        statusEl.textContent = stateLabels[state] || state;
        statusEl.className = 'connection-status status-' + state;

        if (state === 'connected') {
            this._isConnected = true;
        } else if (state === 'disconnected' || state === 'failed' || state === 'closed') {
            this._isConnected = false;
        }
    }

    /**
     * Start WebRTC call
     */
    async _startWebRTCCall() {
        if (!this._webrtcClient) return false;

        try {
            const success = await this._webrtcClient.startCall();
            return success;
        } catch (error) {
            console.error('Failed to start WebRTC call:', error);
            return false;
        }
    }

    /**
     * End WebRTC call
     */
    async _endWebRTCCall() {
        if (this._webrtcClient) {
            await this._webrtcClient.stopCall();
            this._webrtcClient = null;
        }

        // Clean up audio element
        if (this._remoteAudio) {
            this._remoteAudio.srcObject = null;
            this._remoteAudio = null;
        }

        // Clean up local stream
        if (this._localStream) {
            this._localStream.getTracks().forEach(track => track.stop());
            this._localStream = null;
        }

        this._isConnected = false;
        this._isMuted = false;
    }

    /**
     * Toggle mute
     */
    _toggleMute() {
        if (!this._webrtcClient) return;

        this._isMuted = !this._isMuted;
        this._webrtcClient.setAudioEnabled(!this._isMuted);
        this._updateMuteButton();
    }

    /**
     * Update mute button state
     */
    _updateMuteButton() {
        const muteBtn = this._dialog?.querySelector('.mute-btn');
        if (!muteBtn) return;

        if (this._isMuted) {
            muteBtn.setAttribute('icon', 'mdi:microphone-off');
            muteBtn.style.setProperty('--mdc-theme-primary', this._config.colors.decline);
        } else {
            muteBtn.setAttribute('icon', 'mdi:microphone');
            muteBtn.style.setProperty('--mdc-theme-primary', this._config.colors.mute);
        }
    }

    /**
     * Update audio indicator
     */
    _updateAudioIndicator(active) {
        const indicator = this._dialog?.querySelector('.audio-indicator');
        if (!indicator) return;

        if (active) {
            indicator.classList.add('active');
        } else {
            indicator.classList.remove('active');
        }
    }

    _showCallPopup(data) {
        if (this._dialog) {
            this._dialog.close();
        }

        const callerName = data.caller_name || 'Неизвестно';
        const callerNumber = data.caller_number || 'Неизвестно';
        const extension = data.extension || '';
        const theme = this._getTheme();

        // Создаём диалог
        this._dialog = document.createElement('ha-dialog');
        this._dialog.heading = this._config.title;
        this._dialog.scrimClickAction = 'close';
        this._dialog.escapeKeyAction = 'close';

        // Применяем стили позиционирования
        const dialogStyles = document.createElement('style');
        dialogStyles.textContent = `
            ha-dialog {
                --mdc-dialog-min-width: ${this._config.width};
                --mdc-dialog-max-width: ${this._config.width};
                --mdc-dialog-max-height: ${this._config.height};
                --ha-dialog-border-radius: 16px;
            }
            .mdc-dialog__container {
                ${this._getPositionStyles()}
            }
        `;
        this._dialog.appendChild(dialogStyles);

        const content = document.createElement('div');
        content.className = 'sip-call-popup';
        
        // Определяем тему (светлая/тёмная)
        const themeClass = theme === 'dark' ? 'theme-dark' : 'theme-light';
        content.classList.add(themeClass);

        // HTML для камеры (если указана)
        let cameraHtml = '';
        if (this._config.camera_entity) {
            cameraHtml = `
                <div class="camera-container">
                    <hui-image
                        .hass="${this._hass}"
                        .cameraImage="${this._config.camera_entity}"
                        .cameraView="live"
                        .width="100%"
                        .height="auto"
                    ></hui-image>
                </div>
            `;
        }

        // HTML для кастомных кнопок
        let customActionsHtml = '';
        if (this._config.custom_actions && this._config.custom_actions.length > 0) {
            const buttonsHtml = this._config.custom_actions.map((action, index) => `
                <mwc-button 
                    ${action.style || 'raised'}
                    class="custom-action-btn"
                    data-action-index="${index}"
                    icon="${action.icon || 'mdi:gesture-tap'}"
                >
                    ${action.name || 'Действие'}
                </mwc-button>
            `).join('');
            
            customActionsHtml = `
                <div class="custom-actions">
                    ${buttonsHtml}
                </div>
            `;
        }

        // WebRTC audio indicator
        const webrtcHtml = this._config.enable_webrtc ? `
            <div class="webrtc-controls" style="display: none;">
                <div class="connection-status">Подключение...</div>
                <div class="audio-indicator" style="display: ${this._config.show_audio_indicator ? 'block' : 'none'}">
                    <ha-icon icon="mdi:volume-high"></ha-icon>
                    <span>Аудио активно</span>
                </div>
                <audio id="remote-audio" autoplay playsinline></audio>
            </div>
        ` : '';

        content.innerHTML = `
            <style>
                .sip-call-popup {
                    padding: 0;
                    min-width: 300px;
                }
                .sip-call-popup.theme-dark {
                    --popup-bg: var(--card-background-color, #1c1c1c);
                    --text-color: var(--primary-text-color, #ffffff);
                }
                .sip-call-popup.theme-light {
                    --popup-bg: var(--card-background-color, #ffffff);
                    --text-color: var(--primary-text-color, #212121);
                }
                .camera-container {
                    width: 100%;
                    margin-bottom: 16px;
                    border-radius: 8px;
                    overflow: hidden;
                }
                .camera-container img,
                .camera-container hui-image {
                    width: 100%;
                    height: auto;
                    display: block;
                }
                .caller-info {
                    display: flex;
                    align-items: center;
                    padding: 16px;
                    gap: 16px;
                }
                .call-icon {
                    --mdc-icon-size: 48px;
                    color: var(--primary-color);
                }
                .caller-details {
                    flex: 1;
                }
                .caller-name {
                    font-size: 1.4em;
                    font-weight: 500;
                    color: var(--text-color);
                }
                .caller-number {
                    font-size: 1.1em;
                    color: var(--secondary-text-color);
                    margin-top: 4px;
                }
                .caller-extension {
                    font-size: 0.9em;
                    color: var(--disabled-text-color);
                    margin-top: 2px;
                }
                .webrtc-controls {
                    padding: 8px 16px;
                    background: var(--secondary-background-color);
                }
                .connection-status {
                    text-align: center;
                    font-size: 0.9em;
                    color: var(--secondary-text-color);
                    margin-bottom: 4px;
                }
                .connection-status.status-connected {
                    color: #4caf50;
                }
                .connection-status.status-connecting {
                    color: #ff9800;
                }
                .connection-status.status-failed,
                .connection-status.status-disconnected {
                    color: #f44336;
                }
                .audio-indicator {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 8px;
                    color: var(--secondary-text-color);
                    font-size: 0.85em;
                }
                .audio-indicator.active {
                    color: #4caf50;
                }
                .audio-indicator.active ha-icon {
                    animation: pulse 1.5s infinite;
                }
                @keyframes pulse {
                    0% { opacity: 1; }
                    50% { opacity: 0.5; }
                    100% { opacity: 1; }
                }
                .call-actions {
                    display: flex;
                    justify-content: center;
                    gap: 12px;
                    padding: 0 16px 16px;
                }
                .answer-btn {
                    --mdc-theme-primary: ${this._config.colors.answer};
                    flex: 1;
                }
                .decline-btn {
                    --mdc-theme-primary: ${this._config.colors.decline};
                    flex: 1;
                }
                .mute-btn {
                    --mdc-theme-primary: ${this._config.colors.mute};
                }
                .custom-actions {
                    display: flex;
                    flex-wrap: wrap;
                    justify-content: center;
                    gap: 8px;
                    padding: 0 16px 16px;
                }
                .dtmf-panel {
                    padding: 16px;
                    background: var(--secondary-background-color);
                    border-radius: 0 0 16px 16px;
                }
                .dtmf-panel p {
                    margin: 0 0 12px;
                    text-align: center;
                    color: var(--secondary-text-color);
                    font-size: 0.9em;
                }
                .dtmf-buttons {
                    display: grid;
                    grid-template-columns: repeat(3, 1fr);
                    gap: 8px;
                }
                .dtmf-buttons mwc-button {
                    --mdc-theme-primary: ${this._config.colors.dtmf};
                }
                .hangup-btn {
                    margin-top: 12px;
                    width: 100%;
                    --mdc-theme-primary: ${this._config.colors.decline};
                }
                .call-timer {
                    text-align: center;
                    font-size: 1.2em;
                    color: var(--primary-color);
                    padding: 8px;
                }
            </style>
            
            ${cameraHtml}
            
            <div class="caller-info">
                <ha-icon icon="mdi:phone-incoming" class="call-icon"></ha-icon>
                <div class="caller-details">
                    <div class="caller-name">${callerName}</div>
                    <div class="caller-number">${callerNumber}</div>
                    ${extension ? `<div class="caller-extension">Extension: ${extension}</div>` : ''}
                </div>
            </div>
            
            ${webrtcHtml}
            
            <div class="call-actions">
                <mwc-button 
                    raised 
                    class="answer-btn"
                    icon="mdi:phone"
                >
                    Ответить
                </mwc-button>
                <mwc-button 
                    outlined 
                    class="decline-btn"
                    icon="mdi:phone-hangup"
                >
                    Отклонить
                </mwc-button>
            </div>
            
            ${customActionsHtml}
            
            <div class="call-controls" style="display: none; padding: 0 16px 16px;">
                <div class="call-timer">00:00</div>
                <div style="display: flex; gap: 12px; justify-content: center;">
                    <mwc-button 
                        raised 
                        class="mute-btn"
                        icon="mdi:microphone"
                    >
                        Мute
                    </mwc-button>
                    <mwc-button 
                        raised 
                        class="hangup-btn"
                        icon="mdi:phone-hangup"
                    >
                        Завершить
                    </mwc-button>
                </div>
            </div>
            
            <div class="dtmf-panel" style="display: none;">
                <p>Отправить DTMF:</p>
                <div class="dtmf-buttons">
                    <mwc-button data-digit="1">1</mwc-button>
                    <mwc-button data-digit="2">2</mwc-button>
                    <mwc-button data-digit="3">3</mwc-button>
                    <mwc-button data-digit="4">4</mwc-button>
                    <mwc-button data-digit="5">5</mwc-button>
                    <mwc-button data-digit="6">6</mwc-button>
                    <mwc-button data-digit="7">7</mwc-button>
                    <mwc-button data-digit="8">8</mwc-button>
                    <mwc-button data-digit="9">9</mwc-button>
                    <mwc-button data-digit="*">*</mwc-button>
                    <mwc-button data-digit="0">0</mwc-button>
                    <mwc-button data-digit="#">#</mwc-button>
                </div>
            </div>
        `;

        this._dialog.appendChild(content);
        document.body.appendChild(this._dialog);

        // Initialize audio element reference
        if (this._config.enable_webrtc) {
            this._remoteAudio = content.querySelector('#remote-audio');
            // Initialize WebRTC
            this._initWebRTC(extension);
        }

        // Звук и вибрация
        this._playNotificationSound();
        this._sendVibration();

        // Обработчики кнопок
        const answerBtn = content.querySelector('.answer-btn');
        const declineBtn = content.querySelector('.decline-btn');
        const hangupBtn = content.querySelector('.call-controls .hangup-btn');
        const muteBtn = content.querySelector('.mute-btn');
        const dtmfButtons = content.querySelectorAll('.dtmf-buttons mwc-button');

        answerBtn.addEventListener('click', async () => {
            // Start WebRTC call if enabled
            if (this._config.enable_webrtc && this._webrtcClient) {
                content.querySelector('.webrtc-controls').style.display = 'block';
                const webrtcSuccess = await this._startWebRTCCall();
                if (!webrtcSuccess) {
                    console.warn('WebRTC failed, continuing without audio');
                }
            }

            // Answer via SIP
            this._hass.callService('sip_doorbell', 'answer');
            
            // Show call controls
            content.querySelector('.call-actions').style.display = 'none';
            content.querySelector('.call-controls').style.display = 'block';
            content.querySelector('.dtmf-panel').style.display = 'block';
            
            // Start call timer
            this._startCallTimer();
        });

        declineBtn.addEventListener('click', () => {
            this._hass.callService('sip_doorbell', 'hangup');
            this._endWebRTCCall();
            this._closeCallPopup();
        });

        if (hangupBtn) {
            hangupBtn.addEventListener('click', () => {
                this._hass.callService('sip_doorbell', 'hangup');
                this._endWebRTCCall();
                this._closeCallPopup();
            });
        }

        if (muteBtn) {
            muteBtn.addEventListener('click', () => {
                this._toggleMute();
            });
        }

        dtmfButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const digit = e.target.getAttribute('data-digit');
                this._hass.callService('sip_doorbell', 'send_dtmf', {
                    digits: digit,
                    duration: 250
                });
            });
        });

        // Обработчики кастомных кнопок
        if (this._config.custom_actions) {
            const customBtns = content.querySelectorAll('.custom-action-btn');
            customBtns.forEach((btn, index) => {
                btn.addEventListener('click', () => {
                    const action = this._config.custom_actions[index];
                    if (action) {
                        // Выполняем кастомное действие
                        if (action.service) {
                            this._hass.callService(
                                action.service.split('.')[0],
                                action.service.split('.')[1],
                                action.service_data || {}
                            );
                        }
                        if (action.dtmf_digit) {
                            this._hass.callService('sip_doorbell', 'send_dtmf', {
                                digits: action.dtmf_digit,
                                duration: action.duration || 250
                            });
                        }
                    }
                });
            });
        }

        this._dialog.show();
        this._activeCall = data;

        // Автозакрытие через timeout (только если не в разговоре)
        if (this._config.auto_close && this._config.timeout > 0) {
            this._closeTimeout = setTimeout(() => {
                if (!this._isConnected) {
                    this._endWebRTCCall();
                    this._closeCallPopup();
                }
            }, this._config.timeout * 1000);
        }
    }

    /**
     * Start call timer
     */
    _startCallTimer() {
        let seconds = 0;
        const timerEl = this._dialog?.querySelector('.call-timer');
        if (!timerEl) return;

        this._callTimer = setInterval(() => {
            seconds++;
            const mins = Math.floor(seconds / 60).toString().padStart(2, '0');
            const secs = (seconds % 60).toString().padStart(2, '0');
            timerEl.textContent = `${mins}:${secs}`;
        }, 1000);
    }

    _closeCallPopup() {
        if (this._closeTimeout) {
            clearTimeout(this._closeTimeout);
            this._closeTimeout = null;
        }

        if (this._callTimer) {
            clearInterval(this._callTimer);
            this._callTimer = null;
        }

        if (this._dialog) {
            this._dialog.close();
            this._dialog.remove();
            this._dialog = null;
        }
        
        this._activeCall = null;
        this._isConnected = false;
        this._isMuted = false;
    }

    /**
     * Show notification
     */
    _showNotification(message, type = 'info') {
        // Use Home Assistant's notification system if available
        if (this._hass && this._hass.callService) {
            this._hass.callService('persistent_notification', 'create', {
                title: 'SIP Doorbell',
                message: message,
                notification_id: `sip_doorbell_${Date.now()}`
            });
        }
    }

    getCardSize() {
        return 1;
    }
}

customElements.define('sip-doorbell-call-popup', SIPDoorbellCallPopup);

// Register as custom card for Home Assistant
window.customCards = window.customCards || [];
window.customCards.push({
    type: 'sip-doorbell-call-popup',
    name: 'SIP Doorbell Call Popup',
    description: 'Auto-popup card for incoming SIP calls with WebRTC support',
    preview: true,
    documentationURL: 'https://github.com/Miromani4/SIP-Phone-for-HA'
});

console.info('%c SIP Doorbell Call Popup %c WebRTC Enabled ', 'background: #03a9f4; color: white; border-radius: 3px; padding: 2px;', 'background: #4caf50; color: white; border-radius: 3px; padding: 2px;');
