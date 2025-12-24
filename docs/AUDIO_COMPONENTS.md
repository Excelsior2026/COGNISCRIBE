# CogniScribe In-App Audio Components

Goal: ship studio-grade recording without a second app, using best-of-breed open-source building blocks.

## Recommended Stack (Phase 1-2)
- Capture: `cpal` (Rust, cross-platform input device capture)
- Encoding: `hound` (WAV writer, zero external deps)
- DSP primitives: `dasp` or lightweight in-house filters (EQ, HPF, limiter)
- Noise suppression: RNNoise (C, BSD-style) via Rust bindings
- Echo cancellation / AGC: WebRTC Audio Processing Module (APM, BSD)

## Component Shortlist

### Capture / Device IO
- `cpal` (Rust, Apache-2.0/MIT)  
  Cross-platform capture with low-level access to device configs.

### Noise Suppression
- RNNoise (C, BSD-style)  
  High-quality noise suppression used widely in VOIP and streaming.

### Echo Cancellation + AGC + NS
- WebRTC APM (C++, BSD)  
  Industry standard for AEC/AGC/NS. Requires 10 ms frames, usually 48 kHz.

### DSP Building Blocks
- `dasp` (Rust, Apache-2.0/MIT)  
  DSP primitives: filters, resampling, mixing.
- `rubato` (Rust, MIT)  
  High-quality resampling (if input sample rates vary).

### Loudness / Metering
- `ebur128` (Rust, MIT)  
  Integrated loudness metering for consistent output levels.

### Decoding (Optional)
- `symphonia` (Rust, MPL-2.0)  
  Decoder if we want to process user-provided audio in-app.

## Notes
- RNNoise and WebRTC APM are the primary targets for “studio” quality.
- APM expects fixed frame sizes (10 ms) and often 48 kHz; we may resample
  upstream to maintain consistent processing quality.
- Phase 1 focuses on clean, stable capture + WAV output so the backend
  pipeline remains reliable while we iterate on DSP.
