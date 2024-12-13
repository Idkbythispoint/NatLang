import json
import os

class PasswordManager:
    def __init__(self, storage_file='passwords.json'):
        self.storage_file = storage_file
        self.load_passwords()

    def load_passwords(self):
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r') as f:
                    self.passwords = json.load(f)
            except (json.JSONDecodeError, TypeError):
                self.passwords = {}
        else:
            self.passwords = {}

    def save_passwords(self):
        with open(self.storage_file, 'w') as f:
            json.dump(self.passwords, f)

    def store_password(self, site: str, password: str) -> None:
        if site and password:
            self.passwords[site] = password
            self.save_passwords()

    def retrieve_password(self, site: str) -> str:
        return self.passwords.get(site, 'Password not found.')

    def delete_password(self, site: str) -> str:
        if site in self.passwords:
            del self.passwords[site]
            self.save_passwords()
            return f'Password for {site} deleted.'
        return 'Password not found to delete.'

    def __str__(self):
        return json.dumps(self.passwords, indent=2)


def main():
    pm = PasswordManager()
    while True:
        print('\n1. Store Password\n2. Retrieve Password\n3. Delete Password\n4. Exit')
        choice = input('Choose an option: ')
        if choice == '1':
            site = input('Enter site name: ')
            password = input('Enter password: ')
            pm.store_password(site, password)
            print('Password stored.')
        elif choice == '2':
            site = input('Enter site name to retrieve: ')
            print(pm.retrieve_password(site))
        elif choice == '3':
            site = input('Enter site name to delete: ')
            print(pm.delete_password(site))
        elif choice == '4':
            print('Exiting...')
            break
        else:
            print('Invalid choice, please try again.')

if __name__ == '__main__':
    main()