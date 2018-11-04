#! /usr/bin/env python3

__author__ = 'Dejan Spasic <spasic.dejan@yahoo.de>'
__doc__ = """Updating Tags for Existing CloudFormation Stacks

This script is iterating through all root stacks and updates the tags.

It uses the UsePreviousTemplate and UsePreviousValue for each parameter to 
achieve this task without a need to touch the templates.

In case all declarations are already done, update_stack function will throw an 
ValidationError with a message that nothing has been changed. This is absolutely
okay (except that the design is not) and the script will just ignore this case.

To resolve the function and the environment it uses the stack name where by 
convention all information can be extracted. There is one exception namely
the base stack names. In this case the environment will be set to n/a and 
the function to `base`.

You can as well map function names to a more common name. This can be useful
if you want to group stacks by there product. To achieve this you have just
to adjust the FUNC_MAPS list with corresponding callbacks.

This script here will filter *only* inventory stacks and accordingly set the 
tags for the matching team. So be aware of this settings, before execution.
"""

import argparse
import re
import pprint
import sys
import logging
from typing import Optional, Generator, Callable, Iterable, List, Dict


_log = logging.getLogger(__name__)
_log.setLevel(logging.WARNING)
_default_handler = logging.StreamHandler(stream=sys.stdout)
_error_handler = logging.StreamHandler(stream=sys.stderr)
_error_handler.setLevel(logging.ERROR)
_log.addHandler(_default_handler)
_log.addHandler(_error_handler)

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    _log.fatal('Please ensure you have boto3 installed')
    sys.exit(-1)

_Param = Dict[str, str]
_Tag = Dict[str, str]

# Map some function names extracted from stack name
_func_maps = [
    lambda x: 'matcher' if re.match('^matcher-', x) else x,
    lambda x: 'sink' if re.match('^sink-', x) else x,
    lambda x: 'crowd' if re.match('^crowd-', x) else x,
    lambda x: 'matchbox' if re.match('^matchbox-', x) else x,
    lambda x: 'matchbox' if re.match('^matching-', x) else x,
]

_cf = boto3.client('cloudformation')


def get_stacks(ntoken: Optional[str] = None) -> Generator:
    """Get All Root CloudFormation Stacks From an AWS Account"""
    if ntoken:
        kwargs = dict(NextToken=ntoken)
    else:
        kwargs = {}
    res = _cf.describe_stacks(**kwargs)

    if len(res['Stacks']) <= 0:
        raise StopIteration()

    for s in res['Stacks']:
        # Avoid nested stacks 
        if not s.get('RootId', None):
            yield s

    if res.get('NextToken', None):
        yield from get_stacks(ntoken=res['NextToken'])


def filter_stack(stacks: Iterable, f: Callable) -> None:
    """Filters Stack Based On the Given Filter Condition"""
    for s in stacks:
        if f(s):
            yield s


def prepare_params(params: List[_Param]) -> List[_Param]:
    """Return a List of Given Parameters With UserPreviousValues Enabled"""
    res = []
    for param in params:
        res.append(dict(ParameterKey=param['ParameterKey'],
                        UsePreviousValue=True))
    return res


def update_stack(stackname: str, params: List[_Param], tags: List[_Tag]):
    """Updates Given Stack with Previous Template"""
    try:
        _cf.update_stack(
            StackName=stackname,
            UsePreviousTemplate=True,
            Parameters=params,
            Capabilities=['CAPABILITY_NAMED_IAM'],
            Tags=tags
        )
    except ClientError as err:
        errmsg = str(err)
        if not re.search(errmsg, str(err), re.IGNORECASE):
            raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Updates Tags for CloudFormation Stacks',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-v', '--verbosity', help='Specify verbosity',
                        action='count', default=0)

    args = parser.parse_args()

    print(args.verbosity)

    if args.verbosity >= 2:
        _log.setLevel(logging.DEBUG)
    elif args.verbosity >= 1:
        _log.setLevel(logging.INFO)
    else:
        _log.setLevel(logging.WARNING)

    pp = pprint.PrettyPrinter(indent=2, stream=sys.stdout)

    # filter only for inventory stacks
    sn = re.compile('inventory', re.IGNORECASE)
    resn = lambda x: sn.match(x['StackName'])

    # Extract some useful parts like function and env from stack name
    snext = re.compile('([\w]+)--([\w-]+)--([\w]+)')

    for stack in filter_stack(get_stacks(), resn):
        stackname = stack['StackName']
        snparts = snext.match(stackname)

        if snparts:
            funcname = snparts.group(2)
            env = snparts.group(3)
        else:
            funcname = 'base'
            env = ''

        for fmap in _func_maps:
            funcname = fmap(funcname)

        params = prepare_params(stack.get('Parameters', []))

        _log.info(f'Processing {stackname}')
        _log.debug(f'  Determined function {funcname}')
        _log.debug(f'  Determined environment {env}')
        _log.debug(f'  Determined parameters {pp.pformat(params)}')

        tags = [
            {
                'Key': 'Pillar',
                'Value': 'hs'
            },
            {
                'Key': 'Domain',
                'Value': 'identity'
            },
            {
                'Key': 'Team',
                'Value': 'matching'
            },
            {
                'Key': 'Environment',
                'Value': env if env else 'n/a'
            },
            {
                'Key': 'Function',
                'Value': funcname
            }
        ]

        update_stack(stackname, params, tags)

    sys.exit(0)
