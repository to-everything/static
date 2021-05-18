from flask import Flask
from graphqlclient import GraphQLClient
import json
from flask import render_template
from flask_frozen import Freezer
from utils import *

db_url = "https://api-us-east-1.graphcms.com/v2/ckkqtwg6bk28401z95sgaau7i/master"
client = GraphQLClient(db_url)

app = Flask(__name__)

app.config['FREEZER_DESTINATION'] = 'www'

freezer = Freezer(app)

domains_to_run = []
domains_to_run.append('to-bigquery.com')
domains_to_run.append('to-datastudio.com')
domains_to_run.append('to-snowflake.com')
#domains_to_run.append('to-marketo.com')
#domains_to_run.append('to-sendgrid.com')
#domains_to_run.append('to-mailchimp.com')
#domains_to_run.append('to-salesforce.com')
#domains_to_run.append('to-hubspot.com')
#domains_to_run.append('to-google-sheets.com')
#domains_to_run.append('to-postgres.com')
#domains_to_run.append('to-redshift.com')
#domains_to_run.append('to-oracle.com')
#domains_to_run.append('to-tableau.com')
#domains_to_run.append('to-databricks.com')
domains_to_run.append('to-powerbi.com')
#domains_to_run.append('to-mongodb.com')



all_integrations = get_all_combinations()

all_connectors = get_all_connectors()

all_destinations = get_all_destinations(domains_to_run)


#@app.route('/')
#def main():
#    return True

@app.route('/<string:domain>.com/')
def domain_page(domain):
    domain = domain+'.com'

    # TODO: remove self from destinations
    destination = all_destinations.loc[all_destinations.domain == domain].to_dict('records')[0]

    available_sources = all_integrations.loc[all_integrations.destination==destination['slug'], 'source'].to_list()

    available_sources = all_connectors.loc[all_connectors.slug.isin(available_sources), :].to_dict('records')

    return(render_template(
        'main.html',
        domain = domain,
        current_url = domain,

        sources = available_sources,
        destination = destination,

        title = 'Find the best software to integration your data - ',
        description = 'description of a page',
        footer_text = ''
    ))

@freezer.register_generator
def domain_page():
    for x in domains_to_run:
        yield {'domain': x.replace('.com','')}

@app.route('/<string:subdomain>.<string:domain>.com/')
def subdomain_page(domain, subdomain):
    domain = domain+'.com'

    destination = all_destinations.loc[all_destinations.domain == domain].to_dict('records')[0]
    destination['logo'] = all_connectors.loc[all_connectors.slug == destination['slug'], 'logo'].values[0]
    source = all_connectors.loc[all_connectors.slug == subdomain].to_dict('records')[0]

    # find all integrationPlatforms
    integration_platforms = json.loads(client.execute('''
    {
    integrationPlatforms(where: {connectors_some: {slug: "%s"}, AND: {connectors_some: {slug: "%s"}}}, orderBy: priority_ASC) {
        name
        logo {
        url(transformation: {image: {resize: {width: 170}}})
        }
        website
        pricingUrl
        g2CrowdRating
        shortbio
    }
    }
    ''' % (subdomain, destination['slug'])))['data']['integrationPlatforms']

    # find all similar integrations to destination
    available_sources = all_integrations.loc[all_integrations.destination == 'bigquery', 'source'].to_list()

    available_sources.remove(source['slug'])

    available_sources = all_connectors.loc[all_connectors.slug.isin(available_sources)].to_dict('records')
    ## TODO: remove the current one

    # find all similar integrations to source
    relevant_integrations = all_integrations.loc[all_integrations.destination.isin(all_destinations.slug.to_list())]
    relevant_integrations = relevant_integrations.loc[relevant_integrations.source.isin(['google-analytics'])]
    available_destinations = all_connectors.loc[
        all_connectors.slug.isin(relevant_integrations.destination.to_list())
    ]
    available_destinations['domain'] = available_destinations.apply(
        lambda x: all_destinations.loc[all_destinations.slug == x['slug'], 'domain'].values[0],
        axis=1
    )
    available_destinations = available_destinations.to_dict('records')


    # format subdomain.html

    return(render_template(
        'subdomain.html',
        current_url = "%s.%s/" % (subdomain, domain),
        domain = domain,

        destination = destination,
        source = source,

        integration_platforms = integration_platforms,

        available_sources = available_sources,
        available_destinations = available_destinations,

        title = 'Find the best software to integration your data - ',
        description = 'description of a page',
        footer_text = ''
    ))

@freezer.register_generator
def subdomain_page():
    for x in domains_to_run:
        dest = all_destinations.loc[all_destinations.domain == x,'slug'].values[0]
        for y in all_integrations.loc[all_integrations.destination == dest,'source'].to_list():
            yield {'domain': x.replace('.com',''), 'subdomain': y}

if __name__ == '__main__':
    freezer.freeze()