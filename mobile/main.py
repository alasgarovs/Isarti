from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.anchorlayout import MDAnchorLayout
from kivymd.uix.screenmanager import MDScreenManager
from kivy.uix.screenmanager import FadeTransition
from kivy.core.window import Window
from screens.login import LoginScreen
from screens.home import HomeScreen
from screens.profile import ProfileScreen
from screens.about import AboutScreen
from screens.connection import ConnectionScreen
from screens.session import SessionScreen
from screens.workspace import WorkSpaceScreen
from db_connect import *
from style import load_all_kv_files
from kivy.factory import Factory
import gc

# Define navigation bar
class NavigationBar(MDAnchorLayout):
    def __init__(self, screen_manager, **kwargs):
        super(NavigationBar, self).__init__(**kwargs)
        self.screen_manager = screen_manager
        self.anchor_x = 'center'
        self.active_icon = None
        self._previous_screen = None

    def change_screen(self, screen_name):
        # Store previous screen for cleanup
        self._previous_screen = self.screen_manager.current
                
        # Change to the requested screen
        self.screen_manager.transition = FadeTransition(duration=0.1)
        self.screen_manager.current = screen_name

    
    def show_icons(self):
        for child in self.children[0].children: 
            child.opacity = 1
            child.disabled = False
    
    def hide_icons(self):
        for child in self.children[0].children:
            child.opacity = 0
            child.disabled = True


# Main App class
class Main(MDApp):
    def __init__(self, **kwargs):
        super(Main, self).__init__(**kwargs)
        self.sm = None
        self.nav_bar = None
        self.previous_screen = None
    
    def build(self):
        load_all_kv_files()
        self.theme_cls.accent_palette = "BlueGray"
        self.load_theme()
        
        # Create screen manager
        self.sm = MDScreenManager()
        
        # Add screens
        self.sm.add_widget(LoginScreen(name='login'))
        self.sm.add_widget(HomeScreen(name='home'))
        self.sm.add_widget(ProfileScreen(name='profile'))
        self.sm.add_widget(ConnectionScreen(name='connection'))
        self.sm.add_widget(AboutScreen(name='about'))
        self.sm.add_widget(WorkSpaceScreen(name='workspace'))
        self.sm.add_widget(SessionScreen(name='session'))

        # Check if user is already logged in
        is_logged_in = self.check_login_status()
        
        # Create the navigation bar
        self.nav_bar = NavigationBar(self.sm)
        
        # Create the root layout
        root = MDBoxLayout(orientation='vertical')
        root.add_widget(self.sm)
        root.add_widget(self.nav_bar)
        
        # Set initial screen and navbar visibility based on login status
        self.sm.current = 'home' if is_logged_in else 'login'
        if is_logged_in:
            self.nav_bar.show_icons()
        else:
            self.nav_bar.hide_icons()
            
        # Bind to screen changes to update icon visibility and manage screens
        self.sm.bind(current=lambda instance, value: self.on_screen_change(value))
        
        return root
    
    def on_screen_change(self, screen_name):
        """Handle screen changes - update icons and manage screen lifecycle"""
        # Update navigation icons visibility
        self.update_icons_visibility(screen_name)
        
        # Handle screen-specific cleanup for the previous screen
        if hasattr(self, 'previous_screen') and self.previous_screen and self.previous_screen != screen_name:
            # Check if previous screen still exists
            if self.previous_screen in self.sm.screen_names:
                old_screen = self.sm.get_screen(self.previous_screen)
                
                # Trigger any cleanup methods on the screen being left
                if hasattr(old_screen, 'cleanup'):
                    old_screen.cleanup()
        
        # Store current screen name for next change
        self.previous_screen = screen_name
        
        # Force garbage collection after screen change
        gc.collect()
    
    def update_icons_visibility(self, screen_name):
        is_logged_in = self.check_login_status()
        if screen_name == 'login' or not is_logged_in:
            self.nav_bar.hide_icons()
        else:
            self.nav_bar.show_icons()
            
    def check_login_status(self):
        session = Session()
        try:
            settings = session.query(Settings).first()
            if settings and settings.is_logged_in:
                return True
            return False
        finally:
            session.close()
    
    def toggle_theme(self, *args):
        if self.theme_cls.theme_style == "Dark":
            self.theme_cls.primary_palette = "BlueGray"
            self.theme_cls.primary_hue = "900"
            self.theme_cls.theme_style = "Light"
            theme = 'Light'
        else:
            self.theme_cls.primary_palette = "BlueGray"
            self.theme_cls.primary_hue = "50"
            self.theme_cls.theme_style = "Dark"
            theme = 'Dark'
        
        current_screen = self.sm.current_screen
        if hasattr(current_screen, 'on_theme_change'):
            current_screen.on_theme_change()
        else:
            current_screen.dispatch('on_enter')
        
        session = Session()
        try:
            settings = session.query(Settings).first()
            if settings:
                settings.theme = theme
                session.commit()
        finally:
            session.close()
    
    def load_theme(self):
        session = Session()
        try:
            theme = session.query(Settings).first()

            if theme and theme.theme == "Dark":
                self.theme_cls.primary_palette = "BlueGray"
                self.theme_cls.primary_hue = "50"
                self.theme_cls.theme_style = "Dark"
            else:
                self.theme_cls.primary_palette = "BlueGray"
                self.theme_cls.primary_hue = "900"
                self.theme_cls.theme_style = "Light"
        finally:
            session.close()

    def on_stop(self):
        engine.dispose()
        
        gc.collect()


if __name__ == '__main__':
    Main().run()