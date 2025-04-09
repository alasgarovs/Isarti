from kivymd.uix.screen import MDScreen
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivy.uix.screenmanager import CardTransition
from db_connect import *

DEFAULT_FONT_SIZE = "18sp"

class ConnectionScreen(MDScreen):
    def __init__(self, **kwargs):
        super(ConnectionScreen, self).__init__(**kwargs)
        self.dialog = None
    
    def on_enter(self):
        self.load_connection_settings()
    
    def on_leave(self):
        if self.dialog and self.dialog.content_cls:
            self.dialog.dismiss()
            self.dialog = None
    
    def cleanup(self):
        if self.dialog and self.dialog.content_cls:
            self.dialog.dismiss()
            self.dialog = None
    
    def on_theme_change(self):
        self.load_connection_settings()
    
    def load_connection_settings(self):
        """Load connection settings from database"""
        session = Session()
        try:
            settings = session.query(Settings).first()
            if settings:
                self.ids.device_name.text = settings.device_name
                self.ids.server_ip.text = settings.server_ip
                self.ids.port_number.text = settings.port_number
        finally:
            session.close()
    
    def save_connection(self):
        """Save connection settings to database"""
        device_name = self.ids.device_name.text[:10].strip()
        server_ip = self.ids.server_ip.text[:15].strip()
        port_number = self.ids.port_number.text[:5].strip()
        
        if not device_name:
            self.show_error_dialog("Cihaz adı boş ola bilməz")
            return
        if not server_ip:
            self.show_error_dialog("Server ünvanı boş ola bilməz")
            return
        if not port_number:
            self.show_error_dialog("Port nömrəsi boş ola bilməz")
            return
        
        session = Session()
        try:
            session.query(Settings).update({
                "device_name": device_name,
                "server_ip": server_ip,
                "port_number": port_number
            })
            session.commit()
        finally:
            session.close()
        
        self.show_success_dialog()
    
    def show_error_dialog(self, message):
        """Show error dialog with message"""
        if self.dialog and self.dialog.content_cls:
            self.dialog.dismiss()
        
        self.dialog = MDDialog(
            title="Xəta",
            text=message,
            buttons=[
                MDFlatButton(
                    text="OK",
                    font_size=DEFAULT_FONT_SIZE,
                    on_release=lambda x: self.dialog.dismiss()
                )
            ]
        )
        self.dialog.ids.text.font_size = DEFAULT_FONT_SIZE
        self.dialog.open()
    
    def show_success_dialog(self):
        """Show success dialog"""
        if self.dialog and self.dialog.content_cls:
            self.dialog.dismiss()
        
        self.dialog = MDDialog(
            title="Bildiriş",
            text="Məlumatlar qeyd edildi",
            buttons=[
                MDFlatButton(
                    text="OK",
                    font_size=DEFAULT_FONT_SIZE,
                    on_release=lambda x: self.dialog.dismiss()
                )
            ]
        )
        self.dialog.ids.text.font_size = DEFAULT_FONT_SIZE
        self.dialog.open()
    
    def navigate_to_profile(self):
        """Navigate back to profile screen"""
        self.manager.transition = CardTransition(direction='right', duration=0.1)
        self.manager.current = 'profile'