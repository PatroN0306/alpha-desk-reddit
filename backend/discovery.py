"""Untrusted social leads. Optional approved Reddit API; never factual evidence."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import urllib.parse
import urllib.request
from backend.universe import BY_SYMBOL


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):
        raise ValueError('Redirect refused; API token must stay at Reddit OAuth origin')


def valid_reddit_url(value):
    parsed=urllib.parse.urlsplit(value)
    return (parsed.scheme=='https' and parsed.hostname in ('www.reddit.com','reddit.com') and
            not parsed.username and not parsed.password and parsed.port in (None,443) and
            bool(re.fullmatch(r'/r/[A-Za-z0-9_]+/comments/[A-Za-z0-9]+/[^?#]*/?',parsed.path)))


def fetch_reddit():
    """Requires independently approved usage and an existing access token in env.

    Does not create accounts, perform OAuth sign-in, post, vote, or retain bodies.
    """
    token=None
    if os.environ.get('REDDIT_USAGE_APPROVED')=='1': token=os.environ.get('REDDIT_ACCESS_TOKEN','')
    if not token:
        from backend.reddit_auth import get_access_token
        token,status=get_access_token()
        if not token: return [],status
    results=[]
    for subreddit in ('stocks','Biotechplays'):
        request=urllib.request.Request(f'https://oauth.reddit.com/r/{subreddit}/new?limit=25&raw_json=1',
                    headers={'Authorization':'Bearer '+token,'User-Agent':'windows:AlphaDeskResearch:0.2'})
        try:
            with urllib.request.build_opener(NoRedirect()).open(request,timeout=15) as response:
                raw=response.read(2_000_001)
            if len(raw)>2_000_000: raise ValueError('API response too large')
            payload=json.loads(raw)
            for child in payload.get('data',{}).get('children',[]):
                post=child.get('data',{})
                title=str(post.get('title',''))[:300]
                symbols=[symbol for symbol,company in BY_SYMBOL.items()
                         if re.search(r'\b'+re.escape(symbol)+r'\b',title) or company['name'].lower() in title.lower()]
                url='https://www.reddit.com'+post.get('permalink','')
                if not symbols or not valid_reddit_url(url): continue
                # Only title metadata/links; no usernames, comments, vote counts or post bodies.
                results.append({'id':str(post.get('id','')),'url':url,'title':title,'symbols':symbols,
                                'published_at':dt.datetime.fromtimestamp(post['created_utc'],dt.timezone.utc).isoformat(),
                                'observed_at':dt.datetime.now(dt.timezone.utc).isoformat(),'origin':'approved_reddit_api'})
        except Exception as exc:
            # Do not print request headers, credentials, API response bodies or sensitive URLs.
            return results,'Reddit API unavailable: '+type(exc).__name__
    return results,'Approved API checked; social claims remain unverified.'


def build_discovery(snapshot,root,fetch_api=False):
    path=root/'config/discovery_leads.json'
    configured=json.loads(path.read_text(encoding='utf-8')) if path.exists() else {'leads':[]}
    leads=list(configured.get('leads',[]))
    api_status='Not connected — continuous Reddit monitoring needs approved API access.'
    if fetch_api:
        current,api_status=fetch_reddit(); leads.extend(current)
    records=[]; seen=set()
    for lead in leads[:100]:
        if not valid_reddit_url(lead.get('url','')) or lead['url'] in seen: continue
        seen.add(lead['url'])
        symbols=[symbol for symbol in lead.get('symbols',[]) if symbol in BY_SYMBOL]
        records.append({'id':hashlib.sha256(lead['url'].encode()).hexdigest()[:20],
                        'url':lead['url'],'title':str(lead.get('title','Social lead'))[:300],
                        'claim':str(lead.get('claim','A social discussion to investigate; no claim verified.'))[:500],
                        'symbols':symbols,'origin':lead.get('origin','manual_link'),
                        'observed_at':lead.get('observed_at'), 'published_at':lead.get('published_at'),
                        'status':'UNVERIFIED_LEAD','fact_verified':False,
                        'blocker':'Find the exact original announcement and verify the claim; popularity is not evidence.',
                        'execution_authorized':False})
    return {'schema_version':1,'kind':'UNTRUSTED_DISCOVERY_LEADS',
            'generated_at':dt.datetime.now(dt.timezone.utc).isoformat(),
            'reddit_api_status':api_status,'leads':records,'execution_authorized':False}
