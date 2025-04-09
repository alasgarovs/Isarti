from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.screen import MDScreen
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.uix.label import MDLabel, MDIcon
from kivymd.uix.card.card import MDSeparator
from kivymd.uix.pickers import MDDatePicker
from kivymd.uix.button import MDFlatButton, MDIconButton, MDTextButton
from kivymd.uix.snackbar import Snackbar
from kivy.uix.screenmanager import FadeTransition
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.clock import Clock
from kivy import platform
from db_connect import *
from .client import *
from datetime import datetime
import pandas as pd
import os
import threading
import time


DIALOG_HEIGHT = dp(170)
DEFAULT_FONT_SIZE = "18sp"

class WorkSpaceScreen(MDScreen):
    def __init__(self, **kwargs):
        super(WorkSpaceScreen, self).__init__(**kwargs)
        self.search_available = False
        self.current_barcode = ''
        self.show_edit_dialog_open = False
        self.show_info_dialog_open = False
        self._selected_date = None
        self.is_checked = False
        self.suggested_filename = None
        self.edit_dialog = None
        self.dialog = None
        self.ids.barcode_input.text = ""
        
    def on_enter(self):
        self.current_barcode = ''
        self.ids.barcode_input.text = ""
        # Window.bind(on_key_down=self.on_key_down)
        self.load_barcode_data()
        
    def on_leave(self):
        # Unbind to prevent memory leaks
        # Window.unbind(on_key_down=self.on_key_down)
        Clock.unschedule(self.set_focus)
        
    def focus_input(self, dt):
        self.ids.barcode_input.text = ""
        self.ids.barcode_input.focus = True

    def set_focus(self):
        if not self.is_dialog_open():
            Clock.schedule_once(self.focus_input, 0.001)

    def is_dialog_open(self):
        dialog_methods = [
            'show_edit_dialog', 
            'show_info_dialog'
        ]
        
        # Check if any of these methods have been recently called
        for method_name in dialog_methods:
            if hasattr(self, method_name + '_open') and getattr(self, method_name + '_open', False):
                return True
        
        return False


    def on_key_down(self, instance, keyboard, keycode, text, modifiers):
        if keycode == 40 or keycode == 43:  # Enter key or Tab key
            if self.current_barcode:
                self.add_barcode(self.current_barcode)
                self.current_barcode = ''
            return True
        # Only accumulate printable characters
        if text and text.isprintable():
            self.current_barcode += text
        return False
        
    def load_barcode_data(self):
        self.set_focus()
        session = Session()
        try:
            settings = session.query(Settings).first()
            if not settings:
                return
                
            # Get counts with a single query for better performance
            barcodes_query = session.query(Barcodes).filter_by(
                workspace_id=settings.current_workspace_id
            ).order_by(desc(Barcodes.id)).limit(10)
            
            # Calculate totals in a single query
            total_count = session.query(func.count(Barcodes.id)).filter_by(
                workspace_id=settings.current_workspace_id
            ).scalar() or 0
            
            total_stock_count = session.query(func.sum(Barcodes.count)).filter(
                Barcodes.workspace_id == settings.current_workspace_id
            ).scalar() or 0
            
            # Prepare data
            data = [{'id': b.id, 'code': b.code, 'count': b.count} for b in barcodes_query]
            
            # Update UI
            self.ids.total_barcode_count.text = f"{total_count}"
            self.ids.total_stock_count.text = f"{total_stock_count}"
            
            for i in range(10):
                if i < len(data):
                    code_btn = getattr(self.ids, f'code_{i}')
                    code_btn.text = data[i]['code']
                    code_btn.item_id = data[i]['id']
                    
                    count_label = getattr(self.ids, f'count_{i}')
                    count_label.text = str(data[i]['count'])
                else:
                    code_btn = getattr(self.ids, f'code_{i}')
                    code_btn.text = ''
                    code_btn.item_id = 0
                    
                    count_label = getattr(self.ids, f'count_{i}')
                    count_label.text = ''
                    
        finally:
            session.close()

        
    def add_barcode(self, barcode):
        if not str(barcode).isdigit():
            self.show_error_dialog("Barkod düzgün deyil")
            return
    
        if (self.show_edit_dialog_open is False) and (self.show_info_dialog_open is False):
            session = Session()
            try:
                settings = session.query(Settings).first()
                if not settings:
                    return
                
                if self.search_available:
                    existing = session.query(Barcodes).filter_by(code=barcode, workspace_id=settings.current_workspace_id).first()
                    if not existing:
                        self.show_error_dialog("Barkod tapılmadı")
                        return

                    self.show_edit_dialog(existing.id, existing.code, existing.count)
                else:                    
                    existing = session.query(Barcodes).filter_by(code=barcode, workspace_id=settings.current_workspace_id).first()
                    
                    if existing:
                        existing.count += 1
                    else:
                        new_barcode = Barcodes(
                            code=barcode, 
                            count=1, 
                            workspace_id=settings.current_workspace_id
                        )
                        session.add(new_barcode)
                    
                    session.commit()
                    self.load_barcode_data()
            finally:
                session.close()
        else:
            pass

    def toggle_search_availability(self):
        self.search_available = not self.search_available
        self.ids.search_toggle.icon = 'magnify-plus' if self.search_available else 'magnify-close'

    def show_edit_dialog(self, barcode_id, barcode_code, barcode_count):
        self.show_edit_dialog_open = True
        
        content = MDBoxLayout(
            orientation="vertical",
            spacing=dp(15),
            padding=dp(20),
            size_hint_y=None,
            height=DIALOG_HEIGHT
        )

        barcode_field = MDTextField(
            font_size=DEFAULT_FONT_SIZE,
            hint_text="Barkod",
            text=barcode_code,
            multiline=False,
            size_hint_y=None,
            height=dp(48),
            input_filter='int'
        )
        content.add_widget(barcode_field)
        
        count_layout = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(5),
            size_hint_y=None,
            height=dp(50)
        )
        
        count_layout.add_widget(MDIconButton(
            icon="minus-circle-outline",
            icon_size=dp(26),
            on_release=lambda x: self.decrease_edit_count(count_field)
        ))
        
        count_field = MDTextField(
            hint_text="Miqdar",
            font_size=DEFAULT_FONT_SIZE,
            text=str(barcode_count),
            multiline=False,
            input_filter="int",
            size_hint_x=0.5,
            max_text_length=5
        )
        count_layout.add_widget(count_field)
        
        count_layout.add_widget(MDIconButton(
            icon="plus-circle-outline",
            icon_size=dp(26),
            on_release=lambda x: self.increase_edit_count(count_field)
        ))
        
        content.add_widget(count_layout)
        
        self.edit_dialog = MDDialog(
            title="Düzəliş et",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(
                    text="LƏĞV ET",
                    font_size=DEFAULT_FONT_SIZE,
                    on_release=lambda x: self.dismiss_and_focus(self.edit_dialog)
                ),
                MDFlatButton(
                    text="SİL",
                    font_size=DEFAULT_FONT_SIZE,
                    theme_text_color="Error",
                    on_release=lambda x: self.delete_barcode(barcode_id)
                ),
                MDFlatButton(
                    text="YENİLƏ",
                    font_size=DEFAULT_FONT_SIZE,
                    theme_text_color="Primary",
                    on_release=lambda x: self.update_barcode(
                        barcode_id, barcode_field.text[:20], count_field.text[:5]
                    )
                ),
            ],
        )
        self.edit_dialog.ids.text.font_size = DEFAULT_FONT_SIZE
        self.edit_dialog.open()

    def decrease_edit_count(self, count_field):
        current_count = int(count_field.text) if count_field.text.isdigit() else 1
        count_field.text = str(max(1, current_count - 1))
        
    def increase_edit_count(self, count_field):
        current_count = int(count_field.text) if count_field.text.isdigit() else 1
        count_field.text = str(current_count + 1)
    
    def delete_barcode(self, barcode_id):
        confirm_dialog = MDDialog(
            title="Barkod silinməsi",
            text="Barkodu silmək istəyirsiniz?",
            buttons=[
                MDFlatButton(
                    text="LƏĞV ET",
                    font_size=DEFAULT_FONT_SIZE,
                    on_release=lambda x: self.dismiss_and_focus(confirm_dialog)
                ),
                MDFlatButton(
                    text="SİL",
                    font_size=DEFAULT_FONT_SIZE,
                    theme_text_color="Error",
                    on_release=lambda x: self.confirm_delete(barcode_id, confirm_dialog)
                ),
            ],
        )
        confirm_dialog.ids.text.font_size = DEFAULT_FONT_SIZE
        confirm_dialog.open()
    
    def confirm_delete(self, barcode_id, dialog):
        session = Session()
        try:
            barcode = session.query(Barcodes).filter_by(id=barcode_id).first()
            if barcode:
                session.delete(barcode)
                session.commit()
        finally:
            session.close()
        
        dialog.dismiss()
        self.dismiss_and_focus(self.edit_dialog)
        self.load_barcode_data()
    
    def update_barcode(self, barcode_id, new_barcode, new_count):
        if not new_barcode:
            self.show_error_dialog("Barkod boş ola bilməz")
            return
        
        try:
            new_count = int(new_count)
            if new_count <= 0:
                self.show_error_dialog("Miqdar 0 ola bilməz")
                return
        except ValueError:
            self.show_error_dialog("Miqdar düzgün rəqəm olmalıdır")
            return
        
        session = Session()
        try:
            settings = session.query(Settings).first()
            if not settings:
                return
                
            existing = session.query(Barcodes.id).filter(
                Barcodes.code == new_barcode,
                Barcodes.workspace_id == settings.current_workspace_id,
                Barcodes.id != barcode_id
            ).first()
            
            if existing:
                self.show_error_dialog("Barkod artıq mövcuddur")
                return
                
            session.query(Barcodes).filter_by(id=barcode_id).update({
                "code": new_barcode,
                "count": new_count
            })
            session.commit()
        finally:
            session.close()
        
        self.dismiss_and_focus(self.edit_dialog)
        self.load_barcode_data()
    
    def show_error_dialog(self, message):
        dialog = MDDialog(
            title="Xəta",
            text=message,
            buttons=[
                MDFlatButton(
                    text="OK",
                    font_size=DEFAULT_FONT_SIZE,
                    on_release=lambda x: self.dismiss_and_focus(dialog)
                )
            ]
        )
        dialog.ids.text.font_size = DEFAULT_FONT_SIZE
        dialog.open()

    def dismiss_and_focus(self, dialog):
        dialog.dismiss()
        self.set_focus()
        self.show_edit_dialog_open = False
        self.show_info_dialog_open = False

    def delete_workspace(self):
        confirm_dialog = MDDialog(
            title="Anbar silinməsi",
            text="Anbarı silmək istədiyinizdən əminsiniz?",
            buttons=[
                MDFlatButton(
                    text="LƏĞV ET",
                    font_size=DEFAULT_FONT_SIZE,
                    on_release=lambda x: self.dismiss_and_focus(confirm_dialog)
                ),
                MDFlatButton(
                    text="SİL",
                    font_size=DEFAULT_FONT_SIZE,
                    theme_text_color="Error",
                    on_release=lambda x: self.confirm_delete_workspace(confirm_dialog)
                ),
            ],
        )
        confirm_dialog.ids.text.font_size = DEFAULT_FONT_SIZE
        confirm_dialog.open()
    
    def confirm_delete_workspace(self, dialog):
        session = Session()
        try:
            settings = session.query(Settings).first()
            if not settings:
                return
                
            session.query(Barcodes).filter_by(
                workspace_id=settings.current_workspace_id
            ).delete(synchronize_session=False)
            
            session.query(WorkSpaces).filter_by(
                id=settings.current_workspace_id
            ).delete(synchronize_session=False)
            
            session.commit()
        finally:
            session.close()
        
        self.dismiss_and_focus(dialog)
        self.manager.transition = FadeTransition(duration=0.1)
        self.manager.current = 'home'
    
    def show_info(self):
        self.show_info_dialog_open = True
        session = Session()
        
        try:
            settings = session.query(Settings).first()
            if not settings:
                return
                
            workspace = session.query(WorkSpaces).filter_by(
                id=settings.current_workspace_id
            ).first()
            
            if not workspace:
                return
                
            name = workspace.name
            formatted_date = workspace.created_date.strftime("%Y-%m-%d") if workspace.created_date else ""
            
            content = MDBoxLayout(
                orientation="vertical",
                spacing=dp(10),
                padding=dp(20),
                size_hint_y=None,
                height=dp(150)
            )
            
            workspace_name_input = MDTextField(
                font_size=DEFAULT_FONT_SIZE,
                hint_text="Anbar adı",
                text=name,
                multiline=False,
                size_hint_y=None,
                height=dp(50),
                max_text_length=20
            )
            content.add_widget(workspace_name_input)
            
            date_layout = MDBoxLayout(
                orientation="horizontal",
                spacing=dp(5),
                size_hint_y=None,
                size_hint_x=0.85,
                height=dp(50)
            )
            
            workspace_date_input = MDTextField(
                text=formatted_date,
                multiline=False,
                max_text_length=10,
                hint_text="Tarix",
                readonly=True,
                font_size=DEFAULT_FONT_SIZE,
                size_hint_x=0.9
            )
            date_layout.add_widget(workspace_date_input)
            
            date_layout.add_widget(MDIconButton(
                icon="calendar",
                icon_size=dp(26),
                pos_hint={"center_y": 0.5},
                on_release=lambda x: self.show_date_picker(workspace_date_input)
            ))
            
            content.add_widget(date_layout)
            
            self.dialog = MDDialog(
                title="Anbar məlumatı",
                type="custom",
                content_cls=content,
                buttons=[
                    MDFlatButton(
                        text="LƏĞV ET",
                        font_size=DEFAULT_FONT_SIZE,
                        on_release=lambda x: self.dismiss_and_focus(self.dialog)
                    ),
                    MDFlatButton(
                        text="SAXLA",
                        font_size=DEFAULT_FONT_SIZE,
                        theme_text_color="Primary",
                        on_release=lambda x: self.update_workspace_info(
                            workspace_name_input.text[:20], 
                            workspace_date_input.text, 
                            self.dialog
                        )
                    ),
                ],
            )
            self.dialog.ids.text.font_size = DEFAULT_FONT_SIZE
            self.dialog.open()
        finally:
            session.close()

    def show_date_picker(self, date_field):
        app = MDApp.get_running_app()
        date_dialog = MDDatePicker(
            title='Tarix Seç',
            title_input='Tarix seç',
            primary_color= app.theme_cls.bg_dark if app.theme_cls.theme_style == "Dark" else app.theme_cls.bg_light,
            selector_color= app.theme_cls.bg_dark if app.theme_cls.theme_style == "Dark" else app.theme_cls.primary_color,
            text_toolbar_color=app.theme_cls.primary_color,
            text_button_color=app.theme_cls.primary_color,
            input_field_background_color=app.theme_cls.primary_color
        )
        
        date_dialog.bind(on_save=lambda instance, value, date_range: self.on_date_save(instance, value, date_range, date_field))
        date_dialog.open()

    def on_date_save(self, instance, value, date_range, date_field):
        date_field.text = value.strftime("%Y-%m-%d")
        self._selected_date = value

    def update_workspace_info(self, workspace_name, workspace_date, dialog):
        if not workspace_name or not workspace_date:
            self.show_error_dialog("Anbar adı və tarix boş ola bilməz")
            return
        
        session = Session()
        try:
            settings = session.query(Settings).first()
            if not settings:
                return
                
            session.query(WorkSpaces).filter_by(id=settings.current_workspace_id).update({
                "name": workspace_name,
                "created_date": datetime.strptime(workspace_date, "%Y-%m-%d")
            })
            session.commit()
        finally:
            session.close()
        
        self.dismiss_and_focus(dialog)
    
    def export_to_excel(self):
        threading.Thread(target=self._run_export_excel_process).start()
        
        self.progress_dialog = MDDialog(
            title="Fayl hazırlanır",
            text="Zəhmət olmasa, gözləyin...",
            auto_dismiss=False
        )
        self.progress_dialog.ids.text.font_size = DEFAULT_FONT_SIZE
        self.progress_dialog.open()

    def _run_export_excel_process(self):
        try:
            workspace_data = {}
            barcodes_data = []
            
            def fetch_data_on_main_thread(dt):
                nonlocal workspace_data, barcodes_data
                try:
                    session = Session()
                    settings = session.query(Settings).first()
                    if not settings:
                        Clock.schedule_once(lambda dt: self._show_export_result_excel("error", "Tənzimləmələr tapılmadı"), 0)
                        return
                        
                    workspace = session.query(WorkSpaces).filter_by(id=settings.current_workspace_id).first()
                    if not workspace:
                        Clock.schedule_once(lambda dt: self._show_export_result_excel("error", "Anbar məlumatları tapılmadı"), 0)
                        return
                    
                    workspace_data = {
                        'name': workspace.name,
                        'created_date': workspace.created_date,
                        'user': workspace.user
                    }
                    
                    barcodes = session.query(Barcodes.code, Barcodes.count).filter_by(
                        workspace_id=settings.current_workspace_id
                    ).all()
                    
                    if not barcodes:
                        Clock.schedule_once(lambda dt: self._show_export_result_excel("error", "Məlumatlar köçürülə bilmədi"), 0)
                        return
                    
                    for code, count in barcodes:
                        barcodes_data.append({'Barkod': code, 'Miqdar': count})
                    
                    Clock.schedule_once(lambda dt: self._process_excel_data(workspace_data, barcodes_data), 0)
                except Exception as e:
                    Clock.schedule_once(lambda dt: self._show_export_result_excel("error", f"Xəta baş verdi: {str(e)}"), 0)
                finally:
                    session.close()
            
            Clock.schedule_once(fetch_data_on_main_thread, 0)
            
        except Exception as e:
            Clock.schedule_once(lambda dt: self._show_export_result_excel("error", f"Xəta baş verdi: {str(e)}"), 0)

    def _process_excel_data(self, workspace_data, barcodes_data):
        try:
            import pandas as pd
            df = pd.DataFrame(barcodes_data)
            
            date_str = workspace_data['created_date'].strftime('%Y-%m-%d')
            self.suggested_filename = f"{workspace_data['user']}_{workspace_data['name']}_{date_str}.xlsx"
            
            result = self._export_excel_file(df)
            
            Clock.schedule_once(lambda dt: self._show_export_result_excel(result[0], result[1]), 0)
            
        except Exception as e:
            Clock.schedule_once(lambda dt: self._show_export_result_excel("error", f"Xəta baş verdi: {str(e)}"), 0)

    def _export_excel_file(self, df):
        try:
            if platform == 'android':
                from android.storage import primary_external_storage_path
                from android.permissions import request_permissions, Permission
                
                request_permissions([Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE])
                
                possible_paths = [
                    os.path.join(primary_external_storage_path(), 'Download'),
                    os.path.join(primary_external_storage_path(), 'Documents')
                ]
                
                for export_path in possible_paths:
                    try:
                        os.makedirs(export_path, exist_ok=True)
                        file_path = os.path.join(export_path, self.suggested_filename)
                        df.to_excel(file_path, index=False, engine='openpyxl')
                        return ("success", f"Fayl uğurla köçürüldü:\n{file_path}")
                    except (PermissionError, OSError):
                        continue
                else:
                    return ("error", "No suitable export location found")
            else:
                export_path = os.path.expanduser('~/Documents')
                if not os.path.exists(export_path):
                    export_path = os.path.expanduser('~')
                
                os.makedirs(export_path, exist_ok=True)
                file_path = os.path.join(export_path, self.suggested_filename)
                df.to_excel(file_path, index=False)
                return ("success", f"Fayl uğurla köçürüldü:\n{file_path}")
            
        except Exception as e:
            return ("error", f"Fayl köçürülə bilmədi:\n{str(e)}")

    def _show_export_result_excel(self, status, message):
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.dismiss()
        
        title = "Uğurlu əməliyyat" if status == "success" else "Uğursuz əməliyyat"
        
        result_dialog = MDDialog(
            title=title,
            text=message,
            buttons=[
                MDFlatButton(
                    text="TAMAM",
                    font_size=DEFAULT_FONT_SIZE,
                    on_release=lambda x: self.dismiss_and_focus(result_dialog)
                ),
            ],
        )
        result_dialog.ids.text.font_size = DEFAULT_FONT_SIZE
        result_dialog.open()



    def export_database(self):
        session = Session()
        try:
            settings = session.query(Settings).first()
            if settings:
                if settings.server_ip == '255.255.255.255':
                    self.show_error_dialog("Bağlantı ünvanı düzgün deyil")
                    return
                    
                confirm_dialog = MDDialog(
                    title="Server bağlantısı",
                    text="Məlumatlar əsas bazaya köçürülsün?",
                    buttons=[
                        MDFlatButton(
                            text="LƏĞV ET",
                            font_size=DEFAULT_FONT_SIZE,
                            on_release=lambda x: self.dismiss_and_focus(confirm_dialog)
                        ),
                        MDFlatButton(
                            text="TƏSDİQLƏ",
                            font_size=DEFAULT_FONT_SIZE,
                            theme_text_color="Primary",
                            on_release=lambda x: self.start_export_database(settings, confirm_dialog)
                        ),
                    ],
                )
                confirm_dialog.ids.text.font_size = DEFAULT_FONT_SIZE
                confirm_dialog.open()
        finally:
            session.close()

    def start_export_database(self, settings, dialog):
        self.dismiss_and_focus(dialog)
        
        self.server_ip = settings.server_ip
        self.port = int(settings.port_number)
        self.workspace_id = int(settings.current_workspace_id)
        
        self.progress_dialog = MDDialog(
            title="Məlumat köçürülür",
            text="Zəhmət olmasa, gözləyin...",
            auto_dismiss=False
        )
        self.progress_dialog.ids.text.font_size = DEFAULT_FONT_SIZE
        self.progress_dialog.open()
        
        threading.Thread(target=self.run_export_database).start()

    def run_export_database(self):
        try:
            workspace_data = self.fetch_workspace_data()
            if not workspace_data:
                Clock.schedule_once(lambda dt: self._show_export_result({
                    "status": "error",
                    "message": "Anbar məlumatı tapılmadı"
                }), 0)
                return
                
            client = IsartiClient(self.server_ip, self.port)
            
            if not client.connect():
                Clock.schedule_once(lambda dt: self._show_export_result({
                    "status": "error",
                    "message": "Serverə qoşula bilmədi"
                }), 0)
                return
            
            server_workspace_id = client.send_workspace(self.workspace_id)
            
            if server_workspace_id:
                barcode_count = client.send_barcodes(self.workspace_id, server_workspace_id)
                client.disconnect()
                
                result = {
                    "status": "success",
                    "message": f"'{workspace_data['name']}' adlı anbar {barcode_count} ədəd barkod ilə uğurla köçürüldü"
                }
            else:
                client.disconnect()
                result = {
                    "status": "error",
                    "message": f"'{workspace_data['name']}' adlı anbar köçürülə bilmədi"
                }
                
            Clock.schedule_once(lambda dt: self._show_export_result(result), 0)
            
        except Exception as exc: 
            error_message = f"Xəta baş verdi: {str(exc)}"
            Clock.schedule_once(
                lambda dt: self._show_export_result({
                    "status": "error",
                    "message": error_message
                }), 0
            )

    def fetch_workspace_data(self):
        data = {}
        
        def get_data_from_main_thread(dt):
            nonlocal data
            session = Session()
            try:
                workspace = session.query(WorkSpaces).filter_by(id=self.workspace_id).first()
                if workspace:
                    data = {
                        'id': workspace.id,
                        'name': workspace.name,
                        'user': workspace.user
                    }
            finally:
                session.close()
        
        Clock.schedule_once(get_data_from_main_thread, 0)
        import time
        timeout = 3 
        start_time = time.time()
        while not data and time.time() - start_time < timeout:
            time.sleep(0.1)
        
        return data

    def _show_export_result(self, result):
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.dismiss()
        
        if result["status"] == "success":
            icon = "check-circle"
            title = "Uğurlu əməliyyat"
            text = result["message"]
        else:
            icon = "alert-circle"
            title = "Xəta"
            text = result["message"]
        
        result_dialog = MDDialog(
            title=title,
            text=text,
            buttons=[
                MDFlatButton(
                    text="TAMAM",
                    font_size=DEFAULT_FONT_SIZE,
                    on_release=lambda x: self.dismiss_and_focus(result_dialog)
                ),
            ],
        )
        result_dialog.ids.text.font_size = DEFAULT_FONT_SIZE
        result_dialog.open()
