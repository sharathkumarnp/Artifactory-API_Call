#! /usr/bin/python3

import sys
import json
from tokenize import group
import requests
import argparse
import getpass
import re
from secrets import SERVER

INDENTATION_THRESHOLD = 10

class CLI:
    def __init__(self) -> None:
        self.username = ''
        self.password = ''
        self.server = SERVER
        self.group = 'administrators'
        self.url = f'https://{self.server}.jfrog.io/artifactory/api/'
        self._user_credentials()
        self.token = self._get_token_for_group(self.group)
        self.session = requests.Session()
        self._set_session(self.token)

    def _user_credentials(self) -> None:
        # Get user credentials from the command line on script start
        parser = argparse.ArgumentParser(description='CLI for the JFrog REST API')
        parser.add_argument('-u', '--username', help="personal username to login to JFrog's REST API", required=True)
        args = parser.parse_args()
        self.username = args.username
        self.password = getpass.getpass(prompt='Enter password: ')

    #----- Utility methods -----
    def _set_session(self, token: str) -> None:
        self.headers = {'Authorization': f'Bearer {token}'}
        self.session.headers.update(self.headers)

    def _set_url(self, endpoint: str) -> str:
        url = ''.join([self.url, endpoint])
        return url

    def _get_token_for_group(self, group: str) -> str:
        # curl -u $user:$password -XPOST "https://<server_name>.jfrog.io/artifactory/api/security/token" -d "username=$user" -d "scope=member-of-groups:readers" > .tok
        endpoint = 'security/token'
        url = self._set_url(endpoint)
        data = {'username':self.username, 'password':self.password, 'scope=member-of-groups':group}
        try:
            r = requests.post(url, auth=(self.username, self.password), data=data)
        except Exception as e:
            print(f'API call error in {r}\n{e}')

        return r.json()['access_token']

    #----- Menu options implementation -----
    # 1
    def _system_ping(self) -> str:
        # curl -H "Authorization: Bearer $Access_Token" https://<server_name>.jfrog.io/artifactory/api/system/ping
        endpoint = 'system/ping'
        url = self._set_url(endpoint)
        try:
            r = self.session.get(url, headers=self.session.headers)
        except Exception as e:
            print(f'API call error in {r}\n{e}')

        return f"{(self.url).split('artifactory', 1)[0]} - Status: {r.text}"

    # 2
    def _system_version(self) -> str:
        # curl -H "Authorization: Bearer $Access_Token" https://<server_name>.jfrog.io/artifactory/api/system/ping
        endpoint = 'system/version'
        url = self._set_url(endpoint)
        try:
            r = self.session.get(url, headers=self.session.headers)
        except Exception as e:
            print(f'API call error in {r}\n{e}')

        return f"{r.json()['version']}"

    def _is_valid_email(self, email) -> bool:
        regex = r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+'
        if re.fullmatch(regex, email):
            return True
        return False

    # 3
    def _create_user(self) -> str:
        '''
        Notes: Requires Artifactory Pro
        Usage: PUT /api/security/users/{userName}
        '''
        username = input("Enter username: ")
        email = input("Enter email: ")
        password = input("Enter password: ")
        if not self._is_valid_email(email):
            raise ValueError("Invalid Email")
        if not all([username, email, password]):
            raise ValueError("Missing one or more values (username, email, password)")

        endpoint = f'security/users/{username}'
        url = self._set_url(endpoint)
        # email and password are mandatory, name is optional
        json = {'name': username,
                'email' : email,
                'password': password
                }

        try:
            r = self.session.put(url, headers=self.session.headers, json=json)
        except Exception as e:
            print(f'API call error in {r}\n{e}')

        return f"User {username} created successfully" if r.status_code == 201 else f"HTTP {r.status_code}- Something went wrong, try again.."

    # 4
    def _delete_user(self) -> str:
        '''
        Notes: Requires Artifactory Pro
        Usage: DELETE /api/security/users/{userName}
        '''
        username = input("Enter username to delete: ")
        if username is None or username == "":
            raise ValueError("Missing username")
        endpoint = f'security/users/{username}'
        url = self._set_url(endpoint)
        try:
            r = self.session.delete(url, headers=self.session.headers)
        except Exception as e:
            print(f'API call error in {r}\n{e}')

        return f"User {username} deleted successfully" if r.status_code == 200 else f"HTTP {r.status_code}- Something went wrong, try again.."

    # 5
    def _get_storage_info(self) -> json:
        '''
        Returns storage summary information regarding binaries, file store and repositories.
        Usage: GET /api/storageinfo
        '''
        endpoint = 'storageinfo'
        url = self._set_url(endpoint)
        try:
            r = self.session.get(url, headers=self.session.headers)
        except Exception as e:
            print(f'API call error in {r}\n{e}')

        return r.json()

    # 0
    def _exit(self) -> str:
        '''
        sys.exit() does not work from within a loop
        '''
        # sys.exit(0)
        # raise SystemExit(0)
        return "Bye.."

    #----- UI -----
    def _menu_options(self) -> dict:
        menu_options = {
            1: ("Ping", self._system_ping),
            2: ("Artifactory Version", self._system_version),
            3: ("Create User", self._create_user),
            4: ("Delete User", self._delete_user),
            5: ("Get Storage Info", self._get_storage_info),
            0: ("Exit", None)
        }

        return menu_options

    def _display_menu(self, menu_options) -> None:
        for op_number, op_data in menu_options.items():
            indentation = " --" if op_number < INDENTATION_THRESHOLD else "--"
            print(op_number, indentation, op_data[0])

    def main(self):
        menu_options = self._menu_options()
        while True:
            print() # for better readability
            self._display_menu(menu_options)

            try:
                op = int(input("Enter your choice: "))
                if op == list(menu_options.keys())[-1]: # exit is always the last option in the menu
                    print(self._exit())
                    break

                info, func = menu_options.get(op, (None, None))
                if func:
                    print(info + ":")
                    r = func()
                    print(r)
                else:
                    print(f"{op} is not defined")

            except Exception as e:
                print(e, "\n")

if __name__ == '__main__':
    cli = CLI()
    cli.main()


