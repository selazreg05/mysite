
import os

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth.models import User

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from selenium.common.exceptions import (
    StaleElementReferenceException,
    NoSuchElementException,
)


class MySeleniumTests(StaticLiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Configuracio del navegador Firefox
        opts = Options()
        opts.add_argument("-headless")

        firefox_bin = os.environ.get("FIREFOX_BIN")
        if firefox_bin:
            opts.binary_location = firefox_bin

        cls.selenium = webdriver.Firefox(options=opts)
        cls.selenium.implicitly_wait(3)

        # Creacio del superusuari
        User.objects.create_superuser(
            username="isard",
            email="isard@isardvdi.com",
            password="pirineus"
        )

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def test_staff_question_permissions(self):

        wait = WebDriverWait(
            self.selenium,
            15,
            ignored_exceptions=(
                StaleElementReferenceException,
                NoSuchElementException,
            )
        )

        # 1. Entrar com a superusuari
        self.selenium.get(self.live_server_url + "/admin/")

        wait.until(
            EC.visibility_of_element_located((By.ID, "id_username"))
        ).send_keys("isard")

        self.selenium.find_element(
            By.ID, "id_password"
        ).send_keys("pirineus")

        self.selenium.find_element(
            By.CSS_SELECTOR, "input[type='submit']"
        ).click()

        wait.until(
            EC.presence_of_element_located((By.ID, "user-tools"))
        )

        # 2. Crear l'usuari consulta
        self.selenium.get(
            self.live_server_url + "/admin/auth/user/add/"
        )

        wait.until(
            EC.visibility_of_element_located((By.ID, "id_username"))
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

        # 3. Buscar l'usuari consulta
        self.selenium.get(
            self.live_server_url + "/admin/auth/user/"
        )

        cerca = wait.until(
            EC.visibility_of_element_located((By.ID, "searchbar"))
        )

        cerca.clear()
        cerca.send_keys("consulta")
        cerca.send_keys(Keys.ENTER)

        selector_usuari = (
            By.XPATH,
            "//table//a[contains(@href, '/change/') "
            "and contains(text(), 'consulta')]"
        )

        wait.until(
            EC.presence_of_element_located(selector_usuari)
        )

        # Clicar l'enllaç tornant a localitzar-lo si canvia el DOM
        def clicar_usuari(driver):
            try:
                element = driver.find_element(*selector_usuari)

                if element.is_displayed() and element.is_enabled():
                    element.click()
                    return True

            except (
                StaleElementReferenceException,
                NoSuchElementException,
            ):
                return False

            return False

        wait.until(clicar_usuari)

        # 4. Donar permisos a l'usuari
        wait.until(
            EC.presence_of_element_located((By.ID, "id_is_staff"))
        )

        camp_staff = self.selenium.find_element(
            By.ID, "id_is_staff"
        )

        if not camp_staff.is_selected():
            camp_staff.click()

        permisos = Select(
            self.selenium.find_element(
                By.ID, "id_user_permissions_from"
            )
        )

        opcio_trobada = False

        for opcio in permisos.options:
            if "Can view question" in opcio.text:
                permisos.select_by_value(
                    opcio.get_attribute("value")
                )
                opcio_trobada = True
                break

        self.assertTrue(
            opcio_trobada,
            "No s'ha trobat el permís Can view question"
        )

        self.selenium.find_element(
            By.ID, "id_user_permissions_add"
        ).click()

        self.selenium.find_element(
            By.NAME, "_save"
        ).click()

        # 5. Tancar la sessio del superusuari
        self.selenium.delete_all_cookies()

        # 6. Entrar com a usuari consulta
        self.selenium.get(
            self.live_server_url + "/admin/login/"
        )

        wait.until(
            EC.visibility_of_element_located((By.ID, "id_username"))
        ).send_keys("consulta")

        self.selenium.find_element(
            By.ID, "id_password"
        ).send_keys("Consulta!2026Segura")

        self.selenium.find_element(
            By.CSS_SELECTOR, "input[type='submit']"
        ).click()

        wait.until(
            EC.presence_of_element_located((By.ID, "user-tools"))
        )

        # 7. Comprovar que pot veure les preguntes
        self.selenium.get(
            self.live_server_url + "/admin/polls/question/"
        )

        wait.until(
            EC.presence_of_element_located((By.ID, "changelist"))
        )

        self.assertIn(
            "changelist",
            self.selenium.page_source
        )

        # 8. Comprovar que no pot afegir preguntes
        self.selenium.get(
            self.live_server_url + "/admin/polls/question/add/"
        )

        self.assertNotIn(
            'id="question_form"',
            self.selenium.page_source
        )

        # 9. Comprovar que no pot eliminar preguntes
        self.selenium.get(
            self.live_server_url + "/admin/polls/question/"
        )

        enllacos_eliminar = self.selenium.find_elements(
            By.XPATH,
            "//a[contains(@href, '/delete/')]"
        )

        self.assertEqual(
            len(enllacos_eliminar),
            0,
            "L'usuari consulta no hauria de poder eliminar preguntes"
        )
