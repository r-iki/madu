import json
import asyncio
import logging
import traceback
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.utils.timezone import now
from .models import ml_model_manager, MLTestData
from sensors.models import SpectralReading

# Set up logging
logger = logging.getLogger(__name__)

class MLTestConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Handle WebSocket connection"""
        try:
            logger.info("WebSocket connection attempt to ML consumer")
            await self.channel_layer.group_add("ml_test_group", self.channel_name)
            await self.accept()
            logger.info("WebSocket connection accepted")
            
            connection_info = {
                'type': 'connection_established',
                'message': 'Connected to ML Test WebSocket',
                'server_time': str(now()),
                'debug_info': {
                    'channel_name': self.channel_name,
                    'path': self.scope.get('path', 'unknown'),
                    'client': f"{self.scope.get('client', ('unknown', 0))[0]}:{self.scope.get('client', ('unknown', 0))[1]}"
                }
            }
            
            await self.send(text_data=json.dumps(connection_info))
            logger.info(f"Connection established message sent to {connection_info['debug_info']['client']}")
        except Exception as e:
            logger.error(f"Error in WebSocket connect: {str(e)}")
            logger.error(traceback.format_exc())

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        await self.channel_layer.group_discard("ml_test_group", self.channel_name)
        
    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            # Log incoming message for debugging
            logger.info(f"Received WebSocket message: {text_data[:200]}...")
            
            # Handle diagnostic messages specially
            if text_data.find('"test_name": "Debug Test"') > -1:
                logger.info("Detected debug test request, responding with diagnostic info")
                await self.send(text_data=json.dumps({
                    'type': 'debug_response',
                    'message': 'Debug test successful',
                    'server_time': str(now()),
                    'server_status': 'running',
                    'channel_layer_status': 'connected' if hasattr(self, 'channel_layer') else 'disconnected'
                }))
                return
                
            # Parse data
            data = json.loads(text_data)
            
            # Extract test name if provided
            test_name = data.get('test_name', 'Test ML')
            logger.info(f"Processing request for test: {test_name}")
            
            # Extract spectral data
            if 'spectral_data' in data:
                spectral_data = data['spectral_data']
                logger.info(f"Spectral data received with {len(spectral_data)} fields")
            else:
                spectral_data = data  # Assume the whole payload is spectral data
                logger.info("No spectral_data field found, using whole payload")
                
            # Process and validate spectral data
            valid_data, validation_message = await self.validate_spectral_data(spectral_data)
            
            if not valid_data:
                logger.warning(f"Validation failed: {validation_message}")
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': validation_message
                }))
                return
            
            logger.info("Data validation successful")
                
            # Get ML predictions
            logger.info("Getting ML predictions")
            predictions = await self.get_ml_predictions(spectral_data)
            
            if 'error' in predictions:
                logger.error(f"ML prediction error: {predictions['error']}")
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': predictions['error']
                }))
                return
            
            logger.info(f"ML predictions successful: {len(predictions)} model results")
                
            # Save data to database
            logger.info("Saving test data to database")
            saved_data = await self.save_test_data(spectral_data, predictions, test_name)
            logger.info(f"Data saved with ID: {saved_data.get('id')}")
            
            # Send response
            logger.info("Sending prediction response")
            await self.send(text_data=json.dumps({
                'type': 'ml_prediction',
                'test_name': test_name,
                'predictions': predictions,
                'saved_data_id': saved_data.get('id'),
                'timestamp': saved_data.get('timestamp')
            }))
            logger.info("Response sent successfully")
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON data. Please check your input format.'
            }))
        except Exception as e:
            logger.error(f"Error in MLTestConsumer.receive: {str(e)}")
            logger.error(traceback.format_exc())
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Internal server error: {str(e)}',
                'debug_info': {
                    'error_type': str(type(e).__name__),
                    'error_details': str(e)
                }
            }))

    @sync_to_async
    def validate_spectral_data(self, data):
        """Validate incoming spectral data"""
        required_fields = [
            'uv_410', 'uv_435', 'uv_460', 'uv_485', 'uv_510', 'uv_535',
            'vis_560', 'vis_585', 'vis_645', 'vis_705', 'vis_900', 'vis_940',
            'nir_610', 'nir_680', 'nir_730', 'nir_760', 'nir_810', 'nir_860',
        ]
        
        missing = [field for field in required_fields if field not in data]
        if missing:
            return False, f"Missing required fields: {', '.join(missing)}"
        
        return True, "Data is valid"

    @sync_to_async
    def get_ml_predictions(self, spectral_data):
        """Get predictions from ML models"""
        try:
            return ml_model_manager.predict(spectral_data)
        except Exception as e:
            logger.error(f"Error getting ML predictions: {str(e)}")
            logger.error(traceback.format_exc())
            return {'error': f"Prediction error: {str(e)}"}

    @sync_to_async
    def save_test_data(self, spectral_data, predictions, test_name):
        """Save test data and predictions to database"""
        try:
            # First save the spectral reading
            reading = SpectralReading.objects.create(
                name=spectral_data.get('name', 'ML Test Sample'),
                # Ultraviolet
                uv_410=spectral_data['uv_410'],
                uv_435=spectral_data['uv_435'],
                uv_460=spectral_data['uv_460'],
                uv_485=spectral_data['uv_485'],
                uv_510=spectral_data['uv_510'],
                uv_535=spectral_data['uv_535'],
                # Visible
                vis_560=spectral_data['vis_560'],
                vis_585=spectral_data['vis_585'],
                vis_645=spectral_data['vis_645'],
                vis_705=spectral_data['vis_705'],
                vis_900=spectral_data['vis_900'],
                vis_940=spectral_data['vis_940'],
                # Near Infrared
                nir_610=spectral_data['nir_610'],
                nir_680=spectral_data['nir_680'],
                nir_730=spectral_data['nir_730'],
                nir_760=spectral_data['nir_760'],
                nir_810=spectral_data['nir_810'],
                nir_860=spectral_data['nir_860'],
                # Temperature (optional)
                temperature=spectral_data.get('temperature', 25.0)
            )
            
            # Extract predictions
            ann_pred = predictions.get('ANN', {}).get('prediction', None)
            rf_pred = predictions.get('RF', {}).get('prediction', None)
            svm_pred = predictions.get('SVM', {}).get('prediction', None)
            
            # Extract confidence values
            ann_conf = predictions.get('ANN', {}).get('confidence', {})
            rf_conf = predictions.get('RF', {}).get('confidence', {})
            svm_conf = predictions.get('SVM', {}).get('confidence', {})
            
            # Create ML test data record
            ml_test = MLTestData.objects.create(
                spectral_reading=reading,
                test_name=test_name,
                ann_prediction=ann_pred,
                rf_prediction=rf_pred,
                svm_prediction=svm_pred,
                ann_confidence=ann_conf,
                rf_confidence=rf_conf,
                svm_confidence=svm_conf,
                notes=spectral_data.get('notes', '')
            )
            
            return {
                'id': ml_test.id,
                'timestamp': str(ml_test.created_at)
            }
            
        except Exception as e:
            logger.error(f"Error saving test data: {str(e)}")
            logger.error(traceback.format_exc())
            return {'error': f"Database error: {str(e)}"}
