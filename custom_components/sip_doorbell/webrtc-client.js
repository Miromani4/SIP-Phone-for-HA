/**
 * SIP Doorbell WebRTC Client
 * 
 * Handles WebRTC peer connections for audio/video calls in Home Assistant
 */

(function() {
    'use strict';

    // WebRTC configuration
    const RTC_CONFIG = {
        iceServers: [
            { urls: 'stun:stun.l.google.com:19302' },
            { urls: 'stun:stun1.l.google.com:19302' },
            { urls: 'stun:stun2.l.google.com:19302' },
        ],
        iceCandidatePoolSize: 10
    };

    class SIPWebRTCClient {
        constructor(options = {}) {
            this.extension = options.extension;
            this.hass = options.hass;
            this.callId = null;
            this.pc = null;
            this.localStream = null;
            this.remoteStream = null;
            this.iceCandidatesQueue = [];
            this.connectionState = 'disconnected';
            
            // Callbacks
            this.onRemoteStream = options.onRemoteStream || (() => {});
            this.onLocalStream = options.onLocalStream || (() => {});
            this.onConnectionStateChange = options.onConnectionStateChange || (() => {});
            this.onError = options.onError || (() => {});
        }

        /**
         * Generate unique call ID
         */
        _generateCallId() {
            return Date.now().toString(36) + Math.random().toString(36).substr(2);
        }

        /**
         * Initialize WebRTC peer connection
         */
        async _createPeerConnection() {
            try {
                this.pc = new RTCPeerConnection(RTC_CONFIG);
                
                // Handle connection state changes
                this.pc.onconnectionstatechange = () => {
                    this.connectionState = this.pc.connectionState;
                    this.onConnectionStateChange(this.connectionState);
                    
                    if (this.connectionState === 'failed') {
                        this.onError('Connection failed');
                    }
                };

                // Handle ICE candidates
                this.pc.onicecandidate = (event) => {
                    if (event.candidate) {
                        this._sendIceCandidate(event.candidate);
                    }
                };

                // Handle remote stream
                this.pc.ontrack = (event) => {
                    this.remoteStream = event.streams[0];
                    this.onRemoteStream(this.remoteStream);
                };

                // Add local stream
                await this._addLocalStream();

                return true;
            } catch (error) {
                this.onError(`Failed to create peer connection: ${error.message}`);
                return false;
            }
        }

        /**
         * Get local media stream (microphone/camera)
         */
        async _addLocalStream() {
            try {
                // Try video + audio first, fall back to audio only
                let constraints = {
                    audio: {
                        echoCancellation: true,
                        noiseSuppression: true,
                        sampleRate: 44100
                    },
                    video: false // Can be enabled later
                };

                this.localStream = await navigator.mediaDevices.getUserMedia(constraints);
                
                // Add tracks to peer connection
                this.localStream.getTracks().forEach(track => {
                    this.pc.addTrack(track, this.localStream);
                });

                this.onLocalStream(this.localStream);
                return true;
            } catch (error) {
                console.warn('Failed to get local stream:', error);
                return false;
            }
        }

        /**
         * Send ICE candidate to server
         */
        _sendIceCandidate(candidate) {
            if (!this.hass || !this.callId) return;

            this.hass.callWS({
                type: 'sip_doorbell/webrtc_ice_candidate',
                extension: this.extension,
                call_id: this.callId,
                candidate: {
                    candidate: candidate.candidate,
                    sdpMid: candidate.sdpMid,
                    sdpMLineIndex: candidate.sdpMLineIndex,
                }
            }).catch(err => {
                console.error('Failed to send ICE candidate:', err);
            });
        }

        /**
         * Start a call (initiate WebRTC connection)
         */
        async startCall() {
            if (!this.hass) {
                this.onError('Home Assistant connection not available');
                return false;
            }

            this.callId = this._generateCallId();

            // Create peer connection
            const created = await this._createPeerConnection();
            if (!created) return false;

            try {
                // Create offer
                const offer = await this.pc.createOffer();
                await this.pc.setLocalDescription(offer);

                // Send offer to server
                const response = await this.hass.callWS({
                    type: 'sip_doorbell/webrtc_offer',
                    extension: this.extension,
                    sdp: offer.sdp,
                    call_id: this.callId
                });

                // Set remote description (answer)
                await this.pc.setRemoteDescription(new RTCSessionDescription({
                    type: 'answer',
                    sdp: response.sdp
                }));

                // Process queued ICE candidates
                this._processQueuedCandidates();

                return true;
            } catch (error) {
                this.onError(`Failed to start call: ${error.message}`);
                await this.stopCall();
                return false;
            }
        }

        /**
         * Process queued ICE candidates
         */
        _processQueuedCandidates() {
            while (this.iceCandidatesQueue.length > 0) {
                const candidate = this.iceCandidatesQueue.shift();
                this.pc.addIceCandidate(new RTCIceCandidate(candidate))
                    .catch(err => console.error('Failed to add ICE candidate:', err));
            }
        }

        /**
         * Add ICE candidate from server
         */
        addIceCandidate(candidate) {
            if (!this.pc || !this.pc.remoteDescription) {
                this.iceCandidatesQueue.push(candidate);
                return;
            }

            this.pc.addIceCandidate(new RTCIceCandidate(candidate))
                .catch(err => console.error('Failed to add ICE candidate:', err));
        }

        /**
         * Stop the call and cleanup
         */
        async stopCall() {
            // Notify server
            if (this.hass && this.callId) {
                try {
                    await this.hass.callWS({
                        type: 'sip_doorbell/webrtc_close',
                        extension: this.extension,
                        call_id: this.callId
                    });
                } catch (err) {
                    console.error('Failed to close WebRTC on server:', err);
                }
            }

            // Stop all tracks
            if (this.localStream) {
                this.localStream.getTracks().forEach(track => track.stop());
                this.localStream = null;
            }

            // Close peer connection
            if (this.pc) {
                this.pc.close();
                this.pc = null;
            }

            this.callId = null;
            this.remoteStream = null;
            this.connectionState = 'disconnected';
            this.iceCandidatesQueue = [];
        }

        /**
         * Enable/disable local audio
         */
        setAudioEnabled(enabled) {
            if (this.localStream) {
                this.localStream.getAudioTracks().forEach(track => {
                    track.enabled = enabled;
                });
            }
        }

        /**
         * Enable/disable local video
         */
        setVideoEnabled(enabled) {
            if (this.localStream) {
                this.localStream.getVideoTracks().forEach(track => {
                    track.enabled = enabled;
                });
            }
        }

        /**
         * Get current connection state
         */
        getState() {
            return {
                connectionState: this.connectionState,
                callId: this.callId,
                signalingState: this.pc?.signalingState || 'closed',
                iceConnectionState: this.pc?.iceConnectionState || 'closed'
            };
        }
    }

    // Make available globally
    window.SIPWebRTCClient = SIPWebRTCClient;

    // Auto-initialize if Home Assistant is available
    if (window.hassConnection && window.hassConnection.then) {
        window.hassConnection.then(conn => {
            window.SIPWebRTCHass = conn;
        });
    }

})();