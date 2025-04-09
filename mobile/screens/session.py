from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.dialog import MDDialog
from kivymd.uix.pickers import MDDatePicker
from kivymd.uix.button import MDFlatButton
from kivy.uix.screenmanager import FadeTransition
from db_connect import *

DEFAULT_FONT_SIZE = "18sp"
TRANSITION_DURATION = 0.2

class SessionScreen(MDScreen):
    def __init__(self, **kwargs):
        super(SessionScreen, self).__init__(**kwargs)
        self.dialog = None
        self._selected_date = None
    
    def on_enter(self):
        """Load user information and reset form when entering the screen"""
        self.reset_form()
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
        self._selected_date = None
    
    def on_theme_change(self):
        """Handle theme changes"""
        self.load_user_info()
    
    def reset_form(self):
        """Reset form fields"""
        self.ids.workspace_name.text = ""
        self.ids.workspace_date.text = ""
        self._selected_date = None
    
    def load_user_info(self):
        """Load current user information"""
        session = Session()
        try:
            user = session.query(Settings).first()
            if user and user.current_user:
                self.ids.workspace_user.text = f"Salam, {user.current_user}"
        finally:
            session.close()
    
    def create_session(self):
        """Create a new workspace session"""
        workspace_name = self.ids.workspace_name.text[:20].strip()
        workspace_date = self.ids.workspace_date.text
        
        if not workspace_name or not workspace_date:
            self.show_error_dialog("Anbar adını və tarixi daxil edin")
            return
        
        if not self._selected_date:
            self.show_error_dialog("Zəhmət olmasa tarix seçin")
            return
        
        session = Session()
        try:
            settings = session.query(Settings).first()
            if not settings or not settings.current_user:
                self.show_error_dialog("İstifadəçi tapılmadı")
                return
            
            new_workspace = WorkSpaces(
                name=workspace_name,
                created_date=self._selected_date,
                user=settings.current_user
            )
            session.add(new_workspace)
            session.commit()
            
            workspace_id = new_workspace.id
            
            settings.current_workspace_id = workspace_id
            session.commit()

            self.manager.transition = FadeTransition(duration=TRANSITION_DURATION)
            self.manager.current = 'workspace'
        finally:
            session.close()
    
    def show_date_picker(self):
        """Show date picker dialog"""
        app = MDApp.get_running_app()

        primary_color = app.theme_cls.bg_dark if app.theme_cls.theme_style == "Dark" else app.theme_cls.bg_light
        selector_color = app.theme_cls.bg_dark if app.theme_cls.theme_style == "Dark" else app.theme_cls.primary_color
        
        date_dialog = MDDatePicker(
            title='Tarix Seç',
            title_input='Tarix seç',
            primary_color=primary_color,
            selector_color=selector_color,
            text_toolbar_color=app.theme_cls.primary_color,
            text_button_color=app.theme_cls.primary_color,
            input_field_background_color=app.theme_cls.primary_color
        )
        date_dialog.bind(on_save=self.on_date_save)
        date_dialog.open()
    
    def on_date_save(self, instance, value, date_range):
        """Handle date selection"""
        self.ids.workspace_date.text = value.strftime("%Y-%m-%d")
        self._selected_date = value
    
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