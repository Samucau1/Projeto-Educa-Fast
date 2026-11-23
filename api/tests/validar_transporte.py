"""Real TLS integration using temporary certificates and isolated Docker resources.

Usage: python tests/validar_transporte.py --directory <temporary-artifact-directory>
Build educafast-security-app from the application Dockerfile first.
Never connects to an existing installation; containers/network are removed in finally.
"""
import argparse
import ipaddress
import json
import secrets
import ssl
import subprocess
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography import x509
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID


def docker(*args, check=True):
    return subprocess.run(['docker', *args], capture_output=True, text=True, check=check)


def certificates(folder):
    now = datetime.now(timezone.utc)
    ca_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'EducaFast test CA')])
    ca = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(ca_key.public_key())
          .serial_number(x509.random_serial_number()).not_valid_before(now-timedelta(minutes=1))
          .not_valid_after(now+timedelta(days=1)).add_extension(x509.BasicConstraints(ca=True,path_length=0),critical=True)
          .add_extension(x509.KeyUsage(digital_signature=True,content_commitment=False,key_encipherment=False,
                                      data_encipherment=False,key_agreement=False,key_cert_sign=True,crl_sign=True,
                                      encipher_only=None,decipher_only=None),critical=True)
          .add_extension(x509.SubjectKeyIdentifier.from_public_key(ca_key.public_key()),critical=False)
          .sign(ca_key,hashes.SHA256()))
    (folder/'ca.crt').write_bytes(ca.public_bytes(serialization.Encoding.PEM))
    for role, domains in [('db',[x509.DNSName('db')]),('web',[x509.DNSName('localhost'),x509.IPAddress(ipaddress.ip_address('127.0.0.1'))])]:
        key = rsa.generate_private_key(public_exponent=65537,key_size=2048)
        cert = (x509.CertificateBuilder().subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,role)]))
                .issuer_name(name).public_key(key.public_key()).serial_number(x509.random_serial_number())
                .not_valid_before(now-timedelta(minutes=1)).not_valid_after(now+timedelta(days=1))
                .add_extension(x509.BasicConstraints(ca=False,path_length=None),critical=True)
                .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_key.public_key()),critical=False)
                .add_extension(x509.SubjectAlternativeName(domains),critical=False).sign(ca_key,hashes.SHA256()))
        (folder/f'{role}.crt').write_bytes(cert.public_bytes(serialization.Encoding.PEM))
        (folder/f'{role}.key').write_bytes(key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory',required=True)
    args=parser.parse_args()
    folder=(Path(args.directory).resolve()/('tls-'+secrets.token_hex(4)))
    folder.mkdir(parents=True)
    certificates(folder)
    suffix=secrets.token_hex(4)
    network='educafast-tls-'+suffix
    db='educafast-tls-db-'+suffix
    app='educafast-tls-app-'+suffix
    password=secrets.token_urlsafe(32)
    try:
        docker('network','create','--internal',network)
        docker('run','-d','--name',db,'--network',network,'--network-alias','db',
               '--mount',f'type=bind,src={folder},dst=/run/tls,readonly','--tmpfs','/var/lib/mysql',
               '-e','MYSQL_DATABASE=educafast_tls','-e','MYSQL_USER=tls_user','-e','MYSQL_PASSWORD='+password,
               '-e','MYSQL_ROOT_PASSWORD='+secrets.token_urlsafe(32),'mysql:8.4',
               '--require-secure-transport=ON','--ssl-ca=/run/tls/ca.crt',
               '--ssl-cert=/run/tls/db.crt','--ssl-key=/run/tls/db.key',
               '--innodb-buffer-pool-size=32M','--max-connections=30','--performance-schema=OFF')
        for _ in range(90):
            ready=docker('exec','-e','MYSQL_PWD='+password,db,'mysql','--protocol=socket','-utls_user','-e','SELECT 1',check=False)
            if ready.returncode==0: break
            time.sleep(1)
        else: raise RuntimeError('Temporary MySQL did not become ready')
        # A second bridge provides only the loopback host publish; DB remains internal.
        docker('run','-d','--name',app,'--publish','127.0.0.1::5000',
               '--mount',f'type=bind,src={folder},dst=/run/tls,readonly',
               '-e','APP_ENV=production','-e','COOKIE_SECURE=1',
               '-e','LGPD_CONTATO=teste@localhost','-e','TRUSTED_HOSTS=localhost,127.0.0.1',
               '-e','SECRET_KEY='+secrets.token_urlsafe(48),'-e','DATA_ENCRYPTION_KEY='+Fernet.generate_key().decode(),
               '-e','DB_HOST=db','-e','DB_NAME=educafast_tls','-e','DB_USER=tls_user','-e','DB_PASSWORD='+password,
               '-e','DB_SSL_CA=/run/tls/ca.crt','-e','TLS_CERT_FILE=/run/tls/web.crt','-e','TLS_KEY_FILE=/run/tls/web.key',
               'educafast-security-app')
        docker('network','connect',network,app)
        port=json.loads(docker('inspect',app).stdout)[0]['NetworkSettings']['Ports']['5000/tcp'][0]['HostPort']
        url='https://127.0.0.1:'+port
        context=ssl.create_default_context(cafile=str(folder/'ca.crt'))
        for _ in range(60):
            state=docker('inspect','--format','{{.State.Status}}',app).stdout.strip()
            if state == 'exited':
                raise RuntimeError('HTTPS process exited: '+docker('logs','--tail','15',app).stderr)
            try:
                with urllib.request.urlopen(url+'/privacidade',context=context,timeout=2) as response:
                    assert response.status==200
                    assert response.headers['Strict-Transport-Security']=='max-age=31536000'
                break
            except (OSError,urllib.error.URLError): time.sleep(1)
        else: raise RuntimeError('HTTPS server did not become ready')
        try:
            urllib.request.urlopen(url,timeout=3)
        except urllib.error.URLError as error:
            assert isinstance(error.reason,ssl.SSLCertVerificationError)
        else: raise AssertionError('Untrusted certificate was accepted')
        try:
            urllib.request.urlopen('http://127.0.0.1:'+port,timeout=3)
        except (OSError,urllib.error.URLError): pass
        else: raise AssertionError('Plain HTTP accepted on TLS endpoint')
        result=docker('exec',app,'python','-c',"from app.database import engine; from sqlalchemy import text; c=engine.connect(); assert c.execute(text(\"SHOW SESSION STATUS LIKE 'Ssl_cipher'\")).one()[1]; c.close()")
        assert result.returncode==0
        plaintext=docker('exec','-e','MYSQL_PWD='+password,db,'mysql','--ssl-mode=DISABLED','-hdb','-utls_user','-e','SELECT 1',check=False)
        assert plaintext.returncode!=0 and '3159' in plaintext.stderr
        ip=json.loads(docker('inspect',db).stdout)[0]['NetworkSettings']['Networks'][network]['IPAddress']
        mismatch=docker('exec','-e','DB_HOST='+ip,app,'python','-c','from app.database import engine; engine.connect()',check=False)
        assert mismatch.returncode!=0 and ('CERTIFICATE_VERIFY_FAILED' in mismatch.stderr or 'certificate verify failed' in mismatch.stderr)
        print('PASS: HTTPS trusted CA; untrusted CA rejected; plaintext HTTP rejected; HSTS; MySQL TLS cipher; plaintext MySQL rejected; database identity mismatch rejected.')
        return 0
    finally:
        docker('rm','-f',app,db,check=False)
        docker('network','rm',network,check=False)


if __name__=='__main__':
    raise SystemExit(main())
