# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society

import pytest
from copy import deepcopy
from decimal import Decimal as D
from fractions import Fraction as F

import utils
import distribution


# === Split ===================================================================

# --- Fixtures ----------------------------------------------------------------

def _generate_fractions(roles, fractions={}):
    # distribution
    if isinstance(roles, list):
        for dist in roles:
            if dist['type'] in fractions:
                continue
            fraction = _generate_split(dist['split'])
            if fraction:
                fractions[dist['type']] = fraction
            _generate_fractions(dist['split'], fractions)
        return
    # rightsholders
    if 'rightsholders' in roles:
        return
    # split
    for key in roles:
        _generate_fractions(roles[key], fractions)


def _generate_split(roles, length=1):
    fractions = {}
    fractions['fraction'] = F(1, length)
    # distribution
    if isinstance(roles, list):
        fractions['distribution'] = roles[0]['type']
        return fractions
    # rightsholders
    if 'rightsholders' in roles:
        return fractions
    # split
    fractions["split"] = {}
    for item in roles:
        split = _generate_split(roles[item], len(roles))
        if split is not None:
            fractions["split"][item] = _generate_split(roles[item], len(roles))
    return fractions


@pytest.fixture
def set_fractions():
    def _set_fractions(role):
        fractions = {}
        _generate_fractions([role], fractions)
        version = utils.convert_version(role['plan'])
        setattr(distribution, f"fractions__{version}", fractions)
        return fractions

    return _set_fractions


@pytest.fixture
def role():
    return {
        'plan': '0.0',
        'type': 'original',
        'creation': 'C00001',
        'utilisation': 'U00001',
        'meta': {},
        'split': {}
    }


# --- Behaviour ---------------------------------------------------------------

def test_split_behaviour_init_unredistributed(set_fractions, role):
    role['split'] = {
        'role': {
            'rightsholders': [
                'licenser',
            ],
        },
    }
    set_fractions(role)
    split = distribution.Split([role], redistribute=False)

    node = split
    assert node.key == 'root'
    assert node.parent is None
    assert node.fraction == 1
    assert node.initial_fraction == 1
    assert node.amount is None
    assert len(node.splits) == 1
    assert len(node.rightsholders) == 0
    assert node.reentry is False
    assert node.redistributed is False
    assert node._meta is None
    assert node._creation is None
    assert node._distribution_plan is None
    assert node._distribution_type is None
    assert node._config['log'] is True
    assert node._config['debug'] is False
    assert node._config['verbose'] is False
    assert node._log == []
    assert 'C00001' in node

    key = 'C00001'
    parent = node
    node = node[key]
    assert node.key == key
    assert node.parent == parent
    assert node.fraction == 1
    assert node.initial_fraction == 1
    assert node.amount is None
    assert len(node.splits) == 1
    assert len(node.rightsholders) == 0
    assert node.reentry is True
    assert node.redistributed is False
    assert node._utilisation == 'U00001'
    assert node._creation == 'C00001'
    assert node._distribution_plan == '0.0'
    assert node._distribution_type == 'original'
    assert not getattr(node, '_config', False)
    assert not getattr(node, '_log', False)
    assert 'role' in node

    key = 'role'
    parent = node
    node = node[key]
    assert node.key == key
    assert node.parent == parent
    assert node.fraction == 1
    assert node.initial_fraction == 1
    assert node.amount is None
    assert len(node.splits) == 0
    assert len(node.rightsholders) == 1
    assert node.reentry is False
    assert node.redistributed is False
    assert node._meta is None
    assert node._creation is None
    assert node._distribution_plan is None
    assert node._distribution_type is None
    assert not getattr(node, '_config', False)
    assert not getattr(node, '_log', False)

    rightsholder = node.rightsholders[0]
    assert rightsholder.licenser == 'licenser'
    assert rightsholder.fraction == 1
    assert rightsholder.amount is None


