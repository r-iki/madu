from django.contrib import admin
from .models import MLModel, MLTestData

@admin.register(MLModel)
class MLModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'model_type', 'accuracy', 'is_active', 'created_at')
    list_filter = ('model_type', 'is_active')
    search_fields = ('name',)
    ordering = ('-updated_at',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('name', 'model_type', 'is_active')
        }),
        ('Performance Metrics', {
            'fields': ('accuracy', 'precision', 'recall', 'f1_score')
        }),
        ('Model Information', {
            'fields': ('parameters', 'created_at', 'updated_at')
        }),
    )

@admin.register(MLTestData)
class MLTestDataAdmin(admin.ModelAdmin):
    list_display = ('id', 'test_name', 'created_at', 'ann_prediction', 'rf_prediction', 'svm_prediction')
    list_filter = ('created_at',)
    search_fields = ('test_name', 'notes')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'spectral_reading')
    
    fieldsets = (
        (None, {
            'fields': ('test_name', 'spectral_reading', 'created_at', 'notes')
        }),
        ('Predictions', {
            'fields': ('ann_prediction', 'rf_prediction', 'svm_prediction')
        }),
        ('Confidence Scores', {
            'fields': ('ann_confidence', 'rf_confidence', 'svm_confidence')
        }),
    )
