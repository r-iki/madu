import json
import logging
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import ml_model_manager, MLTestData, MLModel
from sensors.models import SpectralReading
import traceback

# Set up logging
logger = logging.getLogger(__name__)

def ml_dashboard(request):
    """ML Dashboard view"""
    # Get statistics
    total_tests = MLTestData.objects.count()
    recent_tests = MLTestData.objects.all()[:10]
    
    # Get models information
    ml_models = MLModel.objects.all()
    
    context = {
        'total_tests': total_tests,
        'recent_tests': recent_tests,
        'ml_models': ml_models,
        'page_title': 'ML Dashboard'
    }
    
    return render(request, 'ml/dashboard.html', context)

@csrf_exempt
def ml_predict_api(request):
    """HTTP API endpoint for ML prediction"""
    if request.method == 'POST':
        try:
            # Parse data
            data = json.loads(request.body)
            
            # Extract test name
            test_name = data.get('test_name', 'Test ML')
            
            # Extract spectral data
            if 'spectral_data' in data:
                spectral_data = data['spectral_data']
            else:
                spectral_data = data  # Assume the whole payload is spectral data
                
            # Validate spectral data
            required_fields = [
                'uv_410', 'uv_435', 'uv_460', 'uv_485', 'uv_510', 'uv_535',
                'vis_560', 'vis_585', 'vis_645', 'vis_705', 'vis_900', 'vis_940',
                'nir_610', 'nir_680', 'nir_730', 'nir_760', 'nir_810', 'nir_860',
            ]
            
            missing = [field for field in required_fields if field not in spectral_data]
            if missing:
                return JsonResponse({
                    'status': 'error',
                    'message': f"Missing required fields: {', '.join(missing)}"
                }, status=400)
                
            # Get ML predictions
            try:
                predictions = ml_model_manager.predict(spectral_data)
            except Exception as e:
                logger.error(f"Error getting ML predictions: {str(e)}")
                logger.error(traceback.format_exc())
                return JsonResponse({
                    'status': 'error',
                    'message': f"Prediction error: {str(e)}"
                }, status=500)
                
            if 'error' in predictions:
                return JsonResponse({
                    'status': 'error',
                    'message': predictions['error']
                }, status=500)
                
            # Save data to database
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
                
                test_data_id = ml_test.id
                
            except Exception as e:
                logger.error(f"Error saving test data: {str(e)}")
                logger.error(traceback.format_exc())
                return JsonResponse({
                    'status': 'error',
                    'message': f"Database error: {str(e)}"
                }, status=500)
                
            # Return predictions
            return JsonResponse({
                'status': 'success',
                'test_name': test_name,
                'predictions': predictions,
                'test_data_id': test_data_id
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON data'
            }, status=400)
            
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            logger.error(traceback.format_exc())
            return JsonResponse({
                'status': 'error',
                'message': f'Unexpected error: {str(e)}'
            }, status=500)
    else:
        return JsonResponse({
            'status': 'error',
            'message': 'Method not allowed'
        }, status=405)

@login_required
def ml_test_list(request):
    """View to list all ML tests"""
    tests = MLTestData.objects.all()
    
    context = {
        'tests': tests,
        'page_title': 'ML Test List'
    }
    
    return render(request, 'ml/test_list.html', context)

@login_required
def ml_test_detail(request, pk):
    """View to show details of a specific ML test"""
    try:
        test = MLTestData.objects.get(pk=pk)
        
        context = {
            'test': test,
            'page_title': f'ML Test #{test.id}'
        }
        
        return render(request, 'ml/test_detail.html', context)
    except MLTestData.DoesNotExist:
        return render(request, 'ml/error.html', {'error': 'Test not found'})
        
@login_required
def ml_model_list(request):
    """View to list all ML models"""
    models = MLModel.objects.all()
    
    context = {
        'models': models,
        'page_title': 'ML Models'
    }
    
    return render(request, 'ml/model_list.html', context)

@login_required
def ml_diagnostics(request):
    """View untuk halaman diagnostik WebSocket"""
    
    # Cek status Channels
    channel_layer_available = False
    try:
        from channels.layers import get_channel_layer
        channel_layer = get_channel_layer()
        if channel_layer is not None:
            channel_layer_available = True
    except Exception:
        pass
    
    # Cek konfigurasi routing
    routing_status = "Unknown"
    try:
        from django.conf import settings
        asgi_app = getattr(settings, 'ASGI_APPLICATION', None)
        if asgi_app:
            routing_status = f"ASGI Application configured: {asgi_app}"
        else:
            routing_status = "ASGI Application not configured"
    except Exception as e:
        routing_status = f"Error checking ASGI config: {str(e)}"
    
    context = {
        'page_title': 'WebSocket Diagnostics',
        'channel_layer_available': channel_layer_available,
        'routing_status': routing_status,
    }
    
    return render(request, 'ml/diagnostics.html', context)