def test_split_behaviour_init_redistributed(set_fractions, role):
    role['split'] = {
        'role': {
            'rightsholders': [
                'licenser',
            ],
        },
    }
    set_fractions(role)
    split = distribution.Split([role], redistribute=True)

    node = split
    assert node.key == 'root'
    assert node.parent is None
    assert node.fraction == 1
    assert node.initial_fraction == 1
    assert node.amount is None
    assert len(node.splits) == 1
    assert len(node.rightsholders) == 0
    assert node.reentry is False
    assert node.redistributed is False
    assert node._meta is None
    assert node._creation is None
    assert node._distribution_plan is None
    assert node._distribution_type is None
    assert node._config['log'] is True
    assert node._config['debug'] is False
    assert node._config['verbose'] is False
    assert node._log == []
    assert 'C00001' in node

    key = 'C00001'
    parent = node
    node = node[key]
    assert node.key == key
    assert node.parent == parent
    assert node.fraction == 1
    assert node.initial_fraction == 1
    assert node.amount is None
    assert len(node.splits) == 1
    assert len(node.rightsholders) == 0
    assert node.reentry is True
    assert node.redistributed is False
    assert node._utilisation == 'U00001'
    assert node._creation == 'C00001'
    assert node._distribution_plan == '0.0'
    assert node._distribution_type == 'original'
    assert not getattr(node, '_config', False)
    assert not getattr(node, '_log', False)
    assert 'role' in node

    key = 'role'
    parent = node
    node = node[key]
    assert node.key == key
    assert node.parent == parent
    assert node.fraction == 1
    assert node.initial_fraction == 1
    assert node.amount is None
    assert len(node.splits) == 0
    assert len(node.rightsholders) == 1
    assert node.reentry is False
    assert node.redistributed is False
    assert node._meta is None
    assert node._creation is None
    assert node._distribution_plan is None
    assert node._distribution_type is None
    assert not getattr(node, '_config', False)
    assert not getattr(node, '_log', False)

    rightsholder = node.rightsholders[0]
    assert rightsholder.licenser == 'licenser'
    assert rightsholder.fraction == 1
    assert rightsholder.amount is None


def test_split_behaviour_init_assert_key(set_fractions, role):
    role['split'] = {
        'role.invalid': {
            'rightsholders': [],
        },
    }
    set_fractions(role)
    with pytest.raises(AssertionError, match="dot is not allowed"):
        distribution.Split([role])


def test_split_behaviour_init_assert_distribution_only(set_fractions, role):
    dist = role
    dist['split'] = {
        '1': {
            '1-1': {
                'rightsholders': ['licencer'],
            },
            '1-3': {
                'rightsholders': [],
            },
        },
    }
    _dist = deepcopy(dist)
    dist['split']['1']['1-2'] = [deepcopy(_dist)]
    dist['split']['1']['1-2'][0]['split']['1']['1-2'] = []

    set_fractions(role)

    dist['split']['1']['1-2'].append({'no': 'distribution'})
    with pytest.raises(AssertionError, match="not contain only distributions"):
        distribution.Split([role])


def test_split_behaviour_init_assert_fraction_match(set_fractions, role):
    dist = role
    dist['split'] = {
        '1': {
            '1-1': {
                'rightsholders': ['licencer'],
            },
            '1-3': {
                'rightsholders': [],
            },
        },
    }
    _dist = deepcopy(dist)
    dist['split']['1']['1-2'] = [deepcopy(_dist)]
    dist['split']['1']['1-2'][0]['split']['1']['1-2'] = []

    set_fractions(role)

    dist['split']['1']['1-2'][0]['type'] = 'invalid'
    with pytest.raises(AssertionError, match="does not match the type"):
        distribution.Split([role])


def test_split_behaviour_init_assert_fraction_sum(set_fractions, role):
    dist = role
    dist['split'] = {
        '1': {
            '1-1': {
                'rightsholders': ['licencer'],
            },
        },
    }
    _dist = deepcopy(dist)
    dist['split']['1']['1-2'] = [deepcopy(_dist), deepcopy(_dist)]
    dist['split']['1']['1-2'][0]['split']['1']['1-2'] = []
    dist['split']['1']['1-2'][0]['fraction'] = F(1, 2)
    dist['split']['1']['1-2'][1]['split']['1']['1-2'] = []
    dist['split']['1']['1-2'][0]['fraction'] = F(1, 3)
    set_fractions(role)

    with pytest.raises(AssertionError,
                       match="sums of split fractions.* don't equal 1"):
        distribution.Split([role])


def test_split_behaviour_init_assert_split_expected(set_fractions, role):
    role['split'] = {
        '1': {
            '1-1': {
                'rightsholders': [],
            }
        },
    }
    set_fractions(role)
    role['split']['1'] = {'rightsholders': []}
    with pytest.raises(AssertionError,
                       match=r"rightsholders given (.|\s)* split expected"):
        distribution.Split([role])


def test_split_behaviour_init_assert_rightsholder_sum(set_fractions, role):
    role['split'] = {
        '1': {
            'rightsholders': [
                {'licenser': 'licenser1', 'fraction': F(1, 2)},
                {'licenser': 'licenser2', 'fraction': F(1, 3)},
            ],
        },
    }
    set_fractions(role)

    with pytest.raises(AssertionError,
                       match="sums of rightsholder fractions.* don't equal 1"):
        distribution.Split([role])


def test_split_behaviour_contains(set_fractions, role):
    role['split'] = {
        'role1': {
            'rightsholders': [],
        },
        'role2': {
            'rightsholders': [],
        },
        'role3': {
            'rightsholders': [],
        },
    }
    set_fractions(role)
    split = distribution.Split([role])
    node = split['C00001']

    for name in ['role1', 'role2', 'role3']:
        assert name in node
    for name in ['non-role1', 'non-role2', 'non-role3']:
        assert name not in node


