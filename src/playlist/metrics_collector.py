"""
Metrics Collector - Sistema de coleta e análise de métricas
Coleta métricas de performance, uso e qualidade do sistema
"""

import os
import time
import json
import sqlite3
import psutil
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

class MetricsCollector:
    """Coletor de métricas do sistema"""
    
    def __init__(self, db_path: str, log_path: str = None):
        self.db_path = db_path
        self.log_path = log_path
        self.logger = logging.getLogger(__name__)
        self.start_time = time.time()
        
    def collect_system_metrics(self) -> Dict:
        """Coleta métricas do sistema"""
        try:
            process = psutil.Process()
            
            return {
                'timestamp': datetime.now().isoformat(),
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_usage_mb': process.memory_info().rss / 1024 / 1024,
                'memory_percent': process.memory_percent(),
                'disk_usage': self._get_disk_usage(),
                'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0],
                'process_count': len(psutil.pids()),
                'uptime_seconds': time.time() - self.start_time
            }
        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")
            return {}
    
    def collect_database_metrics(self) -> Dict:
        """Coleta métricas do banco de dados"""
        try:
            if not os.path.exists(self.db_path):
                return {'error': 'Database not found'}
                
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Estatísticas básicas
            cursor.execute("SELECT COUNT(*) FROM downloads")
            total_downloads = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM downloads WHERE status = 'SUCCESS'")
            successful_downloads = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM downloads WHERE status = 'ERROR'")
            failed_downloads = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM downloads WHERE status = 'NOT_FOUND'")
            not_found = cursor.fetchone()[0]
            
            # Cache statistics
            cursor.execute("SELECT COUNT(*) FROM search_cache")
            cache_entries = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM search_cache WHERE expires_at > datetime('now')")
            valid_cache_entries = cursor.fetchone()[0]
            
            # Tamanho do banco
            db_size_bytes = os.path.getsize(self.db_path)
            
            # Downloads por dia (últimos 7 dias)
            cursor.execute("""
                SELECT DATE(created_at) as date, COUNT(*) as count
                FROM downloads 
                WHERE created_at >= datetime('now', '-7 days')
                GROUP BY DATE(created_at)
                ORDER BY date DESC
            """)
            daily_downloads = dict(cursor.fetchall())
            
            # Top usuários
            cursor.execute("""
                SELECT username, COUNT(*) as count
                FROM downloads 
                WHERE username IS NOT NULL
                GROUP BY username
                ORDER BY count DESC
                LIMIT 10
            """)
            top_users = dict(cursor.fetchall())
            
            conn.close()
            
            success_rate = successful_downloads / total_downloads if total_downloads > 0 else 0
            cache_hit_rate = valid_cache_entries / cache_entries if cache_entries > 0 else 0
            
            return {
                'timestamp': datetime.now().isoformat(),
                'total_downloads': total_downloads,
                'successful_downloads': successful_downloads,
                'failed_downloads': failed_downloads,
                'not_found': not_found,
                'success_rate': round(success_rate, 3),
                'cache_entries': cache_entries,
                'valid_cache_entries': valid_cache_entries,
                'cache_hit_rate': round(cache_hit_rate, 3),
                'database_size_mb': round(db_size_bytes / 1024 / 1024, 2),
                'daily_downloads': daily_downloads,
                'top_users': top_users
            }
            
        except Exception as e:
            self.logger.error(f"Error collecting database metrics: {e}")
            return {'error': str(e)}
    
    def collect_performance_metrics(self) -> Dict:
        """Coleta métricas de performance"""
        try:
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'execution_metrics': self._get_execution_metrics(),
                'rate_limiting_metrics': self._get_rate_limiting_metrics(),
                'error_metrics': self._get_error_metrics(),
                'quality_metrics': self._get_quality_metrics()
            }
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error collecting performance metrics: {e}")
            return {'error': str(e)}
    
    def collect_all_metrics(self) -> Dict:
        """Coleta todas as métricas"""
        return {
            'collection_time': datetime.now().isoformat(),
            'system': self.collect_system_metrics(),
            'database': self.collect_database_metrics(),
            'performance': self.collect_performance_metrics(),
            'health_status': self.get_health_status()
        }
    
    def get_health_status(self) -> Dict:
        """Determina status de saúde do sistema"""
        try:
            system_metrics = self.collect_system_metrics()
            db_metrics = self.collect_database_metrics()
            
            # Critérios de saúde
            health_checks = {
                'database_accessible': 'error' not in db_metrics,
                'memory_usage_ok': system_metrics.get('memory_percent', 100) < 80,
                'cpu_usage_ok': system_metrics.get('cpu_percent', 100) < 80,
                'disk_space_ok': self._check_disk_space(),
                'recent_activity': self._check_recent_activity(),
                'cache_healthy': db_metrics.get('cache_hit_rate', 0) > 0.1
            }
            
            # Status geral
            healthy_checks = sum(health_checks.values())
            total_checks = len(health_checks)
            health_score = healthy_checks / total_checks
            
            if health_score >= 0.8:
                status = 'healthy'
            elif health_score >= 0.6:
                status = 'warning'
            else:
                status = 'critical'
            
            return {
                'status': status,
                'health_score': round(health_score, 2),
                'checks': health_checks,
                'recommendations': self._get_health_recommendations(health_checks)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting health status: {e}")
            return {
                'status': 'unknown',
                'error': str(e)
            }
    
    def generate_report(self, days: int = 7) -> Dict:
        """Gera relatório detalhado"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Estatísticas do período
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) as success,
                    SUM(CASE WHEN status = 'ERROR' THEN 1 ELSE 0 END) as errors,
                    SUM(CASE WHEN status = 'NOT_FOUND' THEN 1 ELSE 0 END) as not_found,
                    AVG(file_size) as avg_file_size
                FROM downloads 
                WHERE created_at >= ? AND created_at <= ?
            """, (start_date.isoformat(), end_date.isoformat()))
            
            stats = cursor.fetchone()
            
            # Tendências diárias
            cursor.execute("""
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) as success,
                    AVG(file_size) as avg_size
                FROM downloads 
                WHERE created_at >= ? AND created_at <= ?
                GROUP BY DATE(created_at)
                ORDER BY date
            """, (start_date.isoformat(), end_date.isoformat()))
            
            daily_trends = [
                {
                    'date': row[0],
                    'total': row[1],
                    'success': row[2],
                    'success_rate': row[2] / row[1] if row[1] > 0 else 0,
                    'avg_size_mb': row[3] / 1024 / 1024 if row[3] else 0
                }
                for row in cursor.fetchall()
            ]
            
            # Top artistas/álbuns
            cursor.execute("""
                SELECT 
                    SUBSTR(file_line, 1, INSTR(file_line, ' - ') - 1) as artist,
                    COUNT(*) as count
                FROM downloads 
                WHERE created_at >= ? AND created_at <= ?
                    AND file_line LIKE '% - %'
                GROUP BY artist
                ORDER BY count DESC
                LIMIT 10
            """, (start_date.isoformat(), end_date.isoformat()))
            
            top_artists = [{'artist': row[0], 'count': row[1]} for row in cursor.fetchall()]
            
            conn.close()
            
            # Calcular métricas
            total, success, errors, not_found, avg_size = stats
            success_rate = success / total if total > 0 else 0
            error_rate = errors / total if total > 0 else 0
            
            return {
                'report_period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': days
                },
                'summary': {
                    'total_downloads': total,
                    'successful_downloads': success,
                    'failed_downloads': errors,
                    'not_found': not_found,
                    'success_rate': round(success_rate, 3),
                    'error_rate': round(error_rate, 3),
                    'avg_file_size_mb': round(avg_size / 1024 / 1024, 2) if avg_size else 0
                },
                'daily_trends': daily_trends,
                'top_artists': top_artists,
                'current_health': self.get_health_status()
            }
            
        except Exception as e:
            self.logger.error(f"Error generating report: {e}")
            return {'error': str(e)}
    
    def export_metrics(self, output_path: str, format: str = 'json'):
        """Exporta métricas para arquivo"""
        try:
            metrics = self.collect_all_metrics()
            
            if format.lower() == 'json':
                with open(output_path, 'w') as f:
                    json.dump(metrics, f, indent=2, default=str)
            elif format.lower() == 'csv':
                self._export_to_csv(metrics, output_path)
            else:
                raise ValueError(f"Unsupported format: {format}")
                
            self.logger.info(f"Metrics exported to {output_path}")
            
        except Exception as e:
            self.logger.error(f"Error exporting metrics: {e}")
            raise
    
    def _get_disk_usage(self) -> Dict:
        """Obtém uso de disco"""
        try:
            db_dir = os.path.dirname(self.db_path)
            usage = psutil.disk_usage(db_dir)
            
            return {
                'total_gb': round(usage.total / 1024**3, 2),
                'used_gb': round(usage.used / 1024**3, 2),
                'free_gb': round(usage.free / 1024**3, 2),
                'percent_used': round((usage.used / usage.total) * 100, 1)
            }
        except Exception:
            return {}
    
    def _get_execution_metrics(self) -> Dict:
        """Métricas de execução baseadas em logs"""
        if not self.log_path or not os.path.exists(self.log_path):
            return {}
            
        try:
            # Analisar logs das últimas 24h
            cutoff_time = datetime.now() - timedelta(hours=24)
            
            execution_times = []
            search_times = []
            
            with open(self.log_path, 'r') as f:
                for line in f:
                    if 'execution_time' in line:
                        # Extrair tempo de execução
                        try:
                            time_str = line.split('execution_time')[1].split()[0]
                            execution_times.append(float(time_str))
                        except (IndexError, ValueError):
                            continue
                    
                    if 'search_time' in line:
                        # Extrair tempo de busca
                        try:
                            time_str = line.split('search_time')[1].split()[0]
                            search_times.append(float(time_str))
                        except (IndexError, ValueError):
                            continue
            
            return {
                'avg_execution_time': sum(execution_times) / len(execution_times) if execution_times else 0,
                'max_execution_time': max(execution_times) if execution_times else 0,
                'avg_search_time': sum(search_times) / len(search_times) if search_times else 0,
                'total_executions': len(execution_times)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting execution metrics: {e}")
            return {}
    
    def _get_rate_limiting_metrics(self) -> Dict:
        """Métricas de rate limiting"""
        # Implementar análise de logs para rate limiting
        return {
            'rate_limit_hits': 0,
            'avg_wait_time': 0,
            'backoff_events': 0
        }
    
    def _get_error_metrics(self) -> Dict:
        """Métricas de erros"""
        if not self.log_path or not os.path.exists(self.log_path):
            return {}
            
        try:
            error_count = 0
            warning_count = 0
            
            with open(self.log_path, 'r') as f:
                for line in f:
                    if 'ERROR' in line:
                        error_count += 1
                    elif 'WARNING' in line:
                        warning_count += 1
            
            return {
                'error_count_24h': error_count,
                'warning_count_24h': warning_count,
                'error_rate': error_count / 1440 if error_count > 0 else 0  # por minuto
            }
            
        except Exception:
            return {}
    
    def _get_quality_metrics(self) -> Dict:
        """Métricas de qualidade"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Distribuição de qualidade (baseado no tamanho do arquivo)
            cursor.execute("""
                SELECT 
                    CASE 
                        WHEN file_size > 50000000 THEN 'high_quality'
                        WHEN file_size > 30000000 THEN 'medium_quality'
                        ELSE 'standard_quality'
                    END as quality,
                    COUNT(*) as count
                FROM downloads 
                WHERE file_size IS NOT NULL AND status = 'SUCCESS'
                GROUP BY quality
            """)
            
            quality_dist = dict(cursor.fetchall())
            
            conn.close()
            
            total = sum(quality_dist.values())
            
            return {
                'quality_distribution': quality_dist,
                'high_quality_rate': quality_dist.get('high_quality', 0) / total if total > 0 else 0
            }
            
        except Exception:
            return {}
    
    def _check_disk_space(self) -> bool:
        """Verifica se há espaço em disco suficiente"""
        try:
            usage = self._get_disk_usage()
            return usage.get('percent_used', 100) < 90
        except Exception:
            return False
    
    def _check_recent_activity(self) -> bool:
        """Verifica se houve atividade recente"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT COUNT(*) FROM downloads 
                WHERE created_at >= datetime('now', '-1 hour')
            """)
            
            recent_count = cursor.fetchone()[0]
            conn.close()
            
            return recent_count > 0
            
        except Exception:
            return False
    
    def _get_health_recommendations(self, health_checks: Dict) -> List[str]:
        """Gera recomendações baseadas nos health checks"""
        recommendations = []
        
        if not health_checks.get('memory_usage_ok'):
            recommendations.append("High memory usage detected. Consider restarting the process.")
        
        if not health_checks.get('cpu_usage_ok'):
            recommendations.append("High CPU usage detected. Check for resource-intensive operations.")
        
        if not health_checks.get('disk_space_ok'):
            recommendations.append("Low disk space. Clean up old files or expand storage.")
        
        if not health_checks.get('cache_healthy'):
            recommendations.append("Low cache hit rate. Consider increasing cache TTL or size.")
        
        if not health_checks.get('recent_activity'):
            recommendations.append("No recent activity detected. Check if the processor is running.")
        
        return recommendations
    
    def _export_to_csv(self, metrics: Dict, output_path: str):
        """Exporta métricas para CSV"""
        import csv
        
        # Flatten metrics for CSV
        flat_metrics = self._flatten_dict(metrics)
        
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Metric', 'Value'])
            for key, value in flat_metrics.items():
                writer.writerow([key, value])
    
    def _flatten_dict(self, d: Dict, parent_key: str = '', sep: str = '.') -> Dict:
        """Achata dicionário aninhado"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)


def main():
    """Função principal para execução standalone"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Playlist Processor Metrics Collector')
    parser.add_argument('--db-path', required=True, help='Path to SQLite database')
    parser.add_argument('--log-path', help='Path to log file')
    parser.add_argument('--output', help='Output file path')
    parser.add_argument('--format', choices=['json', 'csv'], default='json', help='Output format')
    parser.add_argument('--report-days', type=int, default=7, help='Days for report generation')
    parser.add_argument('--action', choices=['collect', 'health', 'report'], default='collect', help='Action to perform')
    
    args = parser.parse_args()
    
    collector = MetricsCollector(args.db_path, args.log_path)
    
    if args.action == 'collect':
        metrics = collector.collect_all_metrics()
        if args.output:
            collector.export_metrics(args.output, args.format)
        else:
            print(json.dumps(metrics, indent=2, default=str))
    
    elif args.action == 'health':
        health = collector.get_health_status()
        print(json.dumps(health, indent=2))
    
    elif args.action == 'report':
        report = collector.generate_report(args.report_days)
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(report, f, indent=2, default=str)
        else:
            print(json.dumps(report, indent=2, default=str))


if __name__ == '__main__':
    main()
