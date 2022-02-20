import time
import requests
import json
from colorama import Fore, init as colorama_init
from functools import lru_cache
colorama_init(autoreset=True)
from datetime import datetime

ANILIST_USER_NAME = None
if ANILIST_USER_NAME is None: ANILIST_USER_NAME = input("Enter your AniList username: ")

print('\n\n\n')
print(' '*5 + Fore.MAGENTA + '@' + Fore.CYAN + ANILIST_USER_NAME, '\n')

def get_user_list(user, status):
    query = '''
query ($page: Int, $userName: String, $Status: MediaListStatus) {
  Page(page: $page) {
    pageInfo {
      lastPage
      hasNextPage
    }
    mediaList(userName: $userName, status: $Status) {
      media {
        id
        relations {
          edges {
            relationType
            node {
              id
              format
            }
          }
        }
      }
    }
  }
}
    '''
    print(Fore.CYAN + 'FETCHING ANIME LIST' + Fore.WHITE + '  -  ' + Fore.GREEN + '1/9 [01] ' + Fore.WHITE + '(' + Fore.CYAN + status + Fore.WHITE + ')' )
    response = requests.post(
        'https://graphql.anilist.co',
        json={
            'query': query,
            'variables': {
                'userName': user,
                'page': 1,
                'Status': status,
                }
            }
    ).json()
    for i in range(2, response['data']['Page']['pageInfo']['lastPage'] + 1):
        print(Fore.CYAN + 'FETCHING ANIME LIST' + Fore.WHITE + '  -  ' + Fore.GREEN + '1/9 [' + ('0' if i < 10 else '') + str(i) + '] ' + Fore.WHITE + '(' + Fore.CYAN + status + Fore.WHITE + ')' )
        ani_res = requests.post(
            'https://graphql.anilist.co',
            json={
                'query': query,
                'variables': {
                    'userName': user,
                    'page': i,
                    'Status': status,
                }
            }
        ).json()
        response['data']['Page']['mediaList'].extend(
            ani_res['data']['Page']['mediaList']
        )
        if not ani_res['data']['Page']['pageInfo']['hasNextPage']:
            break
        
    response = response['data']['Page']['mediaList']
    res = {}
    
    for i in response:
        i = i['media']
        r = []
        for n in i['relations']['edges']:
            if n['relationType'] in ['ADAPTATION', 'PREQUEL', 'SEQUEL', 'PARENT', 'SIDE_STORY', 'ALTERNATIVE', 'SPIN_OFF'] and n['node']['format'] in ['TV', 'TV_SHORT', 'MOVIE', 'SPECIAL', 'OVA', 'ONA', 'MUSIC']:
                r.append(str(n['node']['id']))
        res[str(i['id'])] = r
        
    return res

@lru_cache(maxsize = 1000)
def get_relations(id):
    query = '''
query ($id: Int) {
  Media(id: $id, type: ANIME) {
    relations {
      edges {
        relationType
        node {
          id
          format
        }
      }
    }
  }
}
'''
    response = requests.post(
        'https://graphql.anilist.co',
        json={
            'query': query,
            'variables': {
                'id': id,
                }
            }
    ).json()
    
    return [str(i['node']['id']) for i in response['data']['Media']['relations']['edges'] if i['relationType'] in ['ADAPTATION', 'PREQUEL', 'SEQUEL', 'PARENT', 'SIDE_STORY', 'ALTERNATIVE', 'SPIN_OFF'] and i['node']['format'] in ['TV', 'TV_SHORT', 'MOVIE', 'SPECIAL', 'OVA', 'ONA', 'MUSIC']]
    

ANIME_COMPLETED = get_user_list(ANILIST_USER_NAME, 'COMPLETED')

