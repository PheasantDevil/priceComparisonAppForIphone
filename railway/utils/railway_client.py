"""
Railway CLIクライアントユーティリティ
"""
import json
import logging
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from ..config.settings import railway_config


class RailwayClient:
    """Railway CLIクライアントクラス"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {
            'project_id': railway_config.project_id,
            'service_id': railway_config.service_id,
            'environment': railway_config.environment
        }
        self.logger = logging.getLogger(__name__)
    
    def get_logs(self, limit: Optional[int] = None, 
                 since: Optional[datetime] = None) -> List[Dict]:
        """ログを取得"""
        try:
            cmd = self._build_logs_command(limit, since)
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                self.logger.error(f"Railway CLI error: {result.stderr}")
                return []
            
            return self._parse_logs(result.stdout)
            
        except subprocess.TimeoutExpired:
            self.logger.error("Timeout getting logs from Railway CLI")
            return []
        except Exception as e:
            self.logger.error(f"Error getting logs: {e}")
            return []
    
    def get_service_logs(self, service_id: str, limit: Optional[int] = None,
                        since: Optional[datetime] = None) -> List[Dict]:
        """特定サービスのログを取得"""
        try:
            cmd = self._build_logs_command(limit, since, service_id)
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                self.logger.error(f"Railway CLI error for service {service_id}: {result.stderr}")
                return []
            
            return self._parse_logs(result.stdout)
            
        except subprocess.TimeoutExpired:
            self.logger.error(f"Timeout getting logs for service {service_id}")
            return []
        except Exception as e:
            self.logger.error(f"Error getting logs for service {service_id}: {e}")
            return []
    
    def get_project_info(self) -> Optional[Dict]:
        """プロジェクト情報を取得"""
        try:
            cmd = ['railway', 'status', '--project', self.config['project_id'], '--json']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                self.logger.error(f"Error getting project info: {result.stderr}")
                return None
            
            return json.loads(result.stdout)
            
        except Exception as e:
            self.logger.error(f"Error getting project info: {e}")
            return None
    
    def get_service_info(self, service_id: str) -> Optional[Dict]:
        """サービス情報を取得"""
        try:
            cmd = [
                'railway', 'service', '--project', self.config['project_id'],
                '--service', service_id, '--json'
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                self.logger.error(f"Error getting service info: {result.stderr}")
                return None
            
            return json.loads(result.stdout)
            
        except Exception as e:
            self.logger.error(f"Error getting service info: {e}")
            return None
    
    def _build_logs_command(self, limit: Optional[int], since: Optional[datetime],
                           service_id: Optional[str] = None) -> List[str]:
        """ログ取得コマンドを構築"""
     def _build_logs_command(self, limit: Optional[int], since: Optional[datetime],
                             service_id: Optional[str] = None) -> List[str]:
         """ログ取得コマンドを構築"""
+        if not self.config.get('project_id'):
+            raise ValueError("project_id is required for Railway commands")
+
         cmd = [
             'railway', 'logs',
             '--project', self.config['project_id'],
             '--json'
         ]
        
        if service_id:
            cmd.extend(['--service', service_id])
        elif self.config['service_id']:
            cmd.extend(['--service', self.config['service_id']])
        
        if limit:
            cmd.extend(['--limit', str(limit)])
        
        if since:
            # ISO形式のタイムスタンプに変換
            since_str = since.isoformat()
            cmd.extend(['--since', since_str])
        
        return cmd
    
    def _parse_logs(self, output: str) -> List[Dict]:
        """ログ出力をパース"""
        logs = []
        
        for line in output.strip().split('\n'):
            if not line.strip():
                continue
            
            try:
                log_entry = json.loads(line)
                logs.append(log_entry)
            except json.JSONDecodeError as e:
                self.logger.warning(f"Failed to parse log line: {e}")
                continue
        
        return logs
    
    def is_cli_available(self) -> bool:
        """Railway CLIが利用可能かチェック"""
        try:
            result = subprocess.run(['railway', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except Exception:
            return False
    
    def login_if_needed(self) -> bool:
        """必要に応じてログイン"""
        try:
            # ログイン状態をチェック
            result = subprocess.run(
                ['railway', 'whoami'],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode != 0:
                self.logger.info("Railway CLI login required")
                self.logger.warning("Please run 'railway login' manually to authenticate")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking Railway CLI login: {e}")
            return False