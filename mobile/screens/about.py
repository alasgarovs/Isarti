from kivymd.uix.screen import MDScreen
from kivy.uix.screenmanager import CardTransition
from mobile.app_info import AppName, AppVersion, LastUpdate, FileDescription
from db_connect import *
import webbrowser

class AboutScreen(MDScreen):
    def __init__(self, **kwargs):
        super(AboutScreen, self).__init__(**kwargs)
        self.app_name = f'{AppName}'
        self.app_version = f'Versiya. \n{AppVersion}'
        self.last_update = f'Son yeniləmə. \n{LastUpdate}'
        self.file_description = f'Açıqlama. \n{FileDescription}'
        self.github = f'Github. \n[ref=github_link]https://github.com/alasgarovs/Isarti[/ref]'
        self._initialized = False
    
    def on_enter(self):
        if not self._initialized:
            self.ids.app_name_label.text = self.app_name
            self.ids.app_version_label.text = self.app_version
            self.ids.last_update_label.text = self.last_update
            self.ids.file_description_label.text = self.file_description
            self.ids.github_page_label.text = self.github
            self._initialized = True
    
    def on_leave(self):
        pass
    
    def cleanup(self):
        self._initialized = False
    
    def on_theme_change(self):
        pass
    
    def open_url(self, url):
        webbrowser.open(url)
    
    def navigate_to_profile(self):
        self.manager.transition = CardTransition(direction='right', duration=0.1)
        self.manager.current = 'profile'