def test_split_behaviour_getitem(set_fractions, role):
    role['split'] = {
        'role1': {
            'rightsholders': [],
        },
        'role2': {
            'rightsholders': [],
        },
        'role3': {
            'rightsholders': [],
        },
    }
    set_fractions(role)
    split = distribution.Split([role])
    node = split['C00001']

    for index, name in enumerate(['role1', 'role2', 'role3']):
        assert node[name] == node.splits[index]


def test_split_behaviour_iter(set_fractions, role):
    role['split'] = {
        'role1': {
            'rightsholders': [],
        },
        'role2': {
            'rightsholders': [],
        },
        'role3': {
            'rightsholders': [],
        },
    }
    set_fractions(role)
    split = distribution.Split([role])
    node = split['C00001']

    for item in node:
        assert isinstance(item, distribution.Split)
        assert item.key in role['split']


def test_split_behaviour_str(set_fractions, role):
    role['split'] = {
        'role1': {
            'rightsholders': [],
        },
        'role2': {
            'rightsholders': [],
        },
        'role3': {
            'rightsholders': [],
        },
    }
    set_fractions(role)
    split = distribution.Split([role])
    node = split['C00001']

    for item in node:
        assert f'{item}' in role['split']


def test_split_behaviour_len(set_fractions, role):
    role_1 = role.copy()
    role_1['split'] = {
        'role1': {
            'rightsholders': [],
        },
    }
    set_fractions(role_1)
    split = distribution.Split([role_1])
    node = split['C00001']

    assert len(node) == 1

    role_2 = role.copy()
    role_2['split'] = {
        'role1': {
            'rightsholders': [],
        },
        'role2': {
            'rightsholders': [],
        },
    }
    set_fractions(role_2)
    split = distribution.Split([role_2])
    node = split['C00001']

    assert len(node) == 2

    role_3 = role.copy()
    role_3['split'] = {
        'role1': {
            'rightsholders': [],
        },
        'role2': {
            'rightsholders': [],
        },
        'role3': {
            'rightsholders': [],
        },
    }
    set_fractions(role_3)
    split = distribution.Split([role_3])
    node = split['C00001']

    assert len(node) == 3


# --- Tree --------------------------------------------------------------------

def test_split_tree_root(set_fractions, role):
    role['split'] = {
        'role-1': {
            'role-1-1': {
                'rightsholders': [
                    'licenser',
                ],
            },
            'role-1-2': {
                'rightsholders': [
                    'licenser',
                ],
            },
        },
        'role-2': {
            'role-2-1': {
                'rightsholders': [
                    'licenser',
                ],
            },
            'role-2-2': {
                'rightsholders': [
                    'licenser',
                ],
            },
        },
    }
    set_fractions(role)
    root = distribution.Split([role], redistribute=False)

    for node in [root,
                 root['C00001'],
                 root['C00001']['role-1'],
                 root['C00001']['role-1']['role-1-1'],
                 root['C00001']['role-1']['role-1-2'],
                 root['C00001']['role-2'],
                 root['C00001']['role-2']['role-2-1'],
                 root['C00001']['role-2']['role-2-2']]:
        assert node.root == root
        assert node.root.is_root()

    for node in [root['C00001'],
                 root['C00001']['role-1'],
                 root['C00001']['role-1']['role-1-1'],
                 root['C00001']['role-1']['role-1-2'],
                 root['C00001']['role-2'],
                 root['C00001']['role-2']['role-2-1'],
                 root['C00001']['role-2']['role-2-2']]:
        assert not node.is_root()


def test_split_tree_leaves(set_fractions, role):
    role['split'] = {
        'role-1': {
            'role-1-1': {
                'rightsholders': [
                    'licenser',
                ],
            },
            'role-1-2': {
                'rightsholders': [
                    'licenser',
                ],
            },
        },
        'role-2': {
            'role-2-1': {
                'rightsholders': [
                    'licenser',
                ],
            },
            'role-2-2': {
                'rightsholders': [
                    'licenser',
                ],
            },
        },
    }
    set_fractions(role)
    root = distribution.Split([role], redistribute=False)

    for node in [root, root['C00001']]:
        assert node.leaves == [
            root['C00001']['role-1']['role-1-1'],
            root['C00001']['role-1']['role-1-2'],
            root['C00001']['role-2']['role-2-1'],
            root['C00001']['role-2']['role-2-2']
        ]
    assert root['C00001']['role-1'].leaves == [
        root['C00001']['role-1']['role-1-1'],
        root['C00001']['role-1']['role-1-2'],
    ]
    assert root['C00001']['role-2'].leaves == [
        root['C00001']['role-2']['role-2-1'],
        root['C00001']['role-2']['role-2-2'],
    ]
    for leaf in [root['C00001']['role-1']['role-1-1'],
                 root['C00001']['role-1']['role-1-2'],
                 root['C00001']['role-2']['role-2-1'],
                 root['C00001']['role-2']['role-2-2']]:
        assert leaf.leaves == [leaf]


