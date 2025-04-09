from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivy.uix.screenmanager import FadeTransition, CardTransition
from kivy.clock import Clock
from db_connect import *
from .client import *
import threading

DEFAULT_FONT_SIZE = "18sp"
TRANSITION_DURATION = 0.2

class ProfileScreen(MDScreen):
    def __init__(self, **kwargs):
        super(ProfileScreen, self).__init__(**kwargs)
        self.dialog = None
    
    def on_enter(self):
        """Load user information when entering the screen"""
        self.load_user_info()
    
    def on_leave(self):
        """Clean up resources when leaving the screen"""
        if self.dialog and self.dialog.content_cls:
            self.dialog.dismiss()
            self.dialog = None
    
    def cleanup(self):
        """Reset screen state when screen is recycled"""
        if self.dialog and self.dialog.content_cls:
            self.dialog.dismiss()
            self.dialog = None
    
    def on_theme_change(self):
        """Handle theme changes if needed"""
        pass
    
    def load_user_info(self):
        """Load current user information"""
        session = Session()
        try:
            settings = session.query(Settings).first()
            if settings and settings.current_user:
                self.ids.user_label.text = settings.current_user
        finally:
            session.close()
    
    def logout(self):
        """Show logout confirmation dialog"""
        
        self.dialog = MDDialog(
            title="Hesabdan çıxış",
            text="Çıxış etmək istəyirsiniz?",
            buttons=[
                MDFlatButton(
                    text="LƏĞV ET",
                    font_size=DEFAULT_FONT_SIZE,
                    on_release=lambda x: self.dialog.dismiss()
                ),
                MDFlatButton(
                    text="TƏSDİQLƏ",
                    font_size=DEFAULT_FONT_SIZE,
                    on_release=lambda x: self.confirm_logout()
                ),
            ],
        )
        self.dialog.ids.text.font_size = DEFAULT_FONT_SIZE
        self.dialog.open()
    
    def confirm_logout(self):
        """Process logout confirmation"""
        self.dialog.dismiss()
        self.dialog = None
        
        session = Session()
        try:
            session.query(Settings).update({
                "is_logged_in": 0,
                "current_user": None
            })
            session.commit()
        finally:
            session.close()
        
        app = MDApp.get_running_app()
        app.nav_bar.hide_icons()
        
        self.manager.transition = FadeTransition(duration=TRANSITION_DURATION)
        self.manager.current = 'login'
    
    def navigate_to_page(self, signal):
        """Navigate to different pages based on signal"""
        self.manager.transition = CardTransition(direction='left', duration=TRANSITION_DURATION)
        
        if signal == "connect":
            self.manager.current = 'connection'
        else:
            self.manager.current = 'about'

    def show_error_dialog(self, message):
        dialog = MDDialog(
            title="Xəta",
            text=message,
            buttons=[
                MDFlatButton(
                    text="OK",
                    font_size=DEFAULT_FONT_SIZE,
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.ids.text.font_size = DEFAULT_FONT_SIZE
        dialog.open()

    def fetch_users(self):
        session = Session()
        try:
            settings = session.query(Settings).first()
            if settings:
                if settings.server_ip == '255.255.255.255':
                    self.show_error_dialog("Bağlantı ünvanı düzgün deyil")
                    return
                    
                self.progress_dialog = MDDialog(
                    title="İstifadəçilər köçürülür",
                    text="Zəhmət olmasa, gözləyin...",
                    auto_dismiss=False
                )
                self.progress_dialog.ids.text.font_size = DEFAULT_FONT_SIZE
                self.progress_dialog.open()
                
                self.server_ip = settings.server_ip
                self.port = int(settings.port_number)

                threading.Thread(target=self.run_fetch_users).start()
        finally:
            session.close()


    def run_fetch_users(self):
        result = get_users_from_server(self.server_ip, self.port)
        
        Clock.schedule_once(lambda dt: self.show_users_result(result), 0)

    def show_users_result(self, result):
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.dismiss()
        
        if result["status"] == "success":
            users = result.get("data", [])
            self.save_users(users)
        else:
            self.show_error_dialog(result['message'])

    def save_users(self, users):
        """Save users received from server to local database"""
        try:
            session = Session()
            saved_count = 0
            updated_count = 0
            
            for user_data in users:
                username = user_data.get('username')
                password = user_data.get('password')
                
                if not username or not password:
                    continue

                existing_user = session.query(Users).filter_by(username=username).first()
                
                if existing_user:
                    existing_user.password = password
                    updated_count += 1
                else:
                    new_user = Users(
                        username=username,
                        password=password
                    )
                    session.add(new_user)
                    saved_count += 1
            
            session.commit()
            
            result_text = f"{saved_count} yeni istifadəçi əlavə edildi, {updated_count} istifadəçi yeniləndi."
            success_dialog = MDDialog(
                title="Uğurlu əməliyyat",
                text=result_text,
                buttons=[
                    MDFlatButton(
                        text="OK",
                        font_size=DEFAULT_FONT_SIZE,
                        on_release=lambda x: success_dialog.dismiss()
                    ),
                ],
            )
            success_dialog.ids.text.font_size = DEFAULT_FONT_SIZE
            success_dialog.open()
            
        except Exception as e:
            error_dialog = MDDialog(
                title="Xəta",
                text=f"İstifadəçilər saxlanarkən xəta baş verdi: {str(e)}",
                buttons=[
                    MDFlatButton(
                        text="OK",
                        font_size=DEFAULT_FONT_SIZE,
                        on_release=lambda x: error_dialog.dismiss()
                    ),
                ],
            )
            error_dialog.ids.text.font_size = DEFAULT_FONT_SIZE
            error_dialog.open()
        finally:
            session.close()
