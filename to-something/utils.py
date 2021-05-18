import itertools
import pandas as pd
from graphqlclient import GraphQLClient
import json

db_url = "https://api-us-east-1.graphcms.com/v2/ckkqtwg6bk28401z95sgaau7i/master"
client = GraphQLClient(db_url)

def get_all_combinations():
    integrationPlatforms = pd.DataFrame.from_dict(json.loads(client.execute('''
    {
    integrationPlatforms(orderBy: priority_ASC) {
        name
    }
    }
    '''))['data']['integrationPlatforms'])['name'].to_list()
    all_combinations = pd.DataFrame(columns = ['source', 'destination'])
    for platform in integrationPlatforms:
        data = pd.DataFrame.from_dict(json.loads(client.execute('''
        {
        connectors(where: {integrationPlatforms_some: {name: "%s"}}) {
            slug
            type
        }
        }
        ''' % platform))['data']['connectors'])
        if len(data) == 0:
            continue
        combinations = pd.DataFrame(
            list(
                itertools.product(
                    data.loc[data.type=='source','slug'],
                    data.loc[data.type=='destination','slug']
                )
            ),
            columns = ['source', 'destination']
        )
        all_combinations = all_combinations.append(combinations)
    all_combinations.drop_duplicates(subset=['source', 'destination'], inplace=True)
    return all_combinations

def get_all_connectors():
    all_connectors = json.loads(client.execute('''
    {
    connectors(first: 10000) {
        slug
        logo {
        url(transformation: {image: {resize: {width: 300}}})
        }
        name
    }
    }
    '''))['data']['connectors']
    all_connectors = pd.DataFrame.from_dict(all_connectors)
    all_connectors['logo'] = pd.DataFrame.from_dict(all_connectors['logo'].to_list())
    return all_connectors

def get_all_destinations(domains):
    domains_str = ("%s" % domains).replace('\'', '"')
    destinations = json.loads(client.execute('''
    {
    minisites(where: {domain_in: %s}) {
        domain
        destination_connector {
        name
        slug
        }
    }
    }
    ''' % domains_str))['data']['minisites']
    destinations = pd.DataFrame.from_dict(destinations)
    # pd.concat([df.drop(['b'], axis=1), df['b'].apply(pd.Series)], axis=1)
    destinations = pd.concat(
        [
            destinations.drop(['destination_connector'], axis=1),
            destinations['destination_connector'].apply(pd.Series)
        ],
        axis=1
    )
    return destinations