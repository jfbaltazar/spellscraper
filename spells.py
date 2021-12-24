import requests
import json
import sys
import argparse

baseURL = 'http://5e.tools/data/spells/'
core_books = ['PHB', 'SCC', 'FTD', 'XGE', 'TCE', 'GGR', 'EGW', 'AI']

def load_spells_from_file(filename):
    print('Loading spells from file: {}...'.format(filename))
    with open(filename, 'r') as file:
        data = file.read()
        data_json = json.loads(data)
        spells = data_json['spell']
    print('Done!')
    return spells

def load_spells_from_website(base_url):
    books_json = requests.get(base_url + 'index.json')
    books_json = json.loads(books_json.text)
    spells = []
    print('Loading spells from website: {}...'.format(base_url))
    for book in args.books:
        print('Loading from {}.'.format(book))
        book_spells = requests.get(base_url + books_json[book])
        book_spells = json.loads(book_spells.text)
        spells += book_spells['spell']
    print('Done!')
    return spells

def write_spells_to_file(spells, filename):
    print('Writing spells to file: {}...'.format(filename))
    with open(filename, 'w') as file:
        spells_json = {'spell' : spells}
        file.write(json.dumps(spells_json))
    print('Done!')

def wanted_class(spell, classes):
    spell_classes = spell.get('classes', {}).get('fromClassList', [])
    matches = [cl for cl in spell_classes if cl.get('name','') in classes]
    return len(matches) > 0

def wanted_subclass(spell, subclasses):
    spell_subclasses = spell.get('classes', {}).get('fromSubclass', [])
    matches = [cl for cl in spell_subclasses if cl.get('subclass', {}).get('name', '') in subclasses]
    return len(matches) > 0

def query_by_name(spells):
    def concrete_query(name):
        result = []
        if type(name) == list:
            name = ' '.join(name)
        for spell in spells:
            if name.lower() in spell['name'].lower():
                result.append(spell)
        return result
    return concrete_query

def query_by_level(spells):
    def concrete_query(level):
        result = []
        for spell in spells:
            if spell['level'] == level:
                result.append(spell)
        return result
    return concrete_query

def query_by_school(spells):
    def concrete_query(school):
        result = []
        school = school.lower()
        full_school_names = {'abjuration':'a', 'conjuration':'c', 'divination':'d', 'enchantment':'e', 'evocation':'v', 'illusion':'i', 'necromancy':'n', 'transmutation':'t'}
        school = full_school_names.get(school, school)
        for spell in spells:
            if spell['school'].lower() == school:
                result.append(spell)
        return result
    return concrete_query

def query_by_cast_time(spells):
    def concrete_query(cast_time):
        result = []
        cast_time = cast_time.lower()
        for spell in spells:
            for time in spell.get('time', []):
                if time.get('unit', '') == cast_time:
                    result.append(spell)
                    break
        return result
    return concrete_query

def handle_query(spells, request, spell_list):
    queries = [(request.name, query_by_name),
               (request.level, query_by_level),
               (request.school, query_by_school),
               (request.cast_time, query_by_cast_time)]
    
    if request.from_spells:
        spells = spell_list

    result = []

    for query in queries:
        arg = query[0]
        func = query[1]

        if not arg:
            continue
        
        print("arg:{}".format(arg))
        q_result = func(spells)(arg)

        for spell in q_result:
            print('Added spell \'{}\''.format(spell['name']))
        
        if request.type == 'or':
            result += q_result
            spells = [spell for spell in spells if spell not in q_result]
        elif request.type == 'and':
            result = q_result
            spells = result
    
    if request.sort != '':
        result = sorted(spells, key=lambda x: x[request.sort])

    return result
        

def handle_spell_list(spells, request, spell_list):
    spell_ops = []

def handle_requests(spells):
    runtime_parser = argparse.ArgumentParser()
    runtime_subparsers = runtime_parser.add_subparsers()
    
    query_parser = runtime_subparsers.add_parser('query')
    query_parser.add_argument('-type', choices=['and', 'or'], required=True, dest='type')
    query_parser.add_argument('-n', '--name', nargs='+', type=str, dest='name')
    query_parser.add_argument('-lv', '--level', type=int, dest='level')
    query_parser.add_argument('-sort', type=str, choices=['name', 'level', 'school'], dest='sort', default='')
    query_parser.add_argument('--school', type=str, dest='school')
    query_parser.add_argument('--cast-time', type=str, dest='cast_time')
    query_parser.add_argument('--my-spells', action='store_true', dest='from_spells')
    query_parser.set_defaults(func=handle_query)

    spells_parser = runtime_subparsers.add_parser('spell')
    spells_parser.add_argument('-add', nargs='+', type=str, dest='spells_to_add')
    spells_parser.add_argument('-rem', nargs='+', type=str, dest='spells_to_remove')
    spells_parser.add_argument('-show', action='store_true', dest='show')
    spells_parser.add_argument('--spells-size', type=int, choices=range(1,1000), dest='spells_size')
    spells_parser.set_defaults(func=handle_spell_list)

    exit_parser = runtime_subparsers.add_parser('quit')
    exit_parser.set_defaults(func=lambda x,y,z: None)

    spell_list = []

    inp = ''

    while(inp != 'quit'):
        print('Send me a request, baby!')
        
        inp = input()

        try:
            request = runtime_parser.parse_args(inp.split())
        except Exception:
            print('Oopsie!')
        
        result = request.func(spells, request, spell_list)

        if result:
            print(json.dumps(result, indent=2))

if __name__ == '__main__':
    load_parser = argparse.ArgumentParser(prog=sys.argv[0], description='Retrieve D&D 5e spells.')
    load_parser.add_argument('-b', '--books', nargs='+', default=core_books, type=str, dest='books', metavar='BOOK')
    load_parser.add_argument('-c', '--classes', nargs='+', default=['Cleric'], type=str, dest='classes', metavar='CLASS')
    load_parser.add_argument('-sc', '--subclasses', nargs='+', default=['Grave'], type=str, dest='subclasses', metavar='SUBCLASS')
    load_parser.add_argument('--from', type=str, dest='from_file')
    load_parser.add_argument('--to', type=str, dest='dest_file')

    args = load_parser.parse_args(sys.argv[1:])

    if args.from_file:
        spells = load_spells_from_file(args.from_file)
    else:
        spells = load_spells_from_website(baseURL)

    # filter by class or subclass
    spells = [spell for spell in spells if wanted_class(spell, args.classes) or wanted_subclass(spell, args.subclasses)]

    handle_requests(spells)

    print('Done!')

    if args.dest_file:
        write_spells_to_file(spells, args.dest_file)