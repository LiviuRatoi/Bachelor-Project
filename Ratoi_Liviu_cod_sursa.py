import sys
import time
import subprocess
import re
import matplotlib
matplotlib.use('Qt5Agg')

import matplotlib.pyplot as plt
import serial
from PyQt5.QtWidgets import QApplication,QDialog, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton, QTextEdit, QMessageBox, QGridLayout, QButtonGroup, QRadioButton, QComboBox, QCheckBox, QLineEdit
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont, QIcon

def convert_bytes(hex_string):
    try:
        hex_string = hex_string.replace(" ", "")  # Elimină toate spațiile din șirul hexazecimal

        if len(hex_string) >= 4:
            first_byte = hex_string[0:2]  # Primul byte
            second_byte = hex_string[2:4]  # Al doilea byte
            remaining_bytes = hex_string[4:]  # Bytes rămași

            if first_byte == "41" and second_byte == "04":
                decimal_value = int(remaining_bytes, 16)
                result = 0 + decimal_value / 2.55
                return str(result) + " ProcentSarcina" # nu-l vede
            elif first_byte == "41" and second_byte == "05":
                decimal_value = int(remaining_bytes, 16)
                result = -40 + 1 * decimal_value
                return str(result) + " TemperaturaApa"
            elif first_byte == "41" and second_byte == "0B":
                decimal_value = int(remaining_bytes, 16)
                result = 0 + 1 * decimal_value
                return str(result) + " Boost" #presiunea in motor
            elif first_byte == "41" and second_byte == "0C":
                decimal_value = int(remaining_bytes, 16)
                result = 0 + 0.25 * decimal_value
                return str(result) + " RPM"
            elif first_byte == "41" and second_byte == "0D":
                decimal_value = int(remaining_bytes, 16)
                result = 0 + 1 * decimal_value
                return str(result) + " km/h"
            elif first_byte == "41" and second_byte == "0E":
                decimal_value = int(remaining_bytes, 16)
                result = -64 + 0.5 * decimal_value
                return str(result) + " DegAprindere" # numai 41 0E 80
            elif first_byte == "41" and second_byte == "0F":
                decimal_value = int(remaining_bytes, 16)
                result = -40 + 1 * decimal_value
                return str(result) + " deg aer"
            elif first_byte == "41" and second_byte == "10":
                decimal_value = int(remaining_bytes, 16)
                result = 0 + 0.01 * decimal_value
                return str(result) + " GramePeSecunda"
            elif first_byte == "41" and second_byte == "11":
                decimal_value = int(remaining_bytes, 16)
                result = 0 + round(decimal_value / 2.55,2)
                return str(result) + " ProcentApăsată"
            elif first_byte == "41" and second_byte == "1C":
                decimal_value = int(remaining_bytes, 16)
                result = 0 + 1 * decimal_value
                return str(result) + " codăriAdaptateDisponibile"
            elif first_byte == "41" and second_byte == "21":
                decimal_value = int(remaining_bytes, 16)
                result = 0 + 1 * decimal_value
                return str(result) + " kmParcursi"
            """
            else:
                return "Nu se potrivește cu nicio formulă"
        else:
            return "Nu sunt suficienți bytes"
        """
    except ValueError:
        return "Valoarea introdusă nu este în format hexazecimal"
    
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Diagnoza auto")
        self.setGeometry(100, 100, 800, 1000)

        # Layout-ul principal
        layout = QGridLayout()

        """
        button_group = QButtonGroup()
        # Bluetooth radio button
        bt_radio = QRadioButton("Bluetooth")
        layout.addWidget(bt_radio, 0, 0)
        button_group.addButton(bt_radio)

        # USB radio button
        usb_radio = QRadioButton("USB")
        layout.addWidget(usb_radio, 0, 1)
        button_group.addButton(usb_radio)

        # Set exclusive selection for button group
        button_group.setExclusive(True)
        """
        # Dropdown pentru selectarea IP-urilor
        ip_label = QLabel("Selectează adresa MAC:")
        ip_label.setFixedSize(200, 20)  # Setează dimensiunea fixă (200x20)
        layout.addWidget(ip_label, 0, 0)  # Adaugă QLabel la poziția (2, 0)
        

        ip_dropdown = QComboBox()
        ip_dropdown.setFixedSize(200, 30)
        layout.addWidget(ip_dropdown, 1, 0, alignment=Qt.AlignLeft)  # Adaugă QComboBox la poziția (3, 0)
        ip_dropdown.addItem("66:1E:32:F5:34:45")
        ip_dropdown.addItem("00:10:CC:4F:36:03")

        # Dropdown pentru selectarea canalului
        channel_label = QLabel("Selectează canal:")
        channel_label.setFixedSize(200, 20)  # Setează dimensiunea fixă (200x20)
        layout.addWidget(channel_label, 0, 1)  # Adaugă QLabel la poziția (2, 1)

        button_legend = QPushButton("Legenda", self)
        #button_legend.clicked.connect(self.open_legend_dialog)
        layout.addWidget(button_legend, 4, 1)
        button_legend.clicked.connect(self.open_legend_dialog)
        button_legend.setStyleSheet(
    "QPushButton {"
    "   background-color: #007bfa;"
    "   color: #fff;"
    "   font-weight: bold;"
    "   border-radius: 10px;"
    "}"
    "QPushButton:hover {"
    "   background-color: #0056b3;"
    "}"
        )

        channel_dropdown = QComboBox()
        channel_dropdown.setFixedSize(200, 30)
        layout.addWidget(channel_dropdown, 1, 1, alignment=Qt.AlignLeft)  # Adaugă QComboBox la poziția (3, 1)
        channel_dropdown.addItem("1")
        channel_dropdown.addItem("2")
        channel_dropdown.addItem("3")
        channel_dropdown.addItem("4")
        channel_dropdown.addItem("5")
        channel_dropdown.addItem("6")

        # CheckBox pentru oprirea/pornirea Bluetooth-ului
        self.bluetooth_button = QCheckBox("Bluetooth OFF", self)
        self.bluetooth_button.setCheckable(True)
        self.bluetooth_button.clicked.connect(self.toggle_bluetooth)

        layout.addWidget(self.bluetooth_button, 4, 0)

        # Buton pentru trimiterea comenzii
        button_connect = QPushButton("Conectare")
        layout.addWidget(button_connect, 5, 0)  # Adaugă QPushButton la poziția (5, 0)

        button_disconnect = QPushButton("Deconectare")
        layout.addWidget(button_disconnect, 5, 1)  # Adaugă QPushButton la poziția (5, 1)

        # Input textbox
        input_label = QLabel("Introduceți mesajul:")
        layout.addWidget(input_label, 6, 0)

        self.input_textbox = QTextEdit()
        layout.addWidget(self.input_textbox, 7, 0)

        # Output textbox
        output_label = QLabel("Răspunsul CuteCom:")
        layout.addWidget(output_label, 6, 1)

        self.output_textbox = QTextEdit()
        #self.output_textbox.selectAll()
        #self.output_textbox.setReadOnly(True)
        layout.addWidget(self.output_textbox, 7, 1)

        # Numărul de trimiteri textbox
        num_sends_label = QLabel("Numărul de trimiteri:")
        layout.addWidget(num_sends_label, 8, 0)

        self.num_sends_textbox = QLineEdit()
        layout.addWidget(self.num_sends_textbox, 9, 0)

        # Delay între trimiteri textbox
        delay_label = QLabel("Delay între trimiteri (secunde):")
        layout.addWidget(delay_label, 8, 1)
        
        self.delay_textbox = QLineEdit()
        layout.addWidget(self.delay_textbox, 9, 1)

        # Buton pentru trimiterea mesajelor
        send_button = QPushButton("Trimite")
        #Aceasta comanda apeleaza cautarea caracterelor de "41" pana la endline sau ">"
        #send_button.clicked.connect(self.decode_octeti) 
        layout.addWidget(send_button, 10, 0, 1, 2)

        # Input bytes
        self.bytes_in_label = QLabel("Introduceți octeti pentru decodificare:")
        layout.addWidget(self.bytes_in_label, 11, 0)

        self.bytes_in_textbox = QTextEdit()
        layout.addWidget(self.bytes_in_textbox, 12, 0)

        # Output bytes
        self.bytes_out_label = QLabel("Răspunsul decodificat din octetii primiti:")
        layout.addWidget(self.bytes_out_label, 11, 1)

        self.bytes_out_textbox = QTextEdit()
        self.bytes_out_textbox.setReadOnly(True)
        layout.addWidget(self.bytes_out_textbox, 12, 1)

        # Buton pentru trimiterea comenzii
        self.button_decodare = QPushButton("Decodificare")
        self.button_decodare.clicked.connect(self.convert_bytes1)
        layout.addWidget(self.button_decodare, 13, 0) 

        # Buton pentru generare grafic
        self.button_grafic = QPushButton("Genereaza grafic")
        self.button_grafic.clicked.connect(self.generate_graph)
        layout.addWidget(self.button_grafic, 13, 1) 


        #
        self.decoded_octeti=''

        # Widget-ul central
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        # Serial connection
        self.serial_connection = None

        # Conectarea butoanelor la funcțiile corespunzătoare
        button_connect.clicked.connect(lambda: self.send_command(ip_dropdown.currentText(), channel_dropdown.currentText(), "connect"))
        button_disconnect.clicked.connect(lambda: self.send_command(ip_dropdown.currentText(), channel_dropdown.currentText(), "disconnect"))
        send_button.clicked.connect(self.send_messages)
        #send_button.clicked.connect(self.decode_octeti)
        self.bluetooth_button.stateChanged.connect(self.toggle_bluetooth)
    
        self.data = {}
        self.current_param = ""
        self.figure = None
        self.result = ""
    def send_command(self, selected_ip, selected_channel, action):
        if action == "connect":
            command = f"xterm -e 'sudo rfcomm connect /dev/rfcomm0 {selected_ip} {selected_channel} -b PP0C'"
        elif action == "disconnect":
            command = "sudo rfcomm release /dev/rfcomm0"

        try:
            subprocess.Popen(command, shell=True)
        except subprocess.CalledProcessError as e:
            QMessageBox.warning(self, "Eroare", f"A apărut o eroare în timpul execuției comenzii:\n{e}")

        if action == "connect":
            QMessageBox.information(self, "Conectare", "Comanda de conectare a fost trimisă într-un terminal separat.")
        elif action == "disconnect":
            QMessageBox.information(self, "Deconectare", "Dispozitivul a fost deconectat.")

    def establish_connection(self):
        try:
            # Open serial connection
            self.serial_connection = serial.Serial('/dev/rfcomm0', 115200, timeout=1)
        except serial.SerialException as e:
            QMessageBox.warning(self, "Eroare", f"A apărut o eroare în timpul stabilirii conexiunii:\n{e}")
            return False

        # Wait for device response
        self.serial_connection.write(b'ATZ\r')
        response = self.read_response()

        if b'ELM327' in response:
            return True

        QMessageBox.warning(self, "Eroare", "Conexiunea cu dispozitivul nu a fost stabilită corect.")
        return False

    def send_messages(self):
        message = self.input_textbox.toPlainText()
        num_sends = int(self.num_sends_textbox.text())
        delay = float(self.delay_textbox.text())
        self.output_textbox.clear()
        try:
            self.output_textbox.clear()
            if not self.serial_connection:
                # Establish connection if not already established
                if not self.establish_connection():
                    return

            for _ in range(num_sends):
                self.serial_connection.write(message.encode() + b'\r')
                response = self.read_response()
                self.output_textbox.clear()
                self.output_textbox.append(response.decode())
                time.sleep(2)
                #Actualizeaza output_textbox la fiecare iteratie
                #self.output_textbox.repaint() 
                # print(response.decode())

                # Obținerea șirului de caractere din textboxul de output (CuteCom)
                input_text = self.output_textbox.toPlainText()  # Obținere text cu linii noi din textboxul de output al raspunsului CuteCom
                #print(input_text)
                #self.decode_octeti
                time.sleep(delay)
                # Căutarea secvenței "41" și extragerea caracterele dintre "41" (inclusiv) și ">" (exclusiv) sau newline ("\n") (exclusiv)
                self.decoded_octeti = ''
                found_41 = False
                capture_chars = False
                self.bytes_in_textbox.clear()

                for char in input_text:
                    if capture_chars:
                        if char == '\n' or char == '>':
                            break
                        self.decoded_octeti += char

                    if char == '4' and not found_41:
                        found_41 = True
                        if len(input_text) >= 2 and input_text[input_text.index(char) + 1] == '1':
                            capture_chars = True
                            self.decoded_octeti += '4'  # Adăugăm secvența "41" la rezultat
                print("acesta este decoded_octeti:")
                print(self.decoded_octeti) #410D51
                # Afișarea octeților decodificați în caseta de text
                #self.bytes_in_textbox.clear()
                if self.decoded_octeti:
                    self.bytes_in_textbox.append(self.decoded_octeti) 
                    self.bytes_in_textbox.repaint()
                    time.sleep(2)
                    self.button_decodare.click()


            QApplication.processEvents()
        
        except serial.SerialException as e:
            QMessageBox.warning(self, "Eroare", f"A apărut o eroare în timpul trimiterii mesajelor:\n{e}")

    def read_response(self):
        response = b''

        while True:
            byte = self.serial_connection.read()
            response += byte

            if byte == b'>':
                break

        return response

    def toggle_bluetooth(self):
        if self.bluetooth_button.isChecked():
            subprocess.Popen("sudo rfkill block bluetooth", shell=True)
            self.bluetooth_button.setText("Bluetooth OFF")
        else:
            subprocess.Popen("sudo rfkill unblock bluetooth", shell=True)
            self.bluetooth_button.setText("Bluetooth ON")

    def convert_bytes1(self):
        bytes_value = self.bytes_in_textbox.toPlainText()
        self.result = convert_bytes(bytes_value) #aici se stocheaza noua valoare
        print(self.result)
        print(type(self.result))
        # self.data=self.result
        self.add_data_to_list()
        self.bytes_out_textbox.setText(self.result)
        # self.data=''

    def add_data_to_list(self):#Aici am ramas cu trimiterea datelor.
        data = self.result
        match = re.match(r'(\d+(\.\d+)?)\s*(\w+)', data)
        if match:
            value = float(match.group(1)) # aici se salveaza numarul din raspunsul decodat
            param = match.group(3)  #aici se salveaza tipul (km/h, RPM, etc)
            # print("Valoare :"+ str(value))
            # print("Tip valoare:"+str(type(value)))
            # print("Param:"+str(param))
            # print("Tip Param"+str(type(param)))
            if param == self.current_param:
                if param in self.data:
                    print("IF:param in...:Self.data[param]:")
                    print(self.data)
                    self.data[param].append(value)
                else:
                    print("ELSE:param in...:Self.data[param]:"+str(self.data[param]))
                    self.data[param] = [value]
            else:
                print("ELSE")
                self.data = {param: [value]}
                self.current_param = param
            print(self.data)

                

    def generate_graph(self):
        if self.current_param in self.data:
            if self.figure is not None:
                plt.close(self.figure)
            self.figure = plt.figure()
            x = range(len(self.data[self.current_param]))
            plt.plot(x, self.data[self.current_param])
            plt.xlabel("Index")
            plt.ylabel("Valoare")
            plt.title(f"Grafic pentru {self.current_param}")
            plt.show()


    def clear_graph(self):
        if self.figure is not None:
            plt.close(self.figure)
            self.figure = None
    
    def open_legend_dialog(self):
        dialog = LegendDialog(self)
        dialog.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        dialog.exec_()
        

class LegendDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Legenda utilizării programului")
        
        # Eticheta pentru informații
        label = QLabel("Lista mesajelor de trimitere:", self)
        label.setFont(QFont("Arial", 20, QFont.Bold))
        
        # Câmpul de text pentru afișarea informațiilor
        text_edit = QTextEdit(self)
        text_edit.setReadOnly(True)
        text_edit.setFont(QFont("Arial", 10))
        text_edit.setText("")
        text = ("01 04 (Calculated engine load-Procentul de sarcina a motorului)\n")
        text += "01 05 (Engine coolant temperature-Temperatura apei)\n"
        text += "01 0B (Intake manifold absolute pressure-Presiune debitmetru)\n"
        text += "01 0C (Engine Speed -Turatii)\n"
        text += "01 0D (Vehicle Speed – Viteza)\n"
        text += "01 0E (Timing advance -Avansul de aprindere)\n"
        text += "01 0F (Intake air temperature -Temperatura de intrare in motor)\n"
        text += "01 10 (Mass air flow sensor (MAF) air flow rate- Cantitatea de aer la intrarea in motor)\n"
        text += "01 11 (Throttle position-Pozitia pedalei de acceleratie)\n"
        text += "01 1C (OBD standards the vehicle conforms to- Standarde OBD conform vehiculului)\n"
        text += "01 21 (Distance traveled with malfunction indicator lamp(MIL) on-Distanta parcursa cu Check Engine ON)\n"



        text_edit.setText(text)
        # Layout vertical pentru elementele dialogului
        layout = QVBoxLayout(self)
        layout.addWidget(label)
        layout.addWidget(text_edit)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    color = QColor(216, 226, 228)
    window.setStyleSheet(f"background-color:{color.name()};")
    
    window.show()
    sys.exit(app.exec_())

