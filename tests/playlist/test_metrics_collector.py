import pytest
import tempfile
import os
import json
import time
from unittest.mock import Mock, patch
from src.playlist.metrics_collector import MetricsCollector
from src.playlist.database_manager import DatabaseManager

class TestMetricsCollector:
    
    @pytest.fixture
    def metrics_collector(self):
        """Cria MetricsCollector com banco temporário"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        # Criar log temporário
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            f.write("INFO execution_time 45.2 seconds\n")
            f.write("INFO search_time 2.3 seconds\n")
            f.write("ERROR Failed to download\n")
            f.write("WARNING Rate limit hit\n")
            log_path = f.name
        
        # Inicializar banco
        db = DatabaseManager(db_path)
        db.init_database()
        
        # Adicionar dados de teste
        db.save_download({
            'file_line': 'Test Song 1',
            'username': 'user1',
            'filename': 'song1.flac',
            'file_size': 45000000
        }, 'SUCCESS')
        
        db.save_download({
            'file_line': 'Test Song 2',
            'username': 'user2', 
            'filename': 'song2.flac',
            'file_size': 52000000
        }, 'ERROR')
        
        db.save_search_cache('cache1', 'query1', [], 24)
        
        collector = MetricsCollector(db_path, log_path)
        
        yield collector
        
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)
        if os.path.exists(log_path):
            os.unlink(log_path)
    
    def test_collect_system_metrics(self, metrics_collector):
        """Testa coleta de métricas do sistema"""
        metrics = metrics_collector.collect_system_metrics()
        
        assert 'timestamp' in metrics
        assert 'cpu_percent' in metrics
        assert 'memory_usage_mb' in metrics
        assert 'disk_usage' in metrics
        assert 'uptime_seconds' in metrics
        
        # Verificar tipos
        assert isinstance(metrics['cpu_percent'], (int, float))
        assert isinstance(metrics['memory_usage_mb'], (int, float))
        assert isinstance(metrics['disk_usage'], dict)
    
    def test_collect_database_metrics(self, metrics_collector):
        """Testa coleta de métricas do banco"""
        metrics = metrics_collector.collect_database_metrics()
        
        assert 'timestamp' in metrics
        assert 'total_downloads' in metrics
        assert 'successful_downloads' in metrics
        assert 'failed_downloads' in metrics
        assert 'success_rate' in metrics
        assert 'cache_entries' in metrics
        assert 'database_size_mb' in metrics
        
        # Verificar valores esperados
        assert metrics['total_downloads'] == 2
        assert metrics['successful_downloads'] == 1
        assert metrics['failed_downloads'] == 1
        assert metrics['success_rate'] == 0.5
        assert metrics['cache_entries'] == 1
    
    def test_collect_performance_metrics(self, metrics_collector):
        """Testa coleta de métricas de performance"""
        metrics = metrics_collector.collect_performance_metrics()
        
        assert 'timestamp' in metrics
        assert 'execution_metrics' in metrics
        assert 'rate_limiting_metrics' in metrics
        assert 'error_metrics' in metrics
        assert 'quality_metrics' in metrics
    
    def test_get_health_status_healthy(self, metrics_collector):
        """Testa status de saúde - sistema saudável"""
        with patch.object(metrics_collector, 'collect_system_metrics') as mock_system:
            with patch.object(metrics_collector, 'collect_database_metrics') as mock_db:
                
                # Simular sistema saudável
                mock_system.return_value = {
                    'memory_percent': 50,
                    'cpu_percent': 30
                }
                
                mock_db.return_value = {
                    'cache_hit_rate': 0.8
                }
                
                health = metrics_collector.get_health_status()
                
                assert health['status'] in ['healthy', 'warning', 'critical']
                assert 'health_score' in health
                assert 'checks' in health
                assert 'recommendations' in health
    
    def test_get_health_status_critical(self, metrics_collector):
        """Testa status de saúde - sistema crítico"""
        with patch.object(metrics_collector, 'collect_system_metrics') as mock_system:
            with patch.object(metrics_collector, 'collect_database_metrics') as mock_db:
                
                # Simular sistema com problemas
                mock_system.return_value = {
                    'memory_percent': 95,  # Memória alta
                    'cpu_percent': 90      # CPU alta
                }
                
                mock_db.return_value = {
                    'error': 'Database not accessible',
                    'cache_hit_rate': 0.05  # Cache ruim
                }
                
                health = metrics_collector.get_health_status()
                
                assert health['status'] == 'critical'
                assert health['health_score'] < 0.6
                assert len(health['recommendations']) > 0
    
    def test_generate_report(self, metrics_collector):
        """Testa geração de relatório"""
        report = metrics_collector.generate_report(days=7)
        
        assert 'report_period' in report
        assert 'summary' in report
        assert 'daily_trends' in report
        assert 'top_artists' in report
        assert 'current_health' in report
        
        # Verificar período
        assert report['report_period']['days'] == 7
        
        # Verificar sumário
        summary = report['summary']
        assert 'total_downloads' in summary
        assert 'success_rate' in summary
        assert 'error_rate' in summary
    
    def test_export_metrics_json(self, metrics_collector):
        """Testa exportação em JSON"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = f.name
        
        try:
            metrics_collector.export_metrics(output_path, 'json')
            
            # Verificar se arquivo foi criado
            assert os.path.exists(output_path)
            
            # Verificar conteúdo
            with open(output_path, 'r') as f:
                data = json.load(f)
                
            assert 'collection_time' in data
            assert 'system' in data
            assert 'database' in data
            assert 'performance' in data
            assert 'health_status' in data
            
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def test_export_metrics_csv(self, metrics_collector):
        """Testa exportação em CSV"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            output_path = f.name
        
        try:
            metrics_collector.export_metrics(output_path, 'csv')
            
            # Verificar se arquivo foi criado
            assert os.path.exists(output_path)
            
            # Verificar conteúdo básico
            with open(output_path, 'r') as f:
                content = f.read()
                
            assert 'Metric,Value' in content  # Header CSV
            assert len(content.split('\n')) > 1  # Múltiplas linhas
            
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def test_execution_metrics_parsing(self, metrics_collector):
        """Testa parsing de métricas de execução dos logs"""
        metrics = metrics_collector._get_execution_metrics()
        
        # Deve ter encontrado métricas nos logs de teste
        assert 'avg_execution_time' in metrics
        assert 'avg_search_time' in metrics
        assert 'total_executions' in metrics
        
        # Verificar valores esperados dos logs de teste
        assert metrics['avg_execution_time'] == 45.2
        assert metrics['avg_search_time'] == 2.3
        assert metrics['total_executions'] == 1
    
    def test_error_metrics_parsing(self, metrics_collector):
        """Testa parsing de métricas de erro dos logs"""
        metrics = metrics_collector._get_error_metrics()
        
        assert 'error_count_24h' in metrics
        assert 'warning_count_24h' in metrics
        assert 'error_rate' in metrics
        
        # Verificar valores dos logs de teste
        assert metrics['error_count_24h'] == 1
        assert metrics['warning_count_24h'] == 1
    
    def test_disk_usage_metrics(self, metrics_collector):
        """Testa métricas de uso de disco"""
        disk_usage = metrics_collector._get_disk_usage()
        
        assert 'total_gb' in disk_usage
        assert 'used_gb' in disk_usage
        assert 'free_gb' in disk_usage
        assert 'percent_used' in disk_usage
        
        # Verificar tipos
        assert isinstance(disk_usage['total_gb'], (int, float))
        assert isinstance(disk_usage['percent_used'], (int, float))
        assert 0 <= disk_usage['percent_used'] <= 100
    
    def test_quality_metrics(self, metrics_collector):
        """Testa métricas de qualidade"""
        metrics = metrics_collector._get_quality_metrics()
        
        assert 'quality_distribution' in metrics
        assert 'high_quality_rate' in metrics
        
        # Verificar distribuição baseada no tamanho dos arquivos de teste
        quality_dist = metrics['quality_distribution']
        assert isinstance(quality_dist, dict)
    
    def test_flatten_dict_utility(self, metrics_collector):
        """Testa utilitário de flatten dict"""
        nested_dict = {
            'level1': {
                'level2': {
                    'value': 123
                },
                'simple': 'test'
            },
            'root': 'value'
        }
        
        flattened = metrics_collector._flatten_dict(nested_dict)
        
        assert 'level1.level2.value' in flattened
        assert 'level1.simple' in flattened
        assert 'root' in flattened
        
        assert flattened['level1.level2.value'] == 123
        assert flattened['level1.simple'] == 'test'
        assert flattened['root'] == 'value'
    
    def test_collect_all_metrics(self, metrics_collector):
        """Testa coleta de todas as métricas"""
        all_metrics = metrics_collector.collect_all_metrics()
        
        assert 'collection_time' in all_metrics
        assert 'system' in all_metrics
        assert 'database' in all_metrics
        assert 'performance' in all_metrics
        assert 'health_status' in all_metrics
        
        # Verificar que cada seção tem dados
        assert len(all_metrics['system']) > 0
        assert len(all_metrics['database']) > 0
        assert len(all_metrics['performance']) > 0
        assert len(all_metrics['health_status']) > 0
    
    def test_health_recommendations(self, metrics_collector):
        """Testa geração de recomendações de saúde"""
        # Simular checks com problemas
        health_checks = {
            'memory_usage_ok': False,
            'cpu_usage_ok': False,
            'disk_space_ok': False,
            'cache_healthy': False,
            'recent_activity': False
        }
        
        recommendations = metrics_collector._get_health_recommendations(health_checks)
        
        # Deve ter recomendações para cada problema
        assert len(recommendations) == 5
        assert any('memory' in rec.lower() for rec in recommendations)
        assert any('cpu' in rec.lower() for rec in recommendations)
        assert any('disk' in rec.lower() for rec in recommendations)
        assert any('cache' in rec.lower() for rec in recommendations)
        assert any('activity' in rec.lower() for rec in recommendations)