def test_split_tree_path(set_fractions, role):
    role['split'] = {
        'role-1': {
            'role-1-1': {
                'rightsholders': [
                    'licenser',
                ],
            },
            'role-1-2': {
                'rightsholders': [
                    'licenser',
                ],
            },
        },
        'role-2': {
            'role-2-1': {
                'rightsholders': [
                    'licenser',
                ],
            },
            'role-2-2': {
                'rightsholders': [
                    'licenser',
                ],
            },
        },
    }
    set_fractions(role)
    root = distribution.Split([role], redistribute=False)

    assert root.path == 'root'
    assert root['C00001'].path == 'root.C00001'
    assert root['C00001']['role-1'].path == 'root.C00001.role-1'
    assert root['C00001']['role-2'].path == 'root.C00001.role-2'
    assert (root['C00001']['role-1']['role-1-1'].path
            == 'root.C00001.role-1.role-1-1')
    assert (root['C00001']['role-2']['role-2-1'].path
            == 'root.C00001.role-2.role-2-1')


def test_split_tree_config(set_fractions, role):
    role['split'] = {
        'role-1': {
            'role-1-1': {
                'rightsholders': [
                    'licenser',
                ],
            },
            'role-1-2': {
                'rightsholders': [
                    'licenser',
                ],
            },
        },
        'role-2': {
            'role-2-1': {
                'rightsholders': [
                    'licenser',
                ],
            },
            'role-2-2': {
                'rightsholders': [
                    'licenser',
                ],
            },
        },
    }
    set_fractions(role)
    root = distribution.Split([role], redistribute=False)

    for node in [root,
                 root['C00001'],
                 root['C00001']['role-1'],
                 root['C00001']['role-1']['role-1-1'],
                 root['C00001']['role-1']['role-1-2'],
                 root['C00001']['role-2'],
                 root['C00001']['role-2']['role-2-1'],
                 root['C00001']['role-2']['role-2-2']]:
        assert node.config == root._config

    for node in [root['C00001'],
                 root['C00001']['role-1'],
                 root['C00001']['role-1']['role-1-1'],
                 root['C00001']['role-1']['role-1-2'],
                 root['C00001']['role-2'],
                 root['C00001']['role-2']['role-2-1'],
                 root['C00001']['role-2']['role-2-2']]:
        assert not getattr(node, '_config', False)


def test_split_tree_log(set_fractions, role):
    role['split'] = {
        'role-1': {
            'role-1-1': {
                'rightsholders': [
                    'licenser',
                ],
            },
            'role-1-2': {
                'rightsholders': [
                    'licenser',
                ],
            },
        },
        'role-2': {
            'role-2-1': {
                'rightsholders': [
                    'licenser',
                ],
            },
            'role-2-2': {
                'rightsholders': [
                    'licenser',
                ],
            },
        },
    }
    set_fractions(role)
    root = distribution.Split([role], redistribute=False)

    for node in [root,
                 root['C00001'],
                 root['C00001']['role-1'],
                 root['C00001']['role-1']['role-1-1'],
                 root['C00001']['role-1']['role-1-2'],
                 root['C00001']['role-2'],
                 root['C00001']['role-2']['role-2-1'],
                 root['C00001']['role-2']['role-2-2']]:
        assert node.log == root._log

    for node in [root['C00001'],
                 root['C00001']['role-1'],
                 root['C00001']['role-1']['role-1-1'],
                 root['C00001']['role-1']['role-1-2'],
                 root['C00001']['role-2'],
                 root['C00001']['role-2']['role-2-1'],
                 root['C00001']['role-2']['role-2-2']]:
        assert not getattr(node, '_log', False)


# --- Domain ------------------------------------------------------------------

