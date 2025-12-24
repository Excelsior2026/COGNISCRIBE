/// Lightweight in-app audio processing pipeline.
///
/// This is intentionally minimal to keep latency low. We'll expand it with
/// open-source components like RNNoise and WebRTC APM in later iterations.
pub struct AudioPipeline {
    limiter_threshold: f32,
}

impl AudioPipeline {
    pub fn new() -> Self {
        Self {
            limiter_threshold: 0.98,
        }
    }

    pub fn process_sample(&mut self, sample: f32) -> f32 {
        self.apply_limiter(sample)
    }

    fn apply_limiter(&self, sample: f32) -> f32 {
        if sample > self.limiter_threshold {
            self.limiter_threshold
        } else if sample < -self.limiter_threshold {
            -self.limiter_threshold
        } else {
            sample
        }
    }
}
