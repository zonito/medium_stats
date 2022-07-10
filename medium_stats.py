import json
import os
import ssl
import urllib
import urllib3

_HTTP = urllib3.PoolManager(cert_reqs=ssl.CERT_REQUIRED)


def get_medium_stats():
    response = _HTTP.request(
        'GET',
        'https://medium.com/me/stats?limit=100',
        headers={
            'content-type': 'application/json',
            'accept': 'application/json',
            'cookie': f'uid={os.environ.get("MEDIUM_UID")}; sid={os.environ.get("MEDIUM_SID")}'
        }
    )

    if response.status != 200:
        raise Exception(f'HTTP status code: {response.status}')

    return json.loads(
        response.data.decode('utf-8')[response.data.decode('utf-8').find('{'):]
    )


def pushover(title, md_body):
    print(title)
    print(os.environ.get('API_TOKEN'))
    print(os.environ.get("USER_KEY"))
    try:
        payload = urllib.parse.urlencode({
            'title': title,
            'message': '\n'.join(md_body),
            'token': os.environ.get('API_TOKEN'),
            'user': os.environ.get('USER_KEY')
        })
        response = _HTTP.request(
            'POST',
            os.environ.get('GOTIFY_URL'),
            body=payload,
            headers={
                'Content-Type': 'application/x-www-form-urlencoded'
            }
        )
        print(response.status, response.data)
    except urllib3.exceptions.MaxRetryError as error:
        print(error)


def send_daily_stats():
    medium_stats = get_medium_stats()
    stats = sorted(medium_stats.get('payload', {}).get('value', []), key=lambda x: x['views'])
    stats.reverse()

    message = []
    for stat in stats[:5]:
        if not stat['views']:
            continue
        msg = f'{stat["reads"]} Reads / {stat["views"]} Views'
        if stat['upvotes']:
            msg += f' with {stat["upvotes"]} Fans'
            if stat['claps']:
                msg += f' and {stat["claps"]} Claps'
        message.append(f'*{stat["title"]}*:\n{msg}')

    total_views = sum([obj['views'] for obj in stats])
    total_reads = sum([obj['reads'] for obj in stats])
    return pushover(f'Medium: {total_views} V, {total_reads} R', message)


if __name__ == '__main__':
    send_daily_stats()
