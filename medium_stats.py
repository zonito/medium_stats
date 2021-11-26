import json
import os
import ssl
import urllib3

_HTTP = urllib3.PoolManager(cert_reqs=ssl.CERT_REQUIRED)


def get_medium_stats():
    response = _HTTP.request(
        'GET',
        'https://medium.com/me/stats',
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


def gotify(title, md_body):
    try:
        _HTTP.request(
            'POST',
            os.environ.get('GOTIFY_URL'),
            body=json.dumps({
                'title': title,
                'message': '\n'.join(md_body),
                'priority': 10,
                'extras': {
                    'client::display': {
                        'contentType': 'text/markdown'
                    }
                }
            }),
            headers={
                'Content-Type': 'application/json'
            }
        )
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
        msg = f'| {stat["reads"]} Reads / {stat["views"]} Views'
        if stat['upvotes']:
            msg += f' with {stat["upvotes"]} Fans'
            if stat['claps']:
                msg += f' and {stat["claps"]} Claps'
        message.append(f'**{stat["title"]}**:\n{msg}')

    print('\n'.join(message))

    total_views = sum([obj['views'] for obj in stats])
    total_reads = sum([obj['reads'] for obj in stats])
    return gotify(f'Medium: {total_views} V, {total_reads} R', message)


if __name__ == '__main__':
    send_daily_stats()
