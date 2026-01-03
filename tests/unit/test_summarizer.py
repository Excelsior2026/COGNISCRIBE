"""Unit tests for Ollama summarization service."""

import pytest
import requests
from unittest.mock import Mock, patch, MagicMock
from src.api.services import summarizer
from src.utils.errors import ProcessingError, ServiceUnavailableError, ErrorCode


class TestSummaryGeneration:
    """Test summary generation with Ollama."""
    
    @pytest.fixture
    def mock_ollama_response(self):
        """Mock successful Ollama API response."""
        return {
            "response": """### Learning Objectives
Understand cell structure

### Core Concepts
Cells are the basic unit of life

### Clinical Terms
Mitochondria: powerhouse of the cell

### Procedures
Cell staining protocol

### Summary
This lecture covered cell biology basics.""",
            "model": "llama3.1:8b"
        }
    
    @patch('src.api.services.summarizer.requests.post')
    def test_generate_summary_basic(self, mock_post, mock_ollama_response):
        """Test basic summary generation."""
        # Mock successful API call
        mock_response = Mock()
        mock_response.json.return_value = mock_ollama_response
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        text = "This is a lecture about cells. Cells are important."
        summary = summarizer.generate_summary(text)
        
        # Verify summary returned
        assert isinstance(summary, str)
        assert len(summary) > 0
        assert "Learning Objectives" in summary
        
        # Verify API was called
        assert mock_post.called
        call_kwargs = mock_post.call_args[1]
        assert "json" in call_kwargs
        assert call_kwargs["json"]["model"] == "llama3.1:8b"
    
    @patch('src.api.services.summarizer.requests.post')
    def test_generate_summary_with_subject(self, mock_post, mock_ollama_response):
        """Test subject-specific summarization."""
        mock_response = Mock()
        mock_response.json.return_value = mock_ollama_response
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        text = "Anatomy lecture content"
        summary = summarizer.generate_summary(text, subject="anatomy")
        
        assert summary
        # Verify subject was included in prompt
        call_kwargs = mock_post.call_args[1]
        prompt = call_kwargs["json"]["prompt"]
        assert "anatomy" in prompt.lower()
    
    @patch('src.api.services.summarizer.requests.post')
    def test_generate_summary_custom_ratio(self, mock_post, mock_ollama_response):
        """Test summary with custom length ratio."""
        mock_response = Mock()
        mock_response.json.return_value = mock_ollama_response
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        text = "Short lecture content"
        summary = summarizer.generate_summary(text, ratio=0.3)
        
        assert summary
        # Verify num_predict was adjusted for ratio
        call_kwargs = mock_post.call_args[1]
        options = call_kwargs["json"]["options"]
        assert "num_predict" in options
        assert options["num_predict"] > 0
    
    @patch('src.api.services.summarizer.requests.post')
    def test_generate_summary_ratio_validation(self, mock_post, mock_ollama_response):
        """Test invalid ratio is corrected to default."""
        mock_response = Mock()
        mock_response.json.return_value = mock_ollama_response
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        text = "Test content"
        
        # Test ratio > 1.0
        summary = summarizer.generate_summary(text, ratio=1.5)
        assert summary  # Should not raise, uses default
        
        # Test ratio < 0.0
        summary = summarizer.generate_summary(text, ratio=-0.5)
        assert summary  # Should not raise, uses default
    
    @patch('src.api.services.summarizer.requests.post')
    def test_generate_summary_temperature_setting(self, mock_post, mock_ollama_response):
        """Test temperature is set for consistent output."""
        mock_response = Mock()
        mock_response.json.return_value = mock_ollama_response
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        text = "Test content"
        summarizer.generate_summary(text)
        
        # Verify low temperature for consistency
        call_kwargs = mock_post.call_args[1]
        options = call_kwargs["json"]["options"]
        assert options["temperature"] == 0.2
    
    @patch('src.api.services.summarizer.requests.post')
    def test_generate_summary_stream_disabled(self, mock_post, mock_ollama_response):
        """Test streaming is disabled for batch processing."""
        mock_response = Mock()
        mock_response.json.return_value = mock_ollama_response
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        text = "Test content"
        summarizer.generate_summary(text)
        
        # Verify streaming is off
        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["json"]["stream"] is False