def test_split_domain_licenser_shares(set_fractions, role):
    dist = role
    dist['split'] = {
        '1': {
            '1-1': {
                '1-1-1': {
                    'rightsholders': ['licenser1'],
                },
                '1-1-2': {
                    'rightsholders': ['licenser2'],
                },
            },
            '1-2': {
                'rightsholders': [],
            },
        },
        '2': {
            '2-1': {
                'rightsholders': [
                    {'licenser': 'licenser1', 'fraction': F(3, 4)},
                    {'licenser': 'licenser2', 'fraction': F(1, 4)},
                ],
            },
            '2-2': {
                'rightsholders': [],
            },
        },
    }
    _dist = deepcopy(dist)
    dist['split']['1']['1-3'] = [deepcopy(_dist)]
    dist['split']['1']['1-3'][0]['creation'] = 'C00002'
    dist['split']['1']['1-3'][0]['split']['1']['1-3'] = []

    set_fractions(dist)
    split = distribution.Split([dist], redistribute=True)
    amount = D('100000')
    shares = split.distribute(amount)

    for share in shares:
        assert 'licenser' in share
        assert 'amount' in share
        assert 'meta' in share

    assert len(shares) == 2 * 4
    assert len([share
                for share in shares
                if share['creation'] == 'C00001']) == 4
    assert len([share
                for share in shares
                if share['creation'] == 'C00002']) == 4

    assert sum([share['amount']
                for share in shares]) == amount
    assert sum([share['amount']
                for share in shares
                if share['licenser'] == 'licenser1']
               ) == D(12500) + D(37500) + D(6250) + D(9375)
    assert sum([share['amount']
                for share in shares
                if share['licenser'] == 'licenser2']
               ) == D(12500) + D(12500) + D(6250) + D(3125)


def test_split_domain_redistributed_roles(set_fractions, role):
    role['split'] = {
        '1': {
            '1-1': {
                '1-1-1': {
                    'rightsholders': ['licenser'],
                },
                '1-1-2': {
                    'rightsholders': ['licenser'],
                },
            },
            '1-2': {
                'rightsholders': [],
            },
        },
        '2': {
            '2-1': {
                'rightsholders': ['licenser'],
            },
            '2-2': {
                'rightsholders': [],
            },
        },
    }
    set_fractions(role)
    root = distribution.Split([role], redistribute=True)

    for node in [root,
                 root['C00001'],
                 root['C00001']['1'],
                 root['C00001']['2']]:
        assert set(node.redistributed_roles) == set()

    for node in [root['C00001']['1']['1-1'],
                 root['C00001']['1']['1-1']['1-1-1'],
                 root['C00001']['1']['1-1']['1-1-2']]:
        assert set(node.redistributed_roles) == set([
            'root.C00001.1.1-1',
        ])

    node = root['C00001']['1']['1-2']
    assert set(node.redistributed_roles) == set([
        "root.C00001.1.1-2",
    ])

    node = root['C00001']['2']['2-1']
    assert set(node.redistributed_roles) == set([
        "root.C00001.2.2-1",
    ])

    node = root['C00001']['2']['2-2']
    assert set(node.redistributed_roles) == set([
        "root.C00001.2.2-2",
    ])


def test_split_domain_distribution(set_fractions, role):
    role['split'] = {
        '1': {
            '1-1': {
                'rightsholders': [],
            },
        },
        '2': {
            '2-1': {
                'rightsholders': ['licenser'],
            },
            '2-2': {
                'rightsholders': [],
            },
            '2-3': {
                'rightsholders': [],
            },
        },
    }
    set_fractions(role)
    root = distribution.Split([role], redistribute=False)

    node = root
    assert node.distribution == {'C00001': F(1, 1)}
    node = root['C00001']
    assert node.distribution == {'1': F(1, 2), '2': F(1, 2)}
    node = root['C00001']['1']
    assert node.distribution == {'1-1': F(1, 1)}
    node = root['C00001']['2']
    assert node.distribution == {'2-1': F(1, 3),
                                 '2-2': F(1, 3),
                                 '2-3': F(1, 3)}

    for node in [root['C00001']['1']['1-1'],
                 root['C00001']['2']['2-1'],
                 root['C00001']['2']['2-2'],
                 root['C00001']['2']['2-3']]:
        assert node.distribution == {}

    root.redistribute()

    node = root
    assert node.distribution == {'C00001': F(1, 1)}
    node = root['C00001']
    assert node.distribution == {'1': F(0), '2': F(1)}
    node = root['C00001']['1']
    assert node.distribution == {'1-1': F(0)}
    node = root['C00001']['2']
    assert node.distribution == {'2-1': F(1),
                                 '2-2': F(0),
                                 '2-3': F(0)}

    for node in [root['C00001']['1']['1-1'],
                 root['C00001']['2']['2-1'],
                 root['C00001']['2']['2-2'],
                 root['C00001']['2']['2-3']]:
        assert node.distribution == {}


