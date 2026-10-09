import os
import tempfile
import unittest

from app import create_app


class SantaClaraAppTests(unittest.TestCase):
    def setUp(self):
        self.db_path = os.path.join(tempfile.gettempdir(), "test_santaclara.db")
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.app = create_app({"TESTING": True, "DATABASE": self.db_path})
        self.client = self.app.test_client()

    def tearDown(self):
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except OSError:
                pass

    def test_public_pages_render(self):
        paths = (
            "/",
            "/nosotros",
            "/productos",
            "/contacto",
            "/formulario",
            "/pedido-registrado",
        )

        for path in paths:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertIn("Santa Clara", response.get_data(as_text=True))
                response.close()

    def test_registro_page_renders(self):
        response = self.client.get("/registro")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Crear cuenta", response.get_data(as_text=True))
        response.close()

    def test_language_switcher_and_theme_controls_are_available(self):
        response = self.client.get("/productos")
        body = response.get_data(as_text=True)

        self.assertIn("data-lang-toggle", body)
        self.assertIn("btnThemeToggle", body)
        self.assertIn("btnThemeToggleMobile", body)
        self.assertIn("toastContainer", body)
        response.close()

    def test_dark_theme_styles_are_available(self):
        response = self.client.get("/static/css/styles.css")
        stylesheet = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("body.dark-mode", stylesheet)
        self.assertIn("body.dark-mode .text-slate-800", stylesheet)
        self.assertIn('body.dark-mode [class~="bg-white/95"]', stylesheet)
        self.assertIn("body.dark-mode input", stylesheet)
        response.close()

    def test_chatbot_widget_and_script_are_available(self):
        page = self.client.get("/")
        body = page.get_data(as_text=True)

        self.assertIn('id="chatbot-toggle"', body)
        self.assertIn('id="chatbot-panel"', body)
        self.assertIn("js/chatbot.js", body)
        page.close()

        script = self.client.get("/static/js/chatbot.js")
        source = script.get_data(as_text=True)
        self.assertEqual(script.status_code, 200)
        self.assertIn("getReply", source)
        self.assertIn("No tengo esa información", source)
        self.assertIn("I don't have that information", source)
        script.close()

    def test_contact_form_accepts_valid_submission(self):
        response = self.client.post(
            "/contacto",
            data={
                "nombre": "Ana",
                "celular": "999999999",
                "mensaje": "Quisiera información sobre un pedido.",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Gracias, Ana", response.get_data(as_text=True))
        response.close()

    def test_contact_form_escapes_user_input(self):
        response = self.client.post(
            "/contacto",
            data={
                "nombre": "<script>alerta()</script>",
                "celular": "999999999",
                "mensaje": "Mensaje de prueba",
            },
        )

        body = response.get_data(as_text=True)
        self.assertNotIn("<script>alerta()</script>", body)
        self.assertIn("&lt;script&gt;", body)
        response.close()

    def test_incomplete_contact_message_shows_validation_error(self):
        response = self.client.post(
            "/contacto",
            data={"nombre": "Ana", "celular": "", "mensaje": ""},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "Completa tu nombre, celular y mensaje.",
            response.get_data(as_text=True),
        )
        response.close()

    def test_order_form_redirects_to_confirmation(self):
        response = self.client.post(
            "/formulario",
            data={
                "nombre": "Ana",
                "telefono": "999999999",
                "producto": "Queso Fresco",
                "cantidad": "1",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/pedido-registrado"))
        response.close()

    def test_catalog_has_only_three_varieties_per_main_product(self):
        from app.catalog import PRODUCTS

        categories = {"leche": 0, "yogurt": 0, "queso": 0}
        for product in PRODUCTS:
            if product["category"] in categories:
                categories[product["category"]] += 1

        self.assertEqual(categories["leche"], 3)
        self.assertEqual(categories["yogurt"], 3)
        self.assertEqual(categories["queso"], 3)

    def test_compiled_stylesheet_is_available(self):
        response = self.client.get("/static/css/output.css")
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data), 1_000)
        response.close()

    def test_registro_creates_account_and_redirects(self):
        response = self.client.post(
            "/registro",
            data={
                "nombre": "María Pérez",
                "correo": "maria@example.com",
                "telefono": "999888777",
                "password": "secreto123",
                "confirmar_password": "secreto123",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/"))
        response.close()

        with self.app.app_context():
            from app.db import get_db

            user = get_db().execute(
                "SELECT * FROM users WHERE correo = ?", ("maria@example.com",)
            ).fetchone()
            self.assertIsNotNone(user)
            self.assertEqual(user["nombre"], "María Pérez")

    def test_registro_rejects_mismatched_passwords(self):
        response = self.client.post(
            "/registro",
            data={
                "nombre": "Ana",
                "correo": "ana@example.com",
                "password": "secreto123",
                "confirmar_password": "otro123",
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("no coinciden", response.get_data(as_text=True))
        response.close()


if __name__ == "__main__":
    unittest.main()
