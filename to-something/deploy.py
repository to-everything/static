import os
import time
import pandas as pd
import CloudFlare

#cloudflare
cname_point = 'na-west1.surge.sh'
cf_token = 'TwYvSTCT5WserTgatMcg_mWubQn4ZmEV-FBBPOMR'


folders_to_deploy = os.listdir('www')



catalog = pd.DataFrame(columns=['website', 'status'])
catalog['website'] = folders_to_deploy
catalog['status'] = ''
catalog.set_index('website', inplace=True)

try:
    data = pd.read_pickle('deployed.pkl')
    catalog.update(data)
except:
    pass


i = 0
while len(catalog.loc[catalog.status == ''].index) > 0:
    
    site = catalog.loc[catalog.status == ''].index.values[0]
    stream = os.popen('surge www/%s %s' % (site, site))
    output = stream.read()
    stream.close()
    
    if 'Published' in output:
        catalog.loc[catalog.index == site, 'status'] = 'deployed'
        print(' %s deployed' % site)
    elif 'Try again in' in output:
        print(output)
        catalog.to_pickle('deployed.pkl')
        number, mh = output.split('.')[-2].replace(' Try again in ','').split(' ')
        number = int(number)+1

        if mh == 'minutes':
            print('sleep %s minutes' % number)
            time.sleep(number*60)
        elif mh == 'minute':
            print('sleep %s minute' % number)
            time.sleep(number*60)
        elif mh == 'hours':
            print('sleep %s hours' % number)
            time.sleep(number*60*60)
        elif mh == 'hour':
            print('sleep %s hour' % number)
            time.sleep(number*60*60)
        else:
            print(' unidentified delay: %s %s' % (number, mh))
            break
    else:
        print(' unidentified response')
        print(output)
        catalog.to_pickle('deployed.pkl')
        break
    if i >= 15:
        catalog.to_pickle('deployed.pkl')
        i = 0
    else:
        i += 1
print('nothing to deploy')
catalog.to_pickle('deployed.pkl')

exit()
# create DNS records
dns_table = pd.DataFrame(columns=[
    'id',
    'zone_id',
    'zone_name',
    'name',
    'type',
    'content',
    'proxiable',
    'proxied',
    'ttl',
    'locked',
    'meta',
    'created_on',
    'modified_on',
    'priority'
])


cf = CloudFlare.CloudFlare(token=cf_token)
zones = cf.zones.get(params={'per_page':500})
for zone in zones:
    zone_name = zone['name']
    zone_id = zone['id']
    dns_records = cf.zones.dns_records.get(zone_id)

    dns_table = dns_table.append(pd.DataFrame.from_dict(dns_records))

dns_table = dns_table[dns_table.type == 'CNAME']

catalog = pd.read_pickle('deployed.pkl')

domains = list(catalog[catalog.status == 'deployed'].index)

for domain in domains:
    if dns_table.loc[dns_table.name == domain, 'name'].count() == 0:
        try:
            zone_id = dns_table.loc[dns_table.zone_name == '.'.join(domain.split('.')[1:]), 'zone_id'].values[0]
            record_to_add = {'name':domain, 'type':'CNAME', 'content':cname_point, 'proxied':True}
        except:
            continue
        try:
            cf.zones.dns_records.post(zone_id, data=record_to_add)
            print('%s DNS set' % domain)
        except:
            print('%s already exist' % domain)
        time.sleep(0.26)