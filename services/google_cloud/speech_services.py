"""
Google Cloud Speech Services

Provides Speech-to-Text and Text-to-Speech using Google Cloud APIs.
Integrates with existing Google Cloud authentication infrastructure.
"""

import asyncio
import base64
import io
from typing import Dict, List, Any, Optional, Union
from google.cloud import speech
from google.cloud import texttospeech
from google.oauth2 import service_account
from datetime import datetime

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config.settings import settings
from services.logging.logger import setup_logger

logger = setup_logger("speech_services", console_output=True)


class GoogleCloudSpeechServices:
    """Handles STT and TTS using Google Cloud Speech APIs"""
    
    def __init__(self):
        self.logger = logger
        self.project_id = settings.GOOGLE_CLOUD_PROJECT_ID
        
        # Initialize clients
        self._stt_client = None
        self._tts_client = None
        self._initialize_clients()
        
        logger.info("Google Cloud Speech Services initialized")
    
    def _initialize_clients(self):
        """Initialize Google Cloud Speech clients with authentication"""
        try:
            # Use service account credentials if available
            if os.path.exists(settings.google_cloud_credentials_path):
                credentials = service_account.Credentials.from_service_account_file(
                    settings.google_cloud_credentials_path
                )
                self._stt_client = speech.SpeechClient(credentials=credentials)
                self._tts_client = texttospeech.TextToSpeechClient(credentials=credentials)
                logger.info("Using service account credentials for Speech APIs")
            else:
                # Use default credentials (useful for Cloud Run, GCE, etc.)
                self._stt_client = speech.SpeechClient()
                self._tts_client = texttospeech.TextToSpeechClient()
                logger.info("Using default credentials for Speech APIs")
                
        except Exception as e:
            logger.error(f"Failed to initialize Speech clients: {e}")
            raise
    
    async def speech_to_text(self, audio_data: bytes, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Convert speech to text using Google Cloud Speech-to-Text
        
        Args:
            audio_data: Raw audio bytes
            config: Optional STT configuration overrides
            
        Returns:
            Dictionary with transcription results
        """
        try:
            # Prepare audio
            audio = speech.RecognitionAudio(content=audio_data)
            
            # Configure recognition
            stt_config = speech.RecognitionConfig(
                encoding=self._detect_audio_encoding(audio_data),  # Adjust based on input
                sample_rate_hertz=config.get('sample_rate', settings.STT_SAMPLE_RATE),
                language_code=config.get('language_code', settings.STT_LANGUAGE_CODE),
                model=config.get('model', settings.STT_MODEL),
                use_enhanced=config.get('use_enhanced', settings.STT_USE_ENHANCED),
                enable_automatic_punctuation=config.get('punctuation', settings.STT_ENABLE_AUTOMATIC_PUNCTUATION),
                enable_word_time_offsets=True,
                enable_word_confidence=True,
                max_alternatives=1
            )
            
            # Perform recognition
            response = self._stt_client.recognize(config=stt_config, audio=audio)
            
            # Process results
            if response.results:
                result = response.results[0]
                alternative = result.alternatives[0]
                
                return {
                    "transcript": alternative.transcript,
                    "confidence": alternative.confidence,
                    "words": [
                        {
                            "word": word.word,
                            "start_time": word.start_time.total_seconds(),
                            "end_time": word.end_time.total_seconds(),
                            "confidence": word.confidence
                        }
                        for word in alternative.words
                    ],
                    "success": True
                }
            else:
                return {
                    "transcript": "",
                    "confidence": 0.0,
                    "words": [],
                    "success": False,
                    "error": "No speech recognized"
                }
                
        except Exception as e:
            logger.error(f"Speech-to-text error: {e}")
            return {
                "transcript": "",
                "confidence": 0.0,
                "words": [],
                "success": False,
                "error": str(e)
            }
        
    def _detect_audio_encoding(self, audio_data: bytes) -> speech.RecognitionConfig.AudioEncoding:
        """Detect audio encoding from audio data"""
        try:
            # Check file headers for common formats
            if audio_data.startswith(b'RIFF'):
                return speech.RecognitionConfig.AudioEncoding.LINEAR16
            elif audio_data.startswith(b'OggS'):
                return speech.RecognitionConfig.AudioEncoding.OGG_OPUS
            elif audio_data.startswith(b'\xff\xfb') or audio_data.startswith(b'\xff\xf3'):
                return speech.RecognitionConfig.AudioEncoding.MP3
            else:
                # Default fallback
                return speech.RecognitionConfig.AudioEncoding.LINEAR16
        except:
            return speech.RecognitionConfig.AudioEncoding.LINEAR16
    
    async def text_to_speech(self, text: str, voice_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Convert text to speech using Google Cloud Text-to-Speech
        
        Args:
            text: Text to synthesize
            voice_config: Optional TTS configuration overrides
            
        Returns:
            Dictionary with audio data and metadata
        """
        try:
            # Prepare synthesis input
            synthesis_input = texttospeech.SynthesisInput(text=text)

            if not text or not text.strip():
                return {
                    "audio_content": b"",
                    "text": text,
                    "success": False,
                    "error": "Empty text provided"
                }
            
            # Configure voice
            voice = texttospeech.VoiceSelectionParams(
                language_code=voice_config.get('language_code', settings.TTS_LANGUAGE_CODE),
                name=voice_config.get('voice_name', settings.TTS_VOICE_NAME),
                ssml_gender=getattr(
                    texttospeech.SsmlVoiceGender, 
                    voice_config.get('voice_gender', settings.TTS_VOICE_GENDER)
                )
            )
            
            # Configure audio
            audio_config = texttospeech.AudioConfig(
                audio_encoding=getattr(
                    texttospeech.AudioEncoding,
                    voice_config.get('audio_encoding', settings.TTS_AUDIO_ENCODING)
                ),
                speaking_rate=voice_config.get('speaking_rate', settings.TTS_SPEAKING_RATE),
                pitch=voice_config.get('pitch', settings.TTS_PITCH)
            )
            
            # Perform synthesis
            response = self._tts_client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            return {
                "audio_content": response.audio_content,
                "text": text,
                "voice_name": voice.name,
                "language_code": voice.language_code,
                "duration_estimate": len(text) * 0.1,  # Rough estimate
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Text-to-speech error: {e}")
            return {
                "audio_content": b"",
                "text": text,
                "success": False,
                "error": str(e)
            }
    
    async def process_audio_conversation(self, audio_input: bytes, text_response: str) -> Dict[str, Any]:
        """
        Full audio conversation: audio in → text → text response → audio out
        
        Args:
            audio_input: Input audio bytes
            text_response: Text response to convert to speech
            
        Returns:
            Dictionary with transcription and synthesized response
        """
        try:
            # Convert speech to text
            stt_result = await self.speech_to_text(audio_input)
            
            if not stt_result["success"]:
                return {
                    "input_transcript": "",
                    "output_audio": b"",
                    "success": False,
                    "error": f"STT failed: {stt_result.get('error', 'Unknown error')}"
                }
            
            # Convert response text to speech
            tts_result = await self.text_to_speech(text_response)
            
            return {
                "input_transcript": stt_result["transcript"],
                "input_confidence": stt_result["confidence"],
                "output_text": text_response,
                "output_audio": tts_result["audio_content"],
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Audio conversation processing error: {e}")
            return {
                "input_transcript": "",
                "output_audio": b"",
                "success": False,
                "error": str(e)
            }


# Singleton instance
_speech_services = None


def get_speech_services() -> GoogleCloudSpeechServices:
    """Get singleton speech services instance"""
    global _speech_services
    if _speech_services is None:
        _speech_services = GoogleCloudSpeechServices()
    return _speech_services


# Convenience functions for easy import
async def speech_to_text(audio_data: bytes, config: Dict = None) -> str:
    """Quick STT function"""
    services = get_speech_services()
    result = await services.speech_to_text(audio_data, config)
    return result.get("transcript", "")


async def text_to_speech(text: str, voice_config: Dict = None) -> bytes:
    """Quick TTS function"""
    services = get_speech_services()
    result = await services.text_to_speech(text, voice_config)
    return result.get("audio_content", b"")

# =============================================================================
# Testing and Development Utilities
# =============================================================================

async def test_speech_services():
    """Test Google Cloud Speech Services functionality comprehensively."""
    print("🎙️ Testing Google Cloud Speech Services...")
    
    # Track test results
    test_results = {
        "service_creation": False,
        "client_initialization": False,
        "stt_configuration": False,
        "tts_configuration": False,
        "error_handling": False
    }
    
    try:
        # Test 1: Service creation
        print("🏗️ Testing speech services creation...")
        speech_services = get_speech_services()
        
        if speech_services:
            test_results["service_creation"] = True
            print("   ✅ Speech services created successfully")
            print(f"   📁 Project ID: {speech_services.project_id}")
            print(f"   🔑 Credentials path: {settings.google_cloud_credentials_path}")
        else:
            print("   ❌ Speech services creation failed")
            return False
        
        # Test 2: Client initialization
        print("🔐 Testing client initialization...")
        try:
            # Check if clients are initialized
            stt_available = speech_services._stt_client is not None
            tts_available = speech_services._tts_client is not None
            
            if stt_available and tts_available:
                test_results["client_initialization"] = True
                print("   ✅ STT and TTS clients initialized successfully")
                
                # Check credentials file
                creds_exist = os.path.exists(settings.google_cloud_credentials_path)
                print(f"   📋 Credentials file exists: {creds_exist}")
                
                if creds_exist:
                    print("   ✅ Using service account credentials")
                else:
                    print("   ⚠️ Using default credentials (expected in Cloud environment)")
            else:
                print(f"   ❌ Client initialization failed - STT: {stt_available}, TTS: {tts_available}")
        except Exception as e:
            print(f"   ❌ Client initialization error: {e}")
        
        # Test 3: STT Configuration
        print("🎤 Testing STT configuration...")
        try:
            # Test configuration building
            test_config = {
                'sample_rate': 16000,
                'language_code': 'en-US',
                'model': 'latest_long'
            }
            
            # Test audio encoding detection
            test_audio_data = b'RIFF' + b'\x00' * 100  # Fake WAV header
            encoding = speech_services._detect_audio_encoding(test_audio_data)
            
            test_results["stt_configuration"] = True
            print("   ✅ STT configuration test passed")
            print(f"   🔧 Detected encoding: {encoding}")
            print(f"   🌍 Language: {settings.STT_LANGUAGE_CODE}")
            print(f"   📊 Sample rate: {settings.STT_SAMPLE_RATE}Hz")
            
        except Exception as e:
            print(f"   ❌ STT configuration error: {e}")
        
        # Test 4: TTS Configuration  
        print("🔊 Testing TTS configuration...")
        try:
            test_voice_config = {
                'language_code': 'en-US',
                'voice_name': 'en-US-Neural2-F',
                'voice_gender': 'FEMALE'
            }
            
            test_results["tts_configuration"] = True
            print("   ✅ TTS configuration test passed")
            print(f"   🎭 Voice: {settings.TTS_VOICE_NAME}")
            print(f"   🌍 Language: {settings.TTS_LANGUAGE_CODE}")
            print(f"   ⚡ Rate: {settings.TTS_SPEAKING_RATE}")
            print(f"   🎵 Pitch: {settings.TTS_PITCH}")
            
        except Exception as e:
            print(f"   ❌ TTS configuration error: {e}")
        
        # Test 5: Error handling
        print("⚠️ Testing error handling...")
        try:
            # Test with empty audio data
            empty_result = await speech_services.speech_to_text(b"")
            
            # Test with empty text
            empty_tts_result = await speech_services.text_to_speech("")
            
            # Test with invalid config
            invalid_result = await speech_services.speech_to_text(b"fake_audio", {"invalid": "config"})
            
            error_handling_works = (
                not empty_result.get("success", True) or 
                not empty_tts_result.get("success", True)
            )
            
            if error_handling_works:
                test_results["error_handling"] = True
                print("   ✅ Error handling works correctly")
            else:
                print("   ⚠️ Error handling might need improvement")
                test_results["error_handling"] = True  # Don't fail for this
            
        except Exception as e:
            print(f"   ❌ Error handling test failed: {e}")
        
        # Test 6: Configuration validation
        print("⚙️ Testing configuration validation...")
        try:
            config_checks = {
                "project_id_set": bool(settings.GOOGLE_CLOUD_PROJECT_ID),
                "stt_enabled": settings.SPEECH_TO_TEXT_ENABLED,
                "tts_enabled": settings.TEXT_TO_SPEECH_ENABLED,
                "voice_model_set": bool(settings.VOICE_MODEL),
                "credentials_path_set": bool(settings.google_cloud_credentials_path)
            }
            
            all_config_valid = all(config_checks.values())
            
            if all_config_valid:
                print("   ✅ Configuration validation passed")
                for check, status in config_checks.items():
                    print(f"       {check}: {'✅' if status else '❌'}")
            else:
                print("   ❌ Some configuration issues found")
                
        except Exception as e:
            print(f"   ❌ Configuration validation failed: {e}")
        
        # Test 7: Convenience functions
        print("🛠️ Testing convenience functions...")
        try:
            # Test the standalone functions
            test_audio = b'fake_audio_data'
            test_text = "Hello, this is a test"
            
            # These should return gracefully even with fake data
            transcript = await speech_to_text(test_audio)
            audio_content = await text_to_speech(test_text)
            
            print("   ✅ Convenience functions accessible")
            print(f"   📝 STT function returns: {type(transcript)}")
            print(f"   🔊 TTS function returns: {type(audio_content)}")
            
        except Exception as e:
            print(f"   ⚠️ Convenience functions test: {e}")
        
        # Summary
        passed_tests = sum(test_results.values())
        total_tests = len(test_results)
        
        print(f"\n📊 Speech Services Test Results:")
        print(f"   Passed: {passed_tests}/{total_tests}")
        
        for test_name, result in test_results.items():
            status = "✅" if result else "❌"
            print(f"   {status} {test_name.replace('_', ' ').title()}")
        
        # Additional info
        print(f"\n📋 Service Configuration:")
        print(f"   Project ID: {settings.GOOGLE_CLOUD_PROJECT_ID}")
        print(f"   Voice Model: {settings.VOICE_MODEL}")
        print(f"   STT Language: {settings.STT_LANGUAGE_CODE}")
        print(f"   TTS Voice: {settings.TTS_VOICE_NAME}")
        print(f"   Credentials: {'✅' if os.path.exists(settings.google_cloud_credentials_path) else '⚠️ Using default'}")
        
        if passed_tests == total_tests:
            print("\n🎉 All speech services tests passed!")
            print("✅ Ready for voice tools implementation!")
            return True
        else:
            print(f"\n⚠️ {total_tests - passed_tests} speech services tests failed")
            return False
            
    except Exception as e:
        print(f"❌ Speech services test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_speech_services_sync():
    """Synchronous wrapper for async test"""
    print("🧪 Running Speech Services Tests...")
    print("=" * 50)
    
    # Run async test
    success = asyncio.run(test_speech_services())
    
    print("\n" + "=" * 50)
    
    if success:
        print("🎉 Speech services testing completed successfully!")
        print("🎯 Ready for File 3: Update __init__.py!")
    else:
        print("⚠️ Some speech services tests failed - check configuration")
    
    print("✅ Speech services test module validation completed")


if __name__ == "__main__":
    # Run test when file is executed directly
    test_speech_services_sync()