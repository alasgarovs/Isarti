from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivy.uix.screenmanager import FadeTransition
import re
from db_connect import *

DEFAULT_FONT_SIZE = "18sp"

class LoginScreen(MDScreen):
    def __init__(self, **kwargs):
        super(LoginScreen, self).__init__(**kwargs)
        self.dialog = None
        self.username_pattern = re.compile(r"^[a-zA-Z]+$")
    
    def on_enter(self):
        self.ids.username.text = ""
        self.ids.password.text = ""
        
        if self.dialog and self.dialog.content_cls:
            self.dialog.dismiss()
            self.dialog = None
    
    def on_leave(self):
        if self.dialog and self.dialog.content_cls:
            self.dialog.dismiss()
            self.dialog = None
    
    def cleanup(self):
        if self.dialog and self.dialog.content_cls:
            self.dialog.dismiss()
            self.dialog = None
    
    def login(self):
        """Handle login process"""
        username = self.ids.username.text[:15].strip()
        password = self.ids.password.text[:10].strip()
        
        if not username or not password:
            self.show_error_dialog("İstifadəçi adı və şifrəni daxil edin")
            return
        
        session = Session()
        try:
            user = session.query(Users).filter_by(
                username=username,
                password=password
            ).first()
            
            if user:
                session.query(Settings).update({
                    "current_user": username,
                    "is_logged_in": True
                })
                session.commit()
                
                self.manager.transition = FadeTransition(duration=0.2)
                self.manager.current = 'profile'
                
                app = MDApp.get_running_app()
                app.nav_bar.show_icons()

                welcome_dialog = MDDialog(
                    title='Hesaba giriş',
                    text=f'Xoş gəldin {username}! İndi davam edə bilərik',
                    buttons=[
                        MDFlatButton(
                            text="OK",
                            font_size=DEFAULT_FONT_SIZE,
                            on_release=lambda x: welcome_dialog.dismiss()
                        ),
                    ],
                )
                welcome_dialog.ids.text.font_size = DEFAULT_FONT_SIZE
                        
                welcome_dialog.open()

            else:
                self.show_error_dialog("İstifadəçi adı və ya şifrə düzgün deyil")
        finally:
            session.close()
    
    def filter_username(self, text, instance=None):
        """Filter username to allow only letters"""
        if instance is None:
            instance = self.ids.username
        
        if not self.username_pattern.match(text):
            instance.text = re.sub(r"[^a-zA-Z]", "", text)
    
    def show_error_dialog(self, message):
        """Show error dialog with message"""
        if self.dialog and self.dialog.content_cls:
            self.dialog.dismiss()
        
        self.dialog = MDDialog(
            title="Giriş xətası",
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