"""PHI (Protected Health Information) Detection Module.

This module implements detection patterns to identify and prevent
accidental upload of PHI in audio transcripts. Designed for educational
use case protection.

NOTE: This is a basic implementation. For production deployment with
actual patient data, use certified PHI detection services.
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class PHIType(Enum):
    """Types of PHI that can be detected."""
    SSN = "social_security_number"
    MRN = "medical_record_number"
    PHONE = "phone_number"
    EMAIL = "email_address"
    DATE_OF_BIRTH = "date_of_birth"
    NAME_WITH_CONTEXT = "name_with_medical_context"
    ADDRESS = "street_address"
    CREDIT_CARD = "credit_card"
    

@dataclass
class PHIMatch:
    """Represents a detected PHI pattern match."""
    phi_type: PHIType
    matched_text: str
    confidence: float  # 0.0 to 1.0
    position: int
    context: str  # Surrounding text for logging
    

@dataclass
class PHIDetectionResult:
    """Result of PHI detection scan."""
    contains_phi: bool
    confidence_score: float  # Overall confidence
    matches: List[PHIMatch]
    recommendation: str  # Human-readable message
    

class PHIDetector:
    """Detects potential PHI in transcribed text."""
    
    # Rejection threshold (0.0 to 1.0)
    # Higher = more strict, fewer false positives
    REJECTION_THRESHOLD = 0.7
    
    # PHI detection patterns
    PATTERNS = {
        PHIType.SSN: [
            (r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b', 0.9),
            (r'\bSSN[:\s]+\d{3}[-\s]?\d{2}[-\s]?\d{4}\b', 0.95),
            (r'\bsocial\s+security\s+(number)?[:\s]+\d{3}[-\s]?\d{2}[-\s]?\d{4}\b', 0.95),
        ],
        PHIType.MRN: [
            (r'\bMRN[:\s#]+[A-Z0-9]{6,12}\b', 0.9),
            (r'\bmedical\s+record\s+number[:\s#]+[A-Z0-9]{6,12}\b', 0.9),
            (r'\bpatient\s+(?:ID|id|number)[:\s#]+[A-Z0-9]{6,12}\b', 0.85),
        ],
        PHIType.PHONE: [
            (r'\b(?:\+?1[-\s]?)?\(?\d{3}\)?[-\s]?\d{3}[-\s]?\d{4}\b', 0.6),
            (r'\bcall\s+(?:me|him|her)\s+at\s+\(?\d{3}\)?[-\s]?\d{3}[-\s]?\d{4}\b', 0.85),
        ],
        PHIType.EMAIL: [
            (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 0.5),
        ],
        PHIType.DATE_OF_BIRTH: [
            (r'\bborn\s+(?:on\s+)?\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b', 0.9),
            (r'\bDOB[:\s]+\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b', 0.95),
            (r'\bdate\s+of\s+birth[:\s]+\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b', 0.95),
            (r'\bbirthday[:\s]+\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b', 0.8),
        ],
        PHIType.ADDRESS: [
            (r'\b\d+\s+[A-Z][a-z]+\s+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln)\b', 0.7),
        ],
        PHIType.CREDIT_CARD: [
            (r'\b(?:\d{4}[-\s]?){3}\d{4}\b', 0.8),
        ],
    }
    
    # Medical context keywords that increase suspicion
    MEDICAL_CONTEXT_KEYWORDS = [
        'patient', 'diagnosis', 'treatment', 'prescription', 'medication',
        'hospital', 'clinic', 'doctor', 'physician', 'nurse',
        'medical history', 'condition', 'symptoms', 'procedure',
        'admitted', 'discharged', 'surgery', 'operation'
    ]
    
    def __init__(self, custom_patterns: Optional[Dict[PHIType, List[tuple]]] = None):
        """Initialize PHI detector with optional custom patterns.
        
        Args:
            custom_patterns: Additional institution-specific patterns
        """
        self.patterns = self.PATTERNS.copy()
        if custom_patterns:
            for phi_type, patterns in custom_patterns.items():
                if phi_type in self.patterns:
                    self.patterns[phi_type].extend(patterns)
                else:
                    self.patterns[phi_type] = patterns
    
    def scan_text(self, text: str) -> PHIDetectionResult:
        """Scan text for potential PHI.
        
        Args:
            text: Transcribed text to scan
            
        Returns:
            PHIDetectionResult with findings
        """
        matches: List[PHIMatch] = []
        text_lower = text.lower()
        
        # Check for medical context to adjust confidence
        has_medical_context = any(
            keyword in text_lower 
            for keyword in self.MEDICAL_CONTEXT_KEYWORDS
        )
        
        # Scan for each PHI type
        for phi_type, patterns in self.patterns.items():
            for pattern, base_confidence in patterns:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    # Extract context (50 chars before/after)
                    start = max(0, match.start() - 50)
                    end = min(len(text), match.end() + 50)
                    context = text[start:end]
                    
                    # Adjust confidence based on medical context
                    confidence = base_confidence
                    if has_medical_context and phi_type in [
                        PHIType.PHONE, PHIType.EMAIL, PHIType.NAME_WITH_CONTEXT
                    ]:
                        confidence = min(1.0, confidence + 0.2)
                    
                    matches.append(PHIMatch(
                        phi_type=phi_type,
                        matched_text=match.group(),
                        confidence=confidence,
                        position=match.start(),
                        context=context
                    ))
        
        # Calculate overall confidence score
        if not matches:
            overall_confidence = 0.0
        else:
            # Use highest confidence match
            overall_confidence = max(m.confidence for m in matches)
        
        # Determine if PHI is present based on threshold
        contains_phi = overall_confidence >= self.REJECTION_THRESHOLD
        
        # Generate recommendation
        recommendation = self._generate_recommendation(
            contains_phi, matches, overall_confidence
        )
        
        # Log findings
        if contains_phi:
            self._log_phi_detection(matches, text)
        
        return PHIDetectionResult(
            contains_phi=contains_phi,
            confidence_score=overall_confidence,
            matches=matches,
            recommendation=recommendation
        )
    
    def _generate_recommendation(self, contains_phi: bool, 
                                 matches: List[PHIMatch],
                                 confidence: float) -> str:
        """Generate human-readable recommendation."""
        if not contains_phi:
            if not matches:
                return "No PHI detected. Safe to process."
            else:
                return (
                    f"Low-confidence PHI indicators detected ({confidence:.0%}). "
                    "Proceeding with caution."
                )
        
        # PHI detected - explain what was found
        phi_types = set(m.phi_type.value for m in matches)
        types_str = ", ".join(phi_types)
        
        return (
            f"🚨 REJECTED: Potential PHI detected ({confidence:.0%} confidence).\n\n"
            f"Detected types: {types_str}\n\n"
            "This appears to contain Protected Health Information. "
            "CogniScribe is for EDUCATIONAL USE ONLY.\n\n"
            "❌ Do NOT upload:\n"
            "  • Live patient recordings\n"
            "  • Clinical encounters\n"
            "  • Real patient data\n\n"
            "✅ Only upload:\n"
            "  • Classroom lectures\n"
            "  • Educational recordings\n"
            "  • Simulated patient scenarios (clearly labeled)\n\n"
            "If this is a false positive, please contact support."
        )
    
    def _log_phi_detection(self, matches: List[PHIMatch], text: str):
        """Log PHI detection for audit purposes."""
        logger.warning(
            "PHI_DETECTED",
            extra={
                "event": "phi_rejection",
                "num_matches": len(matches),
                "phi_types": [m.phi_type.value for m in matches],
                "max_confidence": max(m.confidence for m in matches),
                "text_length": len(text),
                # DO NOT log actual matched text or context (that would be logging PHI!)
            }
        )
    
    def should_reject(self, result: PHIDetectionResult) -> bool:
        """Determine if upload should be rejected based on detection result."""
        return result.contains_phi


# Singleton instance
_detector: Optional[PHIDetector] = None


def get_phi_detector() -> PHIDetector:
    """Get singleton PHI detector instance."""
    global _detector
    if _detector is None:
        _detector = PHIDetector()
    return _detector
