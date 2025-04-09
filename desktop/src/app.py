import pandas as pd
import sys
import socket
from db_connect import *
from network_server import IsartiServer  
from PyQt6.QtWidgets import QProgressDialog, QApplication, QMainWindow, QMessageBox, QFileDialog, QDialog, QTableWidgetItem, QCheckBox, QWidget, QHBoxLayout
from PyQt6.QtCore import Qt

from ui_pycode.main import Ui_Main
from ui_pycode.user import Ui_User
from ui_pycode.list import Ui_Workspace


class Main(QMainWindow, Ui_Main):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.setup_users_dialog()
        self.setup_list_dialog()
        self.setup_buttons()
        self.setup_window()
    
        self.server = IsartiServer()
        self.server.start()

    def setup_window(self):
        self.setWindowTitle('Isarti')
        self.switch_to_user_page()

    def setup_buttons(self):
        self.btn_users.clicked.connect(self.switch_to_user_page)
        self.btn_new_User.clicked.connect(lambda: self.open_user_window(None))
        self.btn_barcodes.clicked.connect(self.switch_to_barcode_page)
        self.btn_show_info.clicked.connect(self.show_connection_info)
        self.btn_delete_choosen.clicked.connect(self.delete_workspace)
        self.btn_export_choosen.clicked.connect(self.export_to_excel)
        self.btn_reload_Barcodes.clicked.connect(self.load_workspace_data)
        self.table_Users.cellDoubleClicked.connect(self.on_user_click)
        self.table_Workspaces.cellDoubleClicked.connect(self.on_workspace_click)


    def setup_users_dialog(self):
        self.User, self.User_GUI = self.create_dialog(Ui_User)    
        self.User_GUI.button_delete.clicked.connect(self.delete_user)
        self.User_GUI.button_add.clicked.connect(self.create_or_update_user)
        self.User_GUI.button_cancel.clicked.connect(self.User.close)

    def setup_list_dialog(self):
        self.List, self.List_GUI = self.create_dialog(Ui_Workspace)
        self.List_GUI.button_close.clicked.connect(self.List.close)

    def create_dialog(self, ui_class):
        dialog = QDialog(self)
        dialog.setWindowTitle('Isarti')
        ui_instance = ui_class()
        ui_instance.setupUi(dialog)
        return dialog, ui_instance

    ############## SWITCH PAGES ###########################
    ######################################################
    def switch_to_user_page(self):
        self.pages.setCurrentIndex(0)
        self.load_users_data()

    def switch_to_barcode_page(self):
        self.pages.setCurrentIndex(1)
        self.load_workspace_data()

    ############ USER WINDOW ####################################################################################################
    #############################################################################################################################
    def open_user_window(self, user):
        if not user:
            self.User_GUI.label_user_id.clear()
            self.User_GUI.input_username.clear()
            self.User_GUI.input_password.clear()
            self.User_GUI.label_user.setText(f'İstifadəçi əlavə et')
            self.User_GUI.button_delete.hide()
        else:
            self.User_GUI.label_user_id.setText(str(user.id))
            self.User_GUI.input_username.setText(user.name)
            self.User_GUI.input_password.setText(user.password)
            self.User_GUI.label_user.setText(f'Məlumatları yenilə')
            self.User_GUI.button_delete.show()

        self.User.exec()
        
    def create_or_update_user(self):
        user_id = self.User_GUI.label_user_id.text()
        username = self.User_GUI.input_username.text().strip()
        password = self.User_GUI.input_password.text().strip()

        with Session() as session:
            existing_user = session.query(Users).filter(Users.name == username).first()

            if user_id:
                if existing_user:
                    if existing_user.id == int(user_id):
                        pass
                    else:
                        QMessageBox.critical(self.User, 'Isarti', "İstifadəçi adı artıq istifadə olunub.")
                        return
                user = session.query(Users).filter(Users.id == user_id).first()
            else:
                if existing_user:
                    QMessageBox.critical(self.User, 'Isarti', "İstifadəçi adı artıq istifadə olunub.")
                    return

                user = Users()

            user.name = username
            user.password = password
            session.add(user)
            session.commit()

            self.User.close()

            self.load_users_data()

    def load_users_data(self):
        with Session() as session:
            all_users = session.query(Users).all() 
        
            self.table_Users.setRowCount(len(all_users))

            for row_index, user in enumerate(all_users):
                self.table_Users.setItem(row_index, 0, QTableWidgetItem(str(user.id)))
                self.table_Users.setItem(row_index, 1, QTableWidgetItem(user.name))

                password_display = '*' * 10
                self.table_Users.setItem(row_index, 2, QTableWidgetItem(password_display))

            self.table_Users.setColumnHidden(0, True)
            self.table_Users.setColumnWidth(1, 100)
            self.table_Users.setColumnWidth(2, 150)

    def on_user_click(self, row, column):
        user_id = self.table_Users.item(row, 0).text()
        user = self.get_element_by_id(user_id, Users)
        self.open_user_window(user)

    def delete_user(self):
        id = self.User_GUI.label_user_id.text()
        with Session() as session:
            user = session.query(Users).filter(Users.id == id).first()
            reply = QMessageBox.question(self, 'Isarti',
                                         f'{user.name} adlı istifadəçi silinsin?',
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)

            if reply == QMessageBox.StandardButton.Yes:
                    session.delete(user)
                    session.commit()
                    self.User.close()
                    self.load_users_data()
            else:
                pass

    ############ CONNECTION WINDOW ####################################################################################################
    #############################################################################################################################
    def show_connection_info(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80)) 
            local_ip = s.getsockname()[0]
            s.close()
        except:
            local_ip = "127.0.0.1"  # Fallback if network is unavailable

        port = self.server.port if hasattr(self, 'server') else 3344

        info = f"""\n
        IP ünvanı: {local_ip}
        Port: {port}"""

        QMessageBox.information(self, 'Isarti', info)

    ############ WORKSPACE WINDOW ####################################################################################################
    #############################################################################################################################
    def open_workspace_window(self, workspace): 
        self.load_barcodes_data(str(workspace.id))
        self.List.exec()

    def load_workspace_data(self):
        with Session() as session:
            all_workspaces = session.query(WorkSpaces).order_by(WorkSpaces.id.desc()).all()
        
            self.table_Workspaces.setRowCount(len(all_workspaces))

            for row_index, workspace in enumerate(all_workspaces):
                total_count = session.query(func.count(Barcodes.id)).filter_by(workspace_id=workspace.id).scalar() or 0
                total_stock_count = session.query(func.sum(Barcodes.count)).filter(Barcodes.workspace_id == workspace.id).scalar() or 0

                self.table_Workspaces.setItem(row_index, 0, QTableWidgetItem(str(workspace.id)))
                self.table_Workspaces.setItem(row_index, 1, QTableWidgetItem(str(workspace.created_date)))
                self.table_Workspaces.setItem(row_index, 2, QTableWidgetItem(workspace.name))
                self.table_Workspaces.setItem(row_index, 3, QTableWidgetItem(str(workspace.user)))
                self.table_Workspaces.setItem(row_index, 4, QTableWidgetItem(str(total_count)))
                self.table_Workspaces.setItem(row_index, 5, QTableWidgetItem(str(total_stock_count)))

            self.table_Workspaces.setColumnHidden(0, True)

    def on_workspace_click(self, row, column):
        workspace_id = self.table_Workspaces.item(row, 0).text()
        workspace = self.get_element_by_id(workspace_id, WorkSpaces)
        self.open_workspace_window(workspace)

   
    def get_selected_workspace_ids(self):
        selected_rows = self.table_Workspaces.selectedItems()
        selected_row_indices = set()
        
        for item in selected_rows:
            selected_row_indices.add(item.row())
        
        workspace_ids = []
        for row_index in selected_row_indices:
            workspace_id = self.table_Workspaces.item(row_index, 0).text()
            workspace_ids.append(workspace_id)
        
        return workspace_ids


    def load_barcodes_data(self, workspace_id):
        with Session() as session:
            all_barcodes = session.query(Barcodes).filter_by(workspace_id=workspace_id).limit(100).all()
            
            self.List_GUI.table_Barcodes.setRowCount(len(all_barcodes))

            for row_index, barcode in enumerate(all_barcodes):
                self.List_GUI.table_Barcodes.setItem(row_index, 0, QTableWidgetItem(str(barcode.id)))
                self.List_GUI.table_Barcodes.setItem(row_index, 1, QTableWidgetItem(str(barcode.code)))
                self.List_GUI.table_Barcodes.setItem(row_index, 2, QTableWidgetItem(str(barcode.count)))

            self.List_GUI.table_Barcodes.setColumnHidden(0, True)

    def delete_workspace(self):
        selected_ids = self.get_selected_workspace_ids()
        
        if not selected_ids:
            QMessageBox.warning(self, "Isarti", "Heç bir sətir seçilməyib!")
            return
        
        with Session() as session:
            workspace_names = []
            workspaces = []
            for workspace_id in selected_ids:
                workspace = session.query(WorkSpaces).filter(WorkSpaces.id == workspace_id).first()
                if workspace:
                    workspace_names.append(workspace.name)
                    workspaces.append(workspace)
            
            message = "Aşağıdakı anbarlar silinsin?\n" + "\n".join(workspace_names)
            reply = QMessageBox.question(self, 'Isarti', message,
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                        QMessageBox.StandardButton.No)
            
            if reply == QMessageBox.StandardButton.Yes:
                total_steps = len(selected_ids) * 2 
                progress_dialog = QProgressDialog("Anbarlar silinir...", "Ləğv et", 0, total_steps, self)
                progress_dialog.setModal(True)
                progress_dialog.setWindowTitle("Isarti")
                progress_dialog.show()
                
                progress = 0
                
                try:
                    for workspace_id in selected_ids:
                        session.query(Barcodes).filter_by(workspace_id=workspace_id).delete()
                        progress += 1
                        progress_dialog.setValue(progress)
                        
                        workspace = session.query(WorkSpaces).filter(WorkSpaces.id == workspace_id).first()
                        if workspace:
                            session.delete(workspace)
                        progress += 1
                        progress_dialog.setValue(progress)
                    
                    session.commit()
                    
                    if hasattr(self, 'List') and self.List:
                        self.List.close()
                        
                    QMessageBox.information(self, 'Isarti', "Seçilmiş anbarlar uğurla silindi!")
                    self.load_workspace_data()
                    
                except Exception as e:
                    session.rollback()
                    QMessageBox.critical(self, 'Isarti', f"Xəta baş verdi: {str(e)}")


    def export_to_excel(self):
        selected_ids = self.get_selected_workspace_ids()
        
        if not selected_ids:
            QMessageBox.warning(self, "Isarti", "Heç bir sətir seçilməyib!")
            return

        all_barcodes = []
        with Session() as session:
            for workspace_id in selected_ids:
                barcodes = session.query(Barcodes).filter_by(workspace_id=workspace_id).all()
                all_barcodes.extend(barcodes)
        
        data = [{'Barkod': barcode.code, 'Miqdar': barcode.count} for barcode in all_barcodes]
        df = pd.DataFrame(data)
        
        reply = QMessageBox.question(self, 'Isarti',
                                    "Məlumatlar excel formatında köçürülsün?",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                    QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            options = QFileDialog.Option.DontUseNativeDialog
            file_path, _ = QFileDialog.getSaveFileName(self, "Isarti", "", "Excel Files (*.xlsx);;All Files (*)", options=options)
            
            if file_path: 
                if not file_path.endswith('.xlsx'):
                    file_path += '.xlsx'
                df.to_excel(file_path, index=False)
                QMessageBox.information(self, "Isarti", f"Məlumatlar uğurla köçürüldü")
 

    def get_element_by_id(self, element_id, DB_Table):
        with Session() as session:
            return session.query(DB_Table).filter(DB_Table.id == element_id).first()
        
    def closeEvent(self, event):
        reply = self.confirm_exit()
        if reply == QMessageBox.StandardButton.Yes:
            if hasattr(self, 'server'):
                self.server.stop()
            event.accept()
        else:
            event.ignore()

    def confirm_exit(self):
        reply = QMessageBox.question(self, 'Isarti',
                                     'Çıxış etmək istədiyinizdən əminsiniz?',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            QApplication.quit()
        else:
            pass

    def test(self):
        QMessageBox.information(self, 'Isarti', "Test")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = Main()
    main_window.show()
    sys.exit(app.exec())