def test_split_domain_fraction_sum(set_fractions, role):
    role['split'] = {
        '1': {
            '1-1': {
                'rightsholders': [],
            },
        },
        '2': {
            '2-1': {
                'rightsholders': [
                    'licenser1',
                    'licenser2',
                ],
            },
            '2-2': {
                'rightsholders': [],
            },
            '2-3': {
                'rightsholders': [],
            },
        },
    }
    set_fractions(role)
    root = distribution.Split([role], redistribute=False)

    for node in [root,
                 root['C00001'],
                 root['C00001']['1'],
                 root['C00001']['1']['1-1'],
                 root['C00001']['2'],
                 root['C00001']['2']['2-1'],
                 root['C00001']['2']['2-2'],
                 root['C00001']['2']['2-3']]:
        assert node.fraction_sum == (
            sum(split.fraction for split in node.splits)
            + sum(rightsholder.fraction for rightsholder in node.rightsholders)
        )

    node = root['C00001']['2']
    node['2-1'].fraction = F(1, 100)
    node['2-2'].fraction = F(2, 100)
    node['2-3'].fraction = F(3, 100)
    assert node.fraction_sum == F(6, 100)

    node = root['C00001']['2']['2-1']
    node.rightsholders[0].fraction = F(100, 1)
    node.rightsholders[1].fraction = F(100, 2)
    assert node.fraction_sum == F(150, 1)


def test_split_domain_all_rightsholders(set_fractions, role):
    role['split'] = {
        '1': {
            '1-1': {
                'rightsholders': [],
            },
        },
        '2': {
            '2-1': {
                'rightsholders': [
                    'licenser1',
                    'licenser2',
                ],
            },
            '2-2': {
                'rightsholders': [
                    'licenser3',
                    'licenser4',
                ],
            },
            '2-3': {
                'rightsholders': [],
            },
        },
    }
    set_fractions(role)
    root = distribution.Split([role], redistribute=False)

    for node in [root['C00001']['1'],
                 root['C00001']['1']['1-1'],
                 root['C00001']['2']['2-3']]:
        assert node.all_rightsholders == []

    for node in [root,
                 root['C00001'],
                 root['C00001']['2']]:
        assert [rh.licenser for rh in node.all_rightsholders] == [
            'licenser1', 'licenser2', 'licenser3', 'licenser4',
        ]

    node = root['C00001']['2']['2-1']
    assert [rh.licenser for rh in node.all_rightsholders] == [
        'licenser1', 'licenser2'
    ]
    node = root['C00001']['2']['2-2']
    assert [rh.licenser for rh in node.all_rightsholders] == [
        'licenser3', 'licenser4'
    ]


def test_split_domain_meta(set_fractions, role):
    dist = role
    dist['split'] = {
        '1': {
            '1-1': {
                'rightsholders': [],
            },
        },
    }
    _dist = deepcopy(dist)
    dist['meta']['test'] = 1
    dist['split']['1']['1-2'] = [deepcopy(_dist)]

    dist = dist['split']['1']['1-2'][0]
    dist['meta']['test'] = 2
    dist['split']['1']['1-2'] = [deepcopy(_dist)]

    dist = dist['split']['1']['1-2'][0]
    dist['meta']['test'] = 3
    dist['split']['1']['1-2'] = []

    set_fractions(role)
    root = distribution.Split([role], redistribute=False)
    dist1 = root['C00001']
    dist2 = dist1['1']['1-2']['C00001']
    dist3 = dist2['1']['1-2']['C00001']

    assert root.meta is None

    for node in [dist1,
                 dist1['1'],
                 dist1['1']['1-1'],
                 dist1['1']['1-2']]:
        assert node.meta['test'] == 1

    for node in [dist2,
                 dist2['1'],
                 dist2['1']['1-1'],
                 dist2['1']['1-2']]:
        assert node.meta['test'] == 2

    for node in [dist3,
                 dist3['1'],
                 dist3['1']['1-1'],
                 dist3['1']['1-2']]:
        assert node.meta['test'] == 3


def test_split_domain_creation(set_fractions, role):
    dist = role
    dist['split'] = {
        '1': {
            '1-1': {
                'rightsholders': [],
            },
        },
    }
    _dist = deepcopy(dist)
    dist['split']['1']['1-2'] = [deepcopy(_dist)]

    dist = dist['split']['1']['1-2'][0]
    dist['creation'] = 'C00002'
    dist['split']['1']['1-2'] = [deepcopy(_dist)]

    dist = dist['split']['1']['1-2'][0]
    dist['creation'] = 'C00003'
    dist['split']['1']['1-2'] = []

    set_fractions(role)
    root = distribution.Split([role], redistribute=False)
    dist1 = root['C00001']
    dist2 = dist1['1']['1-2']['C00002']
    dist3 = dist2['1']['1-2']['C00003']

    assert root.creation is None

    for node in [dist1,
                 dist1['1'],
                 dist1['1']['1-1'],
                 dist1['1']['1-2']]:
        assert node.creation == 'C00001'

    for node in [dist2,
                 dist2['1'],
                 dist2['1']['1-1'],
                 dist2['1']['1-2']]:
        assert node.creation == 'C00002'

    for node in [dist3,
                 dist3['1'],
                 dist3['1']['1-1'],
                 dist3['1']['1-2']]:
        assert node.creation == 'C00003'


