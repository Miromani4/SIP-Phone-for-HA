/**
 * SIP Doorbell Call Popup
 * 
 * Автоматически открывает карточку звонка при входящем вызове.
 * Установите как "Dashboard Card" или добавьте в resources.
 */

class SIPDoorbellCallPopup extends HTMLElement {
    constructor() {
        super();
        this._hass = null;
        this._config = null;
        this._activeCall = null;
        this._dialog = null;
    }

    setConfig(config) {
        this._config = {
            title: '🔔 Входящий звонок',
            auto_open: true,
            auto_close: true,
            timeout: 30,
            // Позиция окна: 'center', 'top', 'bottom-right', 'bottom-left', 'top-right', 'top-left'
            position: 'center',
            // Тема: 'light', 'dark', 'auto'
            theme: 'auto',
            // Camera entity для показа видео
            camera_entity: null,
            // Кастомные кнопки действий
            custom_actions: [],
            // Звуковое уведомление
            play_sound: true,
            sound_url: '/local/sounds/doorbell.mp3',
            // Цвета кнопок (CSS цвета)
            colors: {
                answer: '#4caf50',
                decline: '#f44336',
                dtmf: '#2196f3'
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
        // ИСПРАВЛЕНО: добавлена точка перед scrimClickAction
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
                .call-actions {
                    display: flex;
                    justify-content: center;
                    gap: 16px;
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
                <mwc-button 
                    outlined 
                    class="hangup-btn"
                    icon="mdi:phone-hangup"
                >
                    Завершить
                </mwc-button>
            </div>
        `;

        this._dialog.appendChild(content);
        document.body.appendChild(this._dialog);

        // Звук и вибрация
        this._playNotificationSound();
        this._sendVibration();

        // Обработчики кнопок
        const answerBtn = content.querySelector('.answer-btn');
        const declineBtn = content.querySelector('.decline-btn');
        const hangupBtn = content.querySelector('.hangup-btn');
        const dtmfButtons = content.querySelectorAll('.dtmf-buttons mwc-button');

        answerBtn.addEventListener('click', () => {
            this._hass.callService('sip_doorbell', 'answer');
            content.querySelector('.dtmf-panel').style.display = 'block';
            // Скрываем кнопки ответа/отклонения
            content.querySelector('.call-actions').style.display = 'none';
        });

        declineBtn.addEventListener('click', () => {
            this._hass.callService('sip_doorbell', 'hangup');
            this._closeCallPopup();
        });

        if (hangupBtn) {
            hangupBtn.addEventListener('click', () => {
                this._hass.callService('sip_doorbell', 'hangup');
                this._closeCallPopup();
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

        // Автозакрытие через timeout
        if (this._config.auto_close && this._config.timeout > 0) {
            this._closeTimeout = setTimeout(() => {
                this._closeCallPopup();
            }, this._config.timeout * 1000);
        }
    }

    _closeCallPopup() {
        if (this._dialog) {
            this._dialog.close();
            this._dialog.remove();
            this._dialog = null;
        }
        
        if (this._closeTimeout) {
            clearTimeout(this._closeTimeout);
            this._closeTimeout = null;
        }
        
        this._activeCall = null;
    }

    getCardSize() {
        return 1;
    }
}

customElements.define('sip-doorbell-call-popup', SIPDoorbellCallPopup);

console.info('%c SIP Doorbell Call Popup %c Loaded ', 'background: #03a9f4; color: white; border-radius: 3px; padding: 2px;', 'background: #4caf50; color: white; border-radius: 3px; padding: 2px;');