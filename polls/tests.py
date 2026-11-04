import os
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth.models import User

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException


class MySeleniumTests(StaticLiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Configuracio del navegador
        opts = Options()
        opts.add_argument("-headless")

        firefox_bin = os.environ.get("FIREFOX_BIN")

        if firefox_bin:
             opts.binary_location = firefox_bin

        cls.selenium = webdriver.Firefox(options=opts)
        # Creacio del superusuari inicial
        user = User.objects.create_user(
            username="isard",
            email="isard@isardvdi.com",
            password="pirineus"
        )
        user.is_superuser = True
        user.is_staff = True
        user.save()

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def test_staff_question_permissions(self):

        # -----------------------------------------
        # 1. LOGIN COM A SUPERUSUARI
        # -----------------------------------------

        self.selenium.get(self.live_server_url + "/admin/")

        self.selenium.find_element(
            By.ID, "id_username"
        ).send_keys("isard")

        self.selenium.find_element(
            By.ID, "id_password"
        ).send_keys("pirineus")

        self.selenium.find_element(
            By.XPATH, "//input[@type='submit']"
        ).click()

        # Comprovar login correcte
        WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located(
                (By.ID, "site-name")
            )
        )

        # -----------------------------------------
        # 2. CREAR USUARI STAFF
        # -----------------------------------------

        self.selenium.get(
            self.live_server_url + "/admin/auth/user/add/"
        )

        self.selenium.find_element(
            By.ID, "id_username"
        ).send_keys("consulta")

        self.selenium.find_element(
            By.ID, "id_password1"
        ).send_keys("Consulta!2026Segura")

        self.selenium.find_element(
            By.ID, "id_password2"
        ).send_keys("Consulta!2026Segura")

        self.selenium.find_element(
            By.NAME, "_save"
        ).click()

        # -----------------------------------------
        # 3. ACTIVAR PERMIS STAFF I VIEW QUESTION
        # -----------------------------------------

        # Activar is_staff
        staff_checkbox = self.selenium.find_element(
            By.ID, "id_is_staff"
        )

        if not staff_checkbox.is_selected():
            staff_checkbox.click()

        # Buscar el permís Can view question
        permissions = Select(
            self.selenium.find_element(
                By.ID, "id_user_permissions_from"
            )
        )

        for option in permissions.options:
            if "Can view question" in option.text:
                option.click()
                break

        # Afegir el permís seleccionat
        self.selenium.find_element(
            By.ID, "id_user_permissions_add"
        ).click()

        # Guardar l'usuari
        self.selenium.find_element(
            By.NAME, "_save"
        ).click()

        # -----------------------------------------
        # 4. TANCAR SESSIO DEL SUPERUSUARI
        # -----------------------------------------
        self.selenium.get(self.live_server_url + "/admin/")

        logout_form = WebDriverWait(self.selenium, 10).until(
              EC.presence_of_element_located((By.ID, "logout-form"))
        )

        logout_form.submit()

        # Esperem que Django ens porti a la pàgina de login
        WebDriverWait(self.selenium, 10).until(
             EC.presence_of_element_located((By.ID, "id_username"))
        )

        # -----------------------------------------
        # 5. LOGIN COM A USUARI CONSULTA
        # -----------------------------------------

        self.selenium.get(
            self.live_server_url + "/admin/"
        )

        self.selenium.find_element(
            By.ID, "id_username"
        ).send_keys("consulta")

        self.selenium.find_element(
            By.ID, "id_password"
        ).send_keys("Consulta!2026Segura")

        self.selenium.find_element(
            By.XPATH, "//input[@type='submit']"
        ).click()

        # Comprovar entrada a l'administracio
        WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located(
                (By.ID, "site-name")
            )
        )

        # -----------------------------------------
        # 6. COMPROVAR QUE POT VEURE QUESTIONS
        # -----------------------------------------

        self.selenium.get(
            self.live_server_url + "/admin/polls/question/"
        )

        # Ha de poder veure el llistat
        self.assertIn(
            "changelist",
            self.selenium.page_source
        )

        # -----------------------------------------
        # 7. COMPROVAR QUE NO POT CREAR QUESTIONS
        # -----------------------------------------

        self.selenium.get(
            self.live_server_url + "/admin/polls/question/add/"
        )

        # No ha d'existir el formulari d'afegir pregunta
        try:
            self.selenium.find_element(
                By.ID, "question_form"
            )
            self.fail("L'usuari pot crear preguntes!")
        except NoSuchElementException:
            pass

        # -----------------------------------------
        # 8. COMPROVAR QUE NO POT ESBORRAR QUESTIONS
        # -----------------------------------------

        self.selenium.get(
            self.live_server_url + "/admin/polls/question/"
        )

        # No ha d'existir cap accio d'esborrar
        delete_links = self.selenium.find_elements(
            By.XPATH,
            "//a[contains(@href, '/delete/')]"
        )

        self.assertEqual(
            len(delete_links),
            0,
            "L'usuari pot esborrar preguntes!"
        )