def load(): 
    i = -1
    l = time.time()
    animation = [
        '...                ',
        ' ...               ',
        '  ...              ',
        '   ...             ',
        '    ...            ',
        '     ...           ',
        '      ...          ',
        '       ...         ',
        '        ...        ',
        '         ...       ',
        '          ...      ',
        '           ...     ',
        '            ...    ',
        '             ...   ',
        '              ...  ',
        '               ... ',
        '                ...',
        '.                ..',
        '..                .',
    ]
    animation = [Fore.WHITE + '[' + Fore.GREEN + i.replace('.', '=') + Fore.WHITE + ']' for i in animation]
    while True:
        if time.time() - l > 0.2:
            i = i + 1
            t = animation[i]
            yield t + ' '*(20 - len(t))
            l = time.time()
        if i > len(animation) - 2: i = -1
gen = load()
tree_num = 0
def get_tree(id, recur = [], extra = [], extra_for=None):
    global tree_num
    print(Fore.WHITE + 'PROCESSING RELATIONS : ' + next(gen) + Fore.WHITE + '   [' + Fore.CYAN + '0' * (5 - len(str(tree_num))) + str(tree_num) + Fore.WHITE + ']',end='\r')
    tree_num = tree_num + 1
    out = ANIME_COMPLETED[id if extra_for is None else extra_for]
    out.extend(extra)
    ANIME_COMPLETED[id if extra_for is None else extra_for] = list(set(ANIME_COMPLETED[id if extra_for is None else extra_for]))
    recur.append(id)
    for i in ANIME_COMPLETED[id if extra_for is None else extra_for]:
        if (i in ANIME_COMPLETED) and (i not in recur):
            out.extend(get_tree(i, recur))
        elif (i not in ANIME_COMPLETED) and (i not in recur):
            out.extend(get_tree(i, recur, get_relations(i), id if extra_for is None else extra_for))
    return out

for i in ANIME_COMPLETED: get_tree(i)

print()

ANIME_DROPPED = get_user_list(ANILIST_USER_NAME, 'DROPPED')
ANIME_PLANNING = get_user_list(ANILIST_USER_NAME, 'PLANNING')
ANIME_CURRENT = get_user_list(ANILIST_USER_NAME, 'CURRENT')
ANIME_PAUSED = get_user_list(ANILIST_USER_NAME, 'PAUSED')
ANIME_REPEATING = get_user_list(ANILIST_USER_NAME, 'REPEATING')

REPEATING = list(set([i for i in ANIME_REPEATING]))
PAUSED = list(set([i for i in ANIME_PAUSED]))
CURRENT = list(set([i for i in ANIME_CURRENT]))
WATCHED = list(set([i for i in ANIME_COMPLETED]))
DROPPED = list(set([i for i in ANIME_DROPPED]))
PLANNING = list(set([i for i in ANIME_PLANNING]))
RELATIONS = list(set(sum([ANIME_COMPLETED[i] for i in ANIME_COMPLETED], [])))

for i in WATCHED + DROPPED + REPEATING + PAUSED + CURRENT:
    if i in RELATIONS:
        RELATIONS.remove(i)

NEW = [i for i in RELATIONS]    
for i in PLANNING:
    if i in NEW:
        NEW.remove(i)
        
for i in RELATIONS:
    if i in PLANNING:
        PLANNING.remove(i)
        
RELATIONS = list(map(int, RELATIONS))

def get_card(id):pass

if len(NEW) != 0: 
    f = open(str(datetime.today().strftime('sequels_%Y-%m-%d_%H-%M-%S.html')), 'w')
    HTML = '\n'.join(['<h1>' + 'Your Sequels Which Are Not In Your List' + '</h1>'] + [f'<a href="https://anilist.co/anime/{i}/">anilist.co/anime/{i}</a><br>' for i in NEW])
    f.write(HTML)
    print('DONE: FOUND', len(NEW), 'ADDITIONS TO YOUR LIST')
else:
    print('NO NEW ANIME DETECTED!!!')
input('PRESS [ENTER] TO EXIT')