import socket
import json
import sys
from datetime import datetime
from db_connect import Session, WorkSpaces, Barcodes

class IsartiClient:
    def __init__(self, server_ip, port=3344):
        self.server_ip = server_ip
        self.port = port
        self.socket = None
        self.success_messages = []
        self.error_messages = []
    
    def connect(self):
        """Connect to the server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.server_ip, self.port))
            self.success_messages.append("Serverə qoşuldu")
            return True
        except Exception as e:
            self.error_messages.append(f"Bağlantı xətası: {e}")
            return False
    
    def disconnect(self):
        """Close the connection"""
        if self.socket:
            self.socket.close()
            self.socket = None
            self.success_messages.append("Serverdən ayrıldı")
    
    def send_workspace(self, workspace_id):
        """Send a workspace to the server"""
        if not self.socket and not self.connect():
            return False
        
        session = Session()
        try:
            workspace = session.query(WorkSpaces).filter(WorkSpaces.id == workspace_id).first()
            if not workspace:
                self.error_messages.append(f"Bazada {workspace_id} nömrəsi anbar tapılmadı")
                return False
            
            data = {
                "type": "workspace",
                "name": workspace.name,
                "user": workspace.user,
                "date": str(workspace.created_date)
            }
            
            try:
                json_data = json.dumps(data) + "\n"
                self.socket.sendall(json_data.encode('utf-8'))
                
                response = self._receive_response()
                if response and response.get("success"):
                    self.success_messages.append(f"{workspace_id} nömrəli anbar uğurla köçürüldü")
                    return response.get("data", {}).get("workspace_id")
                self.error_messages.append(f"Məlumatlar köçürülə bilmədi: {response.get('message') if response else 'Cavab yoxdur'}")
                return False
            except Exception as e:
                self.error_messages.append(f"Xəta baş verdi: {e}")
                self.disconnect()
                return False
        finally:
            session.close()
    
    def send_barcodes(self, workspace_id, server_workspace_id):
        """Send all barcodes for a workspace to the server"""
        if not self.socket and not self.connect():
            return 0
        
        session = Session()
        try:
            barcodes = session.query(Barcodes).filter(Barcodes.workspace_id == workspace_id).all()
            
            if not barcodes:
                self.error_messages.append(f"{workspace_id} nömrəli anbarda barkod tapılamdı")
                return 0
                
            self.success_messages.append(f"{len(barcodes)} ədəd barkod köçürüldü")
            
            success_count = 0
            for barcode in barcodes:
                data = {
                    "type": "barcode",
                    "workspace_id": server_workspace_id,
                    "code": barcode.code,
                    "count": barcode.count
                }
                
                try:
                    json_data = json.dumps(data) + "\n"
                    self.socket.sendall(json_data.encode('utf-8'))
                    
                    response = self._receive_response()
                    if response and response.get("success"):
                        success_count += 1
                except Exception as e:
                    self.error_messages.append(f"Barkodlar köçürülmədi: {e}")
                    self.disconnect()
                    return success_count
            
            self.success_messages.append(f"{success_count} ədəd barkod uğurla köçürüldü")
            return success_count
        
        finally:
            session.close()
    
    def _receive_response(self):
        """Receive and parse response from server"""
        buffer = b""
        try:
            while True:
                chunk = self.socket.recv(4096)
                if not chunk:
                    break
                
                buffer += chunk
                
                try:
                    decoded = buffer.decode('utf-8')
                    if '\n' in decoded:
                        message, remainder = decoded.split('\n', 1)
                        return json.loads(message)
                except (UnicodeDecodeError, json.JSONDecodeError):
                    continue
            
            return None
        except Exception as e:
            self.error_messages.append(f"Əlaqədə xəta baş verdi: {e}")
            return None


    def get_users(self):
        """Get all users from the server"""
        if not self.socket and not self.connect():
            return []
        
        data = {
            "type": "get_users"
        }

        try:
            json_data = json.dumps(data) + "\n"
            self.socket.sendall(json_data.encode('utf-8'))
            
            response = self._receive_response()
            if response and response.get("success"):
                self.success_messages.append("İstifadəçi siyahısı uğurla köçürüldü")
                return response.get("data", {}).get("users", [])
            
            self.error_messages.append(f"İstifadəçilər köçürülə bilmədi: {response.get('message') if response else 'Cavab yoxdur'}")
            return []
        except Exception as e:
            self.error_messages.append(f"İstifadəçi məlumatları köçürülərkən xəta: {e}")
            self.disconnect()
            return []


def send_workspace_to_server(server_ip, workspace_id, port=3344):
    """Send a specific workspace from local database to server"""
    client = IsartiClient(server_ip, port)
    
    if not client.connect():
        return {
            "status": "error",
            "message": "Serverə qoşula bilmədi"
        }

    session = Session()
    try:
        workspace = session.query(WorkSpaces).filter(WorkSpaces.id == workspace_id).first()
        
        if not workspace:
            client.disconnect()
            return {
                "status": "error",
                "message": f"{workspace_id} nömrəli anbar tapılmadı"
            }
        
        server_workspace_id = client.send_workspace(workspace.id)
        
        if server_workspace_id:
            barcode_count = client.send_barcodes(workspace.id, server_workspace_id)
            client.disconnect()
            return {
                "status": "success",
                "message": f"'{workspace.name}' adlı anbar {barcode_count} ədəd barkod ilə uğurla köçürüldü"
            }
        else:
            client.disconnect()
            return {
                "status": "error",
                "message": f"'{workspace.name}' adlı anbar köçürülə bilmədi"
            }
    finally:
        session.close()
        

def get_users_from_server(server_ip, port=3344):
    client = IsartiClient(server_ip, port)
    
    if not client.connect():
        return {
            "status": "error",
            "message": "Serverə qoşula bilmədi"
        }
    
    users = client.get_users()
    client.disconnect()
    
    if users:
        return {
            "status": "success",
            "message": f"{len(users)} istifadəçi məlumatı köçürüldü",
            "data": users
        }
    else:
        return {
            "status": "error",
            "message": "İstifadəçi məlumatları köçürülə bilmədi"
        }