class TestSummaryErrors:
    """Test error handling in summarization."""
    
    @patch('src.api.services.summarizer.requests.post')
    def test_generate_summary_timeout(self, mock_post):
        """Test handling of Ollama timeout."""
        # Mock timeout
        mock_post.side_effect = requests.exceptions.Timeout("Request timed out")
        
        text = "Very long lecture content" * 1000
        
        with pytest.raises(ServiceUnavailableError) as exc_info:
            summarizer.generate_summary(text)
        
        assert exc_info.value.error_code == ErrorCode.OLLAMA_TIMEOUT
        assert "timed out" in exc_info.value.message.lower()
    
    @patch('src.api.services.summarizer.requests.post')
    def test_generate_summary_connection_error(self, mock_post):
        """Test handling of Ollama connection error."""
        # Mock connection error
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")
        
        text = "Test content"
        
        with pytest.raises(ServiceUnavailableError) as exc_info:
            summarizer.generate_summary(text)
        
        assert exc_info.value.error_code == ErrorCode.OLLAMA_UNAVAILABLE
        assert "Cannot connect" in exc_info.value.message
    
    @patch('src.api.services.summarizer.requests.post')
    def test_generate_summary_http_error(self, mock_post):
        """Test handling of HTTP errors from Ollama."""
        # Mock HTTP error
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Server error")
        mock_post.return_value = mock_response
        
        text = "Test content"
        
        with pytest.raises(ServiceUnavailableError) as exc_info:
            summarizer.generate_summary(text)
        
        assert exc_info.value.error_code == ErrorCode.OLLAMA_UNAVAILABLE
    
    @patch('src.api.services.summarizer.requests.post')
    def test_generate_summary_invalid_json(self, mock_post):
        """Test handling of invalid JSON response."""
        # Mock invalid JSON
        mock_response = Mock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        text = "Test content"
        
        with pytest.raises(ProcessingError) as exc_info:
            summarizer.generate_summary(text)
        
        assert exc_info.value.error_code == ErrorCode.SUMMARIZATION_FAILED
        assert "invalid JSON" in exc_info.value.message.lower()
    
    @patch('src.api.services.summarizer.requests.post')
    def test_generate_summary_empty_response(self, mock_post):
        """Test handling of empty response from Ollama."""
        # Mock empty response
        mock_response = Mock()
        mock_response.json.return_value = {"response": ""}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        text = "Test content"
        
        with pytest.raises(ProcessingError) as exc_info:
            summarizer.generate_summary(text)
        
        assert exc_info.value.error_code == ErrorCode.SUMMARIZATION_FAILED
        assert "empty response" in exc_info.value.message.lower()
    
    @patch('src.api.services.summarizer.requests.post')
    def test_generate_summary_whitespace_only_response(self, mock_post):
        """Test handling of whitespace-only response."""
        # Mock whitespace response
        mock_response = Mock()
        mock_response.json.return_value = {"response": "   \n  \t  "}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        text = "Test content"
        
        with pytest.raises(ProcessingError) as exc_info:
            summarizer.generate_summary(text)
        
        assert exc_info.value.error_code == ErrorCode.SUMMARIZATION_FAILED


class TestSectionParsing:
    """Test parsing of structured summary sections."""
    
    def test_parse_summary_sections_complete(self):
        """Test parsing of complete structured summary."""
        text = """### Learning Objectives
Understand basic concepts

### Core Concepts
Key principles explained

### Clinical Terms
Important definitions

### Procedures
Step by step protocols

### Summary
Overall summary content"""
        
        sections = summarizer.parse_summary_sections(text)
        
        assert sections["objectives"] == "Understand basic concepts"
        assert sections["concepts"] == "Key principles explained"
        assert sections["terms"] == "Important definitions"
        assert sections["procedures"] == "Step by step protocols"
        assert sections["summary"] == "Overall summary content"
    
    def test_parse_summary_sections_partial(self):
        """Test parsing when some sections are missing."""
        text = """### Learning Objectives
Some objectives

### Summary
Brief summary"""
        
        sections = summarizer.parse_summary_sections(text)
        
        assert sections["objectives"] == "Some objectives"
        assert sections["summary"] == "Brief summary"
        # Missing sections should be empty
        assert sections["concepts"] == ""
        assert sections["terms"] == ""
        assert sections["procedures"] == ""
    
    def test_parse_summary_sections_no_headings(self):
        """Test parsing of summary without markdown headings."""
        text = "This is a plain summary without any structure."
        
        sections = summarizer.parse_summary_sections(text)
        
        # All content should go to summary
        assert sections["summary"] == text
        assert sections["objectives"] == ""
        assert sections["concepts"] == ""
    
    def test_parse_summary_sections_empty(self):
        """Test parsing of empty summary."""
        sections = summarizer.parse_summary_sections("")
        
        # All sections should be empty
        assert all(v == "" for v in sections.values())
    
    def test_parse_summary_sections_varied_heading_levels(self):
        """Test parsing with different markdown heading levels."""
        text = """## Learning Objectives
Level 2 heading

### Core Concepts
Level 3 heading

#### Summary
Level 4 heading"""
        
        sections = summarizer.parse_summary_sections(text)
        
        # Should handle all heading levels 2-4
        assert sections["objectives"] == "Level 2 heading"
        assert sections["concepts"] == "Level 3 heading"
        assert sections["summary"] == "Level 4 heading"
    
    def test_parse_summary_sections_case_insensitive(self):
        """Test parsing is case insensitive."""
        text = """### learning objectives
Lowercase heading

### CORE CONCEPTS
Uppercase heading

### Clinical Terms
Mixed case heading"""
        
        sections = summarizer.parse_summary_sections(text)
        
        assert sections["objectives"] == "Lowercase heading"
        assert sections["concepts"] == "Uppercase heading"
        assert sections["terms"] == "Mixed case heading"
    
    def test_parse_summary_sections_with_extra_whitespace(self):
        """Test parsing handles extra whitespace."""
        text = """###   Learning Objectives   
  Content with whitespace  

###  Summary  
  More content  """
        
        sections = summarizer.parse_summary_sections(text)
        
        # Content should be stripped
        assert sections["objectives"].strip() == "Content with whitespace"
        assert sections["summary"].strip() == "More content"
    
    def test_parse_summary_sections_alternate_names(self):
        """Test parsing recognizes alternate section names."""
        text = """### Learning Objectives
Objectives content

### Terms
Terms content

### Protocol
Protocol content

### Overall Summary
Summary content"""
        
        sections = summarizer.parse_summary_sections(text)
        
        assert sections["objectives"] == "Objectives content"
        assert sections["terms"] == "Terms content"
        assert sections["procedures"] == "Protocol content"
        assert sections["summary"] == "Summary content"
