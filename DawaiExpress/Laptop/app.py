import sys, os, getpass, sqlite3
from PyQt6.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject, QSize
from PyQt6.uic import loadUi
from PyQt6.QtGui import QColor, QBrush, QFont, QIcon

from dawaiServer import startServer, connect_pyqt_bridge
from database import add_data, create_table, fetch_data, delete
from database2 import add_data_dos, create_table_dos, fetch_data_dos, delete_dos
from verification import send_mail

USER_NAME = getpass.getuser()
if getattr(sys, 'frozen', False):
    curr_path = os.path.dirname(sys.executable)
else:
    curr_path = os.path.dirname(__file__)

print(curr_path)

class Bridge(QObject):
    data_received = pyqtSignal(dict)

class App(QMainWindow):
    def __init__(self):
        super().__init__()
        loadUi(os.path.join(curr_path, 'ui\\mainwindow.ui'), self)
        self.setFixedSize(500, 500)
        # self.move(100, 100)
        self.setWindowTitle("Dawai Express")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.alertIndex = 0
        self.blinkState = False
        self.currentAlert = ""
        self.alertsList = []

        # Create communication bridge
        self.bridge = Bridge()
        self.bridge.data_received.connect(self.handleServerData)
        connect_pyqt_bridge(self.bridge.data_received.emit)

        # Timers
        self.serverTim = QTimer(self)
        self.serverTim.setSingleShot(True)
        self.serverTim.setInterval(1000)
        self.serverTim.timeout.connect(self.serverInit)
        self.serverTim.start()

        self.progressBar.setValue(0)
        self.timer = QTimer()
        self.timer.setInterval(200)
        self.timer.timeout.connect(self.update_progress)
        self.timer.start()

        self.xpressAliveTimer = QTimer()
        self.xpressAliveTimer.setInterval(10000)
        self.xpressAliveTimer.timeout.connect(lambda: self.setXpressStatus("Down"))
        self.xpressAliveTimer.stop()

        self.alarmTimer = QTimer()
        self.alarmTimer.setInterval(500)
        self.alarmTimer.timeout.connect(self.alarmBlinker)
        self.alarmTimer.stop()

        self.serverEnabled = False
        self.showAddPatWin = False
        self.addPatFlag = False
        self.editPatFlag = False
        self.mainScreen.hide()
        self.loading.move(100, 150)
        self.dosage.setText("Dosage: Night")

        # Adding data to row 0
        os.makedirs("Laptop\\Databases", exist_ok=True)
        if not os.path.exists(os.path.join(curr_path,'Databases\\patData.db')):
            create_table_dos()
            create_table()
            print("iuh")
        else:
            pass

        # --- Create table ---
        self.table = QTableWidget(self)
        self.table.setRowCount(4)     # 4 patients
        self.table.setColumnCount(4)  # Morning, Afternoon, Evening, Night

        # --- Set headers ---
        self.table.setHorizontalHeaderLabels(["Morning", "Afternoon", "Evening", "Night"])
        try:
            patName = [x[0] for x in fetch_data("patName")]
            self.table.setVerticalHeaderLabels(patName)
        except:
            pass

        # --- Optional: resize behavior ---
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)


        self.itemList = []

        try:
            dos1 = [x[0] for x in fetch_data_dos("dos1")]
            dos2 = [x[0] for x in fetch_data_dos("dos2")]
            dos3 = [x[0] for x in fetch_data_dos("dos3")]
            dos4 = [x[0] for x in fetch_data_dos("dos4")]
        except:
            pass

        for i in range(4):
            for j in range(4):
                
                item = QTableWidgetItem("✔")
                font = QFont()
                font.setPointSize(20)  # adjust size as you like
                font.setBold(True)
                item.setFont(font)
                item.setForeground(QBrush(QColor("green")))
                self.itemList.append(item)
                try:
                    if j == 0:
                        if dos1[i]:
                            self.table.setItem(i, j, item)
                    if j == 1:
                        if dos2[i]:
                            self.table.setItem(i, j, item)
                    if j == 2:
                        if dos3[i]:
                            self.table.setItem(i, j, item)
                    if j == 3:
                        if dos4[i]:
                            self.table.setItem(i, j, item)
                except:
                    pass

        # --- Optional: example data ---
        # self.table.setItem(0, 0, QTableWidgetItem("✔"))  # Patient 1 Morning
        # self.table.setItem(1, 2, QTableWidgetItem("✖"))  # Patient 2 Evening


        self.tableW.addWidget(self.table)

        
        # Functions when buttons are clicked
        self.addPatient.clicked.connect(self.addPat)
        self.addPatSave.clicked.connect(self.movePatWin)
        self.addPatClose.clicked.connect(self.windowHandler)
        self.addPatCancel.clicked.connect(self.windowHandler)
        self.sendMail.clicked.connect(self.mailPeople)

        self.allPatients.clicked.connect(self.allPat)
        self.allPatClose.clicked.connect(self.closeHandler)
        self.allPatEdit.clicked.connect(self.edit)

    def setXpressStatus(self, string): 
        self.xpressStatus.setText(string) 
    
    def setServerStatus(self, string): 
        self.serverStatus.setText(string) 
    
    def alarmBlinker(self):
        if not self.alertsList:
            return

        self.blinkState = not self.blinkState

        if self.blinkState:
            self.alertBar.setText(self.alertsList[self.alertIndex])
        else:
            self.alertBar.setText("")
            self.alertIndex = (self.alertIndex + 1) % len(self.alertsList)

    def setAlert(self, string): 
        self.alertBar.setText(string) 
        
    def removeAlert(self): 
        self.alertBar.setText("")

    def update_progress(self):
        if self.progressBar.value() < 100:
            self.progressBar.setValue(self.progressBar.value() + 10)
        else:
            self.timer.stop()
            self.loading.move(550, 150)
            # self.loading.hide()
            self.mainScreen.show()

    def serverInit(self):
        if not self.serverEnabled:
            self.serverEnabled = startServer()
            self.serverStatus.setText("Up" if self.serverEnabled else "Down")

    def handleServerData(self, data):
        print("PyQt received data from Flask:", data)

        # Defensive check: ensure it's a dict
        if not isinstance(data, dict):
            print("Invalid data format:", data)
            return

        # --- Handle alert messages ---
        elif "alert" in data:
            self.setAlert(f"Alert: {data['alert']}")            
            self.alertsList.append(f"{data['alert']}")
            self.alarmTimer.start()
            return
        
        # --- Handle Xpress messages ---
        elif "xpress" in data:
            self.xpressAliveTimer.stop()
            self.setXpressStatus(f"{data['xpress']}")
            # self.xpressAliveTimer.start()
            return

        # --- Handle status updates ---
        elif "status" in data:
            status_info = data["status"]
            if isinstance(status_info, dict):
                text = "\n".join(f"{k}: {v}" for k, v in status_info.items())
                self.serverStatus.setText(text)
            else:
                self.serverStatus.setText(str(status_info))
            return

        # --- Default / fallback case ---
        else:
            print("Unknown data type:", data)

    def movePatWin(self):
        self.addPatWin.move(25, 520)
        os.makedirs("Laptop\\Databases", exist_ok=True)
        if not os.path.exists(os.path.join(curr_path,'Databases\\patData.db')):
            create_table()
            print("iuh")
        else:
            pass
        if self.nameEdit.text()!="" and self.emailEdit.text()!="" and self.bedNoEdit.text()!="" and self.diseaseEdit.text()!="":
            print("jhjgf")
            if self.rad1.isChecked():
                dos1 = 1
            else:
                dos1 = 0
            if self.rad2.isChecked():
                dos2 = 1
            else:
                dos2 = 0
            if self.rad3.isChecked():
                dos3 = 1
            else:
                dos3 = 0
            if self.rad4.isChecked():
                dos4 = 1
            else:
                dos4 = 0

            print(dos1, dos2, dos3, dos4)

            try:
                add_data(self.nameEdit.text(), self.emailEdit.text(), int(self.bedNoEdit.text()), self.diseaseEdit.text(), dos1, dos2, dos3, dos4)
                add_data_dos(self.nameEdit.text(), int(self.bedNoEdit.text()), dos1, dos2, dos3, dos4)
            except:
                print("Wrong data !!!")
        else:
            pass
        self.populateAllPatTable()
        self.populateDosageTable()

    def addPat(self):
        self.addPatFlag = True
        self.addPatWin.move(25, 75)
        self.nameEdit.setText("")
        self.emailEdit.setText("")
        self.bedNoEdit.setText("")
        self.diseaseEdit.setText("")
        self.rad1.setChecked(False)
        self.rad2.setChecked(False)
        self.rad3.setChecked(False)
        self.rad4.setChecked(False)

    def allPat(self):
        self.allPatWin.move(25, 75)
        self.populateAllPatTable()

    def clear_layout(self, layout):
        if layout is None:
            return

        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()  # Schedule widget for deletion
            else:
                # If the item is a sub-layout, recursively clear it
                sub_layout = item.layout()
                if sub_layout is not None:
                    self.clear_layout(sub_layout)

    def populateAllPatTable(self):
        # --- Create table ---
        self.table2 = QTableWidget(self)
        self.table2.setRowCount(4)     # 4 patients
        self.table2.setColumnCount(9)  

        # --- Set headers ---
        self.table2.setHorizontalHeaderLabels(["Bed No.", "Name", "Email", "Disease", "Morn", "Noon", "Eve", "Night", "Delete"])
        # print(patList)
        self.table2.setVerticalHeaderLabels(["1", "2", "3", "4"])

        # --- Optional: resize behavior ---
        self.table2.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table2.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table2.resizeColumnsToContents()
        # Adding data to row 0
        self.itemList = []
        patName = [x[0] for x in fetch_data("patName")]
        patEmail = [x[0] for x in fetch_data("patEmail")]
        bedNum = [x[0] for x in fetch_data("bedNum")]
        patDisease = [x[0] for x in fetch_data("patDisease")]
        dos1 = [x[0] for x in fetch_data("dos1")]
        dos2 = [x[0] for x in fetch_data("dos2")]
        dos3 = [x[0] for x in fetch_data("dos3")]
        dos4 = [x[0] for x in fetch_data("dos4")]
        butArr = []
        
        for i in range (5):
            but = QPushButton()
            img = QIcon('Laptop\\dustbin.png')
            but.setIcon(img)
            but.setIconSize(QSize(40, 40))
            but.clicked.connect(self.deleteRow)
            butArr.append(but)

        for i in range(4):
            for j in range(9):
                try:
                    if j == 0:
                        target = bedNum
                    elif j == 1:
                        target = patName
                    elif j == 2:
                        target = patEmail
                    elif j == 3:
                        target = patDisease
                    elif j == 4:
                        target = dos1
                    elif j == 5:
                        target = dos2
                    elif j == 6:
                        target = dos3
                    elif j == 7:
                        target = dos4
                    elif j == 8:
                        target = butArr
                    if j != 8:
                        item = QTableWidgetItem(str(target[i]))
                        font = QFont()
                        font.setPointSize(10)  # adjust size as you like
                        font.setBold(True)
                        item.setFont(font)
                        item.setForeground(QBrush(QColor("green")))
                        self.itemList.append(item)
                        self.table2.setItem(i, j, item)
                    else:
                        item = target[i]
                        self.table2.setCellWidget(i, j, item)
                except:
                    pass
                

        self.clear_layout(self.tableW2)
        self.tableW2.addWidget(self.table2)
        self.table2.setCurrentCell(0, 0)

    def populateDosageTable(self):
        # --- Create table ---
        self.table = QTableWidget(self)
        self.table.setRowCount(4)     # 4 patients
        self.table.setColumnCount(4)  # Morning, Afternoon, Evening, Night

        # --- Set headers ---
        self.table.setHorizontalHeaderLabels(["Morning", "Afternoon", "Evening", "Night"])
        try:
            patName = [x[0] for x in fetch_data("patName")]
            self.table.setVerticalHeaderLabels(patName)
        except:
            pass

        # --- Optional: resize behavior ---
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.itemList = []

        try:
            dos1 = [x[0] for x in fetch_data_dos("dos1")]
            dos2 = [x[0] for x in fetch_data_dos("dos2")]
            dos3 = [x[0] for x in fetch_data_dos("dos3")]
            dos4 = [x[0] for x in fetch_data_dos("dos4")]
        except:
            pass

        for i in range(4):
            for j in range(4):                
                item = QTableWidgetItem("✔")
                font = QFont()
                font.setPointSize(20)  # adjust size as you like
                font.setBold(True)
                item.setFont(font)
                item.setForeground(QBrush(QColor("green")))
                self.itemList.append(item)
                try:
                    if j == 0:
                        if dos1[i]:
                            self.table.setItem(i, j, item)
                    if j == 1:
                        if dos2[i]:
                            self.table.setItem(i, j, item)
                    if j == 2:
                        if dos3[i]:
                            self.table.setItem(i, j, item)
                    if j == 3:
                        if dos4[i]:
                            self.table.setItem(i, j, item)
                except:
                    pass

        # --- Optional: example data ---
        # self.table.setItem(0, 0, QTableWidgetItem("✔"))  # Patient 1 Morning
        # self.table.setItem(1, 2, QTableWidgetItem("✖"))  # Patient 2 Evening


        self.clear_layout(self.tableW)
        self.tableW.addWidget(self.table)
        self.table.setCurrentCell(0, 0)

    def deleteRow(self):
        row = self.table2.currentRow()
        print(row)
        data = self.get_row_data(self.table2, row) 
        print(data)
        delete("patient", data[2])
        delete_dos("dosage", data[0])
        self.populateAllPatTable()

    def edit(self):
        self.editPatFlag = True
        row = self.table2.currentRow()
        print(row)
        data = self.get_row_data(self.table2, row) 
        print(data)
        self.allPatWin.move(25, 520)
        self.showEditPatWin(data)

    def get_row_data(self, table, row: int):
        data = []

        for col in range(table.columnCount()):
            item = table.item(row, col)

            if item is not None:
                data.append(item.text())
            else:
                widget = table.cellWidget(row, col)

                if isinstance(widget, QPushButton):
                    data.append("<Button>")  # or return widget
                else:
                    data.append(None)

        return data

    def showEditPatWin(self, arr):
        print(arr)
        self.addPatWin.move(25, 75)
        self.nameEdit.setText(arr[1])
        self.emailEdit.setText(arr[2])
        self.bedNoEdit.setText(arr[0])
        self.diseaseEdit.setText(arr[3])
        self.rad1.setChecked(True if int(arr[4]) else False)
        self.rad2.setChecked(True if int(arr[5]) else False)
        self.rad3.setChecked(True if int(arr[6]) else False)
        self.rad4.setChecked(True if int(arr[7]) else False)

    def windowHandler(self):
        print("self.addPatFlag", self.addPatFlag)
        print("self.editPatFlag", self.editPatFlag)
        self.addPatWin.move(25, 520)
        if self.addPatFlag:
            pass
        if self.editPatFlag:
            self.allPatWin.move(25, 75)
            self.populateAllPatTable()

    def closeHandler(self):
        self.addPatFlag = False
        self.editPatFlag = False
        self.allPatWin.move(25, 520)
        print("self.addPatFlag", self.addPatFlag)
        print("self.editPatFlag", self.editPatFlag)
        self.populateDosageTable()

    def mailPeople(self):
        patName = [x[0] for x in fetch_data("patName")]
        patEmail = [x[0] for x in fetch_data("patEmail")]
        dos1 = [x[0] for x in fetch_data_dos("dos1")]
        dos2 = [x[0] for x in fetch_data_dos("dos2")]
        dos3 = [x[0] for x in fetch_data_dos("dos3")]
        dos4 = [x[0] for x in fetch_data_dos("dos4")]
        for i in range(len(patName)):
            medicineStr = "Medicine in "
            if dos1[i]:
                medicineStr += "Morning, "
            if dos2[i]:
                medicineStr += "Afternoon, "
            if dos3[i]:
                medicineStr += "Evening, "
            if dos4[i]:
                medicineStr += "and Night"
            send_mail(patName[i], patEmail[i], "regular", quantity=medicineStr)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec())
