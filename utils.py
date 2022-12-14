import json 
import os
from pymongo import MongoClient

def push_entry(tool:dict, collection:'pymongo.collection.Collection', log:dict):
    '''Push tool to collection.

    tool: dictionary. Must have at least an '@id' key.
    collection: collection where the tool will be pushed.
    log : {'errors':[], 'n_ok':0, 'n_err':0, 'n_total':len(insts)}
    '''
    # Push to collection
    # date objects cause trouble and are prescindable
    if 'about' in tool.keys():
            tool['about'].pop('date', None)
    try:
        updateResult = collection.update_many({'@id':tool['@id']}, { '$set': tool }, upsert=True)
    except Exception as e:
        log['errors'].append({'file':tool,'error':e})
        return(log)
    else:
        log['n_ok'] += 1
    finally:
        return(log)


def save_entry(tool, output_file, log):
    '''Save tool to file.

    tool: dictionary. Must have at least an '@id' key.
    output_file: file where the tool will be saved.
    log : {'errors':[], 'n_ok':0, 'n_err':0, 'n_total':len(insts)}
    '''
    # Push to file
    # date objects cause trouble and are prescindable

    if 'about' in tool.keys():
            tool['about'].pop('date', None)
    try:
        if os.path.isfile(output_file) is False:
            with open(output_file, 'w') as f:
                json.dump([tool], f)
        else:
            with open(output_file, 'r+') as outfile:
                print('Saving to file: ' + output_file)
                data = json.load(outfile)
                data.append(tool)
                # Sets file's current position at offset.
                outfile.seek(0)
                json.dump(data, outfile)

    except Exception as e:
        log['errors'].append({'file':tool['name'],'error':e})
        raise
        # return(log)

    else:
        log['n_ok'] += 1
    finally:
        return(log)

def connect_db():
    '''Connect to MongoDB and return the database and collection objects.

    '''
    ALAMBIQUE = os.getenv('ALAMBIQUE', 'alambique')
    HOST = os.getenv('HOST', 'localhost')
    PORT = os.getenv('PORT', 27017)
    DB = os.getenv('DB', 'observatory')
    
    client = MongoClient(HOST, int(PORT))
    alambique = client[DB][ALAMBIQUE]

    return alambique