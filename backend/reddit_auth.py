"""Local read-only Reddit OAuth setup. Secrets are protected with Windows DPAPI."""
import base64
import ctypes
from ctypes import wintypes
from http.server import BaseHTTPRequestHandler, HTTPServer
import html
import json
from pathlib import Path
import secrets
import sys
import time
import urllib.parse
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
ORIGIN='http://127.0.0.1:8765'
CALLBACK=ORIGIN+'/callback'


class Blob(ctypes.Structure):
    _fields_=[('size',wintypes.DWORD),('data',ctypes.POINTER(ctypes.c_ubyte))]


def protect(raw,decrypt=False):
    if sys.platform!='win32': raise RuntimeError('Windows DPAPI is required')
    buffer=ctypes.create_string_buffer(raw)
    source=Blob(len(raw),ctypes.cast(buffer,ctypes.POINTER(ctypes.c_ubyte)))
    target=Blob()
    crypt=ctypes.WinDLL('crypt32',use_last_error=True)
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.LocalFree.argtypes=[ctypes.c_void_p]; kernel.LocalFree.restype=ctypes.c_void_p
    function=crypt.CryptUnprotectData if decrypt else crypt.CryptProtectData
    function.argtypes=[ctypes.POINTER(Blob),ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,wintypes.DWORD,ctypes.POINTER(Blob)]
    function.restype=wintypes.BOOL
    if not function(ctypes.byref(source),None,None,None,None,1,ctypes.byref(target)):
        raise RuntimeError('Windows credential protection failed')
    try: return ctypes.string_at(target.data,target.size)
    finally: kernel.LocalFree(ctypes.cast(target.data,ctypes.c_void_p))


def credential_path(root=ROOT): return root/'.local/credentials/reddit.dpapi'


def save_credentials(data,root=ROOT):
    path=credential_path(root); path.parent.mkdir(parents=True,exist_ok=True)
    encrypted=protect(json.dumps(data).encode())
    temporary=path.with_suffix('.tmp'); temporary.write_bytes(encrypted); temporary.replace(path)


def read_credentials(root=ROOT):
    return json.loads(protect(credential_path(root).read_bytes(),decrypt=True))


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs): raise ValueError('OAuth redirect refused')


def token_request(client_id,client_secret,fields):
    basic=base64.b64encode((client_id+':'+client_secret).encode()).decode()
    request=urllib.request.Request('https://www.reddit.com/api/v1/access_token',
        data=urllib.parse.urlencode(fields).encode(),headers={'Authorization':'Basic '+basic,
        'User-Agent':'windows:AlphaDeskResearch:0.2','Content-Type':'application/x-www-form-urlencoded'})
    with urllib.request.build_opener(NoRedirect()).open(request,timeout=20) as response:
        raw=response.read(64001)
    if len(raw)>64000: raise ValueError('OAuth response too large')
    data=json.loads(raw)
    if not data.get('access_token') or data.get('token_type','').lower()!='bearer': raise ValueError('OAuth token was not granted')
    if set(data.get('scope','').split())!={'read'}: raise ValueError('Expected read-only OAuth scope')
    return data


def get_access_token(root=ROOT):
    path=credential_path(root)
    if not path.exists(): return None,'Not connected — complete local Reddit setup.'
    try:
        data=read_credentials(root)
        if data.get('usage_approved') is not True: return None,'API collection is disabled until Reddit usage approval is confirmed.'
        if data.get('scope')!='read': return None,'Read-only Reddit scope is required.'
        if data.get('expires_at',0)<time.time()+60:
            response=token_request(data['client_id'],data['client_secret'],
                {'grant_type':'refresh_token','refresh_token':data['refresh_token']})
            data.update(access_token=response['access_token'],expires_at=time.time()+int(response['expires_in']))
            save_credentials(data,root)
        return data['access_token'],'Read-only OAuth configured.'
    except Exception as exc: return None,'Reddit credentials unavailable: '+type(exc).__name__


