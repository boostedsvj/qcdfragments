import minimal_cernsso as cernsso
import pprint, logging, re

def setup_logger():
    fmt = logging.Formatter(
        fmt="\033[33m[qcdgetter|%(levelname)8s|%(asctime)s|%(module)s]:\033[0m %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler = logging.StreamHandler()
    handler.setFormatter(fmt)
    logger = logging.getLogger("qcdgetter")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    return logger

logger = setup_logger()


def get_session():
    return cernsso.session_from_cookies_file(
        '/Users/klijnsma/.globus/for_cern_sso/myCert.pem',
        '/Users/klijnsma/.globus/for_cern_sso/myCert.key'
        )

def get_driver_cmd(dataset, s=None):
    if s is None: s = get_session()

    r = s.get(
        'https://cms-pdmv.cern.ch/mcm/search?'
        'db_name=requests'
        '&produce={}'
        '&page=0'
        '&get_raw'
        .format(dataset),
        verify=False
        )
    r.raise_for_status()
    d = r.json()

    logger.debug('Retrieved: %s', d['rows'][0]['doc'])

    moc = d['rows'][0]['doc']['member_of_chain'][0]
    logger.info('Retrieved moc: %s', moc)

    r = s.get(
        'https://cms-pdmv.cern.ch/mcm/search?'
        'db_name=chained_requests'
        '&prepid={}'
        '&page=0'
        '&get_raw'
        .format(moc),
        verify=False
        )
    r.raise_for_status()
    d = r.json()

    chain = d['rows'][0]['doc']['chain'][0]
    logger.info('Retrieved chain: %s', chain)

    r = s.get(
        'https://cms-pdmv.cern.ch/mcm/public/restapi/requests/get_setup/{}'.format(chain),
        verify=False
        )
    r.raise_for_status()
    setup_sh = r.text
    logger.info('Retrieved:\n%s ... %s', setup_sh[:20], setup_sh[-20:])

    match = re.search(r'^cmsDriver\.py.*?$', setup_sh, flags=re.MULTILINE)
    if not match:
        raise Exception('Could not find a cmsDriver command!')
    driver_cmd = match.group()

    # Fix the driver command to yield GEN instead of SIM
    driver_cmd = driver_cmd.replace('--step GEN,SIM', '--step GEN')
    driver_cmd = driver_cmd.replace(' || exit $? ;', '')
    driver_cmd = driver_cmd.replace('$EVENTS', '100')
    logger.info('Retrieved driver cmd: %s', driver_cmd)

    match = re.search(r'^curl.*?$', setup_sh, flags=re.MULTILINE)
    if not match:
        raise Exception('Could not find a curl command!')
    curl_cmd = match.group()
    logger.info('Retrieved curl cmd: %s', curl_cmd)

    return curl_cmd, driver_cmd


def main():
    s = get_session()

    datasets = [
        '/QCD_Pt_170to300_TuneCP5_13TeV_pythia8/RunIIAutumn18MiniAOD-102X_upgrade2018_realistic_v15-v1/MINIAODSIM',
        '/QCD_Pt_300to470_TuneCP5_13TeV_pythia8/RunIIAutumn18MiniAOD-102X_upgrade2018_realistic_v15-v1/MINIAODSIM',
        '/QCD_Pt_470to600_TuneCP5_13TeV_pythia8/RunIIAutumn18MiniAOD-102X_upgrade2018_realistic_v15-v1/MINIAODSIM',
        '/QCD_Pt_600to800_TuneCP5_13TeV_pythia8/RunIIAutumn18MiniAOD-102X_upgrade2018_realistic_v15-v1/MINIAODSIM',
        '/QCD_Pt_800to1000_TuneCP5_13TeV_pythia8/RunIIAutumn18MiniAOD-102X_upgrade2018_realistic_v15_ext1-v2/MINIAODSIM',
        '/QCD_Pt_1000to1400_TuneCP5_13TeV_pythia8/RunIIAutumn18MiniAOD-102X_upgrade2018_realistic_v15-v1/MINIAODSIM',
        '/QCD_Pt_1400to1800_TuneCP5_13TeV_pythia8/RunIIAutumn18MiniAOD-102X_upgrade2018_realistic_v15-v1/MINIAODSIM',
        '/QCD_Pt_1800to2400_TuneCP5_13TeV_pythia8/RunIIAutumn18MiniAOD-102X_upgrade2018_realistic_v15-v1/MINIAODSIM',
        '/QCD_Pt_2400to3200_TuneCP5_13TeV_pythia8/RunIIAutumn18MiniAOD-102X_upgrade2018_realistic_v15-v1/MINIAODSIM',
        '/QCD_Pt_3200toInf_TuneCP5_13TeV_pythia8/RunIIAutumn18MiniAOD-102X_upgrade2018_realistic_v15-v1/MINIAODSIM',
        ]

    curls = []
    drivers = []

    for dataset in datasets:
        curl_cmd, driver_cmd = get_driver_cmd(dataset)
        curls.append(curl_cmd)
        drivers.append(driver_cmd)

    sh_lines = []

    for dataset, curl in zip(datasets, curls):
        sh_lines.extend(['# ' + dataset, curl, ''])

    sh_lines.extend(['scram b', ''])

    for dataset, driver in zip(datasets, drivers):
        sh_lines.extend(['# ' + dataset, driver, ''])

    with open('download_fragments.sh', 'w') as f:
        f.write('\n'.join(sh_lines))


if __name__ == '__main__':
    main()