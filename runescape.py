'''
A slightly memes wrapper for the runescape api, hopefully helps people
best way to contact me with any problems is on discord raatty#3522
'''
import wikia
import requests

BASE_URL = 'http://services.runescape.com/'


class Highscores:
    '''fetches highscores and gives em back as a list of dicts
    6 different types hiscore, hiscore_ironman, hiscore_hardcore_ironman
    'hiscore_oldschool', 'hiscore_oldschool_ironman',
    'hiscore_oldschool_ultimate
    this class takes two arguments rsn and type 'hiscore' is the default
    usage:
    person = runescape.Highscores('raatty', 'hiscore')
    or person = runescape.Highscores('raatty') would give same effect
    person.skills will give a list of skills in game order
    person.total will give you the total
    person.rsn in case you forget who you looked up
    '''
    HIGHSCORES_URL = BASE_URL + 'm={}/index_lite.ws?player={}'
    SKILL_NAMES = {'Total': 0, 'Attack': 1, 'Defence': 7, 'Strength': 4,
                   'Constitution': 2, 'Ranged': 10, 'Prayer': 13,
                   'Magic': 16, 'Cooking': 12, 'Woodcutting': 18,
                   'Fletching': 17, 'Fishing': 9, 'Firemaking': 15,
                   'Crafting': 14, 'Smithing': 6, 'Mining': 3,
                   'Herblore': 8, 'Agility': 5, 'Thieving': 11,
                   'Slayer': 20, 'Farming': 21, 'Runecrafting': 19,
                   'Hunter': 23, 'Construction': 22, 'Summoning': 24,
                   'Dungeoneering': 25, 'Divination': 26, 'Invention': 27}

    def _fetch(self, rsn, type, skill_count: int):
        url = self.HIGHSCORES_URL.format(type, rsn.replace(' ', '+'))
        fetched_scores = requests.get(url).text
        levels = []
        for row in fetched_scores.split('\n'):
            for col in row.split(' '):
                if len(levels) <= skill_count:
                    levels.append(col)
        for index, lvl in enumerate(levels):
            lvl_split = lvl.split(',')
            yield {'level': int(lvl_split[1]), 'xp': int(lvl_split[2]), 'rank': int(lvl_split[0]), 'id': index, 'name': list(self.SKILL_NAMES.keys())[index]}

    def _calculate_combat(self):
        if self.skill_count == 27:
            melee = self.skill('Attack') + self.skill('Strength')
            magic = 2 * self.skill('Magic')
            range = 2 * self.skill('Ranged')
            m = max(melee, magic, range)
            one = 1.3 * m
            two = self.skill('Defence') + self.skill('Constitution')
            three = self.skill('Prayer') // 2
            four = self.skill('Summoning') // 2
            return int(sum([one, two, three, four]) // 4)
        elif self.skill_count == 23:
            first = 0.325 * max(self.skill('Attack') + self.skill('Strength'), 1.5 * self.skill('Magic'), 1.5 * self.skill('Ranged')) 
            second = self.skill('Defence') / 4
            third = self.skill('Constitution') / 4
            fourth = (self.skill('Prayer') // 2) / 4
            return int(sum([first, second, third, fourth]))

    def skill(self, name):
        for s in self.skills:
            if name == s['name']:
                return s['level']

    def __init__(self, rsn: str, type_: str = None):
        self.rsn = rsn
        if type_ is None:
            self.type = 'hiscore'
            self.skill_count = 27
        else:
            if type_ in ['hiscore', 'hiscore_ironman',
                         'hiscore_hardcore_ironman']:
                self.type = type_
                self.skill_count = 27
            elif type_ in ['hiscore_oldschool', 'hiscore_oldschool_ironman',
                           'hiscore_oldschool_ultimate']:
                self.type = type_
                self.skill_count = 23
            else:
                raise AttributeError
        self.skills = list(self._fetch(self.rsn, self.type, self.skill_count))
        self.total = self.skills[0]
        self.skills = sorted(self.skills[1:], key=lambda x: self.SKILL_NAMES[x['name']])
        self.combat_level = self._calculate_combat()


class Player:
    '''
    will look up lots about a player
    '''
    RUNEMETRICS_BASE_URL = 'https://apps.runescape.com/runemetrics/'
    RUNE_METRICS_URL = RUNEMETRICS_BASE_URL + 'profile/profile?user={}&activities=20'
    RUNE_METRICS_QUESTS_URL = RUNEMETRICS_BASE_URL + 'quests?user={}'
    FORUM_PIC_URL = BASE_URL + 'm=avatar-rs/{}/chat.png'

    def _fetch_runemetrics(self):
        metrics = requests.get(self.RUNE_METRICS_URL.format(self._rsn)).json()
        try:
            error = metrics['error']
            if error == 'NO_PROFILE':
                raise LookupError
            elif error == 'PROFILE_PRIVATE':
                self.profile['rsn'] = self._rsn.replace('%20', ' ')
                stats = Highscores(self.profile['rsn'])
                self.profile['overall_total'] = stats.total
                self.profile['combat'] = {'combatlevel': stats.combat_level}
                self.profile['quest_summary'] = {'started': None, 'complete': None, 'notstarted': None}
                self.profile['alog'] = []
                self.profile['stats'] = stats.skills
        except KeyError:
            self.profile['rsn'] = metrics['name']
            self.profile['overall_total'] = {'xp': metrics['totalxp'], 'level': metrics['totalskill'], 'rank': metrics['rank']}
            self.profile['combat'] = {'combatlevel': metrics['combatlevel']}
            self.profile['quest_summary'] = {'started': metrics['questsstarted'], 'complete': metrics['questscomplete'], 'notstarted': metrics['questsnotstarted']}
            self.profile['alog'] = metrics['activities']
            self.profile['stats'] = sorted([dict(i, **{'name': list(Highscores.SKILL_NAMES.keys())[i['id']+1]}) for i in metrics['skillvalues']], key=lambda x: Highscores.SKILL_NAMES[x['name']])

    def _fetch_quests(self):
        self.profile['quest_list'] = requests.get(self.RUNE_METRICS_QUESTS_URL.format(self._rsn)).json()['quests']

    def _fetch_clan_and_title(self):
        pass

    def __init__(self, rsn: str, auto_fetch: bool = False):
        self.profile = {'rsn': None, 'overall_total': None, 'combat': None,
                        'quest_summary': None, 'alog': None, 'stats': None,
                        'quest_list': None, 'clan': None, 'title': None}
        self._rsn = rsn.replace(' ', '%20')
        if auto_fetch:
            self._fetch_runemetrics()
            self._fetch_quests()
            self._fetch_clan_and_title()

    def rsn(self):
        if self.profile['rsn'] is None:
            self._fetch_runemetrics()
        return self.profile['rsn']

    def overall_total(self):
        if self.profile['overall_total'] is None:
            self._fetch_runemetrics()
        return self.profile['overall_total']

    def combat(self):
        if self.profile['combat'] is None:
            self._fetch_runemetrics()
        return self.profile['combat']

    def quest_summary(self):
        if self.profile['quest_summary'] is None:
            self._fetch_runemetrics()
        return self.profile['quest_summary']

    def alog(self):
        if self.profile['alog'] is None:
            self._fetch_runemetrics()
        return self.profile['alog']

    def stats(self):
        if self.profile['stats'] is None:
            self._fetch_runemetrics()
        return self.profile['stats']

    def quest_list(self):
        if self.profile['quest_list'] is None:
            self._fetch_quests()
        return self.profile['quest_list']

    def quest(self, name):
        for q in self.quest_list():
            if q['title'].lower() == name.lower():
                return q

    def clan(self):
        if self.profile['clan'] is None:
            self._fetch_clan_and_title()
        return self.profile['clan']

    def title(self):
        if self.profile['title'] is None:
            self._fetch_clan_and_title()
        return self.profile['title']

    def forum_pic(self):
        return self.FORUM_PIC_URL.format(self._rsn)


class Clan:
    '''
    Gets a list of members in a clan
    usage:
    list(runescape.Clan('empire of elitez'))
    or
    for member in runescape.Clan('empire of elitez')
        #do stuff
    '''
    CLAN_MEM_URL = BASE_URL + 'm=clan-hiscores/members_lite.ws?clanName={}'
    CLAN_MOTIF_URL = BASE_URL + 'm=avatar-rs/{}/clanmotif.png'

    def __init__(self, clan: str):
        self.name = clan
        self.members = requests.get(self.CLAN_MEM_URL.format(clan.replace(' ', '+'))).content.replace(b'\xa0', b' ').decode('ascii').split('\n')[1:-1]
        self.motif = self.CLAN_MOTIF_URL.format(clan.replace(' ', '%20'))

    def __iter__(self):
        for member in self.members:
            member = member.split(',')
            yield {'rsn': member[0], 'rank': member[1], 'clanxp': member[2], 'kills': member[3]}

    def __len__(self):
        return len(self.members)

    def keys(self):
        '''
        will give a list of the key ranks in clan
        usage:
        list(runescape.Clan('empire of elitez').keys())
        or
        for member in runescape.Clan('empire of elitez').keys():
            #do stuff
        '''
        for i in self.members:
            keyRanks = ['Owner', 'Deputy Owner', 'Overseer']
            i = i.split(',')
            if i[1] in keyRanks:
                yield {'rsn': i[0], 'rank': i[1], 'clanxp': i[2], 'kills': i[3]}

    def adminish(self):
        '''
        will give a list of the adminish ranks in clan
        (the ones that kind of look like little badges like admin rank)
        usage:
        list(runescape.Clan('empire of elitez').adminish())
        or
        for member in runescape.Clan('empire of elitez').adminish():
            #do stuff
        '''
        for i in self.members:
            adminishRanks = ['Coordinator', 'Organiser', 'Admin']
            i = i.split(',')
            if i[1] in adminishRanks:
                yield {'rsn': i[0], 'rank': i[1], 'clanxp': i[2], 'kills': i[3]}

    def stars(self):
        '''
        will give a list of the star ranks in clan
        usage:
        list(runescape.Clan('empire of elitez').stars())
        or
        for member in runescape.Clan('empire of elitez').stars():
            #do stuff
        '''
        for i in self.members:
            starRanks = ['General', 'Captain', 'Lieutenant']
            i = i.split(',')
            if i[1] in starRanks:
                yield {'rsn': i[0], 'rank': i[1], 'clanxp': i[2], 'kills': i[3]}

    def bannanas(self):
        '''
        will give a list of the banana ranks in clan
        usage:
        list(runescape.Clan('empire of elitez').bananas())
        or
        for member in runescape.Clan('empire of elitez').bananas():
            #do stuff
        '''
        for i in self.members:
            bananaRanks = ['Sergeant', 'Corporal', 'Recruit']
            i = i.split(',')
            if i[1] in bananaRanks:
                yield {'rsn': i[0], 'rank': i[1], 'clanxp': i[2], 'kills': i[3]}

    def rank(self, rank: str):
        '''
        will give a list of the members with a specific rank in a clan
        usage:
        list(runescape.Clan('empire of elitez').rank('Owner'))
        or
        for member in runescape.Clan('empire of elitez').rank('Owner'):
            #do stuff
        '''
        for i in self.members:
            i = i.split(',')
            if i[1] == rank:
                yield {'rsn': i[0], 'rank': i[1], 'clanxp': i[2], 'kills': i[3]}


class Wikia:
    '''
    a simple wrapper I made to navigate the wikia
    '''
    def __init__(self, wiki: str):
        self.wiki = wiki

    def page(self, pageName: str):
        '''returns an instance of a wikia page'''
        return wikia.page(self.wiki, pageName)

    def search(self, searchTerm: str):
        '''just returns a list of search results from the wikia'''
        return wikia.search(self.wiki, searchTerm)

    def isearch(self, searchTerm: str):
        '''returns a generator that iterates though the search results pages'''
        for i in wikia.search(self.wiki, searchTerm):
            yield wikia.page(self.wiki, i)


osrsWikia = Wikia('2007runescape')
rs3Wikia = Wikia('runescape')


class Beasts:
    '''
    a bunch of methods for getting stats and seaching for monsters
    '''
    @staticmethod
    def by_id(id: int):
        '''returns stats and info about a beast by id'''
        BEAST_ID_URL = BASE_URL + 'm=itemdb_rs/bestiary/beastData.json?beastid={}'
        return requests.get(BEAST_ID_URL.format(id)).json()

    @staticmethod
    def search(query: str):
        '''
        searches the beast database for a name and returns a list seperate with +
        '''
        BEAST_SEARCH_URL = BASE_URL + 'm=itemdb_rs/bestiary/beastSearch.json?term={}'
        return requests.get(BEAST_SEARCH_URL.format(query)).json()

    @staticmethod
    def by_letter(letter: str):
        '''
        returns a list of beasts starting with a letter
        '''
        BEAST_LETTER_URL = BASE_URL + 'm=itemdb_rs/bestiary/bestiaryNames.json?letter={}'
        return requests.get(BEAST_LETTER_URL.format(letter.upper())).json()

    @staticmethod
    def area_names():
        '''returns a list of area names'''
        AREA_URL = BASE_URL + 'm=itemdb_rs/bestiary/areaNames.json'
        return requests.get(AREA_URL).json()

    @staticmethod
    def by_area(area: str):
        '''
        returns a list of beasts in a specific area
        see runescape.Beasts.area_names() for the list
        '''
        BY_AREA_URL = BASE_URL + 'm=itemdb_rs/bestiary/areaBeasts.json?identifier={}'
        return requests.get(BY_AREA_URL.format(area.replace(' ', '+'))).json()

    @staticmethod
    def category_names():
        '''
        returns a list of slayer categorys
        '''
        CATEGORY_URL = BASE_URL + 'm=itemdb_rs/bestiary/slayerCatNames.json'
        return requests.get(CATEGORY_URL).json()

    @staticmethod
    def by_category(cat):
        '''
        returns a list of monsters of a given slayer category
        input a category id as an int or a str of the category name
        searching by string will take longer tho 
        see runescape.Beasts.category_names() for categorys
        '''
        BY_CATEGORY_URL = BASE_URL + 'm=itemdb_rs/bestiary/slayerBeasts.json?identifier={}'
        if type(cat) == int:
            return requests.get(BY_CATEGORY_URL.format(cat)).json()
        elif type(cat) == str:
            cat_list = Beasts.category_names()
            cat = cat_list[cat]
            return requests.get(BY_CATEGORY_URL.format(cat)).json()

    @staticmethod
    def weakness_names():
        '''
        returns a list of weaknesses
        '''
        WEAKNESS_URL = BASE_URL + 'm=itemdb_rs/bestiary/weaknessNames.json'
        return requests.get(WEAKNESS_URL).json()

    @staticmethod
    def by_weakness(weakness):
        '''
        returns a list of beasts with a given weakness, input a weakness
        id or a weakness name searching by name will take longer tho
        see runescape.Beasts.weakness_names() for weaknesses
        '''
        BY_WEAKNESS_URL = BASE_URL + 'm=itemdb_rs/bestiary/weaknessBeasts.json?identifier={}'
        if type(weakness) == int:
            return requests.get(BY_WEAKNESS_URL.format(weakness)).json()
        elif type(weakness) == str:
            weakness_list = Beasts.weakness_names()
            weakness = weakness_list[weakness]
            return requests.get(BY_WEAKNESS_URL.format(weakness)).json()

    @staticmethod
    def by_level(lower_: int, upper_: int):
        '''
        returns a list of beasts within a given level range, takes
        two arguments both ints first argument is the lowest level
        you want to see and the second is the highest level
        you can use 1 for the first and a high number like 10000
        for the second to get a list of all the beasts
        '''
        BY_LEVEL_URL = BASE_URL + 'm=itemdb_rs/bestiary/levelGroup.json?identifier={}-{}'
        return requests.get(BY_LEVEL_URL.format(lower_, upper_)).json()

class GrandExchange:
    pass