def test_split_domain_utilisation(set_fractions, role):
    dist = role
    dist['split'] = {
        '1': {
            '1-1': {
                'rightsholders': [],
            },
        },
    }
    _dist = deepcopy(dist)
    dist['split']['1']['1-2'] = [deepcopy(_dist)]

    dist = dist['split']['1']['1-2'][0]
    dist['utilisation'] = 'U00002'
    dist['split']['1']['1-2'] = [deepcopy(_dist)]

    dist = dist['split']['1']['1-2'][0]
    dist['utilisation'] = 'U00003'
    dist['split']['1']['1-2'] = []

    set_fractions(role)
    root = distribution.Split([role], redistribute=False)
    dist1 = root['C00001']
    dist2 = dist1['1']['1-2']['C00001']
    dist3 = dist2['1']['1-2']['C00001']

    assert root.utilisation is None

    for node in [dist1,
                 dist1['1'],
                 dist1['1']['1-1'],
                 dist1['1']['1-2']]:
        assert node.utilisation == 'U00001'

    for node in [dist2,
                 dist2['1'],
                 dist2['1']['1-1'],
                 dist2['1']['1-2']]:
        assert node.utilisation == 'U00002'

    for node in [dist3,
                 dist3['1'],
                 dist3['1']['1-1'],
                 dist3['1']['1-2']]:
        assert node.utilisation == 'U00003'


def test_split_domain_distribution_plan(set_fractions, role):
    dist = role
    dist['split'] = {
        '1': {
            '1-1': {
                'rightsholders': [],
            },
        },
    }
    _dist = deepcopy(dist)
    dist['plan'] = '0.0.1'
    dist['split']['1']['1-2'] = [deepcopy(_dist)]

    dist = dist['split']['1']['1-2'][0]
    dist['plan'] = '0.0.2'
    dist['split']['1']['1-2'] = [deepcopy(_dist)]

    dist = dist['split']['1']['1-2'][0]
    dist['plan'] = '0.0.3'
    dist['split']['1']['1-2'] = []

    fractions = set_fractions(role)
    distribution.fractions__0_0_1 = fractions
    distribution.fractions__0_0_2 = fractions
    distribution.fractions__0_0_3 = fractions

    root = distribution.Split([role], redistribute=False)
    dist1 = root['C00001']
    dist2 = dist1['1']['1-2']['C00001']
    dist3 = dist2['1']['1-2']['C00001']

    assert root.distribution_plan is None

    for node in [dist1,
                 dist1['1'],
                 dist1['1']['1-1'],
                 dist1['1']['1-2']]:
        assert node.distribution_plan == '0.0.1'

    for node in [dist2,
                 dist2['1'],
                 dist2['1']['1-1'],
                 dist2['1']['1-2']]:
        assert node.distribution_plan == '0.0.2'

    for node in [dist3,
                 dist3['1'],
                 dist3['1']['1-1'],
                 dist3['1']['1-2']]:
        assert node.distribution_plan == '0.0.3'


def test_split_domain_distribution_type(set_fractions, role):
    dist = role
    dist['split'] = {
        '1': {
            '1-1': {
                'rightsholders': [],
            },
        },
    }
    _dist = deepcopy(dist)
    dist['type'] = 'type1'
    dist['split']['1']['1-2'] = [deepcopy(_dist)]

    dist = dist['split']['1']['1-2'][0]
    dist['type'] = 'type2'
    dist['split']['1']['1-2'] = [deepcopy(_dist)]

    dist = dist['split']['1']['1-2'][0]
    dist['type'] = 'type3'
    dist['split']['1']['1-2'] = [deepcopy(_dist)]

    set_fractions(role)
    root = distribution.Split([role], redistribute=False)
    dist1 = root['C00001']
    dist2 = dist1['1']['1-2']['C00001']
    dist3 = dist2['1']['1-2']['C00001']

    assert root.distribution_type is None

    for node in [dist1,
                 dist1['1'],
                 dist1['1']['1-1'],
                 dist1['1']['1-2']]:
        assert node.distribution_type == 'type1'

    for node in [dist2,
                 dist2['1'],
                 dist2['1']['1-1'],
                 dist2['1']['1-2']]:
        assert node.distribution_type == 'type2'

    for node in [dist3,
                 dist3['1'],
                 dist3['1']['1-1'],
                 dist3['1']['1-2']]:
        assert node.distribution_type == 'type3'


