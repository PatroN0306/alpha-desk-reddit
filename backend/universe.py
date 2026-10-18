"""Explicit research universe; inclusion is not an investment recommendation."""
COMPANIES = [
    {'symbol': 'AAPL', 'name': 'Apple', 'sector': 'Technology',
     'feed': 'https://www.apple.com/newsroom/rss-feed.rss', 'source': 'Apple Newsroom',
     'allowed_hosts': ['www.apple.com'], 'article_paths': ['/newsroom/']},
    {'symbol': 'MSFT', 'name': 'Microsoft', 'sector': 'AI & cloud',
     'feed': 'https://news.microsoft.com/source/feed/', 'source': 'Microsoft Source',
     'allowed_hosts': ['news.microsoft.com'], 'article_paths': ['/source/', '/microsoft-signal/']},
    {'symbol': 'NVDA', 'name': 'NVIDIA', 'sector': 'AI & chips',
     'feed': 'https://nvidianews.nvidia.com/releases.xml', 'source': 'NVIDIA Newsroom',
     'allowed_hosts': ['nvidianews.nvidia.com'], 'article_paths': ['/releases/', '/news/']},
    {'symbol': 'REGN', 'name': 'Regeneron', 'sector': 'Biotech',
     'feed': 'https://investor.regeneron.com/rss/news-releases.xml', 'source': 'Regeneron Investor Relations',
     'allowed_hosts': ['investor.regeneron.com'], 'article_paths': ['/news-releases/news-release-details/']},
]
BY_SYMBOL = {company['symbol']: company for company in COMPANIES}
OFFICIAL_HOSTS = {host for company in COMPANIES for host in company['allowed_hosts']} | {
    'www.microsoft.com', 'www.federalreserve.gov', 'www.bls.gov',
    'clinicaltrials.gov', 'www.fda.gov', 'www.ema.europa.eu',
}
