"""
Railway CLIクライアント
"""
import json
import logging
import subprocess
from typing import Dict, List, Optional


class RailwayClient:
    """Railway CLIクライアント"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def is_cli_available(self) -> bool:
        """Railway CLIが利用可能かチェック"""
        try:
            result = subprocess.run(
                ["railway", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception as e:
            self.logger.error(f"Railway CLI check failed: {e}")
            return False
    
    def login_if_needed(self) -> bool:
        """必要に応じてログイン"""
        try:
            # ログイン状態をチェック
            result = subprocess.run(
                ["railway", "whoami"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                self.logger.info("Already logged in to Railway")
                return True
            else:
                self.logger.info("Not logged in, attempting login...")
                login_result = subprocess.run(
                    ["railway", "login"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                return login_result.returncode == 0
                
        except Exception as e:
            self.logger.error(f"Login check failed: {e}")
            return False
    
    def get_logs(self, limit: int = 100) -> List[Dict]:
        """ログを取得"""
        try:
            cmd = ["railway", "logs", "--limit", str(limit)]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                self.logger.error(f"Failed to get logs: {result.stderr}")
                return []
            
            # ログの解析（簡易版）
            logs = []
            lines = result.stdout.strip().split('\n')
            
            for line in lines:
                if line.strip():
                    # タイムスタンプとメッセージを抽出
                    parts = line.split(' ', 2)
                    if len(parts) >= 3:
                        timestamp = parts[0] + ' ' + parts[1]
                        message = parts[2]
                        
                        # ログレベルを推定
                        level = "INFO"
                        if any(keyword in message.lower() for keyword in ["error", "failed", "exception"]):
                            level = "ERROR"
                        elif any(keyword in message.lower() for keyword in ["warn", "warning"]):
                            level = "WARN"
                        
                        logs.append({
                            "timestamp": timestamp,
                            "message": message,
                            "level": level,
                            "service": "railway"
                        })
            
            return logs
            
        except Exception as e:
            self.logger.error(f"Error getting logs: {e}")
            return []
    
    def get_project_info(self) -> Optional[Dict]:
        """プロジェクト情報を取得"""
        try:
            result = subprocess.run(
                ["railway", "status"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                self.logger.error(f"Failed to get project info: {result.stderr}")
                return None
            
            # プロジェクト情報の解析（簡易版）
            # プロジェクト情報の解析（簡易版）
            info = {
                "name": os.getenv("RAILWAY_PROJECT_NAME", "Railway Project"),
                "services": []
            }
            
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if "Service:" in line:
                    service_name = line.split("Service:")[1].strip()
                    info["services"].append({"name": service_name})
            
            return info
            
        except Exception as e:
            self.logger.error(f"Error getting project info: {e}")
            return None
    
    def get_service_info(self, service_id: str) -> Optional[Dict]:
        """サービス情報を取得"""
        try:
            result = subprocess.run(
                ["railway", "status", "--service", service_id],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                self.logger.error(f"Failed to get service info: {result.stderr}")
                return None
            
            # サービス情報の解析（簡易版）
            info = {
                "status": "running",
                "url": "https://price-comparison-app-production.up.railway.app"
            }
            
            return info
            
        except Exception as e:
            self.logger.error(f"Error getting service info: {e}")
            return None