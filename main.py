#!/usr/bin/env python
# coding=utf-8

import json
import os
import sys
import re

FQDN_RE = re.compile(r'(?=^.{4,255}$)(^((?!-)[a-zA-Z0-9-]{1,63}(?<!-)\.)+[a-zA-Z0-9-]{2,63}$)')


def settings():
    path = os.path.join(os.path.expanduser('~'), '.hostup')

    if not os.path.exists(path):
        f = open(path, 'w')
        f.close()

    f = open(path, 'r')
    out = f
    f.close()

    default = {
        'apache_port': 80,
        'projects_path': os.path.join(os.path.expanduser('~'), 'projects'),
        'user': os.path.dirname(os.path.expanduser('~'))
    }

    try:
        data = json.loads(out)
        if 'apache_port' in data and 'projects_path' in data and 'user' in data:
            return data
        else:
            return default
    except:
        return {
            'apache_port': 80,
            'projects_path': os.path.join(os.path.expanduser('~'), 'projects'),
            'user': os.path.basename(os.path.expanduser('~'))
        }


def main(*args):
    params = list(args[1:])
    if len(params) == 0 or len(params) > 1:
        print("Incorrect usage. Example usage: hostup example.com")
        return 255
    else:
        domain = params.pop()
        if not FQDN_RE.match(domain):
            print("Please select correct domain. Validation RE: (?=^.{4,255}$)(^((?!-)[a-zA-Z0-9-]{1,63}(?<!-)\.)+[a-zA-Z0-9-]{2,63}$)")
            return 255

        config = settings()
        config.update({
            'domain': domain,
        })

        dirs = ['{project_path}/www', '{project_path}/logs']

        project_path = '{projects_path}/{domain}'.format(**config)
        for dir in dirs:
            tmp = dir.format(project_path=project_path)

            if os.environ.get('FORCE', False) and os.path.exists(tmp):
                print("Project path already exists")
                return 255
            else:
                os.system('mkdir -p {tmp}'.format(tmp=tmp))

        template = """
<VirtualHost 127.0.0.1:{apache_port}>
    DocumentRoot "{project_path}"
    DirectoryIndex index.html index.php
    ServerAlias terem.dev
    ErrorLog "{projects_path}/{domain}/logs/apache-error.log"
    CustomLog "{projects_path}/{domain}/logs/apache-access.log" common

    <IfModule mpm_itk_module>
        AssignUserId {user} staff
    </IfModule>

    <Directory "{projects_path}/{domain}/www">
        Options +ExecCGI FollowSymLinks +SymLinksIfOwnerMatch
        AllowOverride All
        Allow from all
    </Directory>
</VirtualHost>
""".format(project_path=project_path, **config)

    os.system('mkdir -p /etc/apache2/sites')
    if os.environ.get('FORCE', False) and os.path.exists('/etc/apache2/sites/{domain}.conf'.format(domain=domain)):
        print('Config file already exists: /etc/apache2/sites/{domain}.conf'.format(domain=domain))
        return 255

    f = open('/etc/apache2/sites/{domain}.conf'.format(domain=domain), 'w')
    f.write(template)
    f.close()

    os.system('echo "127.0.0.1 {domain}" >> /etc/hosts'.format(domain=domain))
    os.system('apachectl restart')

    return 0

if __name__ == "__main__":
    """
    Add Include /private/etc/apache2/sites/*.conf to /etc/apache2/httpd.conf
    """
    exit_code = main(*sys.argv)
    sys.exit(exit_code)
