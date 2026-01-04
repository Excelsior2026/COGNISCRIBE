"""Unit tests for PHI detection module."""
import pytest
from src.utils.phi_detector import (
    PHIDetector,
    PHIType,
    PHIDetectionResult,
    get_phi_detector
)


class TestPHIDetector:
    """Test PHI detection functionality."""
    
    @pytest.fixture
    def detector(self) -> PHIDetector:
        """Create PHI detector instance."""
        return PHIDetector()
    
    # SSN Detection Tests
    def test_detect_ssn_standard_format(self, detector):
        """Should detect SSN in standard format."""
        text = "The patient's SSN is 123-45-6789."
        result = detector.scan_text(text)
        
        assert result.contains_phi
        assert any(m.phi_type == PHIType.SSN for m in result.matches)
        assert result.confidence_score >= 0.9
    
    def test_detect_ssn_no_dashes(self, detector):
        """Should detect SSN without dashes."""
        text = "Social security number: 123456789"
        result = detector.scan_text(text)
        
        assert result.contains_phi
        assert any(m.phi_type == PHIType.SSN for m in result.matches)
    
    def test_no_false_positive_on_similar_numbers(self, detector):
        """Should not flag non-SSN 9-digit numbers."""
        text = "The reference number is 123456789 for tracking purposes."
        result = detector.scan_text(text)
        
        # Should have low or no matches since no SSN context
        assert not result.contains_phi or result.confidence_score < 0.7
    
    # MRN Detection Tests
    def test_detect_mrn(self, detector):
        """Should detect medical record numbers."""
        text = "Patient MRN: ABC123456"
        result = detector.scan_text(text)
        
        assert result.contains_phi
        assert any(m.phi_type == PHIType.MRN for m in result.matches)
    
    def test_detect_patient_id(self, detector):
        """Should detect patient ID references."""
        text = "Admitted patient ID: MED789012"
        result = detector.scan_text(text)
        
        assert result.contains_phi
        assert any(m.phi_type == PHIType.MRN for m in result.matches)
    
    # Phone Number Tests
    def test_detect_phone_with_context(self, detector):
        """Should detect phone numbers with medical context."""
        text = (
            "The patient can be reached at 555-123-4567. "
            "She was diagnosed with hypertension."
        )
        result = detector.scan_text(text)
        
        # Phone + medical context should trigger
        assert result.contains_phi
        assert any(m.phi_type == PHIType.PHONE for m in result.matches)
    
    def test_phone_in_educational_context_allowed(self, detector):
        """Phone numbers in educational context should have lower confidence."""
        text = "For questions about this lecture, call 555-123-4567."
        result = detector.scan_text(text)
        
        # Educational context, no medical keywords
        # Should not exceed threshold
        assert not result.contains_phi or result.confidence_score < 0.7
    
    # Email Detection Tests
    def test_detect_email_address(self, detector):
        """Should detect email addresses with low-medium confidence."""
        text = "Contact patient at john.doe@email.com"
        result = detector.scan_text(text)
        
        # Email alone has lower confidence
        matches = [m for m in result.matches if m.phi_type == PHIType.EMAIL]
        assert len(matches) > 0
    
    # Date of Birth Tests
    def test_detect_dob_explicit(self, detector):
        """Should detect explicit date of birth."""
        text = "Patient DOB: 05/15/1985"
        result = detector.scan_text(text)
        
        assert result.contains_phi
        assert any(m.phi_type == PHIType.DATE_OF_BIRTH for m in result.matches)
    
    def test_detect_dob_written_out(self, detector):
        """Should detect written-out date of birth."""
        text = "The patient was born on 12/25/1990."
        result = detector.scan_text(text)
        
        assert result.contains_phi
        assert any(m.phi_type == PHIType.DATE_OF_BIRTH for m in result.matches)
    
    def test_general_date_allowed(self, detector):
        """General dates without birth context should be allowed."""
        text = "This lecture was recorded on 01/15/2026."
        result = detector.scan_text(text)
        
        # No DOB context
        assert not result.contains_phi or result.confidence_score < 0.7
    
    # Address Detection Tests
    def test_detect_street_address(self, detector):
        """Should detect street addresses."""
        text = "Patient lives at 123 Main Street, Apt 4B."
        result = detector.scan_text(text)
        
        assert result.contains_phi
        assert any(m.phi_type == PHIType.ADDRESS for m in result.matches)
    
    # Medical Context Tests
    def test_medical_context_increases_confidence(self, detector):
        """Medical context should increase confidence scores."""
        text_without_context = "Call 555-123-4567 for more information."
        text_with_context = (
            "Patient presented with chest pain. "
            "Contact number: 555-123-4567. Prescribed aspirin."
        )
        
        result_without = detector.scan_text(text_without_context)
        result_with = detector.scan_text(text_with_context)
        
        # Medical context should boost confidence
        assert result_with.confidence_score >= result_without.confidence_score
    
    # Edge Cases
    def test_empty_text(self, detector):
        """Should handle empty text."""
        result = detector.scan_text("")
        
        assert not result.contains_phi
        assert result.confidence_score == 0.0
        assert len(result.matches) == 0
    
    def test_clean_educational_content(self, detector):
        """Should not flag clean educational content."""
        text = (
            "Today we will discuss cardiac physiology. "
            "The heart has four chambers and pumps blood throughout the body. "
            "Understanding the Frank-Starling mechanism is essential."
        )
        result = detector.scan_text(text)
        
        assert not result.contains_phi
        assert result.confidence_score < 0.7
    
    def test_simulated_case_study(self, detector):
        """Should allow clearly simulated case studies."""
        text = (
            "Case Study: 45-year-old male presents with hypertension. "
            "This is a simulated scenario for educational purposes."
        )
        result = detector.scan_text(text)
        
        # Age and condition mentioned but no real identifiers
        assert not result.contains_phi
    
    def test_multiple_phi_types(self, detector):
        """Should detect multiple PHI types in same text."""
        text = (
            "Patient John Smith, MRN: ABC123456, DOB: 01/15/1980, "
            "SSN: 123-45-6789, phone: 555-123-4567."
        )
        result = detector.scan_text(text)
        
        assert result.contains_phi
        assert result.confidence_score >= 0.9
        
        # Should detect multiple types
        phi_types = {m.phi_type for m in result.matches}
        assert PHIType.SSN in phi_types
        assert PHIType.MRN in phi_types
        assert PHIType.DATE_OF_BIRTH in phi_types
        assert PHIType.PHONE in phi_types
    
    # Recommendation Tests
    def test_recommendation_for_clean_text(self, detector):
        """Should provide positive recommendation for clean text."""
        text = "The cardiovascular system is complex."
        result = detector.scan_text(text)
        
        assert "safe" in result.recommendation.lower()
    
    def test_recommendation_for_phi(self, detector):
        """Should provide clear rejection message for PHI."""
        text = "Patient SSN: 123-45-6789"
        result = detector.scan_text(text)
        
        assert "rejected" in result.recommendation.lower()
        assert "educational use only" in result.recommendation.lower()
    
    # Custom Patterns Test
    def test_custom_patterns(self):
        """Should support custom institutional patterns."""
        custom_patterns = {
            PHIType.MRN: [
                (r'\bHOSP-\d{6}\b', 0.95),  # Hospital-specific format
            ]
        }
        
        detector = PHIDetector(custom_patterns=custom_patterns)
        text = "Patient medical record: HOSP-123456"
        result = detector.scan_text(text)
        
        assert result.contains_phi
        assert any(m.phi_type == PHIType.MRN for m in result.matches)
    
    # Singleton Test
    def test_singleton_instance(self):
        """Should return same instance from get_phi_detector()."""
        detector1 = get_phi_detector()
        detector2 = get_phi_detector()
        
        assert detector1 is detector2


class TestPHIDetectionIntegration:
    """Integration tests for PHI detection in pipeline."""
    
    @pytest.mark.integration
    def test_should_reject_method(self):
        """Test should_reject decision logic."""
        detector = PHIDetector()
        
        # Clean text - should not reject
        clean_result = detector.scan_text("This is a lecture about anatomy.")
        assert not detector.should_reject(clean_result)
        
        # PHI text - should reject
        phi_result = detector.scan_text("Patient SSN: 123-45-6789")
        assert detector.should_reject(phi_result)
    
    @pytest.mark.integration
    def test_confidence_threshold_boundary(self):
        """Test behavior at confidence threshold boundary."""
        detector = PHIDetector()
        
        # Test with text that should be right at threshold
        # Phone number alone has 0.6 confidence
        text = "Call 555-123-4567"
        result = detector.scan_text(text)
        
        # Should be below 0.7 threshold
        assert result.confidence_score < PHIDetector.REJECTION_THRESHOLD
        assert not detector.should_reject(result)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
