import socket
import threading
import json
from datetime import datetime
from db_connect import Session, WorkSpaces, Barcodes, Users

class IsartiServer:
    def __init__(self, host='0.0.0.0', port=3344):
        self.host = host
        self.port = port
        self.server_socket = None
        self.is_running = False
        self.thread = None
        self.data_received_callback = None
    
    def start(self):
        """Start the server in a separate thread"""
        if self.is_running:
            return True
        
        self.thread = threading.Thread(target=self._run_server)
        self.thread.daemon = True 
        self.thread.start()
        self.is_running = True
        return True
    
    def stop(self):
        """Stop the server"""
        self.is_running = False
        if self.server_socket:
            self.server_socket.close()
        if self.thread:
            self.thread.join(timeout=1.0)


    def _run_server(self):
        """Run the server loop in a thread"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.server_socket.settimeout(1.0)  
            
            while self.is_running:
                try:
                    client_socket, client_address = self.server_socket.accept()
                    client_handler = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket, client_address)
                    )
                    client_handler.daemon = True
                    client_handler.start()
                except socket.timeout:
                    continue 
                except Exception:
                    pass 
                    
        except Exception:
            pass  
        finally:
            if self.server_socket:
                self.server_socket.close()
            self.is_running = False
    
    def _handle_client(self, client_socket, address):
        """Handle communication with a client"""
        try:
            buffer = b""
            while True:
                data = client_socket.recv(4096)
                if not data:
                    break
                
                buffer += data
                
                try:
                    decoded_data = buffer.decode('utf-8')
                    
                    if '\n' in decoded_data:
                        messages = decoded_data.split('\n')
                        for i, message in enumerate(messages[:-1]):
                            if message.strip(): 
                                self._process_message(message.strip(), client_socket)
                        
                        buffer = messages[-1].encode('utf-8')
                except UnicodeDecodeError:
                    pass
                
        except Exception:
            pass
        finally:
            client_socket.close()
    
    def _process_message(self, message, client_socket):
        """Process a complete message from client"""
        try:
            data = json.loads(message)
            message_type = data.get('type')
            
            if message_type == 'workspace':
                self._handle_workspace(data, client_socket)
            elif message_type == 'barcode':
                self._handle_barcode(data, client_socket)
            elif message_type == 'get_users':
                self._handle_get_users(client_socket)
            else:
                self._send_response(client_socket, success=False, message="Unknown message type")
                
        except json.JSONDecodeError:
            self._send_response(client_socket, success=False, message="Invalid JSON format")
        except Exception as e:
            self._send_response(client_socket, success=False, message=str(e))

    def _handle_get_users(self, client_socket):
        """Handle request to get all users"""
        try:
            with Session() as session:
                users = session.query(Users).all()
                user_list = []
                for user in users:
                    user_data = {
                        "id": user.id,
                        "username": user.name,
                        "password": user.password
                    }
                    user_list.append(user_data)
                
                self._send_response(
                    client_socket, 
                    success=True, 
                    message="Users retrieved successfully",
                    data={"users": user_list}
                )
        except Exception as e:
            self._send_response(client_socket, success=False, message=f"Error retrieving users: {str(e)}")

    
    def _handle_workspace(self, data, client_socket):
        """Handle workspace data"""
        try:
            workspace_name = data.get('name')
            username = data.get('user')
            date_string = data.get('date')
            created_date = datetime.strptime(date_string, "%Y-%m-%d")
            
            if not workspace_name or not username:
                self._send_response(client_socket, success=False, message="Missing required fields")
                return
            
            with Session() as session:
                workspace = WorkSpaces(
                    name=workspace_name,
                    user=username,
                    created_date=created_date
                )
                session.add(workspace)
                session.commit()
                workspace_id = workspace.id
                message = "Workspace created"
                
                self._send_response(
                    client_socket, 
                    success=True, 
                    message=message,
                    data={"workspace_id": workspace_id}
                )
                
        except Exception as e:
            print(str(e))
            self._send_response(client_socket, success=False, message=f"Database error: {str(e)}")
    
    def _handle_barcode(self, data, client_socket):
        """Handle barcode data"""
        try:
            barcode_code = data.get('code')
            count = data.get('count', 1)
            workspace_id = data.get('workspace_id')
            
            if not barcode_code or not workspace_id:
                self._send_response(client_socket, success=False, message="Missing required fields")
                return
            
            with Session() as session:
                workspace = session.query(WorkSpaces).filter(WorkSpaces.id == workspace_id).first()
                if not workspace:
                    self._send_response(client_socket, success=False, message=f"Workspace not found")
                    return
                

                barcode = Barcodes(
                    code=barcode_code,
                    count=count,
                    workspace_id=workspace_id
                )
                session.add(barcode)
                session.flush()
                barcode_id = barcode.id
                message = "Barcode added"
            
                session.commit()

                self._send_response(
                    client_socket, 
                    success=True, 
                    message=message,
                    data={"barcode_id": barcode_id}
                )
                
        except Exception as e:
            self._send_response(client_socket, success=False, message=f"Database error: {str(e)}")
    
    def _send_response(self, client_socket, success, message, data=None):
        """Send a JSON response to the client"""
        response = {
            "success": success,
            "message": message
        }
        
        if data:
            response["data"] = data
            
        try:
            response_json = json.dumps(response)
            client_socket.sendall((response_json + "\n").encode('utf-8'))
        except Exception:
            pass