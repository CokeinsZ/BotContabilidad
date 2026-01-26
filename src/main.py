from google_auth.auth_manager import GoogleAuthManager

def main():
    auth_manager = GoogleAuthManager()
    credentials = auth_manager.get_credentials()
    print("Autenticación exitosa. Credenciales obtenidas.")


if __name__ == "__main__":
    main()
