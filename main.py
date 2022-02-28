import sys
import json
from bs4 import BeautifulSoup
from PyQt5.QtWidgets import QApplication, QGridLayout, QLabel, QLineEdit
from PyQt5.QtWidgets import QMainWindow, QPlainTextEdit, QPushButton, QWidget
from PyQt5.QtWidgets import QMessageBox
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By


class App(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(600, 250)
        self.setWindowTitle('AlumniScraper')

        self.cw = QWidget()
        self.grid = QGridLayout(self.cw)

        self.html_label = QLabel('Insira o código HTML da tabela abaixo:')
        self.html_input = QPlainTextEdit()
        self.validate_btn = QPushButton('Validar')
        self.validate_btn.clicked.connect(self.validate_html)

        self.instruct = QLabel('Valide o código HTML inserido.')
        self.email_label = QLabel('E-mail:')
        self.email = QLineEdit()
        self.email.setDisabled(True)
        self.password_label = QLabel('Senha:')
        self.passw = QLineEdit()
        self.passw.setEchoMode(QLineEdit.Password)
        self.passw.setDisabled(True)

        self.submit = QPushButton('Extrair dados')
        self.submit.clicked.connect(self.scrape_data)
        self.submit.setDisabled(True)

        self.grid.addWidget(self.html_label, 1, 1, 1, 2)
        self.grid.addWidget(self.html_input, 2, 1, 1, 2)
        self.grid.addWidget(self.validate_btn, 3, 1, 1, 2)
        self.grid.addWidget(self.instruct, 4, 1, 1, 2)
        self.grid.addWidget(self.email_label, 5, 1, 1, 1)
        self.grid.addWidget(self.email, 5, 2, 1, 1)
        self.grid.addWidget(self.password_label, 6, 1, 1, 1)
        self.grid.addWidget(self.passw, 6, 2, 1, 1)
        self.grid.addWidget(self.submit, 7, 1, 1, 2)

        self.setCentralWidget(self.cw)

    def validate_html(self):
        html = BeautifulSoup(self.html_input.toPlainText(), 'html.parser')
        try:
            html.find('table').find('tr').find('td')
        except AttributeError:
            self.instruct.setText('Código HTML inválido.')
            self.email.setDisabled(True)
            self.passw.setDisabled(True)
            self.submit.setDisabled(True)
            return False
        self.instruct.setText('Insira suas credenciais do LinkedIn:')
        self.email.setDisabled(False)
        self.passw.setDisabled(False)
        self.submit.setDisabled(False)
        return True

    def scrape_data(self):
        if self.validate_html():

            nav = webdriver.Chrome(service=Service('./chromedriver'))

            nav.get('https://www.linkedin.com/login/')
            nav.find_element(By.ID, 'username').send_keys(self.email.text())
            nav.find_element(By.ID, 'password').send_keys(self.passw.text())
            xpath = '//*[@id="organic-div"]/form/div[3]/button'
            nav.find_element(By.XPATH, xpath).click()

            data = []
            errors = []
            html = BeautifulSoup(self.html_input.toPlainText(), 'html.parser')
            for row in html.find_all('tr'):
                if row.parent.name == 'thead':
                    continue
                try:
                    cells = row.find_all('td')
                    aux = cells[-1].find('a')['href']
                    url = 'https://linkedin' + aux.split('linkedin')[1]

                    nav.get(url)
                    doc = BeautifulSoup(nav.page_source, 'html.parser')

                    loc = 'text-body-small inline t-black--light break-words'
                    location = doc.find(class_=loc).text.strip()

                    comp = 'pv-text-details__right-panel-item'
                    company = doc.find(class_=comp).find('div').text.strip()

                    alumnus = {
                        'name': cells[0].text,
                        'company': company,
                        'location': location,
                        'area': cells[3].text,
                        'linkedinUrl': url
                    }
                except Exception as error:
                    alumnus = {
                        'name': cells[0].text,
                        'company': 'ERRO',
                        'location': 'ERRO',
                        'area': cells[3].text,
                        'linkedinUrl': url
                    }
                    errors.append((cells[0].text, error))
                data.append(alumnus)
            with open('data.json', 'w', encoding='utf8') as arq:
                json.dump(data, arq, indent=2, ensure_ascii=False)
            with open('log.txt', 'w') as arq:
                for name, error in errors:
                    arq.write(f'{name}: {error}\n')
            nav.quit()
            msg = (
                'Dados extraídos com sucesso e salvos no arquivo "data.json". '
                'Cheque o arquivo "logs.txt" para conferir erros.'
            )
            QMessageBox.about(self, 'Mensagem', msg)


if __name__ == '__main__':
    qt = QApplication(sys.argv)
    app = App()
    app.show()
    qt.exec_()
