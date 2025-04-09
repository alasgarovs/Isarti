from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel, MDIcon
from kivymd.uix.card.card import MDSeparator
from kivy.uix.screenmanager import FadeTransition
from kivymd.uix.button import MDTextButton
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.metrics import dp
from kivy.clock import Clock
from db_connect import *

ROW_HEIGHT = dp(40)
DEFAULT_FONT_SIZE = "18sp"
ICON_SIZE = [dp(30), dp(30)]

class StockRow(RecycleDataViewBehavior, MDBoxLayout):
    def __init__(self, parent_screen, **kwargs):
        super(StockRow, self).__init__(**kwargs)
        self.parent_screen = parent_screen
        self.orientation = 'vertical'
        self.stock_id = None
        self.stock_name = None

    def refresh_view_attrs(self, rv, index, data):
        self.stock_id = data['id']
        self.stock_name = data['name']
        
        self.clear_widgets()
        
        row_layout = MDBoxLayout(size_hint_y=None, height=ROW_HEIGHT)
        self.add_widget(MDSeparator(height=dp(1)))
        
        row_layout.add_widget(MDIcon(
            icon="file-document-outline",
            theme_text_color="Primary",
            size=ICON_SIZE,
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            padding=[0, 0, dp(5), 0]
        ))
        
        self.stock_btn = MDTextButton(
            text=data['name'],
            font_size=DEFAULT_FONT_SIZE,
            halign='left',
            theme_text_color="Primary",
            pos_hint={"center_x": 0.5, "center_y": 0.5}
        )
        self.stock_btn.bind(on_release=self.on_button_release)
        
        row_layout.add_widget(self.stock_btn)
        self.add_widget(row_layout)

    def on_button_release(self, instance):
        if self.parent_screen:
            self.parent_screen.load_workspace(self.stock_id)

class HomeScreen(MDScreen):
    def __init__(self, **kwargs):
        super(HomeScreen, self).__init__(**kwargs)
        self._data_loaded = False
    
    def on_enter(self):
        session = Session()
        try:
            settings = session.query(Settings).first()
            if settings:
                settings.current_workspace_id = 0
                session.commit()
        finally:
            session.close()
        
        self.load_workspaces_data()
    
    def on_leave(self):
        pass
    
    def cleanup(self):
        if hasattr(self.ids, 'stock_rv'):
            self.ids.stock_rv.data = []
        self._data_loaded = False
    
    def on_theme_change(self):
        self.load_workspaces_data()
    
    def load_workspaces_data(self):
        if self._data_loaded:
            return
            
        session = Session()
        try:
            settings = session.query(Settings).first()
            if not settings:
                return
            
            workspaces = session.query(
                WorkSpaces.id, WorkSpaces.name
            ).filter_by(
                user=settings.current_user
            ).order_by(
                desc(WorkSpaces.id)
            ).all()
            
            data = [{'id': w.id, 'name': w.name} for w in workspaces]
            
            self.ids.stock_rv.data = data
            self._data_loaded = True
            
        finally:
            session.close()

    def on_kv_post(self, base_widget):
        self.ids.stock_rv.viewclass = lambda: StockRow(self)

    def load_workspace(self, workspace_id):
        session = Session()
        try:
            session.query(Settings).update({"current_workspace_id": workspace_id})
            session.commit()
        finally:
            session.close()
        
        self.manager.transition = FadeTransition(duration=0.2)
        self.manager.current = 'workspace'