def test_split_domain_contains_rightsholders(set_fractions, role):
    dist = role
    dist['split'] = {
        '1': {
            '1-1': {
                'rightsholders': ['licencer'],
            },
            '1-3': {
                'rightsholders': [],
            },
        },
    }
    _dist = deepcopy(dist)
    dist['split']['1']['1-2'] = [deepcopy(_dist)]

    dist = dist['split']['1']['1-2'][0]
    dist['split']['1']['1-2'] = [deepcopy(_dist)]

    dist = dist['split']['1']['1-2'][0]
    dist['split']['1']['1-2'] = []

    set_fractions(role)
    root = distribution.Split([role], redistribute=False)
    dist1 = root['C00001']
    dist2 = dist1['1']['1-2']['C00001']
    dist3 = dist2['1']['1-2']['C00001']

    for node in [root,
                 dist1,
                 dist1['1'],
                 dist1['1']['1-1'],
                 dist1['1']['1-2'],
                 dist2,
                 dist2['1'],
                 dist2['1']['1-1'],
                 dist2['1']['1-2'],
                 dist3,
                 dist3['1'],
                 dist3['1']['1-1']]:
        assert node.contains_rightsholders()

    for node in [dist1['1']['1-3'],
                 dist2['1']['1-3'],
                 dist3['1']['1-2'],
                 dist3['1']['1-3']]:
        assert not node.contains_rightsholders()


# --- Actions -----------------------------------------------------------------

def test_split_actions_redistribute(set_fractions, role):
    role['split'] = {
        '1': {
            '1-1': {
                'rightsholders': [],
            },
        },
        '2': {
            '2-1': {
                'rightsholders': [
                    'licenser1',
                    'licenser2',
                ],
            },
            '2-2': {
                'rightsholders': [],
            },
            '2-3': {
                'rightsholders': [],
            },
        },
    }
    set_fractions(role)
    root = distribution.Split([role], redistribute=True)

    for node in [root['C00001']['1'],
                 root['C00001']['1']['1-1'],
                 root['C00001']['2']['2-2'],
                 root['C00001']['2']['2-3']]:
        assert node.fraction == 0

    for node in [root,
                 root['C00001'],
                 root['C00001']['2'],
                 root['C00001']['2']['2-1']]:
        assert node.fraction == 1


def test_split_actions_redistribute_assert_fraction_sum(set_fractions, role):
    role['split'] = {
        '1': {
            '1-1': {
                'rightsholders': ['licencer'],
            },
            '1-2': {
                'rightsholders': [],
            },
        },
    }
    set_fractions(role)
    split = distribution.Split([role], redistribute=False)

    split['C00001']['1']['1-1'].fraction = F(1, 2)
    split['C00001']['1']['1-2'].fraction = F(1, 3)
    with pytest.raises(AssertionError,
                       match="sums of split fractions.* don't equal 0 or 1"):
        split.redistribute()


def test_split_actions_distribute(set_fractions, role):
    role['split'] = {
        '1': {
            '1-1': {
                'rightsholders': [],
            },
        },
        '2': {
            '2-1': {
                'rightsholders': [
                    'licenser1',
                    'licenser2',
                ],
            },
            '2-2': {
                'rightsholders': [],
            },
            '2-3': {
                'rightsholders': [],
            },
        },
    }
    set_fractions(role)
    root = distribution.Split([role], redistribute=True)
    root.distribute(D(100))

    for node in [root['C00001']['1'],
                 root['C00001']['1']['1-1'],
                 root['C00001']['2']['2-2'],
                 root['C00001']['2']['2-3']]:
        assert not node.amount

    for node in [root,
                 root['C00001'],
                 root['C00001']['2'],
                 root['C00001']['2']['2-1']]:
        assert node.amount == D(100)


def test_split_actions_distribute_assert_rightsholders(set_fractions, role):
    role['split'] = {
        '1': {
            'rightsholders': [],
        }
    }
    set_fractions(role)
    split = distribution.Split([role])

    with pytest.raises(AssertionError,
                       match="contain no rightsholders"):
        split.distribute(D(1))


def test_split_actions_distribute_assert_rightsholder_amount_sum(
        set_fractions, role, mocker):
    role['split'] = {
        '1': {
            'rightsholders': ['licenser1'],
        }
    }
    set_fractions(role)
    split = distribution.Split([role])

    def _distribute(self):
        self.amount = 10

    mocker.patch('distribution.Split._distribute', _distribute)
    with pytest.raises(AssertionError,
                       match="sum of rightsholder amounts not equal"):
        split.distribute(D(1))


def test_split_actions_distribute_assert_share_amount_sum(
        set_fractions, role, mocker):
    role['split'] = {
        '1': {
            'rightsholders': ['licenser1'],
        }
    }
    set_fractions(role)
    split = distribution.Split([role])

    mocker.patch('distribution.Split.licenser_shares', [{'amount': D(100)}])
    with pytest.raises(AssertionError,
                       match="sum of licenser share amounts not equal"):
        split.distribute(D(1))