def main():
    if sys.platform!='win32': raise SystemExit('This setup uses Windows DPAPI and requires Windows.')
    csrf=secrets.token_urlsafe(32)
    session={'expires':time.monotonic()+900}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args): pass  # Never log OAuth callback URLs or codes.

        def page(self,body,status=200):
            self.send_response(status)
            self.send_header('Content-Type','text/html; charset=utf-8')
            self.send_header('Cache-Control','no-store')
            self.send_header('Referrer-Policy','no-referrer')
            self.send_header('Content-Security-Policy',"default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'")
            self.end_headers()
            self.wfile.write(('''<!doctype html><html lang="en"><meta name="viewport" content="width=device-width"><title>Alpha Desk · Reddit setup</title><style>body{background:#f7f8f3;color:#19251d;font:16px/1.6 system-ui;max-width:600px;margin:60px auto;padding:24px}h1{letter-spacing:-1px}input[type=text],input[type=password]{display:block;width:100%;box-sizing:border-box;padding:13px;border:1px solid #cad5bd;border-radius:8px;margin:8px 0 22px}button{background:#19251d;color:white;border:0;border-radius:24px;padding:14px 24px;margin-top:24px}small{color:#687268}a{color:#315d36}</style>'''+body+'</html>').encode())

        def permitted(self):
            return self.headers.get('Host')=='127.0.0.1:8765' and time.monotonic()<session['expires']

        def do_GET(self):
            if not self.permitted(): self.page('<h1>Setup expired or host refused.</h1><p>Restart the local setup command.</p>',403); return
            parsed=urllib.parse.urlsplit(self.path)
            if parsed.path=='/':
                self.page(f'''<small>LOCAL SETUP · READ-ONLY</small><h1>Connect Reddit for research.</h1><p>Enter the app details here on your own computer. They are never sent to the dashboard or this chat.</p><form action="/configure" method="post"><input type="hidden" name="csrf" value="{csrf}"><label>Reddit app client ID<input required type="text" name="client_id" autocomplete="off" maxlength="150"></label><label>Reddit app client secret<input required type="password" name="client_secret" autocomplete="off" maxlength="300"></label><label><input type="checkbox" name="usage_approved" value="yes"> Reddit has approved API access for my described investment-research use.</label><p><small>Leave unchecked if approval is pending. Creating an app does not itself confirm usage approval. Collection stays off until this is confirmed.</small></p><button>Authorize read-only access on Reddit →</button></form><p><small>Reddit will ask you to sign in and approve the read scope. No posting, voting, messaging or broker permissions are requested. Stored credentials are encrypted for your Windows user.</small></p>''')
            elif parsed.path=='/callback':
                query=urllib.parse.parse_qs(parsed.query)
                if not secrets.compare_digest(query.get('state',[''])[0],session.get('state','missing')) or 'client_id' not in session:
                    self.page('<h1>Authorization could not be matched.</h1><p>Restart setup.</p>',403); return
                if query.get('error') or not query.get('code'):
                    self.page('<h1>Authorization was not completed.</h1><p>No connection has been enabled.</p>',400); return
                try:
                    response=token_request(session['client_id'],session['client_secret'],
                        {'grant_type':'authorization_code','code':query['code'][0],'redirect_uri':CALLBACK})
                    if not response.get('refresh_token'): raise ValueError('Refresh token missing')
                    save_credentials({'client_id':session['client_id'],'client_secret':session['client_secret'],
                        'access_token':response['access_token'],'refresh_token':response['refresh_token'],
                        'scope':'read','expires_at':time.time()+int(response['expires_in']),
                        'usage_approved':session['usage_approved']})
                    approved=session['usage_approved']; session.clear(); session['expires']=0
                    self.page('<h1>Read-only authorization saved.</h1><p>'+('You can now run the research refresh to test Reddit access.' if approved else 'Usage approval is pending. API collection remains disabled.')+'</p><p>Close this page and stop the setup server with Ctrl-C.</p>')
                except Exception as exc:
                    self.page('<h1>Reddit authorization failed.</h1><p>No connection enabled. Error type: '+html.escape(type(exc).__name__)+'</p>',400)
            else: self.page('<h1>Page not found.</h1>',404)

        def do_POST(self):
            if not self.permitted() or self.path!='/configure' or self.headers.get('Origin')!=ORIGIN:
                self.page('<h1>Request refused.</h1>',403); return
            try: size=int(self.headers.get('Content-Length','0'))
            except ValueError: size=0
            if not 0<size<=4096: self.page('<h1>Invalid request.</h1>',400); return
            fields=urllib.parse.parse_qs(self.rfile.read(size).decode())
            if not secrets.compare_digest(fields.get('csrf',[''])[0],csrf): self.page('<h1>Request refused.</h1>',403); return
            client_id=fields.get('client_id',[''])[0].strip(); secret=fields.get('client_secret',[''])[0].strip()
            if not client_id or not secret or ':' in client_id or len(client_id)>150 or len(secret)>300:
                self.page('<h1>Check the app ID and secret.</h1>',400); return
            session.update(client_id=client_id,client_secret=secret,usage_approved=fields.get('usage_approved')==['yes'],state=secrets.token_urlsafe(32))
            url='https://www.reddit.com/api/v1/authorize?'+urllib.parse.urlencode({'client_id':client_id,
                'response_type':'code','state':session['state'],'redirect_uri':CALLBACK,'duration':'permanent','scope':'read'})
            self.send_response(303); self.send_header('Location',url); self.send_header('Cache-Control','no-store'); self.end_headers()

    print('Local Reddit setup: '+ORIGIN)
    print('Open that address yourself. Do not paste secrets into chat. Ctrl-C stops setup.')
    with HTTPServer(('127.0.0.1',8765),Handler) as server:
        try: server.serve_forever()
        except KeyboardInterrupt: pass


if __name__=='__main__': main()
